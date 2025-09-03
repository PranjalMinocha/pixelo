import numpy as np
import random
import json
from datetime import date

with open("word_list.txt", "r") as file:
    word_list = [line.strip() for line in file.readlines()] 

embed_store = np.load("embed_store.npy")

random_idx = random.randint(0, len(word_list) - 1)
random_word = word_list[random_idx]
embedding = embed_store[:, random_idx].reshape(1, -1)

print("Word of the day is: ", random_word)

similarities = np.abs(np.dot(embedding, embed_store)/(np.linalg.norm(embedding)*np.linalg.norm(embed_store, axis=0)))
sim_idx_list = [(sim, idx) for idx, sim in enumerate(similarities[0])]
sim_idx_list.sort(reverse=True, key=lambda x: x[0])

lookup = {}
for i in range(len(sim_idx_list)):
    sim, idx = sim_idx_list[i]
    lookup[word_list[idx]] = i

current_date = date.today()

with open("lookup_files/lookup_"+str(current_date)+".json", "w") as file:
    json.dump(lookup, file)