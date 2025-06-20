import multiprocessing
import ctypes
from digital_twin_tree import py5_led_tree

# mock class that acts as interface between animations and py5
class NeoPixel:
	def __init__(self, pin, count, auto_write=False):
		self.count = count

		self.pixels = [(0, 0, 0)] * count
		self.shared_pixels = multiprocessing.Array(ctypes.c_float, count * 3)

		# start a separate process with Py5 tree rendering
		self.process = multiprocessing.Process(target=py5_led_tree.run_digital_tree, args=(self.shared_pixels, count))
		self.process.start()

	# draft a color change for a pixel
	def __setitem__(self, index, color):
		self.pixels[index] = color

	# return length of pixel array
	def __len__(self):
		return len(self.pixels)

	# update all pixel colors in Py5 animation
	def show(self):
		for i, (b, g, r) in enumerate(self.pixels):
			base = i * 3
			self.shared_pixels[base] = b
			self.shared_pixels[base + 1] = g
			self.shared_pixels[base + 2] = r

if __name__ == '__main__':
	NeoPixel(None, 500)