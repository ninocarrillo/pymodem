# Python3
# Functions for complex arithmetic
# Nino Carrillo
# 17 May 2024

from math import pi, sin, atan, atan2, sqrt

class ComplexNumber:
	def __init__(self, real, imag):
		self.real = real
		self.imag = imag
		self.constellation = [45, -45, 135, -135]
		self.angle = 0

	def multiply(self, arg):
		real = (self.real*arg.real) - (self.imag*arg.imag)
		imag = (arg.real*self.imag) + (self.real*arg.imag)
		self.imag = imag
		self.real = real

	def getangle(self):
		#self.angle = atan(self.imag/self.real) * 180 / pi
		#if self.real < 0:
		#	if self.imag < 0:
		#		self.angle -= 180
		#	else:
		#		self.angle += 180
		self.angle = atan2(self.imag, self.real) * 180 / pi
		return self.angle

	def getmag(self):
		self.magnitude = sqrt((self.imag**2) + (self.real**2))
		return self.magnitude

	def get_angle_error(self):
		self.getangle()
		errors = []
		distances = []
		for point in self.constellation:
			error = self.angle - point
			errors.append(error)
			distances.append(abs(error))
		error = 361
		min_index = 0
		for i in range(len(self.constellation)):
			if distances[i] < error:
				error = distances[i]
				min_index = i
		self.angle_error = errors[min_index]

		return self.angle_error