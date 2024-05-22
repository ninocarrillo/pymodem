# Python3
# Functions for complex arithmetic
# Nino Carrillo
# 17 May 2024

from math import pi, sin, atan, atan2, sqrt
from matplotlib import pyplot as plot


class ComplexNumber:
	def __init__(self, real, imag):
		self.real = real
		self.imag = imag
		self.angle = 0

	def multiply(self, arg):
		real = (self.real*arg.real) - (self.imag*arg.imag)
		imag = (arg.real*self.imag) + (self.real*arg.imag)
		self.imag = imag
		self.real = real

	def getangle(self):
		if self.real < 0:
			real = -self.real
			imag = -self.imag
		factor = 32
		real = round(self.real * factor)
		imag = round(self.imag * factor)
		if imag >= 0:
			self.angle = atan2(imag, real) * 180 / pi
		else:
			self.angle = -atan2(-imag,real) * 180 / pi

		return self.angle

	def getmag(self):
		self.magnitude = sqrt((self.imag**2) + (self.real**2))
		return self.magnitude

	def get_angle_error(self, constellation_id):
		self.getangle()
		errors = []
		distances = []
		if constellation_id == 'qpsk':
			constellation = [45, -45, 135, -135]
		elif constellation_id == 'bpsk':
			constellation = [-180, 0, 180]
		for point in constellation:
			error = self.angle - point
			errors.append(error)
			distances.append(abs(error))
		error = 361
		min_index = 0
		for i in range(len(constellation)):
			if distances[i] < error:
				error = distances[i]
				min_index = i
		self.angle_error = errors[min_index]

		return self.angle_error
