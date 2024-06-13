# afsk
# Python3
# Functions for demodulating FSK
# Nino Carrillo
# 29 Mar 2024

from scipy.signal import firwin
from math import ceil
from numpy import arange, sin, cos, pi, convolve, sqrt
from modems_codecs.rrc import RRC
from modems_codecs.string_ops import check_boolean
from modems_codecs.agc import AGC
from matplotlib import pyplot as plt

class FSKModem:

	def __init__(self, **kwargs):
		self.definition = kwargs.get('config', '9600')
		self.sample_rate = kwargs.get('sample_rate', 96000)

		self.agc_attack_rate = 1		# Normalized to full scale / sec
		self.agc_sustain_time = 0.1 # sec
		self.agc_decay_rate = 1			# Normalized to full scale / sec

		if self.definition == '9600':
			# set some default values for 9600 bps FSK:
			self.symbol_rate = 9600.0			# symbols per second (or baud)
			self.input_filter_type = 'lpf'
			self.input_lpf_cutoff = 6000.0		# low pass filter cutoff frequency for
											# input signal
			self.input_lpf_span = 1.5			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
			self.rrc_rolloff_rate = False
			self.invert = False
		elif self.definition == '4800':
			self.symbol_rate = 4800.0			# symbols per second (or baud)
			self.input_filter_type = 'lpf'
			self.input_lpf_cutoff = 3000.0		# low pass filter cutoff frequency for
											# input signal
			self.input_lpf_span = 1.5			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
			self.rrc_rolloff_rate = False
		elif self.definition == '4800-rrc':
			self.symbol_rate = 4800.0			# symbols per second (or baud)
			self.input_filter_type = 'rrc'
			self.rrc_rolloff_rate = 0.3
			self.input_lpf_span = 8			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
			self.invert = False
		else:
			# set some default values for 9600 bps FSK:
			self.symbol_rate = 9600.0			# symbols per second (or baud)
			self.input_lpf_cutoff = 6000.0		# low pass filter cutoff frequency for
			self.input_filter_type = 'lpf'
											# input signal
			self.input_lpf_span = 1.5			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
			self.invert = False
			self.rrc_rolloff_rate = False

		self.tune()




	def StringOptionsRetune(self, options):
		self.invert = check_boolean(options.get('invert', "false"))

		self.tune()

	def tune(self):
		self.input_lpf_tap_count = round(
			self.sample_rate * self.input_lpf_span / self.symbol_rate
		)

		if self.input_filter_type == 'rrc':
			print('Generating RRC taps.')
			self.rrc = RRC(
				sample_rate = self.sample_rate,
				symbol_rate = self.symbol_rate,
				symbol_span = self.input_lpf_span,
				rolloff_rate = self.rrc_rolloff_rate
			)
			self.input_lpf = self.rrc.taps
		elif self.input_filter_type == 'lpf':
			print('Generating LPF taps.')
			# Use scipy.signal.firwin to generate taps for input bandpass filter.
			# Input bpf is implemented as a Finite Impulse Response filter (FIR).
			self.input_lpf = firwin(
				self.input_lpf_tap_count,
				[ self.input_lpf_cutoff ],
				pass_zero='lowpass',
				fs=self.sample_rate
			)

		self.AGC = AGC(
			sample_rate = self.sample_rate,
			attack_rate = self.agc_attack_rate,
			sustain_time = self.agc_sustain_time,
			decay_rate = self.agc_decay_rate,
			target_amplitude = 1.0,
			record_envelope = True
		)

	def demod(self, input_audio):
		# Apply the input filter.
		audio = convolve(input_audio, self.input_lpf, 'valid')
		if self.invert:
			audio = -audio
		# perform AGC on the audio samples, saving over the original samples
		self.AGC.apply(audio)
		#plt.figure()
		#plt.plot(audio)
		#plt.plot(self.AGC.envelope_buffer)
		#plt.show()
		return audio
