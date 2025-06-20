
import math
import py5
from py5 import Py5Vector

import ctypes
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
screen_dpi = user32.GetDpiForSystem()

singleton = None

# a camera class for orbiting around a 3D model with the mouse
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
        self.set_default_radius(500)

        self.yaw = 0
        self.pitch = 0
        self.target_yaw = self.yaw
        self.target_pitch = self.pitch

        self.pwidth = 0
        self.pheight = 0
        self.is_ortho = False
        self.state_changed = True

    # gets the current camera eye position based on yaw, pitch, and radius
    def get_eye_pos(self):
        return py5.Py5Vector(
            self.radius * math.sin(-self.yaw) * math.cos(self.pitch),
            self.radius * math.sin(self.pitch),
            self.radius * math.cos(-self.yaw) * math.cos(self.pitch)) - self.center_pos

    # gets the current direction vector the camera is facing
    def get_dir(self):
        return py5.Py5Vector(
            math.sin(-self.yaw) * -math.cos(self.pitch),
            -math.sin(self.pitch),
            math.cos(-self.yaw) * -math.cos(self.pitch)
        )

    # gets the current up vector for the camera orientation
    def get_up(self):
        return py5.Py5Vector(
            math.sin(-self.yaw) * math.sin(self.pitch),
            -math.cos(self.pitch),
            math.cos(-self.yaw) * math.sin(self.pitch))

    # sets the orbiting center to snap to
    def set_target_pos(self, v):
        self.target_center_pos = v

    def shift_target_pos(self, v):
        self.target_center_pos += v

    # snaps the camera to the x axis (-x direction if done twice)
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

    # sets the default orbiting radius for zoom = 1
    def set_default_radius(self, r):
        self.default_radius = r
        self.radius = self.default_radius / self.zoom

    # sets the field of view of the camera
    def set_fov(self, fov):
        self.fov = max(30, min(120, fov))
        self.state_changed = True

    # sets the zoom factor to snap to
    def set_target_zoom(self, z):
        self.target_zoom = z

    def set_mouse_sensitivity(self, s):
        self.mouse_sensitivity = s

    # changes the camera perspective to orthographic rendering
    def set_ortho(self, state=True):
        self.is_ortho = state
        self.state_changed = True

    def _window_size_changed(self):
        return self.pheight != py5.height or self.pwidth != py5.width

    # update the camera properties, call every draw() if window can be resized
    def update(self):
        if not (self._window_size_changed() or self.state_changed):
            return
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
            py5.camera(0, 0, self.view_plane_dist, 0, 0, -1, 0, 1, 0)
        else:
            py5.perspective(rad_fov, aspect_ratio, 1, self.view_plane_dist * 10)
            py5.camera(0, 0, 0, 0, 0, -1, 0, 1, 0)

        self.pwidth = py5.width
        self.pheight = py5.height
        self.state_changed = False

    # performs the camera rotation, call before rendering 3D model
    def apply_rotation(self):
        transition = 0.2
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

    # changes the yaw and pitch to snap to based on mouse movement
    def _shift_target_rot_mouse(self, dx, dy):
        dyaw = self.mouse_sensitivity * dx / screen_dpi
        dpitch = self.mouse_sensitivity * dy / screen_dpi
        self.target_yaw += dyaw
        self.target_pitch = max(-py5.HALF_PI, min(py5.HALF_PI, self.target_pitch - dpitch))

    def _shift_target_pos_mouse(self, dx, dy):
        dir_y = self.get_up()
        dir_x = dir_y.cross(self.get_dir())
        shift = dir_x * dx + dir_y * -dy
        shift *= self.mouse_sensitivity / self.zoom * (0.0015 * self.default_radius)
        self.shift_target_pos(shift)

    def _add_scroll_to_target_zoom(self, scroll_count):
        self.target_zoom = max(0.5, min(8, self.target_zoom + scroll_count / 2))


def mouse_dragged():
    dx = py5.mouse_x - py5.pmouse_x
    dy = py5.mouse_y - py5.pmouse_y
    if py5.mouse_button == py5.LEFT:
        singleton._shift_target_rot_mouse(dx, dy)
    elif py5.mouse_button == py5.RIGHT:
        singleton._shift_target_pos_mouse(dx, dy)

def mouse_wheel(e):
    singleton._add_scroll_to_target_zoom(-e.get_count())

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

if __name__ == '__main__':
    # example sketch of the interactive camera
    def settings():
        py5.size(1000, 600, py5.P3D)

    def setup():
        cam = OrbitCamera()

    def draw():
        py5.background(255)
        py5.lights()
        singleton.update()

        py5.push_matrix()
        singleton.apply_rotation()
        py5.fill(128)
        py5.box(100)
        py5.pop_matrix()

        descriptions = [
            'Rotate: Left Click',
            'Translate: Right Click',
            'Zoom: Mouse Wheel',
            'Center: C',
            'Align Axes: X, Y, Z',
            'Toggle Ortho: Spacebar'
        ]
        py5.hint(py5.DISABLE_DEPTH_TEST)
        py5.push_matrix()
        py5.translate(0, 0, -singleton.view_plane_dist)
        py5.fill(0)
        py5.text_size(24)
        py5.text_align(py5.LEFT, py5.TOP)
        for i, desc in enumerate(descriptions):
            py5.text(desc, -py5.width/2, -py5.height/2 + 24*i)
        py5.pop_matrix()
        py5.hint(py5.ENABLE_DEPTH_TEST)

    py5.run_sketch()
