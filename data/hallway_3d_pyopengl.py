import pygame
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *
import sys
import random
import math
import numpy as np
# from line_profiler import LineProfiler
# import cProfile
from functools import cache
import copy
import os
import time
# from functools import lru_cache
# import typing

# with gpu renderer: opengl will be used
# without gpu rendered: custom rendering
def run(maze_size, score, repeats):
  gpu_renderer = True

  # init pygame && the display
  pygame.init()
  # W, H = 800, 500
  W, H = 1280, 720
  screen_center = (W/2, H/2)
  screen_flip_correct = (1, -1)
  # screen_flip_correct = (1, 1)
  # screen = pygame.display.set_mode((W, H))
  if gpu_renderer:
    screen = pygame.display.set_mode((W, H), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=1)
  else:
    screen = pygame.display.set_mode((W, H), flags=pygame.SCALED, vsync=1)
  glViewport(0, 0, W, H)
  glEnable(GL_DEPTH_TEST)
  # add lighting shaders
  # glEnable(GL_LIGHTING)
  # glEnable(GL_LIGHT0)
  # glEnable(GL_COLOR_MATERIAL)
  # glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

  def load_file(file_path):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_path)
    with open(file_path, 'r') as f:
      return f.read()

  shader_program = shaders.compileProgram(
    shaders.compileShader(load_file("vertex_shader.glsl"), GL_VERTEX_SHADER),
    shaders.compileShader(load_file("fragment_shader.glsl"), GL_FRAGMENT_SHADER),
  )
  status = glGetProgramiv(shader_program, GL_LINK_STATUS)
  if not status:
    print("Shader link error:", glGetProgramInfoLog(shader_program))
  """
  # Light position (x, y, z, w) — w=0 means directional, w=1 means positional
  glLightfv(GL_LIGHT0, GL_POSITION,       [0.0, 0.0,  0.0, 1.0])
  glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, [0.0, 0.0, -1.0])   # pointing forward
  glLightf (GL_LIGHT0, GL_SPOT_CUTOFF,    30.0)                # 30deg cone
  glLightf (GL_LIGHT0, GL_SPOT_EXPONENT,  8.0)                 # soft falloff
  # falloff with distance (constant, linear, quadratic)
  glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION,  0.5)
  glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION,    0.3)
  glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.05)

  glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.02, 0.02, 0.02, 1.0])  # near black
  glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0,  1.0,  1.0,  1.0])
  # glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 2.0, 1.0, 0.0])
  # glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 1.0, 1.0, 1.0])
  # glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.2, 0.2, 0.2, 1.0])
  """

  glMatrixMode(GL_PROJECTION)
  gluPerspective(90, W/H, 0.1, 1000)
  glMatrixMode(GL_MODELVIEW)
  glEnable(GL_DEPTH_TEST)
  pygame.display.set_caption("Pygame starting......")
  clock = pygame.time.Clock()
  font = pygame.font.SysFont(None, 30) 
  score_text = font.render("initializing game...", True, (255,255,255)) 
  screen.blit(score_text, (10,10))
  pygame.display.flip()

  class Coord_vector:
    def __init__(self, x, y, z):
      self.coords = (x, y, z)

    def __add__(self, other):
      return Coord_vector(*tuple(self.coords[i] + other.coords[i] for i in range(3)))

    def __sub__(self, other):
      return Coord_vector(*tuple(self.coords[i] - other.coords[i] for i in range(3)))

    def __mul__(self, other):
      if isinstance(other, Coord_vector):
        # dot product
        return sum((self.coords[i] * other.coords[i] for i in range(3)))
      elif isinstance(other, Matrix):
        return other * self
      elif isinstance(other, (int, float)):
        return Coord_vector(*tuple(self.coords[i] * other for i in range(3)))

    def __truediv__(self, num):
      try:
        return Coord_vector(*(self.coords[i] / num for i in range(3)))
      except ZeroDivisionError:
        return Coord_vector(0, 0, 0)

    def __itruediv__(self, num):
      self.coords = tuple(self.coords[i] / num for i in range(3))
      return self

    def __iadd__(self, other):
      self.coords = tuple(self.coords[i] + other.coords[i] for i in range(3))
      return self

    def __isub__(self, other):
      self.coords = tuple(self.coords[i] - other.coords[i] for i in range(3))
      return self

    def __imul__(self, other):
      if isinstance(other, (int, float)):
        self.coords = tuple(self.coords[i] * other for i in range(3))
      elif isinstance(other, Matrix):
        self.coords = (other * self).coords
      return self

    def __abs__(self):
      return (sum(self.coords[i]**2 for i in range(3)))**0.5

    def __matmul__(self, other):
      x1, y1, z1 = self.coords
      x2, y2, z2 = other.coords

      return Coord_vector(
          y1*z2 - z1*y2,
          z1*x2 - x1*z2,
          x1*y2 - y1*x2
      )

    @staticmethod
    def get_average(coord_list):
      return sum(coord_list, start=Coord_vector(0, 0, 0)) / len(coord_list)

    def normalize(self):
      return self / abs(self)

    def get_angle(self, other):
      return math.acos((self * other) / (abs(self) * abs(other)))

  class Matrix:
    def __init__(self, nested_list):
      # matrix[row][column]
      self.nested_list = nested_list

    def __add__(self, other):
      return Matrix([[self.nested_list[row][column] + other.nested_list[row][column] for column in range(len(self.nested_list[0]))] for row in range(len(self.nested_list))])

    def __iadd__(self, other):
      self.nested_list = [[self.nested_list[row][column] + other.nested_list[row][column] for column in range(len(self.nested_list[0]))] for row in range(len(self.nested_list))]

    def __mul__(self, other):
      # only works on 2 square matrices of M * N and N * M size
      if isinstance(other, Matrix):
        return Matrix([[sum(self.nested_list[i][k] * other.nested_list[k][j] for k in range(len(self.nested_list[0]))) for j in range(len(other.nested_list[0]))] for i in range(len(self.nested_list))])
      if isinstance(other, Coord_vector):
        return self.mul_vector(other)

    def mul_vector(self, vector):
      res = self * Matrix([[c] for c in vector.coords])
      return Coord_vector(*tuple(res.nested_list[i][0] for i in range(3)))

    def __imul__(self, other):
      # only works on 2 square matrices of M * N and N * M size
      # return Matrix([[self.nested_list[row][column] * self.nested_list[column][row] for row in column] for column in self.nested_list])
      self.nested_list = [[sum([self.nested_list[i][k] * other.nested_list[k][j] for k in range(len(self.nested_list))]) for j in range(len(self.nested_list[0]))] for i in range(len(self.nested_list))]

    def transpose(self):
      return Matrix([[self.nested_list[j][i] for j in range(len(self.nested_list))] for i in range(len(self.nested_list[0]))])

    @cache
    def rotation_x(angle):
      return Matrix([
        [1, 0, 0],
        [0, math.cos(angle), -math.sin(angle)],
        [0, math.sin(angle), math.cos(angle)]
      ])

    @cache
    def rotation_y(angle):
      return Matrix([
        [math.cos(angle), 0, math.sin(angle)],
        [0, 1, 0],
        [-math.sin(angle), 0, math.cos(angle)]
      ])

    @cache
    def rotation_z(angle):
      return Matrix([
        [math.cos(angle), -math.sin(angle), 0],
        [math.sin(angle), math.cos(angle), 0],
        [0, 0, 1]
      ])

  def triangle_edge_func(a, b, p):
    # calculates opp triangle
    return (p.coords[0] - a.coords[0]) * (b.coords[1] - a.coords[1]) - (p.coords[1] - a.coords[1]) * (b.coords[0] - a.coords[0])

  class Camera:
    def __init__(self, pos, pitch, yaw, FOV, speed, sensitivity):
      self.pos = pos
      self.pitch = pitch
      self.yaw = yaw
      self.f = screen_center[0]//math.tan(math.radians(FOV/2))
      self.speed = speed
      self.base_speed = speed
      self.sensitivity = sensitivity
      self.rotation_matrix = None
      self.rotation_matrix_inverse = None

    def update_rotation_matrix(self):
      self.rotation_matrix = Matrix.rotation_x(-self.pitch) * Matrix.rotation_y(-self.yaw)
      self.rotation_matrix_inverse = self.rotation_matrix.transpose()

    def world_to_camspace(self, coord):
      output_coord = coord - self.pos
      output_coord *= self.rotation_matrix
      return output_coord

    def iter_world_to_camspace(self, coords):
      return tuple(self.world_to_camspace(coord) for coord in coords)

  class Face:
    def __init__(self, color, vertices):
      self.color = color
      self.random_color = gen_random_color()
      # the vertices are the indices, of the vertices in the Object class
      self.vertices = vertices
      self.center = None
      self.normal = None
      self.rel_coords = None
      self.v0 = None

    def draw_face(face, vertices, color, normal=None):
      glColor3f(color[0]/255, color[1]/255, color[2]/255)

      if normal:
        n = normal.normalize()
        glNormal3f(n.coords[0], n.coords[1], n.coords[2])

      glBegin(GL_TRIANGLES)
      for i in face.vertices:
          glVertex3f(vertices[i].coords[0], vertices[i].coords[1], vertices[i].coords[2])
      glEnd()

      # next part is functional
      # this was my first try at rendering, but it was in pygame only, so it was slowwwwwwww
      """
      # coords, rel to cam
      # rel_coords = (coords + vertice - coords_cam for vertice in self.vertices)

      # ray formula R(xt, yt, zt)
      # assume screen is at z = f
      # zt == f => screen
      # t = f/z, t is a scaling factor
      # x_screen = x * t = x * f / z
      # back-face culling
      # if self.normal.get_angle(camera_normal) < 1/2 * math.pi:
        # return
      # screen_coords = tuple(tuple(screen_center[xy] + screen_flip_correct[xy] * rel_coord.coords[xy] * f / rel_coord.coords[2] for xy in range(2)) for rel_coord in self.rel_coords)
      # screen_coords = tuple(tuple(screen_center[xy] + screen_flip_correct[xy] * rel_coord.coords[xy] * f / rel_coord.coords[2] for xy in range(2)) for rel_coord in self.rel_coords)
      screen_coords = []
      for rel_coord in self.rel_coords:
        # for xy in range(2):
        screen_coords.append((screen_center[0] + screen_flip_correct[0] * rel_coord.coords[0] * f / rel_coord.coords[2], screen_center[1] + screen_flip_correct[1] * rel_coord.coords[1] * f / rel_coord.coords[2]))
      # print(screen_coords)
      # screen_coords = tuple(tuple(int(screen_center[xy] + screen_flip_correct[xy] * rel_coord.coords[xy] * f[xy] / rel_coord.coords[2]) for xy in range(2)) for rel_coord in self.rel_coords)
      if color == None:
        pygame.draw.polygon(screen, self.color, screen_coords)
      else:
        pygame.draw.polygon(screen, color, screen_coords)
      """
  class Object:
    def __init__(self, coords, vertices, faces, render_outside = False):
      # all vertices are relative to the coords
      self.coords = coords
      self.vertices = vertices
      self.faces = faces
      self.center = Coord_vector.get_average(self.vertices)
      for face in self.faces:
        face.center = Coord_vector.get_average([self.vertices[i] for i in face.vertices])
        face.v0 = self.vertices[face.vertices[0]]
        v1 = self.vertices[face.vertices[1]]
        v2 = self.vertices[face.vertices[2]]
        face.normal = (v1 - face.v0) @ (v2 - face.v0)
        if face.normal * (face.center - self.center) < 0 and render_outside:
          face.normal *= -1
        elif face.normal * (face.center - self.center) > 0 and not render_outside:
          face.normal *= -1
      # faces is a list of tupples, of the indices used in that face

    def draw(self, use_random_color=False):
      glPushMatrix()
      # move object in world
      glTranslatef(self.coords.coords[0], self.coords.coords[1], self.coords.coords[2])
      for face in self.faces:
        if use_random_color: Face.draw_face(face, self.vertices, face.random_color, face.normal)
        else: Face.draw_face(face, self.vertices, face.color, face.normal)
      glPopMatrix()

  class Txt:
    def __init__(self, size, location, color=pygame.Color(255, 255, 255)):
      pygame.font.init()
      self.font = pygame.font.SysFont(None, size)
      self.txt = None
      self.surface = None
      self.color = color
      self.location = location

    def change_txt(self, new_txt):
      if new_txt != self.txt:
        self.txt = new_txt
        self.surface = self.font.render(self.txt, True, self.color)

    def draw(self, screen):
      screen.blit(self.surface, self.location)

    def draw_opengl(self, screen):
      text_data = pygame.image.tostring(self.surface, "RGBA", True)
      w, h = self.surface.get_size()

      # switch to 2D orthographic mode
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      glLoadIdentity()
      glOrtho(0, W, H, 0, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      glPushMatrix()
      glLoadIdentity()

      glDisable(GL_DEPTH_TEST)
      glUseProgram(0)  # disable shader for text
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

      x, y = self.location
      glRasterPos2f(x, y)
      glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

      glDisable(GL_BLEND)
      glEnable(GL_DEPTH_TEST)

      glMatrixMode(GL_PROJECTION)
      glPopMatrix()
      glMatrixMode(GL_MODELVIEW)
      glPopMatrix()

  def create_square_triangles(vertices, vertice_indices, low_poly=True, color=None):
    if gpu_renderer and low_poly:
      if color: return [Face(color, [vertice_indices[0], vertice_indices[i+1], vertice_indices[3]]) for i in range(2)]
      else: return [Face(gen_random_color(), [vertice_indices[0], vertice_indices[i+1], vertice_indices[3]]) for i in range(2)]
    else:
      length = len(vertices)
      faces = []
      for i in range(len(vertice_indices) - 1):
        for j in range(i + 1, len(vertice_indices)):
          if (i == 1 and j == 2):
            continue
          vertices.append(Coord_vector.get_average((vertices[vertice_indices[i]], vertices[vertice_indices[j]])))  
      new_vertice_indices = [vertice_indices[0], length, vertice_indices[1], length+1, length+2, length+3, vertice_indices[2], length+4, vertice_indices[3]]
      for k in range(2):
        for j in range(2):
          for i in range(2):
            faces.append(Face(gen_random_color(), [new_vertice_indices[0 + j + k*3], new_vertice_indices[4 + j + k*3], new_vertice_indices[1 + i*2 + j + k*3]]))

    return faces

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
  # cd to the assets folder
  script_dir = os.path.dirname(os.path.abspath(__file__))
  dependencies_folder = 'assets'
  target_path = os.path.join(script_dir, dependencies_folder)
  os.chdir(target_path)
  coin_collect_sound = Sound("coins_falling.wav")
  glitch_sound = Sound("fear.mp3")
  glitch_sound_2 = Sound("glitch.wav")

  class Coin:
    def __init__(self, location, value):
      self.value = value
      # center the coin in the middle of the square of the maze
      location += Coord_vector(*((1 - value/15)/2 for _ in range(3)))
      self.cube = gen_cube(location, gen_color_hue(value*50 + random.randint(0, 100)), value/15)

    def draw(self, use_random_color=False):
      self.cube.draw(use_random_color)

    def check_pickup(self, score_counter, player_coords):
      if abs(self.cube.center + self.cube.coords - player_coords) < self.value/10+0.2:
        coin_collect_sound.play()
        return True
      return False
  coin_list = []

  tunnel_vertices = [Coord_vector(k-0.5, j-0.5, i-0.5) for i in range(2) for j in range(2) for k in range(2)]
  # print(tunnel_vertices[5].coords)
  for i in range(len(tunnel_vertices)):
    tunnel_vertices[i] *= 3
  # print(tunnel_vertices[5].coords)
  tunnel = []
  def gen_tunnel_part(coord):
    # tunnel_vertices = []
    # for x in range(2):
      # for y in range(2):
        # for z in range(2):
          # tunnel_vertices.append(Coord_vector(x, y, z))
    # tunnel_faces = []
    # tunnel.append()

    faces = []
    for locked_dim in range(3):
      other_sides = [i for i in range(3) if i != locked_dim]
      for i in range(2):
        face_vertices = []
        coords = [0, 0, 0]
        # temp = []
        for j in range(2):
          for k in range(2):
            coords[locked_dim] = i
            # coords[other_sides[0]] = j
            # coords[other_sides[1]] = k
            tmp = [j, k]
            for side_index in range(2):
              coords[other_sides[side_index]] = tmp[side_index]
            # indice = x*1 + y*2 + z*4
            # face_vertices.append(sum(tuple(coords[i]*2**i for i in range(3))))
            face_vertices.append(coords[0] | (coords[1] << 1) | (coords[2] << 2))
        # for i in range(2): faces.append(Face(gen_random_color(), [face_vertices[0], face_vertices[3], face_vertices[1 + i]]))
        faces += create_square_triangles(tunnel_vertices, face_vertices)
        # if (i == 0) ^ (locked_dim == 1): faces.append(Face(gen_random_color(), [face_vertices[0], face_vertices[1], face_vertices[3], face_vertices[2]]))
        # else: faces.append(Face(gen_random_color(), [face_vertices[0], face_vertices[2], face_vertices[3], face_vertices[1]]))
    tunnel.append(Object(coord, tunnel_vertices, faces, True))

  hue = 0
  def gen_random_color():
    global hue
    color = pygame.Color(0)
    color.hsva = (random.randint(0, 360), 100, 100, 100)
    # hue += 360/12
    # color.hsva = (hue%360, 100, 100, 100)
    return color
  def gen_color_hue(hue):
    color = pygame.Color(0)
    color.hsva = (hue%360, 100, 100, 100)
    return color
  # @cache
  # def grayscale_color(distance):
    # intensity = max(0, min(1, 1/distance**2))  # 100 is just a scale to make values 0-1
    # gray = int(1/((distance/100)**2) * 255)
    # return (gray, gray, gray)
  @cache
  def grayscale_color(distance):
      distance = max(distance, 1)  # avoid divide by zero
      gray = int(255 / ((distance/100)**2)) - 50
      # lock the value between 10 and 255
      gray = max(10, min(gray, 255))
      gray = max(10, min(gray, 200))
      return (gray, gray*0.9, gray*0.4)

  def gen_cube(coords_cube, cube_color, factor):
    cube_vertices = [Coord_vector(k*factor, j*factor, i*factor) for i in range(2) for j in range(2) for k in range(2)]
    cube_faces = []
    for locked_dim in range(3):
      other_sides = [i for i in range(3) if i != locked_dim]
      for i in range(2):
        face_vertices = []
        coords = [0, 0, 0]
        temp = []
        for j in range(2):
          for k in range(2):
            coords[locked_dim] = i
            tmp = [j, k]
            for side_index in range(2):
              coords[other_sides[side_index]] = tmp[side_index]
            # indice = x*1 + y*2 + z*4
            face_vertices.append(coords[0] | (coords[1] << 1) | (coords[2] << 2))
        cube_faces += create_square_triangles(cube_vertices, face_vertices, color=cube_color)
    return Object(coords_cube, cube_vertices, cube_faces, True)

  vertices = [Coord_vector(k-0.5, j-0.5, i-0.5) for i in range(2) for j in range(2) for k in range(2)]
  vertices.append(Coord_vector(0, -2, -0.5))
  faces = []
  for locked_dim in range(3):
    other_sides = [i for i in range(3) if i != locked_dim]
    for i in range(2):
      face_vertices = []
      coords = [0, 0, 0]
      temp = []
      for j in range(2):
        for k in range(2):
          coords[locked_dim] = i
          tmp = [j, k]
          for side_index in range(2):
            coords[other_sides[side_index]] = tmp[side_index]
          # indice = x*1 + y*2 + z*4
          face_vertices.append(coords[0] | (coords[1] << 1) | (coords[2] << 2))
      faces += create_square_triangles(vertices, face_vertices, low_poly=False)

  cube = Object(Coord_vector(-5, 0, 5), vertices, faces, True)
  cam = Camera(Coord_vector(0.5, 0.6, 0.5), 0, -math.pi*3/4, 90, 3, 0.001)
  camera_normal = Coord_vector(0, 0, 1)
  gen_tunnel_part(Coord_vector(2, 2, 2))
  for i in range(10):
    gen_tunnel_part(tunnel[-1].coords + Coord_vector(0, 0, 3))

  """
  generate the maze
    -- first generate the maze with DFS
    -- then "braid" the maze, you remove dead ends, and create loops
    -- then convert the 2d to 3d
  """
  def open_neighbors(maze, x, y):
    h = len(maze)
    w = len(maze[0])
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    count = 0
    for dx,dy in dirs:
      nx,ny = x+dx,y+dy
      if 0 <= nx < w and 0 <= ny < h:
        if maze[ny][nx]:
          count += 1

    return count

  def generate_maze(width, height, start=(0,0)):
    maze = [[False]*width for _ in range(height)]

    stack = [start]
    maze[start[1]][start[0]] = True

    directions = [(1,0),(-1,0),(0,1),(0,-1)]

    while stack:
      x,y = stack[-1]
      neighbors = []

      for dx,dy in directions:
        nx,ny = x+dx,y+dy

        if 0 <= nx < width and 0 <= ny < height:
          if not maze[ny][nx]:
            if open_neighbors(maze, nx, ny) <= 1:
              neighbors.append((nx,ny))

      if neighbors:
        nx,ny = random.choice(neighbors)
        maze[ny][nx] = True
        stack.append((nx,ny))
      else:
        stack.pop()

    return maze

  def braid_maze(maze, probability=0.5):
    h = len(maze)
    w = len(maze[0])
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    for y in range(h):
      for x in range(w):
        if not maze[y][x]:
          continue
        if open_neighbors(maze, x, y) == 1:   # dead end
          if random.random() < probability:
            walls = []
            for dx,dy in dirs:
              nx,ny = x+dx,y+dy
              if 0 <= nx < w and 0 <= ny < h:
                if not maze[ny][nx]:
                  if open_neighbors(maze, nx, ny) >= 2:
                    walls.append((nx,ny))
            if walls:
              nx,ny = random.choice(walls)
              maze[ny][nx] = True

  length_x, length_y = maze_size, maze_size
  maze_2d = generate_maze(length_x, length_y)
  braid_maze(maze_2d, 0.25)
  for row in maze_2d:
    string = ""
    for i in row:
      string += " " if i else "X"

  if not gpu_renderer:
    maze_part_vertices = [Coord_vector(1*k, -0.5, 1*j) for k in range(2) for j in range(2)]
    maze_part_faces = create_square_triangles(maze_part_vertices, [i for i in range(4)])
  maze_objects = []
  for x in range(length_x):
    for y in range(length_y):
      if gpu_renderer:
        if maze_2d[x][y]:
          if (x != 0 and y != 0) and random.randint(0, 10) < 3 or (x == 1 and y == 0) or (x == 0 and y == 1):
            coin_list.append(Coin(Coord_vector(x, 0, y), random.randint(1, 5)))
          maze_part_vertices = [Coord_vector(k, i, j) for i in range(2) for j in range(2) for k in range(2)]
          maze_part_faces = []
          # floor + ceiling
          colors = [pygame.Color(25,36,40), pygame.Color(245, 245, 245)]
          for i in range(2): maze_part_faces += create_square_triangles(maze_part_vertices, [j + i*4 for j in range(4)], color=colors[i])
          # other walls
          if x == 0 or not maze_2d[x-1][y]: maze_part_faces += create_square_triangles(maze_part_vertices, [0, 2, 4, 6], color=pygame.Color(65,76,80))
          if x == length_x-1 or not maze_2d[x+1][y]: maze_part_faces += create_square_triangles(maze_part_vertices, [1, 3, 5, 7], color=pygame.Color(65,76,80))
          if y == 0 or not maze_2d[x][y-1]: maze_part_faces += create_square_triangles(maze_part_vertices, [0, 1, 4, 5], color=pygame.Color(65,76,80))
          if y == length_y-1 or not maze_2d[x][y+1]: maze_part_faces += create_square_triangles(maze_part_vertices, [2, 3, 6, 7], color=pygame.Color(65,76,80))
          maze_objects.append(Object(Coord_vector(x*1, 0, y*1), maze_part_vertices, maze_part_faces))
      else:
        if maze_2d[x][y]:
          maze_objects.append(Object(Coord_vector(x*1, 0.5, y*1), maze_part_vertices, maze_part_faces))

  score_counter = score
  score_text = Txt(50, (10, 50))
  score_text.change_txt(f'score: {score_counter}')
  intro_txt = Txt(50, (300, 100))
  if repeats <= 1: intro_txt.change_txt("collect the blocks before the glitch wins")
  else: intro_txt.change_txt("LEVEL UP!!!!!! YOU ARE ALMOST THERE!!")
  pygame.display.set_caption("3d Hallway")
  last_fps_change = 0
  pygame.mouse.set_visible(False)
  pygame.event.set_grab(True)
  def update_frame(glitch, start_time):
    nonlocal last_fps_change
    nonlocal score_counter
    for event in pygame.event.get(): 
      if event.type == pygame.QUIT: 
        pygame.quit() 
        sys.exit()
        return False

    movement = Coord_vector(0, 0, 0)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
      movement -= Coord_vector(1, 0, 0)
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: 
      movement += Coord_vector(1, 0, 0)
    if keys[pygame.K_UP] or keys[pygame.K_w]: 
      movement -= Coord_vector(0, 0, 1)
    if keys[pygame.K_DOWN] or keys[pygame.K_s]: 
      movement += Coord_vector(0, 0, 1)
    if keys[pygame.K_SPACE]:
      movement += Coord_vector(0, 1, 0)
    if keys[pygame.K_LCTRL]:
      movement -= Coord_vector(0, 1, 0)
    if keys[pygame.K_LSHIFT]:
      cam.speed = cam.base_speed * (1+score_counter/50)
    else:
      cam.speed = cam.base_speed
    rotation_x, rotation_y = (i * cam.sensitivity for i in pygame.mouse.get_rel())
    if gpu_renderer: cam.yaw -= rotation_x
    else: cam.yaw += rotation_x
    if gpu_renderer: cam.pitch -= rotation_y
    else: cam.pitch += rotation_y
    cam.pitch = max(-math.pi/2 + 0.01, min(math.pi/2 - 0.01, cam.pitch))
    cam.update_rotation_matrix()
    rotate_movement = cam.rotation_matrix_inverse

    # move cam, while keeping wasd locked to the y plane
    move_z = Coord_vector(movement.coords[0], 0, movement.coords[2]) * cam.rotation_matrix_inverse
    move_z = Coord_vector(move_z.coords[0], 0, move_z.coords[2]).normalize()
    # use delta time
    # prevent going trough walls
    move = Coord_vector(0, 0, 0)
    move_x = move_z.coords[0] * cam.speed * clock.get_time()/1000
    if move_x + cam.pos.coords[0] > 0.15 and move_x + cam.pos.coords[0] < length_x - 0.15 and maze_2d[int(cam.pos.coords[0] + move_x + (Coord_vector(move_z.coords[0], 0, 0).normalize()*0.15).coords[0])][int(cam.pos.coords[2])]:
      move += Coord_vector(move_x, 0, 0)
    move_y = move_z.coords[2] * cam.speed * clock.get_time()/1000
    if move_y + cam.pos.coords[2] > 0.15 and move_y + cam.pos.coords[2] < length_y - 0.15 and maze_2d[int(cam.pos.coords[0])][int(cam.pos.coords[2] + move_y + (Coord_vector(0, 0, move_z.coords[2]).normalize()*0.15).coords[2])]:
      move += Coord_vector(0, 0, move_y)
    cam.pos += move
    for coin in coin_list[:]:
      if coin.check_pickup(score_counter, cam.pos):
        score_counter += coin.value
        coin_list.remove(coin)
        score_text.change_txt(f'score: {score_counter}')

    # old/legacy pure pygame rendering code
    """
    # --- draw --- 
    screen.fill((10, 10, 10))
    cube.draw(cam)
    # chunk.draw(cam)
    # for i in range(len(tunnel)):
      # tunnel[-i].draw(cam)
    maze_objects.sort(key=lambda maze_part: abs(cam.world_to_camspace(maze_part.coords)))
    # binary search, to search for the max render index
    low, high = 0, len(maze_objects)
    while low < high:
      mid = (low + high) // 2
      if abs(cam.world_to_camspace(maze_objects[mid].coords)) > 5:
        low = mid + 1
      else:
        high = mid
    end_index = high
    for i in range(end_index):
      maze_objects[i].draw(cam)

    pygame.display.flip()
    """
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glRotatef(-math.degrees(cam.pitch), 1, 0, 0)
    glRotatef(-math.degrees(cam.yaw), 0, 1, 0)
    glTranslatef(-cam.pos.coords[0], -cam.pos.coords[1], -cam.pos.coords[2])

    glUseProgram(shader_program)
    cube.draw()
    for obj in maze_objects:
      obj.draw(glitch)
    for coin in coin_list:
      coin.draw(glitch)
    glUseProgram(0)
    score_text.draw_opengl(screen)
    if time.time() - start_time < 5:
      intro_txt.draw_opengl(screen)
    pygame.display.flip()

    last_fps_change += clock.get_time()
    if last_fps_change > 100:
      fps = clock.get_fps()
      pygame.display.set_caption(f'3d Hallway | FPS: {fps: .2f} | coins remaining: {len(coin_list)}')
      last_fps_change = 0
    clock.tick(60)
    # print(cam.pos.coords)
    return True

  def gen_glitch(start_time, end_time):
    choice = random.choice([glitch_sound, glitch_sound_2])
    choice.play()
    # glitch_sound.play()
    last_glitch = time.time()
    next_glitch = last_glitch + random.randint(int((end_time - time.time())/len(coin_list)), 10)
    glitch_duration = min(max(len(coin_list)/2/(end_time - time.time()), 0.01), 0.15)
    return last_glitch, next_glitch, glitch_duration

  def game_loop():
    running = True
    start_time = time.time()
    end_time = start_time + min(min(random.randint(int(len(coin_list) * 0.25), int(len(coin_list) * 5)), 15), 35)
    print(end_time-start_time)
    last_glitch, next_glitch, glitch_duration = gen_glitch(start_time, end_time)
    next_glitch, glitch_duration = time.time(), 0.25
    quiting = False
    # last_glitch = time.time()
    # next_glitch = last_glitch + random.randint(10, 20)
    # glitch_duration = (start_time-time.time)/(length_x+length_y)
    previous_coin_length = len(coin_list)
    while running:
      if len(coin_list) < 3 or len(coin_list) > previous_coin_length:
        break
      if len(coin_list) < previous_coin_length:
        previous_coin_length = len(coin_list)
      if time.time() > next_glitch:
        glitch = True
        if time.time() > glitch_duration + next_glitch:
          last_glitch, next_glitch, glitch_duration = gen_glitch(start_time, end_time)
          if time.time() > end_time :
            glitch_duration = 1
            if quiting: break
            else:
              quiting = True
              choice = random.choice([glitch_sound, glitch_sound_2])
              choice.play()
      else:
        glitch = False
      # print(len(coin_list))
      running = update_frame(glitch, start_time)
  game_loop()
  pygame.quit()
  return score_counter, len(coin_list)