# afsk
# Python3
# Functions for demodulating PSK
# Nino Carrillo
# 9 Apr 2024

from scipy.signal import firwin
from math import ceil, sin
from numpy import convolve

class NCO:
	def __init__(self, **kwargs):
		self.sample_rate = kwargs.get('sample_rate', 8000.0)
		self.amplitude = kwargs.get('amplitude', 10000.0)
		self.set_frequency = kwargs.get('set_frequency', 1500.0)
		
		# control is the frequency adjustment input
		self.control = 0.0
		
		# instantaneous phase of the oscillator (radians)
		self.phase_accumulator = 0.0
		
	def update(self):
		pass
		

class BPSKModem:

	def __init__(self, **kwargs):
		self.definition = kwargs.get('config', '300')
		self.sample_rate = kwargs.get('sample_rate', 8000.0)

		if self.definition == '300':
			# set some default values for 300 bps AFSK:
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1.0	# sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 300.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 1200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 1800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 4.80			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.output_lpf_cutoff = 200.0		# low pass filter cutoff frequency for
											# output signal after I/Q demodulation
			self.output_lpf_span = 1.5			# Number of symbols to span with the output
			
		self.oscillator_amplitude = 10000.0
		
		self.oscillator = NCO(sample_rate=self.sample_rate, amplitude=self.oscillator_amplitude, set_frequency=self.carrier_freq)
		


		self.tune()

	def retune(self, **kwargs):
		self.symbol_rate = kwargs.get('symbol_rate', self.symbol_rate)
		self.input_bpf_low_cutoff = kwargs.get('input_bpf_low_cutoff', self.input_bpf_low_cutoff)
		self.input_bpf_high_cutoff = kwargs.get('input_bpf_high_cutoff', self.input_bpf_high_cutoff)
		self.input_bpf_span = kwargs.get('input_bpf_span', self.input_bpf_span)
		self.mark_freq = kwargs.get('mark_freq', self.mark_freq)
		self.output_lpf_cutoff = kwargs.get('output_lpf_cutoff', self.output_lpf_cutoff)
		self.output_lpf_span = kwargs.get('output_lpf_span', self.output_lpf_span)
		self.sample_rate = kwargs.get('sample_rate', self.sample_rate)

		self.tune()

	def tune(self):
		self.input_bpf_tap_count = round(
			self.sample_rate * self.input_bpf_span / self.symbol_rate
		)
		self.output_lpf_tap_count = round(
			self.sample_rate * self.output_lpf_span / self.symbol_rate
		)

		# Use scipy.signal.firwin to generate taps for input bandpass filter.
		# Input bpf is implemented as a Finite Impulse Response filter (FIR).
		self.input_bpf = firwin(
			self.input_bpf_tap_count,
			[ self.input_bpf_low_cutoff, self.input_bpf_high_cutoff ],
			pass_zero='bandpass',
			fs=self.sample_rate,
			scale=True
		)

		# Use scipy.signal.firwin to generate taps for output low pass filter.
		# Output lpf is implemented as a Finite Impulse Response filter (FIR).
		# firwin defaults to hamming window if not specified.
		self.output_lpf = firwin(
			self.output_lpf_tap_count,
			self.output_lpf_cutoff,
			fs=self.sample_rate,
			scale=True
		)

		self.envelope = 0
		# adjust the agc attack and decay rates to per-sample values
		self.scaled_agc_attack_rate = self.agc_attack_rate / self.sample_rate
		self.scaled_agc_decay_rate = self.agc_decay_rate / self.sample_rate
		self.sustain_increment = self.agc_sustain_time / self.sample_rate


	def demod(self, input_audio):
		# Apply the input filter.
		audio = convolve(input_audio, self.input_bpf, 'valid')

		self.do_agc(audio)

		for sample in audio:
			# do the costas loop
			pass

		# Apply the output filter:
		#audio = convolve(audio, self.output_lpf, 'valid')
		return audio

	def peak_detect(self, sample):
		compare_value = abs(sample)
		if compare_value > self.envelope:
			self.envelope += (self.scaled_agc_attack_rate * self.agc_normal)
			if self.envelope > compare_value:
				self.envelope = compare_value
			self.sustain_count = 0.0
		if self.sustain_count >= self.agc_sustain_time:
			self.envelope -= (self.scaled_agc_decay_rate * self.agc_normal)
			if self.envelope < 0:
				self.envelope = 0
		self.sustain_count += self.sustain_increment

	def do_agc(self, buffer):
		# This routine applies a scaling factor to each sample in buffer.
		# The scaling factor is determined by the detected envelope.

		# For the agc attack and decay rates to makes sense, we need to have
		# some pre-knowledge about the maximum possible value of the data stream.
		self.agc_normal = max(buffer)
		self.envelope_buffer = []
		self.original_sample_buffer = []
		i = 0
		for sample in buffer:
			# detect the Envelope
			self.peak_detect(sample)
			# scale the sample
			# This will drive the signal stream to match the local oscillator amplitude
			if self.envelope!= 0:
				buffer[i] =  self.oscillator_amplitude * sample / (self.envelope)
			self.envelope_buffer.append(self.envelope)
			
			i += 1

