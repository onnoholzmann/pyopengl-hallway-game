import pygame
import time
import os

def run(run_time):
  end_time = 0
  # Get the directory of the current script file2
  script_dir = os.path.dirname(os.path.abspath(__file__))

  # Specify the name of the target folder
  dependencies_folder = 'assets'

  # Create the path to the target folder
  target_path = os.path.join(script_dir, dependencies_folder)

  # Change the working directory to the target folder
  os.chdir(target_path)

  pygame.init()

  # create the display
  screen_x, screen_y = 1280, 720
  screen = pygame.display.set_mode((screen_x, screen_y), flags=pygame.SCALED, vsync=1)
  pygame.display.set_caption("Unnamed Infinite Platformer Game")
  clock = pygame.time.Clock()

  class Random:
    def __init__(self, m = None, s = None):
      if m == None: self.m = 27**9
      else: self.m = m
      if s == None: self.s = 2**31
      else: self.s = s
      self.seed = (time.time() + self.m) * self.s % self.m
    def seed(self, new_seed = None):
      if new_seed == None: self.seed = (time.time() + self.m) * self.s % self.m
      else: self.seed = new_seed
    def random(self):
      new_seed = (self.seed + self.m) * self.s * self.m % self.m
      value = new_seed / self.m
      self.seed = new_seed
      return value
    def randint(self, a , b):
      value = int((b - a) * self.random() + a)
      return value
    def randints(self, a, b, quantity):
      output = []
      times_done = 0
      while times_done <= quantity:
        output.append(self.randint(a, b))
        times_done += 1
      return output
    def chance(self, a, b = None):
      if b == None: output = self.random() < a
      else: output = self.random() < (a / b)
      return output
    def choice(self, choice_list):
      choice_list.index(int(self.random * len(choice_list)))
  random = Random()

  class Stopwatch:
    def __init__(self):
      self.time_started = time.time()
      self.running = True
    def restart(self, time_running = 0):
      self.time_started = time.time() + time_running
    def pause(self):
      if self.running:
        self.time_running = time.time() - self.time_started
        self.running = False

    def resume(self):
      if self.running == False:
        self.time_started = time.time() - self.time_running
        self.running = True
    def get(self):
      if self.running: return time.time() - self.time_started
      else: self.time_running

  obj = []
  player_move_obj_list = []
  #make all classes
  class Player:
    def __init__(self, x, y, keys_up, keys_down, keys_left, keys_right, vel_x, jump_power, color, s_x, s_y, grafity_s_2):
      self.x, self.y = x, y
      self.keys_up = keys_up
      self.keys_down = keys_down
      self.keys_left = keys_left
      self.keys_right = keys_right
      self.vel_x = vel_x
      self.jump_power = jump_power
      self.vel_y = 0
      self.color = color
      self.s_x, self.s_y = s_x, s_y
      self.go_up, self.go_down, self.go_left, self.go_right = False, False, False, False
      self.grafity_moved = time.time()
      self.stopwatch = Stopwatch()
      self.grafity_s_2 = grafity_s_2
      self.can_jump = False

    def move(self):
      move = 0
      if self.go_up == True and self.can_jump == True:
        self.set_y_vel(-self.jump_power)
        self.can_jump = False
      if self.go_right == True: self.x += self.vel_x
      if self.go_left == True: self.x -= self.vel_x
      if move != 0:
        for obj in player_move_obj_list:
          obj.x += move
      self.y += self.vel_y

      if self.y + self.s_y >= screen_y:
        self.y = screen_y - self.s_y
        nonlocal running
        running = False
      elif self.y <= 0:
        self.set_y_vel(0)
        self.y = 1
      if self.x + self.s_x >= screen_x: self.x = screen_x - self.s_x
      elif self.x <= 0: self.x += -self.x
    def move_screen(self):
      if self.x >= 200 and self.x <= 460: pass
      else:
        if self.x <= 200:
          move = 200 - self.x
          self.x += move
          for obj in player_move_obj_list:
            obj.x += move
        elif self.x >= 460:
          move = self.x - 460
          self.x -= move
          for obj in player_move_obj_list:
            obj.x -= move

    def draw(self, screen = screen):
      pygame.draw.rect(screen, self.color, (self.x, self.y, self.s_x, self.s_y))

    def check_key(self, key_pressed, press_type):
      if press_type == "key_down":
        if key_pressed in self.keys_up: self.go_up = True
        elif key_pressed in self.keys_down: self.go_down = True
        elif key_pressed in self.keys_right: self.go_right = True
        elif key_pressed in self.keys_left: self.go_left = True
      elif press_type == "key_up":
        if key_pressed in self.keys_up: self.go_up = False
        elif key_pressed in self.keys_down: self.go_down = False
        elif key_pressed in self.keys_right: self.go_right = False
        elif key_pressed in self.keys_left: self.go_left = False

    def check_collision(self, other, resolve = False):
      if self.x < other.x + other.s_x and self.x + self.s_x > other.x and self.y < other.y + other.s_y and self.y + self.s_y > other.y:
        if resolve:
          if self.x + self.s_x > other.x and self.x + self.s_x - other.x <= self.vel_x and self.go_right!= 0:
            self.x = other.x - self.s_x
          elif other.x + other.s_x > self.x and other.x + other.s_x - self.x <= self.vel_x and self.go_left != 0:
            self.x = other.x + other.s_x
          elif self.y + self.s_y > other.y and self.y + self.s_y - other.y <= self.vel_y:
            self.set_y_vel(0)
            self.can_jump = True
            self.y = other.y - self.s_y
          elif other.y + other.s_y > self.y and other.y + other.s_y - self.y <= -self.vel_y:
            self.set_y_vel(0)
            self.y = other.y + other.s_y
        else: return True
      else: return False

    def grafity(self):
      difference = self.stopwatch.get() ** 2 * self.grafity_s_2 - self.grafity_moved
      self.vel_y += difference
      self.grafity_moved += difference

    def set_y_vel(self, new_vel):
      self.vel_y = new_vel
      if new_vel == 0:
        self.stopwatch.restart()
        self.grafity_moved = 0

  class Squire:
    def __init__(self, x, y, s_x, s_y, color):
      obj.append(self)
      player_move_obj_list.append(self)
      self.x, self.y = x, y
      self.s_x, self.s_y = s_x, s_y
      self.color = color
      self.counter = 0

    def draw(self, screen = screen):
      pygame.draw.rect(screen, self.color, (self.x, self.y, self.s_x, self.s_y))

  squires_collision = []
  squires_ghost = []
  def add_squire(collision, *new_squires):
    if collision == True:
      for new_squire in new_squires:
        squires_collision.append(new_squire)
    elif collision == False:
      for new_squire in new_squires:
        squires_ghost.append(new_squire)

  class Image:
    def __init__(self, file, x, y, size, background = True):
      obj.append(self)
      if background == True: player_move_obj_list.append(self)
      self.file = pygame.image.load(file)
      self.file_rect = self.file.get_rect()
      self.x, self.y = x, y
      self.size = size
      self.file_rect.topleft = (x, y)
      size_x, size_y = self.file.get_width() * self.size, self.file.get_height() * self.size
      self.resized_file = pygame.transform.scale(self.file, (size_x, size_y))

    def draw(self, screen = screen):
      self.file_rect.topleft = (self.x, self.y)
      screen.blit(self.resized_file, self.file_rect)

    def get_size(self, x_or_y):
      if x_or_y == "x": return (self.file.get_width() * self.size)
      elif x_or_y == "y": return (self.file.get_height() * self.size)

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

  class Sound:
    def __init__(self, file):
      self.file = str(file)
      self.sound = pygame.mixer.Sound(self.file)
      self.channel = None

    def play(self):
      self.channel = pygame.mixer.find_channel()
      self.channel.set_volume(1.0)
      self.channel.play(self.sound)

    def stop(self):
      if self.channel is not None:
        self.channel.stop()

    def set_volume(self, volume):
      if self.channel is not None:
        self.channel.set_volume(volume)

  class Pause:
    def __init__(self, keys_start, x, y, txt, color, size):
      self.keys_start = keys_start
      self.x = x
      self.y = y
      self.txt = txt
      self.color = color
      self.size = size
      self.text = Text(self.x, self.y, self.txt, self.size, self.color)

    def display(self):
      self.text.draw(screen)

    def pause(self):
      paused = True
      player.stopwatch.pause()
      while paused:
        clock.tick(60)
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
            pygame.quit()
            exit()
          elif event.type == pygame.KEYDOWN:
            if event.key in self.keys_start:
              player.stopwatch.resume()
              paused = False
        self.text.draw(screen)
        pygame.display.flip()

    def check_key(self, key):
      if key in self.keys_start:
        self.pause()

  class Score:
    def __init__(self, x, y, png, size_png, dist_png_txt, size_txt, color):
      self.score = 0
      self.image = Image(png, x, y, size_png, False)
      text_x = x + self.image.file.get_width() * self.image.size + dist_png_txt
      self.text = Text(text_x, y, self.score, size_txt, color, "topleft")

    def draw(self):
      self.image.draw()
      self.text.draw(screen)

    def change_score(self, change):
      self.score += change
      self.text.update_text(self.score)

  coin_score = Score(20, 20, "coin.png", 4, 20, 60, (150, 100, 255))
  coin_list = []
  coin_draw = []
  squire_coin = []
  class Coins:
    def __init__(self, file, x, y, size, sound_file, value):
      obj.append(self)
      self.image = Image(file, x, y, size)
      squire = Squire(x, y, self.image.file.get_width() * self.image.size, self.image.file.get_height() * self.image.size, (0, 0, 0))
      add_squire(False, squire)
      coin_draw.append(self)
      coin_list.append(squire)
      squire_coin.append({squire : self})
      self.sound = Sound(sound_file)
      self.value = value

    def draw(self):
      self.image.draw()

    def delete(self):
      obj.remove(self)
      obj.remove(squire)
      coin_draw.remove(self)
      coin_list.remove(squire)
      squire_coin.remove({squire : self})

    def collision(self):
      coin_score.change_score(self.value)
      self.sound.play()
      self.delete()

  class Manage_squire:
    def __init__(self, min_length_squire, max_length_squire, min_height_squire, max_height_squire, min_height, max_height, min_x_dist, max_x_dist, min_y_dist, max_y_dist, del_dist, spawn_dist, goal_y, min_goal_y, max_goal_y, ignore_goal_y_chance):
      self.min_length_squire, self.max_length_squire = min_length_squire, max_length_squire
      self.min_height_squire, self.max_height_squire = min_height_squire, max_height_squire
      self.min_height, self.max_height = min_height, max_height
      self.min_x_dist, self.max_x_dist = min_x_dist, max_x_dist
      self.min_y_dist, self.max_y_dist = min_y_dist, max_y_dist
      self.del_dist, self.spawn_dist = del_dist, spawn_dist
      self.del_squire, self.check_del = lambda: squires_collision.remove(squires_collision[0]), lambda: squires_collision[0].x < self.del_dist
      self.check_del_coin = lambda: coin_draw[0].image.x < manage_coin.del_dist
      self.goal_y, self.min_goal_y, self.max_goal_y = goal_y, min_goal_y, max_goal_y
      self.ignore_goal_y_chance = ignore_goal_y_chance

    def create_squire(self, x, y):
      add_squire(True, Squire(x, y, random.randint(self.min_length_squire, self.max_length_squire), random.randint(self.min_height_squire, self.max_height_squire), random.randints(60, 255, 3)))
      manage_coin.calc_requirements()

    def calc_coords(self):
      x = squires_collision[-1].x + random.randint(self.min_x_dist, self.max_x_dist)
      difference_y = random.randint(self.min_y_dist, self.max_y_dist)
      y = squires_collision[-1].y + difference_y
      if squires_collision[-1].y >= self.min_goal_y and squires_collision[-1].y <= self.max_goal_y or random.chance(self.ignore_goal_y_chance): pass
      elif abs(y - self.goal_y) >= abs(squires_collision[-1].y - self.goal_y):
        y = squires_collision[-1].y - difference_y

      if y >= self.min_height and y <= self.max_height: pass  
      else:
        if not y >= self.min_height: y = self.min_height
        elif not y <= self.max_height: y = self.max_height
      return x, y

    def check(self):
      while squires_collision[-1].x + squires_collision[-1].s_x + self.min_x_dist <= self.spawn_dist:
        x, y = self.calc_coords()
        self.create_squire(x, y)
      if self.check_del():
        self.del_squire()
      if self.check_del_coin(): coin_draw[0].delete()

  class Manage_coin:
    def __init__(self, coin_chance, pic_list, pic_rarity_dict, coin_value_dict, size_dict, sound_dict, min_difference, max_difference, del_dist):
      self.pic_list, self.pic_rarity_dict, self.size_dict, self.sound_dict, self.coin_value_dict = pic_list, pic_rarity_dict, size_dict, sound_dict, coin_value_dict
      self.coin_chance = coin_chance
      self.min_difference, self.max_difference = min_difference, max_difference
      self.del_dist = del_dist

    def create_coin(self, file, x, y):
      Coins(file, x, y, self.size_dict[file], self.sound_dict[file], self.coin_value_dict[file])

    def calc_requirements(self):
      if random.chance(self.coin_chance):
        x = random.randint(self.min_difference, squires_collision[-1].s_x + self.max_difference) + squires_collision[-1].x
        y = squires_collision[-1].y
        for pic in self.pic_list:
          if random.chance(self.pic_rarity_dict[pic]):
            self.create_coin(pic, x, y)
            break
        coin_draw[-1].image.y -= coin_draw[-1].image.get_size("y")
        coin_list[-1].y -= coin_draw[-1].image.get_size("y")

  pause = Pause((pygame.K_p, pygame.K_ESCAPE), 400, 200, "the game is PAUSED press ESC to continue", (100, 175, 250), 40)
  player = Player(390, 360, (pygame.K_w, pygame.K_UP), (pygame.K_s, pygame.K_DOWN), (pygame.K_a, pygame.K_LEFT), (pygame.K_d, pygame.K_RIGHT), 5, 5.7, (100, 100, 255), 40, 40, 9.807)
  manage_coin = Manage_coin(0.5, ["coin.png", "coin_bag.png"], {"coin.png" : 0.8, "coin_bag.png" : 1}, {"coin.png" : 1, "coin_bag.png" : 20}, {"coin.png" : 5, "coin_bag.png" : 3}, {"coin.png" : "coins_falling.wav", "coin_bag.png" : "cha-ching.mp3"}, 20, -20, -10000)
  manage_squire = Manage_squire(80, 140, 20, 40, 200, 560, 200, 350, -150, 150, -10000, 20000, 300, 290 , 310, 0)

  add_squire(True, Squire(350, 400, 100, 20, (200, 100, 100)))

  def restart():
    global obj, squires_collision, squires_ghost, coin_list, coin_draw, squire_coin
    obj = []
    squires_collision = []
    squires_ghost = []
    coin_list = []
    coin_draw = []
    squire_coin = []
    player.go_up, player.go_right, player.go_left = False, False, False
    player.x, player.y = 390, 400 - player.s_y
    player.set_y_vel(0)
    add_squire(True,Squire(350, 400, random.randint(75, 150), random.randint(20, 40), (random.randint(60, 255), random.randint(60, 255), random.randint(60, 255))))

  def restart_screen():
    restart_screen = True
    text_restart = Text(400, 150, "NOOOOoooo!!!!! you fell", 40, (229, 172, 43))
    text_restart2 = Text(400, 450, "press ENTER to try again", 40, (37, 221, 167))
    while restart_screen:
      clock.tick(60)
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          pygame.quit()
          exit()
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_RETURN:
            restart_screen = False
            restart()

      text_restart.draw(screen)
      text_restart2.draw(screen)
      pygame.display.flip()
  not_started = True
  def start_screen():
    nonlocal not_started
    try: not_started
    except NameError: not_started = True
    if not_started:
      nonlocal end_time
      end_time = run_time + time.time()
      text_start = Text(640, 150, "press SPACE to start and DON'T STOP", 70, (71, 127, 227))
      text_start_2 = Text(640, 450, "use WASD to move", 60, (167, 206, 236))
    while not_started:
      clock.tick(60)
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          pygame.quit()
          exit()
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_SPACE:
            player.set_y_vel(0)
            not_started = False

      text_start.draw(screen)
      text_start_2.draw(screen)
      pygame.display.flip()

  print(obj)
  running = True
  while running:
    clock.tick(60)

    # Handle events
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        exit()
      elif event.type == pygame.KEYDOWN:
        player.check_key(event.key, "key_down")
        pause.check_key(event.key)
      elif event.type == pygame.KEYUP: player.check_key(event.key, "key_up")

    player.move()
    player.grafity()
    manage_squire.check()

    for squire in squires_collision:
      player.check_collision(squire, True)
    for squire in squires_ghost:
      if player.check_collision(squire):
        for coin_dict in squire_coin:
          if squire in coin_dict:
            coin_dict[squire].collision()

    player.move_screen()

    screen.fill((0, 0, 0))
    player.draw()
    for coin in coin_draw:
      coin.draw()

    for squire in squires_collision:
      squire.draw()

    coin_score.draw()

    start_screen()

    pygame.display.flip()
    if time.time() > end_time:
      running = False
  return coin_score.score