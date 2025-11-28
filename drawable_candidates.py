import os

# A curated list of concrete, drawable nouns
DRAWABLE_NOUNS = [
    # Animals
    "cat", "dog", "bird", "fish", "horse", "cow", "pig", "sheep", "lion", "tiger", "bear", "elephant", "monkey", "rabbit", "mouse", "snake", "frog", "turtle", "spider", "butterfly", "bee", "ant", "whale", "dolphin", "shark", "octopus", "penguin", "owl", "eagle", "duck", "chicken", "goat", "deer", "wolf", "fox", "camel", "giraffe", "zebra", "kangaroo", "panda", "koala", "squirrel", "rat", "bat", "crab", "lobster", "snail", "worm", "mosquito", "fly", "dragon", "dinosaur", "unicorn",
    
    # Food & Drink
    "apple", "banana", "orange", "grape", "strawberry", "watermelon", "pineapple", "cherry", "pear", "peach", "lemon", "lime", "coconut", "mango", "kiwi", "tomato", "potato", "carrot", "onion", "garlic", "corn", "broccoli", "mushroom", "pepper", "cucumber", "pumpkin", "bread", "cheese", "egg", "meat", "fish", "chicken", "pizza", "burger", "sandwich", "hotdog", "taco", "sushi", "cake", "cookie", "pie", "ice cream", "chocolate", "candy", "coffee", "tea", "milk", "juice", "water", "wine", "beer",
    
    # Nature
    "tree", "flower", "grass", "leaf", "plant", "bush", "forest", "mountain", "hill", "valley", "river", "lake", "ocean", "sea", "beach", "island", "volcano", "desert", "sky", "cloud", "sun", "moon", "star", "rain", "snow", "wind", "fire", "rock", "stone", "sand", "dirt", "mud", "cave", "rainbow", "lightning", "tornado", "hurricane",
    
    # Objects / Household
    "table", "chair", "bed", "sofa", "couch", "lamp", "light", "fan", "door", "window", "wall", "floor", "roof", "house", "building", "school", "hospital", "store", "shop", "car", "bus", "truck", "train", "plane", "boat", "ship", "bicycle", "bike", "motorcycle", "phone", "computer", "laptop", "tv", "radio", "camera", "watch", "clock", "book", "pen", "pencil", "paper", "bag", "box", "bottle", "cup", "glass", "plate", "bowl", "spoon", "fork", "knife", "key", "lock", "ring", "necklace", "glasses", "hat", "shoe", "shirt", "pants", "dress", "coat", "jacket", "umbrella", "guitar", "piano", "drum", "violin", "ball", "doll", "toy", "game", "card", "money", "coin",
    
    # Body Parts
    "head", "face", "eye", "nose", "mouth", "ear", "hair", "hand", "finger", "arm", "leg", "foot", "toe", "heart", "brain", "bone", "tooth", "tongue", "lip",
    
    # People / Professions
    "man", "woman", "boy", "girl", "baby", "child", "person", "doctor", "nurse", "teacher", "student", "police", "firefighter", "soldier", "king", "queen", "prince", "princess", "wizard", "witch", "ghost", "robot", "alien", "clown", "pirate", "ninja",
    
    # Misc
    "flag", "map", "globe", "cross", "star", "heart", "circle", "square", "triangle", "arrow", "ladder", "bridge", "fence", "gate", "wheel", "tire", "engine", "battery", "magnet", "telescope", "microscope", "thermometer", "compass", "anchor", "bell", "whistle", "horn", "drum", "hammer", "saw", "drill", "screwdriver", "wrench", "nail", "screw", "bolt", "nut", "rope", "chain", "wire", "string", "thread", "needle", "pin", "clip", "button", "zipper", "pocket", "wallet", "purse", "backpack", "suitcase", "basket", "bucket", "broom", "mop", "brush", "comb", "soap", "towel", "sponge", "toothbrush", "toothpaste", "toilet", "sink", "bath", "shower", "mirror", "pillow", "blanket", "sheet", "curtain", "rug", "carpet", "mat"
]

def main():
    print("Generating drawable_words.txt...")
    
    # Load existing word list to ensure we have embeddings
    word_list_path = "word_list.txt"
    if not os.path.exists(word_list_path):
        print(f"Error: {word_list_path} not found.")
        return

    with open(word_list_path, "r", encoding="utf-8") as f:
        existing_words = set(line.strip() for line in f if line.strip())
    
    valid_drawable_words = []
    
    for word in DRAWABLE_NOUNS:
        # Check if word exists in our embedding list
        # We might need to check for singular/plural if exact match fails, but let's stick to exact for now
        if word in existing_words:
            valid_drawable_words.append(word)
        else:
            # Try plural 's'
            if word + "s" in existing_words:
                valid_drawable_words.append(word + "s")
            # Try singular (if list has plural) - simplistic check
            elif word.endswith("s") and word[:-1] in existing_words:
                valid_drawable_words.append(word[:-1])
                
    # Remove duplicates and sort
    valid_drawable_words = sorted(list(set(valid_drawable_words)))
    
    output_path = "drawable_words.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        for word in valid_drawable_words:
            f.write(word + "\n")
            
    print(f"Successfully wrote {len(valid_drawable_words)} drawable words to {output_path}.")

if __name__ == "__main__":
    main()
