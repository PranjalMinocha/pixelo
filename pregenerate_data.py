import argparse
import os
import json
import numpy as np
import torch
from datetime import date, timedelta
from pathlib import Path
import random
from diffusers import AutoPipelineForText2Image

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

def get_similarity_ranks(target_index, embeddings):
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
    print("Loading Stable Diffusion pipeline...")
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    ).to("cuda")
    
    pipe.load_lora_weights(
        "artificialguybr/doodle-redmond-doodle-hand-drawing-style-lora-for-sd-xl",
        weight_name="DoodleRedmond-Doodle-DoodleRedm.safetensors"
    )
    return pipe

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Pixelo game data for the next N days.")
    parser.add_argument("--days", type=int, default=30, help="Number of days to generate.")
    parser.add_argument("--start_offset", type=int, default=0, help="Start generating from today + offset days.")
    args = parser.parse_args()
    
    words, embeddings = load_data()
    
    # Select random words
    # Use a fixed seed for reproducibility if needed, but random is good for variety
    selected_indices = random.sample(range(len(words)), args.days)
    
    pipe = setup_pipeline()
    
    today = date.today()
    
    print(f"Generating data for {args.days} days starting from {today + timedelta(days=args.start_offset)}...")
    
    for i, idx in enumerate(selected_indices):
        target_date = today + timedelta(days=args.start_offset + i)
        target_word = words[idx]
        date_str = str(target_date)
        
        print(f"[{i+1}/{args.days}] {date_str}: '{target_word}'")
        
        # Create directory
        day_dir = PREGEN_DIR / date_str
        day_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Generate Lookup
        lookup = get_similarity_ranks(idx, embeddings)
        with open(day_dir / "lookup.json", "w", encoding="utf-8") as f:
            json.dump(lookup, f)
            
        # 2. Generate Image
        prompt = f"A playful doodle of a {target_word}, hand-drawn illustration, sketchy lines, slightly abstract, cartoon style, creative interpretation, DoodleRedm"
        image = pipe(prompt, guidance_scale=7.5, num_inference_steps=30).images[0]
        image.save(day_dir / "image.png")
        
    print("Generation complete!")
