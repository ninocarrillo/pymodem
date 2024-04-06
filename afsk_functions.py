# afsk_functions
# Python3
# Functions for demodulating AFSK
# Nino Carrillo
# 29 Mar 2024

from scipy.signal import firwin
from math import ceil
from numpy import arange, array, sin, cos, pi, convolve, sqrt

class AFSK_modem:

	def __init__(self, sample_rate):
		self.input_sample_rate = sample_rate

	def configure(self, **kwargs):
		try:
			self.definition = kwargs.get('config', None)
		except:
			self.definition = '1200'

		if self.definition == '300':
			# set some default values for 300 bps AFSK:
			self.symbol_rate = 300.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 300.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 2500.0	# high cutoff frequency for input filter
			self.input_bpf_span = 4.80			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.mark_freq = 1600.0				# mark tone frequency
			self.space_freq = 1800.0				# space tone frequency
			self.space_gain = 1.0				# gain correction for space tone correlator
											# for optimizing emphasized audio.
											# 1.0 recommended for flat audio, around 1.7
											# for de-emphasized audio.
											# Implement multiple parallel demodulators
											# to handle general cases.
			self.output_lpf_cutoff = 200.0		# low pass filter cutoff frequency for
											# output signal after correlators
			self.output_lpf_span = 1.5			# Number of symbols to span with the output
											# filter. This is used with the sampling
											# rate to determine the tap count.
			self.correlator_span = 1.0		# correlator span in symbols
			self.correlator_offset = 0.0		# frequency offset for correlator in hz
		else:
			# set some default values for 1200 bps AFSK:
			self.symbol_rate = 1200.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 300.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 2500.0	# high cutoff frequency for input filter
			self.input_bpf_span = 4.80			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.mark_freq = 1200.0				# mark tone frequency
			self.space_freq = 2200.0				# space tone frequency
			self.space_gain = 1.0				# gain correction for space tone correlator
											# for optimizing emphasized audio.
											# 1.0 recommended for flat audio, around 1.7
											# for de-emphasized audio.
											# Implement multiple parallel demodulators
											# to handle general cases.
			self.output_lpf_cutoff = 1000.0		# low pass filter cutoff frequency for
											# output signal after correlators
			self.output_lpf_span = 1.5			# Number of symbols to span with the output
											# filter. This is used with the sampling
											# rate to determine the tap count.
			self.correlator_span = 1.0		# correlator span in symbols
			self.correlator_offset = 0.0		# frequency offset for correlator in hz

		self.tune()

	def tune(self):
		self.input_bpf_tap_count = round(
			self.input_sample_rate * self.input_bpf_span / self.symbol_rate
		)
		self.output_lpf_tap_count = round(
			self.input_sample_rate * self.output_lpf_span / self.symbol_rate
		)

		# Use scipy.signal.firwin to generate taps for input bandpass filter.
		# Input bpf is implemented as a Finite Impulse Response filter (FIR).
		self.input_bpf = firwin(
			self.input_bpf_tap_count,
			[ self.input_bpf_low_cutoff, self.input_bpf_high_cutoff ],
			pass_zero='bandpass',
			fs=self.input_sample_rate
		)

		# Use scipy.signal.firwin to generate taps for output low pass filter.
		# Output lpf is implemented as a Finite Impulse Response filter (FIR).
		# firwin defaults to hamming window if not specified.
		self.output_lpf = firwin(
			self.output_lpf_tap_count,
			self.output_lpf_cutoff,
			fs=self.input_sample_rate
		)

		# Create quadrature correlators for mark and space tones. Quadrature means
		# we will have two tone patterns at each frequency, with 90 degrees of
		# phase difference (sine and cosine).
		# First we will create an array of time indices for one symbol length.
		# Computing the time indices in steps. First, create an ascending count,
		# one count for each sample in the symbol-time.
		time_indices = arange(ceil(self.correlator_span * self.input_sample_rate / self.symbol_rate))
		# Now scale the time indices according to frequency.
		mark_indices = time_indices * (2.0 * pi * (self.mark_freq + self.correlator_offset) / self.input_sample_rate)
		# Calculate the mark waveforms.
		self.mark_correlator_i = cos(mark_indices)
		self.mark_correlator_q = sin(mark_indices)
		# Scale time indices for space tone.
		space_indices = time_indices * (2.0 * pi * (self.space_freq + self.correlator_offset) / self.input_sample_rate)
		# Calculate the space waveforms, apply space gain factor (for emphasis)
		self.space_correlator_i = self.space_gain * cos(space_indices)
		self.space_correlator_q = self.space_gain * sin(space_indices)

	def demod(self, input_audio):
		# Apply the input filter.
		audio = convolve(input_audio, self.input_bpf, 'valid')
		# Create the correlation products.
		mark_rms = sqrt(
			convolve(audio, self.mark_correlator_i, 'valid')**2
			+ convolve(audio, self.mark_correlator_q, 'valid')**2
		)
		space_rms = sqrt(
			convolve(audio, self.space_correlator_i, 'valid')**2
			+ convolve(audio, self.space_correlator_q, 'valid')**2
		)
		# The demodulated signal is mark-space:
		audio = mark_rms - space_rms
		# Apply the output filter:
		audio = convolve(audio, self.output_lpf, 'valid')
		return audio
