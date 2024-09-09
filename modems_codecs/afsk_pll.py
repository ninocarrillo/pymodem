# Python3
# Functions for demodulating slow AFSK with a PLL
# Nino Carrillo
# 26 Apr 2024

from scipy.signal import firwin
from math import ceil, sin, pi
from numpy import convolve, zeros, log
from modems_codecs.agc import AGC
from modems_codecs.rrc import RRC
from modems_codecs.data_classes import IQData
from modems_codecs.pi_control import PI_control
from modems_codecs.iir import IIR_1
from modems_codecs.nco import NCO
from matplotlib import pyplot as plot

class AFSKPLLModem:

	def __init__(self, **kwargs):
		self.definition = kwargs.get('config', '300')
		self.sample_rate = kwargs.get('sample_rate', 8000.0)

		if self.definition == '300':
			# set some default values for 300 bps AFSK:
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1.0	# sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 300.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 1500.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 1900.0	# high cutoff frequency for input filter
			self.input_bpf_span = 6.0		# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.carrier_freq = 1700.0				# carrier tone frequency
			self.output_lpf_cutoff = 350.0		# low pass filter cutoff frequency for
											# output signal after I/Q demodulation
			self.output_lpf_span = 1.5			# Number of symbols to span with the output
			self.max_freq_offset = 50*1.25
			self.LoopFilter = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=150.0,
				gain=1.0
			)
			pi_p = 0.3
			pi_i = pi_p/6000
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= 1800
			)

		self.oscillator_amplitude = 1.0



		self.tune()

	def retune(self, **kwargs):
		self.symbol_rate = kwargs.get('symbol_rate', self.symbol_rate)
		self.input_bpf_low_cutoff = kwargs.get('input_bpf_low_cutoff', self.input_bpf_low_cutoff)
		self.input_bpf_high_cutoff = kwargs.get('input_bpf_high_cutoff', self.input_bpf_high_cutoff)
		self.input_bpf_span = kwargs.get('input_bpf_span', self.input_bpf_span)
		self.output_lpf_cutoff = kwargs.get('output_lpf_cutoff', self.output_lpf_cutoff)
		self.output_lpf_span = kwargs.get('output_lpf_span', self.output_lpf_span)
		self.sample_rate = kwargs.get('sample_rate', self.sample_rate)
		self.carrier_freq = kwargs.get('carrier_freq', self.carrier_freq)
		self.tune()

	def StringOptionsRetune(self, options):
		self.symbol_rate = float(options.get('symbol_rate', self.symbol_rate))
		self.input_bpf_low_cutoff = float(options.get('input_bpf_low_cutoff', self.input_bpf_low_cutoff))
		self.input_bpf_high_cutoff = float(options.get('input_bpf_high_cutoff', self.input_bpf_high_cutoff))
		self.input_bpf_span = float(options.get('input_bpf_span', self.input_bpf_span))
		self.output_lpf_cutoff = float(options.get('output_lpf_cutoff', self.output_lpf_cutoff))
		self.output_lpf_span = float(options.get('output_lpf_span', self.output_lpf_span))
		self.sample_rate = float(options.get('sample_rate', self.sample_rate))
		self.carrier_freq = float(options.get('carrier_freq', self.carrier_freq))
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

		# print("Sample Rate: ", self.sample_rate)
		# print("Input BPF Tap Count: ", len(self.input_bpf))
		# print("Input BPF Taps: ")
		# for tap in self.input_bpf:
		# 	print(int(round(tap * 32768,0)), end=', ')
		# print(" ")

		# print("Output LPF Tap Count: ", len(self.output_lpf))
		# print("Output LPF Taps: ")
		# for tap in self.input_bpf:
		# 	print(int(round(tap * 32768,0)), end=', ')
		# print(" ")

		self.AGC = AGC(
			sample_rate = self.sample_rate,
			attack_rate = self.agc_attack_rate,
			sustain_time = self.agc_sustain_time,
			decay_rate = self.agc_decay_rate,
			target_amplitude = self.oscillator_amplitude,
			record_envelope = False
		)

		self.NCO = NCO(
			sample_rate = self.sample_rate,
			amplitude = self.oscillator_amplitude,
			set_frequency = self.carrier_freq,
			wavetable_size = 256
		)
		self.output_sample_rate = self.sample_rate

	def demod(self, input_audio):
		instantaneous_power = []
		power_sampling_filter = firwin(
			int(self.sample_rate / 50),
			[ 3000 ],
			pass_zero='lowpass',
			fs=self.sample_rate,
			scale=True
		)
		power_audio = convolve(input_audio, power_sampling_filter)
		for power_sample in power_audio:
			instantaneous_power.append(10*log(power_sample**2))

		# Apply the input filter.
		audio = convolve(input_audio, self.input_bpf, 'valid')

		# perform AGC on the audio samples, saving over the original samples
		self.AGC.apply(audio)

		self.loop_output = []
		self.pi_i = []
		self.pi_p = []
		demod_audio = []
		# This is the PLL
		for sample in audio:
			self.NCO.update()
			# mix the in phase oscillator output with the input signal
			mixer = sample * self.NCO.sine_output
			# low pass filter this product
			self.LoopFilter.update(mixer)
			# use a P-I control feedback arrangement to update the oscillator frequency
			self.NCO.control = self.FeedbackController.update_saturate(self.LoopFilter.output)
			self.loop_output.append(self.NCO.control)
			#demod_audio.append(self.I_LPF.output)
			demod_audio.append(self.FeedbackController.proportional)
			self.pi_p.append(self.FeedbackController.proportional)
			self.pi_i.append(self.FeedbackController.integral)

		# Apply the output filter:
		demod_audio = convolve(demod_audio, self.output_lpf, 'valid')

		power_filter = firwin(
			int(self.sample_rate / 10),
			[ 30 ],
			pass_zero='lowpass',
			fs=self.sample_rate,
			scale=True
		)
		#plot.figure()
		#plot.plot(convolve(instantaneous_power, power_filter))
		#plot.show()

		return demod_audio
