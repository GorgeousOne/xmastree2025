import multiprocessing
import ctypes
import py5
import py5_led_tree

# Py5 rendering function (in a separate module or dynamically loaded)
def run_py5(pixels, count):
	def setup():
		py5.size(400, 100)

	def draw():
		py5.background(0)
		for i in range(count):
			b, g, r = pixels[i * 3], pixels[i * 3 + 1], pixels[i * 3 + 2]
			py5.fill(r, g, b)
			py5.ellipse(20 + i * 30, 50, 20, 20)

	py5.run_sketch()


class NeoPixel:
	def __init__(self, pin, count, auto_write=False):
		self.pin = pin
		self.count = count
		self.auto_write = auto_write

		self.pixels = [(0, 0, 0)] * count
		self.shared_pixels = multiprocessing.Array(ctypes.c_uint8, count * 3)

		self.process = multiprocessing.Process(target=py5_led_tree.run_led_tree, args=(self.shared_pixels, count))
		self.process.start()

	def __setitem__(self, index, color):
		self.pixels[index] = color  # Only update internal buffer

	def __len__(self):
		return len(self.pixels)

	def show(self):
		# Push internal pixels to shared memory
		for i, (b, g, r) in enumerate(self.pixels):
			base = i * 3
			self.shared_pixels[base] = b
			self.shared_pixels[base + 1] = g
			self.shared_pixels[base + 2] = r

	def close(self):
		self.process.terminate()
		self.process.join()

if __name__ == '__main__':
	NeoPixel('asdf', 500)