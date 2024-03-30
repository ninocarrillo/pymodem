# afsk1200
# Python3
# Demodulate, slice, and decode packets from an audio file.
# Nino Carrillo
# 29 Mar 2024
# Exit codes
# 1 Wrong Python version
# 2 Wrong argument count
# 3 Unable to open audio file

import sys
from scipy.io.wavfile import read as readwav
import afsk_functions
import slicer_functions
import lfsr_functions

def main():
	# check correct version of Python
	if sys.version_info < (3, 0):
		print("Python version should be 3.x, exiting")
		sys.exit(1)
	# check correct number of parameters were passed to command line
	if len(sys.argv) != 2:
		print("Not enough arguments. Usage: python3 afsk1200.py <sound file>")
		sys.exit(2)
	# try to open audio file
	try:
		input_sample_rate, input_audio = readwav(sys.argv[1])
	except:
		print('Unable to open audio file.')
		sys.exit(3)
	# Initialize the AFSK Demodulator with these parameters:
	input_bpf_low_cutoff = 300.0	# low cutoff frequency for input filter
	input_bpf_high_cutoff = 5000.0	# high cutoff frequency for input filter
	input_bpf_tap_count = 115 		# FIR tap count
									# more taps = shaper cutoff, more processing
	mark_freq = 1200.0				# mark tone frequency
	space_freq = 2200.0				# space tone frequency
	space_gain = 1.0				# gain correction for space tone correlator
									# for optimizing pre-emphasized audio
	output_lpf_cutoff = 1200.0		# low pass filter cutoff frequency for
									# output signal after correlators
	output_lpf_tap_count = 39		# FIR tap count
									# more taps = shaper cutoff, more processing
	symbol_rate = 1200.0			# 1200 symbols per second (or baud)
	demodulator = afsk_functions.initialize(
		input_bpf_low_cutoff,
		input_bpf_high_cutoff,
		input_bpf_tap_count,
		mark_freq,
		space_freq,
		space_gain,
		output_lpf_cutoff,
		output_lpf_tap_count,
		input_sample_rate,
		symbol_rate
	)

	demod_audio = afsk_functions.demodulate(demodulator, input_audio)

	# Slice demodulated audio into bitstream.
	lock_rate = 0.90
	slicer = slicer_functions.initialize(
		input_sample_rate,
		symbol_rate,
		lock_rate
	)

	sliced_data = slicer_functions.slice(slicer, demod_audio)
	print(sliced_data)

	# Apply differential decoding through a linear feedback shift register.
	# The same method can be used for de-scrambling.
	# simple differential decoding, the polynomial is x + 1 or 0b11 or 0x3
	polynomial = 0x3
	invert = True
	lfsr = lfsr_functions.initialize(
		polynomial,
		invert
	)

	descrambled_data = lfsr_functions.unscramble(lfsr, sliced_data)
	print(descrambled_data)

if __name__ == "__main__":
	main()
