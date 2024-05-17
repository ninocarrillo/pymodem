# Python3
# Functions for generating a hilbert transform FIR
# Nino Carrillo
# 17 May 2024

from math import pi, sin

class Hilbert:
	def __init__(self, **kwargs):
		self.tap_count = kwargs.get('tap_count', 21)
		self.amplitude = kwargs.get('amplitude', 1.0)
		self.window = kwargs.get('window', 'hann')
		self.taps = []
		self.delay = self.tap_count // 2
		start = -(self.delay)
		end = start + self.tap_count
		for n in range(start,end):
			if n % 2:
				# n is odd
				self.taps.append(2 / (pi * n))
			else:
				# n is even
				self.taps.append(0)
		self.window_taps = []
		N = self.tap_count - 1
		if self.window == 'hann':
				for n in range(self.tap_count):
					self.window_taps.append(sin(pi * n / N)**2)
		for i in range(self.tap_count):
			self.taps[i] = self.taps[i] * self.window_taps[i]
		self.delay_taps = []
		for i in range(self.delay+1):
			self.delay_taps.append(0)
		self.delay_taps[0] = 1
