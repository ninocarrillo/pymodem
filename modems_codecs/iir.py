# Python3
# Functions for infinite impulse response filters
# Nino Carrillo
# 26 Apr 2024

from math import tan, pi

class IIR_1:
	def __init__(self, **kwargs):
		self.sample_rate = kwargs.get('sample_rate', 8000.0)
		self.filter_type = kwargs.get('filter_type', 'lpf')
		self.cutoff_freq = kwargs.get('cutoff', 100.0)
		self.gain = kwargs.get('gain', 2.0)

		radian_cutoff = 2.0 * pi * self.cutoff_freq

		if self.filter_type == 'lpf':
			# prewarp the cutoff frequency for bilinear Z transform
			warp_cutoff = 2.0 * self.sample_rate * tan(radian_cutoff / (2.0 * self.sample_rate))
			# calculate an intermediate value for bilinear Z transform
			omega_T = warp_cutoff / self.sample_rate
			# calculate denominator value
			a1 = (2.0 - omega_T) / (2.0 + omega_T)
			# calculate numerator values
			b0 = omega_T / (2.0 + omega_T)
			b1 = b0
			# save the coefs
			self.b_coefs = [self.gain * b0, self.gain * b1]
			self.a_coefs = [0.0, a1]

		self.output = 0.0
		self.X = [0.0, 0.0]
		self.Y = [0.0, 0.0]
		self.order = 1
		#print(self.a_coefs)
		#print(self.b_coefs)

	def update(self, sample):
		# Update the input delay registers
		for index in range(self.order, 0, -1):
			self.X[index] = self.X[index - 1]
		self.X[0] = sample
		# Calculate the intermediate sum
		v = 0
		for index in range(self.order + 1):
			v += (self.X[index] * self.b_coefs[index])
		# Update the output delay registers
		for index in range(self.order, 0, -1):
			self.Y[index] = self.Y[index - 1]
		# Calculate the final sum
		for index in range(1, self.order + 1):
			v += (self.Y[index] * self.a_coefs[index])
		self.Y[0] = v
		self.output = v
