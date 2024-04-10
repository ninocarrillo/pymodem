# afsk
# Python3
# Functions for demodulating PSK
# Nino Carrillo
# 9 Apr 2024

from scipy.signal import firwin
from math import ceil, tan,sin, pi
from numpy import convolve

class PI_control:
	def __init__(self, **kwargs):
		self.p_rate = kwargs.get('p', 0.1)
		self.i_rate = kwargs.get('i', 0.1)
		self.i_limit = kwargs.get('i_limit', 100.0)
		self.integral = 0.0
		self.proportional = 0.0

	def update_reset(self, sample):
		self.proportional = self.p_rate * sample
		self.integral += self.i_rate * sample
		if self.integral > self.i_limit:
			self.integral = 0.0
		self.output = self.proportional + self.integral

		return self.output


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
		while quadrature_phase_index >= 0 :
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
			self.max_freq_offset = 50.0
			self.I_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=300.0,
				gain=4.0
			)
			self.Q_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=300.0,
				gain=4.0
			)
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=100.0,
				gain=2.0
			)
			self.FeedbackController = PI_control(
				p= 0.05,
				i= 0.0001,
				i_limit=self.max_freq_offset
			)

		self.oscillator_amplitude = 1.0

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

		self.i_output = []
		self.q_output = []
		self.loop_output = []
		demod_audio = []
		# This is a costas loop
		for sample in audio:
			self.NCO.update()
			# mix the in phase oscillator output with the input signal
			i_mixer = sample * self.NCO.in_phase_output
			# low pass filter this product
			self.I_LPF.update(i_mixer)
			self.i_output.append(self.I_LPF.output)
			# mix the quadrature phase oscillator output with the input signal
			q_mixer = sample * self.NCO.quadrature_phase_output
			# low pass filter this product
			self.Q_LPF.update(q_mixer)
			self.q_output.append(self.Q_LPF.output)
			# mix the I and Q products to create the phase detector
			loop_mixer = self.I_LPF.output * self.Q_LPF.output
			# low pass filter this product
			self.Loop_LPF.update(loop_mixer)
			# use a P-I control feedback arrangement to update the oscillator frequency
			self.NCO.control = 50 * self.FeedbackController.update_reset(self.Loop_LPF.output)
			self.loop_output.append(self.NCO.control)
			demod_audio.append(self.I_LPF.output)



		# Apply the output filter:
		demod_audio = convolve(demod_audio, self.output_lpf, 'valid')
		return demod_audio