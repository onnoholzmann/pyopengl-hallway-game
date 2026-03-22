import data.menu as menu
import data.unamed_infinite_platformer_game as platformer
import data.hallway_3d_pyopengl as hallway
import random
import pygame
import os
# from collections import deque
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
scores_file = os.path.join(current_dir, "scores.json")
def load_scores():
    if os.path.exists(scores_file):
        with open(scores_file, "r") as f:
            return json.load(f)
    return []

def save_scores(scores):
    with open(scores_file, "w") as f:
        json.dump(scores, f)

def add_score(scores, new_score):
    scores.append(new_score)
    scores = sorted(scores, reverse=True)[:10]  # keep only top 10
    save_scores(scores)
    return scores

def reset_display():
  pygame.display.quit()
  pygame.display.init()

scores = load_scores()
previous_score = None
while True:
  reset_display()
  menu.run(previous_score, scores)
  reset_display()
  total_score = 0
  total_score += platformer.run(random.randint(15, 25))
  reset_display()
  repeats = 1
  while True:
    total_score, coins_remaining = hallway.run(int(4 * (1 + repeats/2)), total_score, repeats)
    if not coins_remaining < max(int(4 * 1.5 * repeats)*0.1, 3):
      break
    repeats += 1
  previous_score = total_score
  scores = add_score(scores, previous_score)
  reset_display()