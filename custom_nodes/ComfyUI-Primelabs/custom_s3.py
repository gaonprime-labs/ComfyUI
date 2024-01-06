import numpy as np
import nodes
import comfy
from comfy.cli_args import args
import torch
import glob
import pathlib
from util.all import *
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
import boto3
import io


class CustomLoadImageS3:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "config": ("CONFIG", ),
                "keyin": ("STRING", {
                    "default": "path"
                }),
                "aws_access_key": ("STRING", {
                    "default": "aws_access_key"
                }),
                "aws_secret_key": ("STRING", {
                    "default": "aws_secret_key"
                }),
                "bucket_name": ("STRING", {
                    "default": "bucket_name"
                })
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "run"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def run(self, config, keyin: str, aws_access_key: str, aws_secret_key: str, bucket_name: str):
        with lg.context("CustomLoadImageS3"):
            inspect(
                "run.input", {
                    "config": config,
                    "keyin": keyin,
                    "aws_access_key": aws_access_key,
                    "aws_secret_key": aws_secret_key,
                    "bucket_name": bucket_name
                })
            # s3 image download
            path = config[keyin]
            s3 = boto3.resource('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
            f = io.BytesIO()
            s3.Object(bucket_name, path).download_fileobj(f)

            # LoadImage
            i = Image.open(f)
            i = ImageOps.exif_transpose(i)
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32)/255.0
            image = torch.from_numpy(image)[None, ]
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32)/255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            inspect("run.image", {"image": image, "mask": mask})
            return (image, mask[None])


class CustomSaveImageS3:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "config": ("CONFIG", ),
                "keyin": ("STRING", {
                    "default": "path"
                }),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def save_images(self, images, config, keyin, aws_access_key, aws_secret_key, bucket_name, prompt=None,
                    extra_pnginfo=None):
        with lg.context("CustomSaveImageS3"):
            inspect("run.input", {"images": images.shape, "config": config, "keyin": keyin})
            compress_level = 4
            ui_images = []
            result_images = []
            path_base = config[keyin]
            for counter, image in enumerate(images):
                if counter == 0:
                    path = path_base
                else:
                    path = f"{parent(path_base)}/{file_stem(path_base)}-{counter}{file_suffix(path_base)}"
                i = 255.*image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                metadata = None
                if not args.disable_metadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                s3 = boto3.resource('s3', aws_access_key_id=aws_access_key,
                                    aws_secret_access_key=aws_secret_key)
                f = io.BytesIO()
                f.name = path
                Image.fromarray(img).save(f, format="png")
                f.seek(0)
                res = s3.Object(bucket_name, path).put(Body=f)  #@TODO ACL이 필요하면 만들어주기
                ui_images.append({
                    "filename": pathlib.Path(path).name,
                    "subfolder": "",
                    "type": "output"
                })  #@?
                result_images.append({"path": path})
            out = {"ui": {"images": ui_images}, "result": {"images": result_images}}
            inspect("run.out", out)
            return out


# class CustomRabbitMqPublish:
#     @classmethod
#     def INPUT_TYPES(s):
#         return {
#             "required": {
#                 "images": ("IMAGE", ),
#                 "config": ("CONFIG", ),
#                 "keyin": ("STRING", {
#                     "default": "path"
#                 }),
#             },
#         }

NODE_CLASS_MAPPINGS = {
    "CustomLoadImageS3": CustomLoadImageS3,
    "CustomSaveImageS3": CustomSaveImageS3,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomLoadImageS3": "CustomLoadImageS3 Node",
    "CustomSaveImageS3": "CustomSaveImageS3 Node",
}
