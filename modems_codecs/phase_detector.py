# Python3
# Functions for I/Q constellations
# Nino Carrillo
# 17 May 2024

from modems_codecs.complexmath import ComplexNumber
from math import pi, sin, atan, atan2, sqrt
from matplotlib import pyplot as plot


class PhaseDetector:
	def __init__(self, constellation_id, granularity, gain):
		self.angle = 0
		self.constellation = []
		self.constellation_id = constellation_id
		self.granularity = granularity
		if constellation_id == 'qpsk':
			self.constellation = [45, -45, 135, -135]
		elif constellation_id == 'bpsk':
			self.constellation = [-180, 0, 180]
		
		self.atan_table = []
		for imag in range(self.granularity):
			self.atan_table.append([])
			for real in range(self.granularity):
				self.atan_table[imag].append(gain * atan2(imag,real) * 180 / pi)

		self.atan_table[0][0] = 0

		
	def atan2(self, imag, real):
		real = round(real * self.granularity)
		imag = round(imag * self.granularity)
		if real > 0:
			if imag >= 0:
				self.angle = self.atan_table[imag][real]
			else:
				self.angle = -self.atan_table[-imag][real]
		
		return self.angle
	
	def atan(self, imag, real):
		return self.angle

	def getangle(self, imag, real):
		if real < 0:
			real = -real
			imag = -imag
		real = round(real * self.granularity)
		imag = round(imag * self.granularity)
		if imag >= 0:
			self.angle = self.atan_table[imag][real]
		else:
			self.angle = -atan2(-imag,real) * 180 / pi

		return self.angle



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
