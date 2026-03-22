import random
import pygame
import sys

def run(previous_score, scores):
  # scores == highscores
  pygame.init()
  W, H = 1280, 720
  screen_center = (W/2, H/2)
  screen = pygame.display.set_mode((W, H), flags=pygame.SCALED, vsync=1)
  clock = pygame.time.Clock()

  class Text:
    def __init__(self, x, y, text, size, color, place = "center"):
      self.place = place
      self.x = x
      self.y = y
      self.text = str(text)
      self.size = size
      self.color = color
      self.font = pygame.font.Font(None, size)
      self.surface = self.font.render(self.text, True, color)
      self.rect = self.surface.get_rect(**{self.place: (self.x, self.y)})

    def update_text(self, new_text):
      self.text = str(new_text)
      self.surface = self.font.render(self.text, True, self.color)
      self.rect = self.surface.get_rect(**{self.place: (self.x, self.y)})

    def draw(self, screen):
      screen.blit(self.surface, self.rect)

  space_txt = Text(W/2, 50, "press SPACE to start", 40, pygame.Color(100, 255, 255))
  instruct_txt = Text(W/2, 90, "use WASD SHIFT and the mouse for the game", 25, pygame.Color(75, 200, 200))
  if previous_score:
    previous_score_txt = Text(W/2, 680, f'previous score: {previous_score}', 20, pygame.Color(200, 200, 225))
    troll_txt = Text(W/2, 700, f'you failed to escape', 20, pygame.Color(255, 100, 100))
  score_list_txt = []
  score_list_txt.append(Text(W/2, 140, "HIGH SCORES", 40, pygame.Color(255, 200, 100)))
  for i, j in enumerate(scores):
    score_list_txt.append(Text(W/2, 180 + i*40, f'{i+1}. {j}', 40, pygame.Color(255, 215, 150)))
  intro_txt = []
  intro_txt.append(Text(W/2, 180, "You are STUCK in the digital world", 40, pygame.Color(255, 200, 100)))
  intro_txt.append(Text(W/2, 220, "you need to try to ESCAPE", 40, pygame.Color(255, 200, 100)))
  intro_txt.append(Text(W/2, 260, "before the GLITCHES consume you", 40, pygame.Color(255, 200, 100)))
  running = True
  while running:
    for event in pygame.event.get(): 
      if event.type == pygame.QUIT: 
        pygame.quit() 
        sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
      running = False
      return

    screen.fill(pygame.Color(30, 30, 30))
    space_txt.draw(screen)
    instruct_txt.draw(screen)
    if previous_score:
      previous_score_txt.draw(screen)
      troll_txt.draw(screen)
      for score in score_list_txt:
        score.draw(screen)
    if not previous_score:
      for txt in intro_txt:
        txt.draw(screen)

    pygame.display.flip()
    clock.tick(60)
  return