# ax25_functions
# Python3
# Functions for manipulating an ax.25 bitstream
# Nino Carrillo
# 30 Mar 2024

from numpy import zeros, append, rint

def initialize_decoder(min_packet_length, max_packet_length):
	decoder = {}
	decoder['working_byte'] = 0
	decoder['working_packet'] = zeros(max_packet_length)
	decoder['byte_index'] = 0
	decoder['max_packet_length'] = max_packet_length
	decoder['min_packet_length'] = min_packet_length
	decoder['one_count'] = 0
	decoder['bit_index'] = 0
	decoder['stranded_data_flag'] = False
	return decoder

def decode(decoder, data):
	# create an empty list to collect decoded packets
	result = []
	for input_byte in data:
		input_byte = int(input_byte)
		for bit_index in range(8):
			if input_byte & 0x80:
				# this is a '1' bit
				decoder['working_byte'] |= 0x80
				decoder['one_count'] += 1
				decoder['bit_index'] += 1
				if decoder['one_count'] > 6:
					# abort frame for invalid bit sequence
					decoder['bit_index'] = 0
					decoder['byte_index'] = 0
				if decoder['bit_index'] == 8:
					# Byte complete, do something with it
					decoder['bit_index'] = 0
					decoder['working_packet'][
							decoder['byte_index']
						] = decoder['working_byte']
					decoder['byte_index'] += 1
					decoder['working_byte'] >>= 1
					if (
							decoder['byte_index'] >
							decoder['max_packet_length']
					):
						# This packet exceeds max length
						decoder['byte_index'] = 0
						decoder['one_count'] = 0
				else:
					#pass
					decoder['working_byte'] >>= 1
			else:
				# this is a '0' bit
				if decoder['one_count'] < 5:
					decoder['bit_index'] += 1
					if decoder['bit_index'] == 8:
						# Byte complete, do something with it
						decoder['bit_index'] = 0
						decoder['working_packet'][
								decoder['byte_index']
							] = decoder['working_byte']
						decoder['byte_index'] += 1
						if (
								decoder['byte_index'] >
								decoder['max_packet_length']
						):
							# This packet exceeds max length
							decoder['byte_index'] = 0
					else:
						decoder['working_byte'] >>= 1
				elif decoder['one_count'] == 5:
					#ignore stuffed zero
					pass
				elif decoder['one_count'] == 6:
					# This is a flag, check and save the packet
					if (
							(
								decoder['byte_index'] >=
								decoder['min_packet_length']
							) and (
								decoder['bit_index'] == 7
							)
					):
						result.append(
							decoder['working_packet'][
								:decoder['byte_index']
							].copy()
						)
					decoder['byte_index'] = 0
					decoder['bit_index'] = 0
				decoder['one_count'] = 0
			# shift input byte
			input_byte <<= 1
	return result
