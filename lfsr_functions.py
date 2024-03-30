# lfsr_functions
# Python3
# Functions for performing descrambling through linear feedback shift registers
# Nino Carrillo
# 30 Mar 2024

from numpy import zeros

def initialize(polynomial, invert):
	# Create an empty dictionary to hold slicer parameters.
	lfsr = {}
	lfsr['polynomial'] = polynomial
	lfsr['invert'] = invert
	lfsr['shift_register'] = int(0)
	return lfsr

def unscramble(lfsr, data):
	# this process creates one output byte for each input byte
	# create an array for the result
	result = zeros(len(data))
	# step through each input byte
	# and in each input byte, operate on each bit
	working_byte = int(0)
	result_index = 0
	for input_byte in data:
		input_byte = int(input_byte)
		# cycle through each bit in this byte
		for bit_index in range(8):
			# make room in working byte for a new bit
			working_byte <<= 1
			working_byte &= 0xFF
			# advance the lfsr shift register 1 bit
			lfsr['shift_register'] >>= 1
			# msb is first, sample it
			if input_byte & 0x80:
				# if the msb is 1, xor the polynomial into the shift register
				lfsr['shift_register'] ^= lfsr['polynomial']
			input_byte <<= 1
			working_byte |= lfsr['shift_register'] & 1
		# 8 bits have been processed, save the byte
		if lfsr['invert']:
			result[result_index] = 0xFF - working_byte
		else:
			result[result_index] = working_byte
		result_index += 1
	return result
