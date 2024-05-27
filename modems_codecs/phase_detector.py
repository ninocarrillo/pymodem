# Python3
# Functions for I/Q constellations
# Nino Carrillo
# 17 May 2024

from modems_codecs.complexmath import ComplexNumber
from math import pi, sin, atan, atan2, sqrt
from numpy import floor
from matplotlib import pyplot as plot


class PhaseDetector:
	def __init__(self, constellation_id, granularity, gain):
		self.angle = 0
		self.constellation = []
		self.constellation_id = constellation_id
		self.granularity = granularity
		self.gain = gain
		if constellation_id == 'qpsk':
			self.constellation = [45, -45, 135, -135]
		elif constellation_id == 'bpsk':
			self.constellation = [5, -175, 185]

		self.atan_table = []
		for imag in range(self.granularity):
			self.atan_table.append([])
			for real in range(self.granularity):
				self.atan_table[imag].append(gain * atan2(imag,real) * 180 / pi)
		# Table holds Quadrant 1 values (0-90 degrees)
		self.atan_table[0][0] = 0


		#fig = plot.figure()
		#ax = fig.add_subplot(projection='3d')

		self.psk_error_table = []
		for imag in range(self.granularity):
			self.psk_error_table.append([])
			for real in range(self.granularity):
				self.psk_error_table[imag].append(round(gain*((atan2(imag,real) * 180 / pi)-45)))
				#ax.scatter(real,imag,self.psk_error_table[imag][real])

		#plot.show()



	def atan2(self, imag, real):
		# returns angle in range -180, 180
		real = int(floor(real * self.granularity * .5))
		imag = int(floor(imag * self.granularity * .5))
		#real = round(real * self.granularity * .5)
		#imag = round(imag * self.granularity * .5)
		if real >= self.granularity:
			real = self.granularity - 1
		if imag >= self.granularity:
			imag = self.granularity - 1
		if real <= -self.granularity:
			real = -(self.granularity - 1)
		if imag <= -self.granularity:
			imag = -(self.granularity - 1)
		if real >= 0:
			if imag >= 0:
				# Quadrant 1
				# Direct read out of table
				self.angle = self.atan_table[imag][real]
			else:
				# Quadrant 4
				# Reflect across real axis
				# Negate result
				self.angle = -self.atan_table[-imag][real]
		else:
			if imag >=0:
				# Quadrant 2
				# Reflect across imaginary axis
				# Reflect across real axis
				# then add 90 to result
				self.angle = self.atan_table[-real][imag] + (90 * self.gain)
			else:
				# Quadrant 3
				# Reflect across both axes
				# Subtract 180 from result
				self.angle = self.atan_table[-imag][-real] - (180 * self.gain)
		return self.angle

	def get_angle_error(self, imag, real):
		if self.constellation_id == 'qpsk':
			self.atan2(imag,real)
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
		elif self.constellation_id == 'bpsk':
			self.angle_error = imag * real
		return self.angle_error

	def get_angle_error2(self, imag, real):
		real = int(floor(real * self.granularity * .5))
		imag = int(floor(imag * self.granularity * .5))
		if real >= self.granularity:
			real = self.granularity - 1
		if imag >= self.granularity:
			imag = self.granularity - 1
		if real <= -self.granularity:
			real = -(self.granularity - 1)
		if imag <= -self.granularity:
			imag = -(self.granularity - 1)
		if real >= 0:
			if imag >= 0:
				# Quadrant 1
				# Direct read out of table
				self.angle_error = self.psk_error_table[imag][real]
			else:
				# Quadrant 4
				# Reflect across real axis
				# Negate result
				self.angle_error = self.psk_error_table[real][-imag]
				#self.angle_error = 0
		else:
			if imag >=0:
				# Quadrant 2
				self.angle_error = self.psk_error_table[-real][imag]
				#self.angle_error = 0
			else:
				# Quadrant 3
				# Reflect across both axes
				# Subtract 180 from result
				self.angle_error = self.psk_error_table[-imag][-real]
				#self.angle_error = 0
		return self.angle_error
