# Python3
# Functions for numerically controlled oscillator
# Nino Carrillo
# 26 Apr 2024

from math import sin, pi

class NCO:
	def __init__(self, **kwargs):
		self.sample_rate = kwargs.get('sample_rate', 8000.0)
		self.amplitude = kwargs.get('amplitude', 10000.0)
		self.set_frequency = kwargs.get('set_frequency', 1500.0)
		self.wavetable_size = kwargs.get('wavetable_size', 256)

		# control is the frequency adjustment input
		self.control = 0.0

		# instantaneous phase of the oscillator in degrees
		self.phase_accumulator = 0.0

		self.wavetable=[]
		for i in range(self.wavetable_size):
			self.wavetable.append(self.amplitude * sin(i * 2.0 * pi / self.wavetable_size))

		# Calculate the phase accumulator to wavetable index scaling factor
		self.index_scaling_factor = self.wavetable_size / (2.0 * pi)

		# During each update of the NCO (once per sample), it will be advanced according to
		# set_frequency + control. Calculate the scaling factor for phase advance.
		self.phase_scaling_factor = 2.0 * pi / self.sample_rate

	def update(self):
		self.phase_accumulator += (self.phase_scaling_factor * (self.set_frequency + self.control))
		while self.phase_accumulator >= 2.0 * pi:
			self.phase_accumulator -= 2.0 * pi
		sine_phase_index = int(self.phase_accumulator * self.index_scaling_factor)
		self.sine_output = self.wavetable[sine_phase_index]
		cosine_phase_index = int(sine_phase_index + (self.wavetable_size / 4.0))
		while cosine_phase_index >= 0 :
			cosine_phase_index -= self.wavetable_size
		self.cosine_output = self.wavetable[cosine_phase_index]
