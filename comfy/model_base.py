import torch
from comfy.ldm.modules.diffusionmodules.openaimodel import UNetModel
from comfy.ldm.modules.encoders.noise_aug_modules import CLIPEmbeddingNoiseAugmentation
from comfy.ldm.modules.diffusionmodules.openaimodel import Timestep
import comfy.model_management
import comfy.conds
import comfy.ops
from enum import Enum
import contextlib
from . import utils


class ModelType(Enum):
    EPS = 1
    V_PREDICTION = 2
    V_PREDICTION_EDM = 3


from comfy.model_sampling import EPS, V_PREDICTION, ModelSamplingDiscrete, ModelSamplingContinuousEDM


def model_sampling(model_config, model_type):
    s = ModelSamplingDiscrete

    if model_type == ModelType.EPS:
        c = EPS
    elif model_type == ModelType.V_PREDICTION:
        c = V_PREDICTION
    elif model_type == ModelType.V_PREDICTION_EDM:
        c = V_PREDICTION
        s = ModelSamplingContinuousEDM

    class ModelSampling(s, c):
        pass

    return ModelSampling(model_config)


class BaseModel(torch.nn.Module):
    def __init__(self, model_config, model_type=ModelType.EPS, device=None):
        super().__init__()

        unet_config = model_config.unet_config
        self.latent_format = model_config.latent_format
        self.model_config = model_config
        self.manual_cast_dtype = model_config.manual_cast_dtype

        if not unet_config.get("disable_unet_model_creation", False):
            if self.manual_cast_dtype is not None:
                operations = comfy.ops.manual_cast
            else:
                operations = comfy.ops.disable_weight_init
            self.diffusion_model = UNetModel(**unet_config, device=device, operations=operations)
        self.model_type = model_type
        self.model_sampling = model_sampling(model_config, model_type)

        self.adm_channels = unet_config.get("adm_in_channels", None)
        if self.adm_channels is None:
            self.adm_channels = 0
        self.inpaint_model = False
        print("model_type", model_type.name)
        print("adm", self.adm_channels)

    def apply_model(self, x, t, c_concat=None, c_crossattn=None, control=None, transformer_options={},
                    **kwargs):
        sigma = t
        xc = self.model_sampling.calculate_input(sigma, x)
        if c_concat is not None:
            xc = torch.cat([xc] + [c_concat], dim=1)

        context = c_crossattn
        dtype = self.get_dtype()

        if self.manual_cast_dtype is not None:
            dtype = self.manual_cast_dtype

        xc = xc.to(dtype)
        t = self.model_sampling.timestep(t).float()
        context = context.to(dtype)
        extra_conds = {}
        for o in kwargs:
            extra = kwargs[o]
            if hasattr(extra, "to"):
                extra = extra.to(dtype)
            extra_conds[o] = extra

        model_output = self.diffusion_model(xc, t, context=context, control=control,
                                            transformer_options=transformer_options, **extra_conds).float()
        return self.model_sampling.calculate_denoised(sigma, model_output, x)

    def get_dtype(self):
        return self.diffusion_model.dtype

    def is_adm(self):
        return self.adm_channels > 0

    def encode_adm(self, **kwargs):
        return None

    def extra_conds(self, **kwargs):
        out = {}
        if self.inpaint_model:
            concat_keys = ("mask", "masked_image")
            cond_concat = []
            denoise_mask = kwargs.get("denoise_mask", None)
            latent_image = kwargs.get("latent_image", None)
            noise = kwargs.get("noise", None)
            device = kwargs["device"]

            def blank_inpaint_image_like(latent_image):
                blank_image = torch.ones_like(latent_image)
                # these are the values for "zero" in pixel space translated to latent space
                blank_image[:, 0] *= 0.8223
                blank_image[:, 1] *= -0.6876
                blank_image[:, 2] *= 0.6364
                blank_image[:, 3] *= 0.1380
                return blank_image

            for ck in concat_keys:
                if denoise_mask is not None:
                    if ck == "mask":
                        cond_concat.append(denoise_mask[:, :1].to(device))
                    elif ck == "masked_image":
                        cond_concat.append(latent_image.to(
                            device))  #NOTE: the latent_image should be masked by the mask in pixel space
                else:
                    if ck == "mask":
                        cond_concat.append(torch.ones_like(noise)[:, :1])
                    elif ck == "masked_image":
                        cond_concat.append(blank_inpaint_image_like(noise))
            data = torch.cat(cond_concat, dim=1)
            out['c_concat'] = comfy.conds.CONDNoiseShape(data)

        adm = self.encode_adm(**kwargs)
        if adm is not None:
            out['y'] = comfy.conds.CONDRegular(adm)

        cross_attn = kwargs.get("cross_attn", None)
        if cross_attn is not None:
            out['c_crossattn'] = comfy.conds.CONDCrossAttn(cross_attn)

        return out

    def load_model_weights(self, sd, unet_prefix=""):
        to_load = {}
        keys = list(sd.keys())
        for k in keys:
            if k.startswith(unet_prefix):
                to_load[k[len(unet_prefix):]] = sd.pop(k)

        to_load = self.model_config.process_unet_state_dict(to_load)
        m, u = self.diffusion_model.load_state_dict(to_load, strict=False)
        if len(m) > 0:
            print("unet missing:", m)

        if len(u) > 0:
            print("unet unexpected:", u)
        del to_load
        return self

    def process_latent_in(self, latent):
        return self.latent_format.process_in(latent)

    def process_latent_out(self, latent):
        return self.latent_format.process_out(latent)

    def state_dict_for_saving(self, clip_state_dict, vae_state_dict):
        clip_state_dict = self.model_config.process_clip_state_dict_for_saving(clip_state_dict)
        unet_state_dict = self.diffusion_model.state_dict()
        unet_state_dict = self.model_config.process_unet_state_dict_for_saving(unet_state_dict)
        vae_state_dict = self.model_config.process_vae_state_dict_for_saving(vae_state_dict)
        if self.get_dtype() == torch.float16:
            clip_state_dict = utils.convert_sd_to(clip_state_dict, torch.float16)
            vae_state_dict = utils.convert_sd_to(vae_state_dict, torch.float16)

        if self.model_type == ModelType.V_PREDICTION:
            unet_state_dict["v_pred"] = torch.tensor([])

        return {**unet_state_dict, **vae_state_dict, **clip_state_dict}

    def set_inpaint(self):
        self.inpaint_model = True

    def memory_required(self, input_shape):
        if comfy.model_management.xformers_enabled(
        ) or comfy.model_management.pytorch_attention_flash_attention():
            dtype = self.get_dtype()
            if self.manual_cast_dtype is not None:
                dtype = self.manual_cast_dtype
            #TODO: this needs to be tweaked
            area = input_shape[0]*input_shape[2]*input_shape[3]
            return (area*comfy.model_management.dtype_size(dtype)/50)*(1024*1024)
        else:
            #TODO: this formula might be too aggressive since I tweaked the sub-quad and split algorithms to use less memory.
            area = input_shape[0]*input_shape[2]*input_shape[3]
            return (((area*0.6)/0.9) + 1024)*(1024*1024)


def unclip_adm(unclip_conditioning, device, noise_augmentor, noise_augment_merge=0.0):
    adm_inputs = []
    weights = []
    noise_aug = []
    for unclip_cond in unclip_conditioning:
        for adm_cond in unclip_cond["clip_vision_output"].image_embeds:
            weight = unclip_cond["strength"]
            noise_augment = unclip_cond["noise_augmentation"]
            noise_level = round((noise_augmentor.max_noise_level - 1)*noise_augment)
            c_adm, noise_level_emb = noise_augmentor(adm_cond.to(device),
                                                     noise_level=torch.tensor([noise_level], device=device))
            adm_out = torch.cat((c_adm, noise_level_emb), 1)*weight
            weights.append(weight)
            noise_aug.append(noise_augment)
            adm_inputs.append(adm_out)

    if len(noise_aug) > 1:
        adm_out = torch.stack(adm_inputs).sum(0)
        noise_augment = noise_augment_merge
        noise_level = round((noise_augmentor.max_noise_level - 1)*noise_augment)
        c_adm, noise_level_emb = noise_augmentor(adm_out[:, :noise_augmentor.time_embed.dim],
                                                 noise_level=torch.tensor([noise_level], device=device))
        adm_out = torch.cat((c_adm, noise_level_emb), 1)

    return adm_out


class SD21UNCLIP(BaseModel):
    def __init__(self, model_config, noise_aug_config, model_type=ModelType.V_PREDICTION, device=None):
        super().__init__(model_config, model_type, device=device)
        self.noise_augmentor = CLIPEmbeddingNoiseAugmentation(**noise_aug_config)

    def encode_adm(self, **kwargs):
        unclip_conditioning = kwargs.get("unclip_conditioning", None)
        device = kwargs["device"]
        if unclip_conditioning is None:
            return torch.zeros((1, self.adm_channels))
        else:
            return unclip_adm(unclip_conditioning, device, self.noise_augmentor,
                              kwargs.get("unclip_noise_augment_merge", 0.05))


def sdxl_pooled(args, noise_augmentor):
    if "unclip_conditioning" in args:
        return unclip_adm(args.get("unclip_conditioning", None), args["device"], noise_augmentor)[:, :1280]
    else:
        return args["pooled_output"]


class SDXLRefiner(BaseModel):
    def __init__(self, model_config, model_type=ModelType.EPS, device=None):
        super().__init__(model_config, model_type, device=device)
        self.embedder = Timestep(256)
        self.noise_augmentor = CLIPEmbeddingNoiseAugmentation(
            **{
                "noise_schedule_config": {
                    "timesteps": 1000,
                    "beta_schedule": "squaredcos_cap_v2"
                },
                "timestep_dim": 1280
            })

    def encode_adm(self, **kwargs):
        clip_pooled = sdxl_pooled(kwargs, self.noise_augmentor)
        width = kwargs.get("width", 768)
        height = kwargs.get("height", 768)
        crop_w = kwargs.get("crop_w", 0)
        crop_h = kwargs.get("crop_h", 0)

        if kwargs.get("prompt_type", "") == "negative":
            aesthetic_score = kwargs.get("aesthetic_score", 2.5)
        else:
            aesthetic_score = kwargs.get("aesthetic_score", 6)

        out = []
        out.append(self.embedder(torch.Tensor([height])))
        out.append(self.embedder(torch.Tensor([width])))
        out.append(self.embedder(torch.Tensor([crop_h])))
        out.append(self.embedder(torch.Tensor([crop_w])))
        out.append(self.embedder(torch.Tensor([aesthetic_score])))
        flat = torch.flatten(torch.cat(out)).unsqueeze(dim=0).repeat(clip_pooled.shape[0], 1)
        return torch.cat((clip_pooled.to(flat.device), flat), dim=1)


class SDXL(BaseModel):
    def __init__(self, model_config, model_type=ModelType.EPS, device=None):
        super().__init__(model_config, model_type, device=device)
        self.embedder = Timestep(256)
        self.noise_augmentor = CLIPEmbeddingNoiseAugmentation(
            **{
                "noise_schedule_config": {
                    "timesteps": 1000,
                    "beta_schedule": "squaredcos_cap_v2"
                },
                "timestep_dim": 1280
            })

    def encode_adm(self, **kwargs):
        clip_pooled = sdxl_pooled(kwargs, self.noise_augmentor)
        width = kwargs.get("width", 768)
        height = kwargs.get("height", 768)
        crop_w = kwargs.get("crop_w", 0)
        crop_h = kwargs.get("crop_h", 0)
        target_width = kwargs.get("target_width", width)
        target_height = kwargs.get("target_height", height)

        out = []
        out.append(self.embedder(torch.Tensor([height])))
        out.append(self.embedder(torch.Tensor([width])))
        out.append(self.embedder(torch.Tensor([crop_h])))
        out.append(self.embedder(torch.Tensor([crop_w])))
        out.append(self.embedder(torch.Tensor([target_height])))
        out.append(self.embedder(torch.Tensor([target_width])))
        flat = torch.flatten(torch.cat(out)).unsqueeze(dim=0).repeat(clip_pooled.shape[0], 1)
        return torch.cat((clip_pooled.to(flat.device), flat), dim=1)


class SVD_img2vid(BaseModel):
    def __init__(self, model_config, model_type=ModelType.V_PREDICTION_EDM, device=None):
        super().__init__(model_config, model_type, device=device)
        self.embedder = Timestep(256)

    def encode_adm(self, **kwargs):
        fps_id = kwargs.get("fps", 6) - 1
        motion_bucket_id = kwargs.get("motion_bucket_id", 127)
        augmentation = kwargs.get("augmentation_level", 0)

        out = []
        out.append(self.embedder(torch.Tensor([fps_id])))
        out.append(self.embedder(torch.Tensor([motion_bucket_id])))
        out.append(self.embedder(torch.Tensor([augmentation])))

        flat = torch.flatten(torch.cat(out)).unsqueeze(dim=0)
        return flat

    def extra_conds(self, **kwargs):
        out = {}
        adm = self.encode_adm(**kwargs)
        if adm is not None:
            out['y'] = comfy.conds.CONDRegular(adm)

        latent_image = kwargs.get("concat_latent_image", None)
        noise = kwargs.get("noise", None)
        device = kwargs["device"]

        if latent_image is None:
            latent_image = torch.zeros_like(noise)

        if latent_image.shape[1:] != noise.shape[1:]:
            latent_image = utils.common_upscale(latent_image, noise.shape[-1], noise.shape[-2], "bilinear",
                                                "center")

        latent_image = utils.resize_to_batch_size(latent_image, noise.shape[0])

        out['c_concat'] = comfy.conds.CONDNoiseShape(latent_image)

        cross_attn = kwargs.get("cross_attn", None)
        if cross_attn is not None:
            out['c_crossattn'] = comfy.conds.CONDCrossAttn(cross_attn)

        if "time_conditioning" in kwargs:
            out["time_context"] = comfy.conds.CONDCrossAttn(kwargs["time_conditioning"])

        out['image_only_indicator'] = comfy.conds.CONDConstant(torch.zeros((1, ), device=device))
        out['num_video_frames'] = comfy.conds.CONDConstant(noise.shape[0])
        return out


class Stable_Zero123(BaseModel):
    def __init__(self, model_config, model_type=ModelType.EPS, device=None, cc_projection_weight=None,
                 cc_projection_bias=None):
        super().__init__(model_config, model_type, device=device)
        self.cc_projection = comfy.ops.manual_cast.Linear(cc_projection_weight.shape[1],
                                                          cc_projection_weight.shape[0],
                                                          dtype=self.get_dtype(), device=device)
        self.cc_projection.weight.copy_(cc_projection_weight)
        self.cc_projection.bias.copy_(cc_projection_bias)

    def extra_conds(self, **kwargs):
        out = {}

        latent_image = kwargs.get("concat_latent_image", None)
        noise = kwargs.get("noise", None)

        if latent_image is None:
            latent_image = torch.zeros_like(noise)

        if latent_image.shape[1:] != noise.shape[1:]:
            latent_image = utils.common_upscale(latent_image, noise.shape[-1], noise.shape[-2], "bilinear",
                                                "center")

        latent_image = utils.resize_to_batch_size(latent_image, noise.shape[0])

        out['c_concat'] = comfy.conds.CONDNoiseShape(latent_image)

        cross_attn = kwargs.get("cross_attn", None)
        if cross_attn is not None:
            if cross_attn.shape[-1] != 768:
                cross_attn = self.cc_projection(cross_attn)
            out['c_crossattn'] = comfy.conds.CONDCrossAttn(cross_attn)
        return out
