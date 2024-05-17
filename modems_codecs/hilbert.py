# Python3
# Functions for generating a hilbert transform FIR
# Nino Carrillo
# 17 May 2024

from math import pi

class Hilbert:
	def __init__(self, **kwargs):
		self.tap_count = kwargs.get('tap_count', 21)
		self.amplitude = kwargs.get('amplitude', 1.0)
		self.taps = []
		start = -(self.tap_count // 2)
		end = start + self.tap_count
		for n in range(start,end):
			if n % 2:
				# n is odd
				self.taps.append(2 / (pi * n))
			else:
				# n is even
				self.taps.append(0)
