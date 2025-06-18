import ast
import py5
from py5 import Py5Vector
from orbit_cam import OrbitCamera
import orbit_cam as oc

led_positions = []

def run_led_tree(pixels, led_count):
	def settings():
		py5.size(800, 800, py5.P3D)

	def setup():
		# py5.stroke(255)
		py5.no_stroke()
		load_led_positions()

		global cam
		cam = OrbitCamera()
		cam.set_target_zoom(0.5)

	def draw():
		py5.background(0)
		# py5.lights()
		cam.update()

		py5.push_matrix()
		cam.apply_rotation()
		draw_leds()
		py5.pop_matrix()

	def load_led_positions():
		global led_positions
		with open("coords.txt", "r") as f:
			lines = f.readlines()
		led_positions = [Py5Vector(*ast.literal_eval(line.strip())) for line in lines]

	def draw_leds():
		for i in range(min(led_count, len(led_positions))):
			idx = i * 3
			b, g, r = pixels[idx], pixels[idx + 1], pixels[idx + 2]
			py5.fill(r, g, b)
			pos = led_positions[i]
			py5.push_matrix()
			py5.translate(pos.x, pos.z, pos.y)
			py5.box(10)
			py5.pop_matrix()

	def mouse_dragged():
		oc.mouse_dragged()
	def mouse_wheel(e):
		oc.mouse_wheel(e)
	def key_pressed():
		oc.key_pressed()

	py5.run_sketch()


if __name__ == '__main__':
	from multiprocessing import Process, Array
	import random

	led_count = 500
	shared_pixels = Array('B', led_count * 3)
	for i in range(led_count):
		base = i * 3
		shared_pixels[base] = random.randint(0, 255)
		shared_pixels[base + 1] = random.randint(0, 255)
		shared_pixels[base + 2] = random.randint(0, 255)

	# run_led_tree(shared_pixels, led_count)
	p = Process(target=run_led_tree, args=(shared_pixels, led_count))
	p.start()

	import time
	for i in range(100):
		time.sleep(1)
		for i in range(3*led_count):
			shared_pixels[i] = random.randint(0, 255)
	p.join()