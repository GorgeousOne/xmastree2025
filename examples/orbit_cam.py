
import math
import py5
from py5 import Py5Vector

import ctypes
# Get screen DPI (similar to Java's Toolkit)
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
screen_dpi = user32.GetDpiForSystem()

spin_threshold = 0.0001
singleton = None

class OrbitCamera:
	def __init__(self):
		global singleton
		singleton = self

		self.center_pos = Py5Vector(0, 0, 0)
		self.target_center_pos = Py5Vector(0, 0, 0)
		self.set_fov(60)
		self.set_target_zoom(1)
		self.zoom = 0.8
		self.set_mouse_sensitivity(0.8)
		self.set_y_up(True)
		self.set_default_radius(500)
		self.state_changed = True
		self.yaw = 0
		self.pitch = 0
		self.is_ortho = False
		self.pwidth = 0
		self.pheight = 0
		self.update()

	def get_eye_pos(self):
		return py5.Py5Vector(
			self.radius * math.sin(-self.yaw) * math.cos(self.pitch),
			self.radius * math.sin(self.pitch),
			self.radius * math.cos(-self.yaw) * math.cos(self.pitch)
		) - self.center_pos

	def get_dir(self):
		return py5.Py5Vector(
			math.sin(-self.yaw) * -math.cos(self.pitch),
			-math.sin(self.pitch),
			math.cos(-self.yaw) * -math.cos(self.pitch)
		)

	def get_up(self):
		dir = -1 if self.is_y_up else 1
		return py5.Py5Vector(
			math.sin(-self.yaw) * math.sin(self.pitch),
			-math.cos(self.pitch),
			math.cos(-self.yaw) * math.sin(self.pitch)
		) * dir

	def set_target_pos(self, v):
		self.target_center_pos = v

	def shift_target_pos(self, v):
		self.target_center_pos += v

	def align_x(self):
		if self.target_yaw == -py5.HALF_PI and self.target_pitch == 0:
			self.target_yaw = py5.HALF_PI
		else:
			self.target_yaw = -py5.HALF_PI
			self.target_pitch = 0

	def align_y(self):
		if self.target_yaw == 0 and self.target_pitch == py5.HALF_PI:
			self.target_pitch = -py5.HALF_PI
		else:
			self.target_pitch = py5.HALF_PI
			self.target_yaw = 0

	def align_z(self):
		if self.target_yaw == 0 and self.target_pitch == 0:
			self.target_yaw = py5.PI
		else:
			self.target_yaw = 0
			self.target_pitch = 0

	def set_y_up(self, state):
		self.is_y_up = state
		self.state_changed = True

	def set_default_radius(self, r):
		self.default_radius = r
		self.radius = self.default_radius / self.zoom

	def set_fov(self, fov):
		self.fov = max(30, min(120, fov))
		self.state_changed = True

	def set_target_zoom(self, z):
		self.target_zoom = z

	def set_mouse_sensitivity(self, s):
		self.mouse_sensitivity = s

	def set_ortho(self, state):
		self.is_ortho = state
		self.state_changed = True

	def window_size_changed(self):
		return self.pheight != py5.height or self.pwidth != py5.width

	def update(self):
		if self.window_size_changed() or self.state_changed:
			rad_fov = py5.radians(self.fov)
			aspect_ratio = py5.width / py5.height
			self.view_plane_dist = 0.5 * min(py5.width, py5.height) / math.tan(0.5 * rad_fov)

			if self.is_ortho:
				scale = self.default_radius / self.view_plane_dist
				py5.ortho(-py5.width/2 / self.zoom * scale,
					py5.width/2 / self.zoom * scale,
					-py5.height/2 / self.zoom * scale,
					py5.height/2 / self.zoom * scale,
					1, self.view_plane_dist * 10)
				py5.camera(0, 0, self.view_plane_dist, 0, 0, -1, 0, -1 if self.is_y_up else 1, 0)
			else:
				py5.perspective(rad_fov, aspect_ratio, 1, self.view_plane_dist * 10)
				py5.camera(0, 0, 0, 0, 0, -1, 0, -1 if self.is_y_up else 1, 0)

			self.pwidth = py5.width
			self.pheight = py5.height
			self.state_changed = False

	def apply_rotation(self):
		transition = 0.2

		if not hasattr(self, 'target_yaw'):
			self.target_yaw = self.yaw
		if not hasattr(self, 'target_pitch'):
			self.target_pitch = self.pitch
		if not hasattr(self, 'target_zoom'):
			self.target_zoom = self.zoom

		self.yaw += (self.target_yaw - self.yaw) * transition
		self.pitch += (self.target_pitch - self.pitch) * transition

		delta = self.target_center_pos - self.center_pos
		self.center_pos += delta * transition

		dzoom = self.target_zoom - self.zoom
		if abs(dzoom) > 0.001:
			self.zoom += dzoom * transition
			self.radius = self.default_radius / self.zoom
		elif dzoom != 0:
			self.zoom = self.target_zoom
			self.radius = self.default_radius / self.zoom

		py5.translate(0, 0, -self.radius)
		py5.rotate_x(self.pitch)
		py5.rotate_y(self.yaw)
		py5.translate(self.center_pos.x, self.center_pos.y, self.center_pos.z)

	def rotate_target_axes(self, dx, dy):
		direction = -1 if self.is_y_up else 1
		dyaw = self.mouse_sensitivity * dx / screen_dpi * direction
		dpitch = self.mouse_sensitivity * dy / screen_dpi * direction
		self.target_yaw += dyaw
		self.target_pitch = max(-py5.HALF_PI, min(py5.HALF_PI, self.target_pitch - dpitch))

	def shift_target_pos_mouse(self, dx, dy):
		dir_y = self.get_up()
		dir_x = dir_y.cross(self.get_dir())
		shift = dir_x * dx + dir_y * -dy
		shift *= self.mouse_sensitivity / self.zoom * (0.0015 * self.default_radius)
		self.shift_target_pos(shift)

	def add_scroll_to_target_zoom(self, scroll_count):
		self.target_zoom = max(0.5, min(8, self.target_zoom + scroll_count / 2))

# ==== Py5 lifecycle and interaction ====

if __name__ == '__main__':
	def settings():
		py5.size(1000, 600, py5.P3D)

	def setup():
		global cam
		cam = OrbitCamera()
		py5.fill(128)

	def draw():
		py5.background(255)
		py5.lights()
		cam.update()
		py5.push_matrix()
		cam.apply_rotation()
		py5.box(100)
		py5.pop_matrix()
	py5.run_sketch()

def mouse_dragged():
	dx = py5.mouse_x - py5.pmouse_x
	dy = py5.mouse_y - py5.pmouse_y
	if py5.mouse_button == py5.LEFT:
		singleton.rotate_target_axes(dx, dy)
	elif py5.mouse_button == py5.RIGHT:
		singleton.shift_target_pos_mouse(dx, dy)

def mouse_wheel(e):
	singleton.add_scroll_to_target_zoom(-e.get_count())

def key_pressed():
	k = py5.key
	if k == 'c':
		singleton.set_target_pos(py5.Py5Vector(0, 0, 0))
	elif k == 'x':
		singleton.align_x()
	elif k == 'y':
		singleton.align_y()
	elif k == 'z':
		singleton.align_z()
	elif k == ' ':
		singleton.set_ortho(not singleton.is_ortho)

