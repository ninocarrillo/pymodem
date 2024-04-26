# Python3
# Functions for proportional-integral feedback control
# Nino Carrillo
# 26 Apr 2024

class PI_control:
	def __init__(self, **kwargs):
		self.p_rate = kwargs.get('p', 0.1)
		self.i_rate = kwargs.get('i', 0.1)
		self.i_limit = kwargs.get('i_limit', 100.0)
		self.gain = kwargs.get('gain', 1000.0)
		self.integral = 0.0
		self.proportional = 0.0

	def update_reset(self, sample):
		self.proportional = self.gain * self.p_rate * sample
		self.integral += self.gain * (self.i_rate * sample)
		if abs(self.integral) > self.i_limit:
			self.integral = 0.0
		self.output = self.proportional + self.integral

		return self.output
