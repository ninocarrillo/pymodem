# Python3
# Functions for complex arithmetic
# Nino Carrillo
# 17 May 2024

from math import pi, sin, atan

class ComplexNumber:
	def __init__(self, real, imag):
		self.real = real
		self.imag = imag

	def multiply(self, arg):
		self.real = (self.real*arg.real) - (self.imag*arg.imag)
		self.imag = (arg.real*self.imag) + (self.real*arg.imag)

	def getangle(self):
		self.angle = atan(self.imag/self.real) * 180 / pi
		if self.real < 0:
			if self.imag < 0:
				self.angle += 180
			else:
				self.angle -= 180
		return self.angle

	def get_angle_error_4(self):
		self.angle_error = self.getangle()
		while self.angle_error > 45:
			self.angle_error -= 90
		while self.angle_error < -45:
			self.angle_error += 90
		return self.angle_error

	def angle_error_8(self):
		pass
