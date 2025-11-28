import argparse
import os
import json
import numpy as np
import torch
from datetime import date, timedelta
from pathlib import Path
import random
from diffusers import AutoPipelineForText2Image
from concurrent.futures import ThreadPoolExecutor
import time

# Setup paths
BASE_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = BASE_DIR / "backend"
PREGEN_DIR = BACKEND_DIR / "pregen_data"
WORD_LIST_PATH = BASE_DIR / "word_list.txt"
EMBED_STORE_PATH = BASE_DIR / "embed_store.npy"

def load_data():
    print("Loading word list and embeddings...")
    with open(WORD_LIST_PATH, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    
    embeddings = np.load(EMBED_STORE_PATH)
    
    # Ensure dimensions match
    if len(words) != embeddings.shape[1]:
        print(f"Warning: Word list length ({len(words)}) does not match embedding columns ({embeddings.shape[1]}). Truncating to minimum.")
        min_len = min(len(words), embeddings.shape[1])
        words = words[:min_len]
        embeddings = embeddings[:, :min_len]
        
    return words, embeddings

def get_similarity_ranks(target_index, embeddings, words):
    # Get target vector (384,)
    target_vector = embeddings[:, target_index]
    
    # Normalize target vector
    target_norm = np.linalg.norm(target_vector)
    if target_norm > 0:
        target_vector = target_vector / target_norm
        
    # Normalize all embeddings (384, N)
    # Note: Doing this once outside would be faster, but memory might be an issue if huge. 
    # For 10k words it's fine.
    norms = np.linalg.norm(embeddings, axis=0)
    norms[norms == 0] = 1 # Avoid divide by zero
    normalized_embeddings = embeddings / norms
    
    # Calculate cosine similarity: dot product
    # (384,) dot (384, N) -> (N,)
    similarities = np.dot(target_vector, normalized_embeddings)
    
    # Sort indices by similarity (descending)
    # We want rank 0 = most similar (the word itself)
    sorted_indices = np.argsort(similarities)[::-1]
    
    # Create lookup dict: word -> rank
    # rank 0 is the word itself
    lookup = {}
    for rank, idx in enumerate(sorted_indices):
        word = words[idx]
        lookup[word] = rank
        
    return lookup

def setup_pipeline():
    print("Loading SDXL Turbo pipeline...")
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    ).to("cuda")
    
    # Turbo doesn't need the LoRA as much if prompted well, and it's faster without extra weights
    # pipe.load_lora_weights(...) 
    return pipe

def generate_images_batch(pipe, prompts, output_paths):
    # Generate images in batch
    print(f"Generating batch of {len(prompts)} images with SDXL Turbo...")
    # SDXL Turbo needs guidance_scale=0.0 and few steps (1-4)
    images = pipe(prompts, guidance_scale=0.0, num_inference_steps=2).images
    
    for img, path in zip(images, output_paths):
        img.save(path)

def process_day(idx, target_date, words, embeddings):
    # CPU-bound task: calculate lookup
    target_word = words[idx]
    date_str = str(target_date)
    
    # Create directory
    day_dir = PREGEN_DIR / date_str
    day_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Calculating lookup for {date_str}: '{target_word}'")
    lookup = get_similarity_ranks(idx, embeddings, words)
    
    with open(day_dir / "lookup.json", "w", encoding="utf-8") as f:
        json.dump(lookup, f)
        
    return day_dir / "image.png", target_word

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Pixelo game data for the next N days.")
    parser.add_argument("--days", type=int, default=30, help="Number of days to generate.")
    parser.add_argument("--start_offset", type=int, default=0, help="Start generating from today + offset days.")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for image generation.")
    args = parser.parse_args()
    
    words, embeddings = load_data()
    
    # Select random words
    selected_indices = random.sample(range(len(words)), args.days)
    
    pipe = setup_pipeline()
    
    today = date.today()
    start_date = today + timedelta(days=args.start_offset)
    print(f"Generating data for {args.days} days starting from {start_date}...")
    
    # Prepare tasks
    tasks = []
    for i, idx in enumerate(selected_indices):
        target_date = start_date + timedelta(days=i)
        tasks.append((idx, target_date))
    
    # We will process in chunks of batch_size
    for i in range(0, len(tasks), args.batch_size):
        batch_tasks = tasks[i : i + args.batch_size]
        
        # 1. Run CPU tasks (lookup generation) in parallel
        image_paths = []
        prompts = []
        
        with ThreadPoolExecutor() as executor:
            futures = []
            for idx, target_date in batch_tasks:
                futures.append(executor.submit(process_day, idx, target_date, words, embeddings))
            
            for future in futures:
                img_path, target_word = future.result()
                image_paths.append(img_path)
                # Improved prompt for Turbo
                prompt = f"line art doodle of {target_word}, simple, minimal, thick black lines, white background, marker style, vector art, high quality"
                prompts.append(prompt)
        
        # 2. Run GPU task (image generation) in batch
        if prompts:
            generate_images_batch(pipe, prompts, image_paths)
            
    print("Generation complete!")
