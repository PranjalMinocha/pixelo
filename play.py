from datetime import date
import json
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np


current_date = date.today()
with open("lookup_files/lookup_"+str(current_date)+".json", 'r') as file:
    lookup = json.load(file)

seen = set()
counter = 0
history = []
while(True):
    print("\nEnter your guess:")
    input_word = input()
    if(input_word == "exit"):
        print("\nExiting game.")
        break

    if input_word in seen:
        print("\nYou already guessed that word!")
        continue
    seen.add(input_word)

    if input_word not in lookup:
        print("\nWord not in list!")
        continue
    
    counter += 1
    rank = lookup[input_word]
    history.append(rank)

    if rank == 0:
        print("\nCongratulations! You guessed the word!")
        print("Final Score: ", counter)
        break

    print("\nRank: ",rank)
    print("Score: ", counter)

norm = np.array(history)/max(history)

plt.figure()
plt.title("Contexto Performance")
plt.plot(history)

colors = LinearSegmentedColormap.from_list("red_orange_green", ["red", "orange", "green"])
plt.scatter(range(len(history)), history, color=[colors(1 - n) for n in norm], s=50)

plt.xlabel("Number of guesses")
plt.ylabel("Rank of guessed word")

plt.plot(len(history)-1, 0, marker="o", markersize=10, markeredgecolor="green", markerfacecolor="green")

plt.show()