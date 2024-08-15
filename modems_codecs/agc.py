# Python3
# Functions for implementing AGC
# Nino Carrillo
# 9 Apr 2024

class AGC:
	def __init__(self, **kwargs):
		self.attack_rate = kwargs.get('attack_rate', 500.0)
		self.decay_rate = kwargs.get('decay_rate', 50.0)
		self.sustain_time = kwargs.get('sustain_time', 1.0)
		self.sample_rate = kwargs.get('sample_rate', 8000.0)
		self.target_amplitude = kwargs.get('target_amplitude', 10000.0)
		self.record_envelope = kwargs.get('record_envelope', False)
		# adjust the agc attack and decay rates to per-sample values
		self.scaled_attack_rate = self.attack_rate / self.sample_rate
		self.scaled_decay_rate = self.decay_rate / self.sample_rate
		self.sustain_increment = 1 / self.sample_rate
		self.envelope = 0
		self.positive_envelope = 0
		self.negative_envelope = 0
		self.zero = 0
		self.normal = 1.0
		self.envelope_buffer = []
		self.sustain_count = 0

	def peak_detect(self, sample):
		compare_value = abs(sample)
		if compare_value > self.envelope:
			self.envelope += (self.scaled_attack_rate * self.normal)
			if self.envelope > compare_value:
				self.envelope = compare_value
			self.sustain_count = 0.0
		if self.sustain_count >= self.sustain_time:
			self.envelope -= (self.scaled_decay_rate * self.normal)
			if self.envelope < 0:
				self.envelope = 0
		self.sustain_count += self.sustain_increment

	def simple_peak_detect(self, sample):
		if sample > self.positive_envelope:
			self.positive_envelope += self.attack_rate
			if self.positive_envelope > sample:
				self.positive_envelope = sample
			self.sustain_count = 0.0
		elif sample < self.negative_envelope:
			self.negative_envelope -= self.attack_rate
			if self.negative_envelope < sample:
				self.negative_envelope = sample
			self.sustain_count = 0.0
		if self.sustain_count >= self.sustain_time:
			self.positive_envelope -= self.decay_rate
			if self.positive_envelope < 0:
				self.positive_envelope = 0
			self.negative_envelope += self.decay_rate
			if self.negative_envelope > 0:
				self.negative_envelope = 0
		self.envelope = (self.positive_envelope - self.negative_envelope) / 2
		self.zero = self.negative_envelope + self.envelope
		self.sustain_count += self.sustain_increment

	def apply(self, buffer):
		# This routine applies a scaling factor to each sample in buffer.
		# The scaling factor is determined by the detected envelope.

		# For the agc attack and decay rates to makes sense, we need to have
		# some pre-knowledge about the maximum possible value of the data stream.
		self.normal = max(buffer)
		self.envelope_buffer = []
		i = 0
		for sample in buffer:
			# detect the Envelope
			self.peak_detect(sample)
			# scale the sample
			# This will drive the signal stream to match the local oscillator amplitude
			if self.envelope!= 0:
				buffer[i] =  self.target_amplitude * sample / (self.envelope)
			if self.record_envelope:
				self.envelope_buffer.append(self.envelope / self.normal)

			i += 1
