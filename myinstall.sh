# ======================================================== #
# setup
# ======================================================== #
conda create -n primelabs python=3.11 anaconda=2023.09 -y
conda activate primelabs
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121 --no-input
pip install -r requirements.txt
pip install -r requirements-primelabs.txt

# ======================================================== #
# plguins
# ======================================================== #
# https://github.com/ltdrdata/ComfyUI-Manager
cd custom_nodes && git clone https://github.com/ltdrdata/ComfyUI-Manager.git && cd -

# ======================================================== #
# models
# ======================================================== #
cp /home/hosan/ai/ComfyUI/models/face_restore/GFPGANv1.4.pth models/facerestore_models
cp /home/hosan/ai/ComfyUI/models/checkpoints/sd_xl_turbo_1.0_fp16.safetensors models/checkpoints
cp /home/hosan/ai/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors models/checkpoints
cp /home/hosan/ai/ComfyUI/models/checkpoints/aipf_snow_woman_xxmix_9realistic_sdxl_finetune-step00004000.safetensors models/checkpoints

# ======================================================== #
# assets
# ======================================================== #
cp /home/hosan/ai/ComfyUI/input/1.jpg input
cp /home/hosan/ai/ComfyUI/input/tgt_alwayz15.png input
