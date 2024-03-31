# slicer_functions
# Python3
# Functions for bit-slicing a sample stream
# Nino Carrillo
# 30 Mar 2024

from numpy import zeros, uint8

def initialize(
		sample_rate,
		symbol_rate,
		lock_rate
	):
	# Create an empty dictionary to hold slicer parameters.
	slicer = {}
	slicer['phase_clock'] = 0.0
	slicer['samples_per_symbol'] = sample_rate / symbol_rate
	slicer['rollover_threshold'] = slicer['samples_per_symbol'] / 2.0
	slicer['working_byte'] = 0
	slicer['working_bit_count'] = 0
	slicer['lock_rate'] = lock_rate
	slicer['last_sample'] = 0.0
	return slicer

def slice(slicer, samples):
	# This function will attempt to resynchronize a 2-level symbol stream,
	# make binary bit decisions at resynchronized symbol centers, and store the
	# resulting bitstream packed into an int array.
	#
	# phase_clock will be incremented every sample, by 1.0
	# when phase_clock meets or exceeds rollover_threshold:
	#    - evaluate the bit (this should be midpoint of the bit)
	#    - subtract samples_per_symbol from phase_clock
	# sample stream zero-crossings should happen when phase_clock = 0, if
	# it is synchronized. When zero-crossing is detected in sample stream,
	# multiply phase_clock by lock_rate (positive number less than 1.0)
	# this causes phase_clock to converge to synchronization
	#
	# over-estimate how many bytes we will slice out of this sample stream
	estimated_bit_count = len(samples) / slicer['samples_per_symbol']
	estimated_byte_count = int((estimated_bit_count * 1.5) / 8)
	# create an array where bit decisions will be saved
	result = zeros(estimated_byte_count)
	result_index = 0
	for sample in samples:
		# increment phase_clock
		slicer['phase_clock'] += 1.0
		# check for symbol center
		if slicer['phase_clock'] >= slicer['rollover_threshold']:
			# at or past symbol center, reset phase_clock
			slicer['phase_clock'] -= slicer['samples_per_symbol']
			# shift and bound the working byte
			slicer['working_byte'] = (slicer['working_byte'] << 1) & 0xFF
			# make a bit decision
			if sample >= 0:
				# this is a '1' bit
				slicer['working_byte'] |= 1
				# zero bit case is handled by default through the shift operator
			# save this bit into the lsb of the working_byte
			slicer['working_bit_count'] += 1
			# after 8 bits, save this byte in the result array and reset bit
			# count
			if slicer['working_bit_count'] >= 8:
				slicer['working_bit_count'] = 0
				result[result_index] = slicer['working_byte']
				result_index += 1
		# check for zero-crossing in sample stream
		if (
				(slicer['last_sample'] < 0.0 and sample >= 0.0)
				or (slicer['last_sample'] >= 0.0 and sample < 0.0)
			):
			# zero crossing detected, adjust phase_clock
			slicer['phase_clock'] = slicer['phase_clock'] * slicer['lock_rate']
		# save this sample to compare with the next for zero-crossing detect
		slicer['last_sample'] = sample
	# trim the unused byte positions in the result array
	result = result[:result_index]
	return result
