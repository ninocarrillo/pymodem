# afsk_functions
# Python3
# Functions for demodulating AFSK
# Nino Carrillo
# 29 Mar 2024

from scipy.signal import firwin
from math import ceil
from numpy import arange, array, sin, cos, pi, convolve, sqrt

def initialize(
		input_bpf_low_cutoff,
		input_bpf_high_cutoff,
		input_bpf_tap_count,
		mark_freq,
		space_freq,
		space_gain,
		output_lpf_cutoff,
		output_lpf_tap_count,
		sample_rate,
		symbol_rate
	):
	# Create an empty dictionary to hold demodulator parameters.
	demodulator = {}
	# Use scipy.signal.firwin to generate taps for input bandpass filter.
	# Input bpf is implemented as a Finite Impulse Response filter (FIR).
	demodulator['input_bpf'] = firwin(
		input_bpf_tap_count,
		[ input_bpf_low_cutoff/sample_rate, input_bpf_high_cutoff/sample_rate ],
		pass_zero='bandpass'
	)

	# Use scipy.signal.firwin to generate taps for output low pass filter.
	# Output lpf is implemented as a Finite Impulse Response filter (FIR).
	# firwin defaults to hamming window if not specified.
	demodulator['output_lpf'] = firwin(
		output_lpf_tap_count,
		output_lpf_cutoff/sample_rate
	)

	# Create quadrature correlators for mark and space tones. Quadrature means
	# we will have two tone patterns at each frequency, with 90 degrees of
	# phase difference (sine and cosine).
	# First we will create an array of time indices for one symbol length.
	# Computing the time indices in steps. First, create an ascending count,
	# one count for each sample in the symbol-time.
	time_indices = arange(ceil(sample_rate / symbol_rate))
	# Now scale the time indices according to frequency.
	mark_indices = time_indices * (2.0 * pi * mark_freq / sample_rate)
	# Calculate the mark waveforms.
	demodulator['mark_correlator_i'] = cos(mark_indices)
	demodulator['mark_correlator_q'] = sin(mark_indices)
	# Scale time indices for space tone.
	space_indices = time_indices * (2.0 * pi * space_freq / sample_rate)
	# Calculate the space waveforms, apply space gain factor (for emphasis)
	demodulator['space_correlator_i'] = space_gain * cos(space_indices)
	demodulator['space_correlator_q'] = space_gain * sin(space_indices)
	return demodulator

def demodulate(demodulator, input_audio):
	# Apply the input filter.
	audio = convolve(input_audio, demodulator['input_bpf'], 'valid')
	# Create the correlation products.
	mark_rms = sqrt(
		convolve(audio, demodulator['mark_correlator_i'], 'valid')**2
		+ convolve(audio, demodulator['mark_correlator_q'], 'valid')**2
	)
	space_rms = sqrt(
		convolve(audio, demodulator['space_correlator_i'], 'valid')**2
		+ convolve(audio, demodulator['space_correlator_q'], 'valid')**2
	)
	# The demodulated signal is mark-space:
	audio = mark_rms - space_rms
	# Apply the output filter:
	audio = convolve(audio, demodulator['output_lpf'], 'valid')
	return audio
