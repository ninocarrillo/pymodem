# Python3
# Functions for complex arithmetic
# Nino Carrillo
# 17 May 2024

from math import pi, sin, atan, atan2, sqrt

class ComplexNumber:
	def __init__(self, real, imag):
		self.real = real
		self.imag = imag
		self.qpsk_constellation = [45, -45, 135, -135]
		self.bpsk_constellation = [-180, 0, 180]
		self.angle = 0

	def multiply(self, arg):
		real = (self.real*arg.real) - (self.imag*arg.imag)
		imag = (arg.real*self.imag) + (self.real*arg.imag)
		self.imag = imag
		self.real = real

	def getangle(self):
		self.angle = atan2(self.imag, self.real) * 180 / pi
		# need about 1/8 degree resolution for no loss in performance
		# 1 degree resolution is adequate for about 0.3dB performance loss

		return self.angle

	def getmag(self):
		self.magnitude = sqrt((self.imag**2) + (self.real**2))
		return self.magnitude

	def get_angle_error(self, constellation_id):
		self.getangle()
		errors = []
		distances = []
		constellation = self.qpsk_constellation
		if constellation_id == 'qpsk':
			constellation = self.qpsk_constellation
		elif constellation_id == 'bpsk':
			constellation = self.bpsk_constellation
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
