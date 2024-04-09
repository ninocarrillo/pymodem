# afsk
# Python3
# Functions for demodulating PSK
# Nino Carrillo
# 9 Apr 2024

from scipy.signal import firwin
from math import ceil, sin, pi
from numpy import convolve

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
		in_phase_index = int(self.phase_accumulator * self.index_scaling_factor)
		self.in_phase_output = self.wavetable[in_phase_index]
		quadrature_phase_index = int(in_phase_index + (self.wavetable_size / 4.0))
		while quadrature_phase_index >= self.wavetable_size:
			quadrature_phase_index -= self.wavetable_size
		self.quadrature_phase_output = self.wavetable[quadrature_phase_index]
		
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
		self.sustain_increment = self.sustain_time / self.sample_rate
		self.envelope = 0
		self.normal = 1.0
		self.envelope_buffer = []

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
				self.envelope_buffer.append(self.envelope)
			
			i += 1
		

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

		self.AGC = AGC(
			sample_rate = self.sample_rate,
			attack_rate = self.agc_attack_rate,
			sustain_time = self.agc_sustain_time,
			decay_rate = self.agc_decay_rate,
			target_amplitude = self.oscillator_amplitude,
			record_envelope = True
		)
		
		self.NCO = NCO(
			sample_rate = self.sample_rate,
			amplitude = self.oscillator_amplitude,
			set_frequency = self.carrier_freq,
			wavetable_size = 256
		)
		
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



	def demod(self, input_audio):
		# Apply the input filter.
		audio = convolve(input_audio, self.input_bpf, 'valid')

		# perform AGC on the audio samples, saving over the original samples
		self.AGC.apply(audio)

		self.i_oscillator_output = []
		self.q_oscillator_output = []
		for sample in audio:
			self.NCO.update()
			self.i_oscillator_output.append(self.NCO.in_phase_output)
			self.q_oscillator_output.append(self.NCO.quadrature_phase_output)
			# do the costas loop
	

		# Apply the output filter:
		#audio = convolve(audio, self.output_lpf, 'valid')
		return audio



