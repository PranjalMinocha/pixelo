import numpy as np
from wordfreq import top_n_list
from nltk.corpus import stopwords
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm

word_list = top_n_list("en", 25000)
stop_words = set(stopwords.words("english"))
word_list = [w for w in word_list if w not in stop_words]

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("\nEmbedding word list...")
embed_store = np.array([]).reshape(384, 0)

for word in tqdm(word_list):
    vector = np.array(embedding_model.embed_query(word)).reshape(-1, 1)
    embed_store = np.hstack((embed_store, vector))

print("Embedding complete.\n")

with open("word_list.txt", "w", encoding="utf-8") as file:
    for word in word_list:
        file.write(word + "\n")

np.save("embed_store.npy", embed_store)
