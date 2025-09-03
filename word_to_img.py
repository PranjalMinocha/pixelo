from diffusers import AutoPipelineForText2Image
import torch
import json
from datetime import date

pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16"
).to("cuda")

pipe.load_lora_weights(
    "artificialguybr/doodle-redmond-doodle-hand-drawing-style-lora-for-sd-xl",
    weight_name="DoodleRedmond-Doodle-DoodleRedm.safetensors"
)

current_date = date.today()
with open("lookup_files/lookup_"+str(current_date)+".json", 'r') as file:
    lookup = json.load(file)

for i in lookup:
    if lookup[i] == 0:
        word = i
        break

prompt = "A playful doodle of a "+word+", hand-drawn illustration, sketchy lines, slightly abstract, cartoon style, creative interpretation, DoodleRedm"
image = pipe(prompt, guidance_scale=7.5, num_inference_steps=30).images[0]

image.save("images/img_"+str(current_date)+".png")