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
# from functools import lru_cache
# import typing

class Coord_vector:
  # @typing.overload
  # def __init__(self, coords: tuple):
  # def __init__(self, coords):
    # self.coords = coords

  # @typing.overload
  # def __init__(self, x: int, y: int, z: int):
  def __init__(self, x, y, z):
    self.coords = (x, y, z)

  # def __init__(self, *args)

  def __add__(self, other):
    return Coord_vector(*tuple(self.coords[i] + other.coords[i] for i in range(3)))
  
  def __sub__(self, other):
    return Coord_vector(*tuple(self.coords[i] - other.coords[i] for i in range(3)))

  def __mul__(self, other):
    if isinstance(other, Coord_vector):
      # dot product
      return sum((self.coords[i] * other.coords[i] for i in range(3)))
    elif isinstance(other, Matrix):
      # mat = Matrix([[c] for c in self.coords])
      # res = other * mat
      # return Coord_vector(*tuple(res.nested_list[i][0] for i in range(3)))
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
  
  # def __matmul__(self, other):
    # create the cross product
    # return Coord_vector(*[self.coords[i%3]*other.coords[(i+1)%3] - self.coords[(i+1)%3]*other.coords[i%3] for i in range(1, 4)])
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
    # return sum(coord_list, Coord_vector(0, 0, 0))
  
  def normalize(self):
    return self / abs(self)
  
  def get_angle(self, other):
    # returns the angle in rad
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
    # return Matrix([[self.nested_list[row][column] * self.nested_list[column][row] for row in column] for column in self.nested_list])
    if isinstance(other, Matrix):
      return Matrix([[sum(self.nested_list[i][k] * other.nested_list[k][j] for k in range(len(self.nested_list[0]))) for j in range(len(other.nested_list[0]))] for i in range(len(self.nested_list))])
    if isinstance(other, Coord_vector):
      return self.mul_vector(other)
  
  def mul_vector(self, vector):
    # mat = Matrix([[c] for c in vector.coords])
    # res = self * mat
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
    self.sensitivity = sensitivity
    self.rotation_matrix = None
    self.rotation_matrix_inverse = None
    # or use self.rotation = [pitch, yaw]

  def update_rotation_matrix(self):
    self.rotation_matrix = Matrix.rotation_x(-self.pitch) * Matrix.rotation_y(-self.yaw)
    self.rotation_matrix_inverse = self.rotation_matrix.transpose()
  
  def world_to_camspace(self, coord):
    output_coord = coord - self.pos
    output_coord *= self.rotation_matrix
    return output_coord

  def iter_world_to_camspace(self, coords):
    return tuple(self.world_to_camspace(coord) for coord in coords)
"""
def draw_face(face, vertices):  
  glBegin(GL_TRIANGLES)
  for i in face.vertices:
    v = vertices[i]
    glColor3f(1,1,1)
    glVertex3f(
      v.coords[0],
      v.coords[1],
      v.coords[2]
    )
  glEnd()
"""
class Face:
  def __init__(self, color, vertices):
    self.color = color
    self.random_color = gen_random_color()
    # the vertices are the indices, of the vertices in the Object class
    self.vertices = vertices
    # self.center = Coord_vector.get_average(self.vertices)'
    self.center = None
    self.normal = None
    self.rel_coords = None
    # self.view_vec = None
    self.v0 = None
    # these are the indexes of the vertices in the object class

  # def draw(self, coords_cam, coords, f):
  # def draw(self, rel_coords, f):
  def draw_face(face, vertices, color, normal=None):
    glColor3f(color[0]/255, color[1]/255, color[2]/255)

    if normal:
      n = normal.normalize()
      glNormal3f(n.coords[0], n.coords[1], n.coords[2])

    glBegin(GL_TRIANGLES)
    for i in face.vertices:
        # v = vertices[i]
        glVertex3f(vertices[i].coords[0], vertices[i].coords[1], vertices[i].coords[2])
    glEnd()
  
  # def draw(self, f, color = None):
    """
    # --- 1. Convert 3D vertices to 2D screen space (cached) ---
    if not hasattr(self, "_cached_screen_coords") or self._cached_screen_f != f:
        self._cached_screen_coords = np.array([
            [screen_center[0] + screen_flip_correct[0] * v.coords[0] * f / v.coords[2],
             screen_center[1] + screen_flip_correct[1] * v.coords[1] * f / v.coords[2]]
            for v in self.rel_coords
        ], dtype=np.float32)
        self._cached_z = np.array([v.coords[2] for v in self.rel_coords], dtype=np.float32)
        self._cached_screen_f = f

    screen_coords = self._cached_screen_coords
    z = self._cached_z

    ax, ay = screen_coords[0]
    bx, by = screen_coords[1]
    cx, cy = screen_coords[2]
    az, bz, cz = z

    # --- 2. Compute bounding box ---
    bbminx = max(int(min(ax, bx, cx)), 0)
    bbminy = max(int(min(ay, by, cy)), 0)
    bbmaxx = min(int(max(ax, bx, cx)), W-1)
    bbmaxy = min(int(max(ay, by, cy)), H-1)

    # --- 3. Precompute total area ---
    total_area = (bx - ax)*(cy - ay) - (cx - ax)*(by - ay)
    if total_area == 0:
        return

    # --- 4. Rasterize using NumPy arrays (fast) ---
    xs = np.arange(bbminx, bbmaxx+1)
    ys = np.arange(bbminy, bbmaxy+1)
    X, Y = np.meshgrid(xs, ys)
    
    # Compute barycentric coordinates for all pixels at once
    alpha = ((bx - X)*(cy - Y) - (cx - X)*(by - Y)) / total_area
    beta  = ((cx - X)*(ay - Y) - (ax - X)*(cy - Y)) / total_area
    gamma = ((ax - X)*(by - Y) - (bx - X)*(ay - Y)) / total_area

    # Mask outside triangle
    mask = (alpha >= 0) & (beta >= 0) & (gamma >= 0)
    if not np.any(mask):
        return

    # Interpolate depth (z) for shading
    gray = np.clip(alpha*az + beta*bz + gamma*cz, 0, 255).astype(np.uint8)
    gray[~mask] = 0  # outside triangle

    # --- 5. Write to screen efficiently ---
    surf_array = pygame.surfarray.pixels3d(screen)
    surf_array[X[mask], Y[mask]] = np.stack([gray[mask]]*3, axis=-1)
    del surf_array  # unlock surface
    """
    """
    # Convert 3D coordinates to 2D screen space
    screen_coords = [(
      int(screen_center[0] + screen_flip_correct[0] * v.coords[0] * f / v.coords[2]),
      int(screen_center[1] + screen_flip_correct[1] * v.coords[1] * f / v.coords[2])
    ) for v in self.rel_coords]
    # Unpack vertices (triangles only)
    ax, ay = screen_coords[0]
    bx, by = screen_coords[1]
    cx, cy = screen_coords[2]
    # z-values for depth interpolation
    az = self.rel_coords[0].coords[2]
    bz = self.rel_coords[1].coords[2]
    cz = self.rel_coords[2].coords[2]
    # Bounding box
    bbminx = max(min(ax, bx, cx), 0)
    bbminy = max(min(ay, by, cy), 0)
    bbmaxx = min(max(ax, bx, cx), W-1)
    bbmaxy = min(max(ay, by, cy), H-1)
    total_area = triangle_edge_func(Coord_vector(ax, ay, 0),
                                      Coord_vector(bx, by, 0),
                                      Coord_vector(cx, cy, 0))
    if total_area == 0:
      return
    # Rasterize using barycentric coordinates
    for x in range(bbminx, bbmaxx + 1):
      for y in range(bbminy, bbmaxy + 1):
        p = Coord_vector(x, y, 0)
        alpha = triangle_edge_func(p, Coord_vector(bx, by, 0), Coord_vector(cx, cy, 0)) / total_area
        beta  = triangle_edge_func(p, Coord_vector(cx, cy, 0), Coord_vector(ax, ay, 0)) / total_area
        gamma = triangle_edge_func(p, Coord_vector(ax, ay, 0), Coord_vector(bx, by, 0)) / total_area
        if alpha < 0 or beta < 0 or gamma < 0:
          continue  # outside triangle
        # Linear depth for shading
        z = alpha * az + beta * bz + gamma * cz
        # Grayscale value proportional to depth (clamp 0-255)
        gray = max(0, min(255, int(z)**2))
        screen.set_at((x, y), (gray, gray, gray))
    """
    # next part is functional
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
"""
def vertex_visible(v, f):
    x, y, z = v.coords

    if z <= 0:
        return False

    if abs(x * f / z) > screen_center[0]:
        return False

    if abs(y * f / z) > screen_center[1]:
        return False

    return True
"""
"""
def clip_face_z(face):
    new_vertices = []
    verts = face.rel_coords
    n = len(verts)
    for i in range(n):
        v1 = verts[i]
        v2 = verts[(i + 1) % n]
        # Both in front
        if v1.coords[2] > 0:
            new_vertices.append(v1)
        # Edge crosses z=0
        if (v1.coords[2] > 0) != (v2.coords[2] > 0):
            t = v1.coords[2] / (v1.coords[2] - v2.coords[2])
            x = v1.coords[0] + t * (v2.coords[0] - v1.coords[0])
            y = v1.coords[1] + t * (v2.coords[1] - v1.coords[1])
            new_vertices.append(Coord_vector(x, y, 0.01))  # small offset in front of camera
    return new_vertices if len(new_vertices) >= 3 else None
"""
class Object:
  def __init__(self, coords, vertices, faces, render_outside = False):
    # vertices == points
    # all vertices are relative to the coords
    self.coords = coords
    self.vertices = vertices
    self.faces = faces
    self.center = Coord_vector.get_average(self.vertices)
    for face in self.faces:
      face.center = Coord_vector.get_average([self.vertices[i] for i in face.vertices])
      # face.normal = face.center.normalize()
      face.v0 = self.vertices[face.vertices[0]]
      v1 = self.vertices[face.vertices[1]]
      v2 = self.vertices[face.vertices[2]]
      face.normal = (v1 - face.v0) @ (v2 - face.v0)  # proper geometric normal
      # if abs(face.v0 + face.normal) < abs(face.v0):
        # face.normal *= -1
      if face.normal * (face.center - self.center) < 0 and render_outside:
        face.normal *= -1
      elif face.normal * (face.center - self.center) > 0 and not render_outside:
        face.normal *= -1
    # faces is a list of tupples, of the indices used in that face
  """
  def draw(self, cam):
  # def draw(self, cam, f):
    # calc the coords, relative to the cam, and sort them from further to closer
    for face in self.faces:
      # face.rel_coords = [self.coords + self.vertices[vertice] - coords_cam for vertice in face.vertices]
      # face.rel_coords = cam.iter_world_to_camspace([self.vertices[vertice] + self.coords for vertice in face.vertices])
      face.rel_coords = cam.iter_world_to_camspace(tuple(self.vertices[vertice] + self.coords for vertice in face.vertices))
    # calc the coords, relative to the cam, and sort the middles of the faces from further to closer
    # rel_coords = [(self.coords + self.vertices[vertice] - coords_cam for vertice in self.face.vertices) for face in self.faces]

    # back to front rendering
    # self.faces.sort(key=lambda face: abs(sum(face.rel_coords, Coord_vector(0, 0, 0)))/len(face.rel_coords), reverse=True)
    
    culled = 0
    for face in self.faces:
      # back face culling
      # vectors = [self.vertices[face.vertices[1]]- self.vertices[face.vertices[0]], self.vertices[face.vertices[1]]- self.vertices[face.vertices[2]]]
      # if ((self.vertices[face.vertices[0]] - self.vertices[face.vertices[1]]) @ (self.vertices[face.vertices[2]] - self.vertices[face.vertices[1]]) * camera_normal) > 0:
      # if ((face.rel_coords[1] - face.rel_coords[0]) @ (face.rel_coords[2] - face.rel_coords[0]) * camera_normal) > 0:

      # normal = (face.rel_coords[1] - face.rel_coords[0]) @ (face.rel_coords[2] - face.rel_coords[0])
      # print(normal.coords)

      # if ((face.rel_coords[0] - face.rel_coords[1]) @ (face.rel_coords[2] - face.rel_coords[1])).coords[2] < 0:
      # print(face.normal * camera_normal, face.normal * face.rel_coords[0])

      # if face.normal * camera_normal > 0 or face.normal * face.rel_coords[0] > 0:

      # if all(v.coords[2] <= 0 for v in face.rel_coords):
        # culled += 1
        # continue
      # if not any(vertex_visible(v, cam.f) for v in face.rel_coords) and not vertex_visible(Coord_vector.get_average(face.rel_coords), cam.f) and not (abs(Coord_vector.get_average(face.rel_coords)) < 2):
      # if any(v.coords[2] <= 0 for v in face.rel_coords) or abs(face.rel_coords[0]) >  5:
      if any(v.coords[2] <= 0 for v in face.rel_coords):
        culled += 1
        continue
      if not any(vertex_visible(v, cam.f) for v in face.rel_coords) and not vertex_visible(Coord_vector.get_average(face.rel_coords), cam.f):
        culled += 1
        continue
      # if face.normal * cam.rotation_matrix * face.rel_coords[0] > 0 or any(v.coords[2] <= 0 for v in face.rel_coords):
      
      # actualy cull the back faces, back face culling
      # if face.normal * cam.rotation_matrix * face.rel_coords[0] > 0:
      # if face.normal * cam.rotation_matrix * face.rel_coords[0] > 0 or any(v.coords[2] <= 0 for v in face.rel_coords):
      # if ((self.vertices[face.rel_coords[0]] - self.vertices[face.rel_coords[1]]) @ (self.vertices[face.rel_coords[2]] - self.vertices[face.rel_coords[1]]) * camera_normal) > 0:
        # culled += 1
        # continue
      # normal = (face.rel_coords[1] - face.rel_coords[0]) @ (face.rel_coords[2] - face.rel_coords[0])
      # view_vec = face.rel_coords[0]

      # if normal * view_vec >= 0:
      # if normal * camera_normal >= 0:
        # culled += 1
        # continue
      # face.draw(cam.f, grayscale_color(int(100*abs(Coord_vector.get_average([self.vertices[vertice] for vertice in face.vertices])))))
      face.draw(cam.f, grayscale_color(int(abs(Coord_vector.get_average(face.rel_coords)) * 100)))
      # face.draw(cam.f)
      # print(-light)
    # print(culled, camera_normal.coords)
    
    # for face in self.faces:
      # face.draw(f)
  """
  def draw(self, use_random_color=False):
    glPushMatrix()
    # move object in world
    glTranslatef(self.coords.coords[0], self.coords.coords[1], self.coords.coords[2])
    for face in self.faces:
      # Face.draw_face(face, self.vertices, face.color, face.normal)
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
    #  glOrtho(0, W, 0, H, -1, 1)
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
  # if not color: color = gen_random_color()
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
    # faces.append(Face(gen_random_color(), [face_vertices[0], face_vertices[3], face_vertices[1 + i]]))
    for k in range(2):
      for j in range(2):
        for i in range(2):
          faces.append(Face(gen_random_color(), [new_vertice_indices[0 + j + k*3], new_vertice_indices[4 + j + k*3], new_vertice_indices[1 + i*2 + j + k*3]]))

  return faces

class Coin:
  def __init__(self, location, value):
    self.value = value
    # value/10=size_factor
    # center the coin in the middle of the square of the maze
    location += Coord_vector(*((1 - value/15)/2 for _ in range(3)))
    self.cube = gen_cube(location, gen_color_hue(value*50 + random.randint(0, 100)), value/15)
    # coin = gen_cube(Coord_vector(0.75, 0.5, 0.75), pygame.Color(255, 255, 255), 0.5)
  
  def draw(self, use_random_color=False):
    self.cube.draw(use_random_color)
  
  def check_pickup(self, score_counter, player_coords):
    # print((self.cube.center - player_coords).coords)
    if abs(self.cube.center + self.cube.coords - player_coords) < self.value/10+0.2:
      score_counter += self.value
      return True
    return False
coin_list = []