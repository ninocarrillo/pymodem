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
	# initialize the AFSK Demodulator with these parameters:
	input_bpf_low_cutoff = 300.0	# low cutoff frequency for input filter
	input_bpf_high_cutoff = 5000.0	# high cutoff frequency for input filter
	mark_freq = 1200.0				# mark tone frequency
	space_freq = 2200.0				# space tone frequency
	space_gain = 1.0				# gain correction for space tone correlator
									# for optimizing pre-emphasized audio
	output_lpf_cutoff = 800.0		# low pass filter cutoff frequency for
									# output signal after correlators
	symbol_rate = 1200.0			# 1200 symbols per second (or baud)
	demodulator = afsk_functions.initialize(
		input_bpf_low_cutoff,
		input_bpf_high_cutoff,
		mark_freq,
		space_freq,
		space_gain,
		output_lpf_cutoff,
		input_sample_rate,
		symbol_rate
	)

	demod_audio = afsk_functions.demodulate(demodulator, input_audio)

if __name__ == "__main__":
	main()
