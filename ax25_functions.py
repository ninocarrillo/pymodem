# ax25_functions
# Python3
# Functions for manipulating an ax.25 bitstream
# Nino Carrillo
# 30 Mar 2024

from numpy import zeros, append

def initialize_decoder(min_packet_length, max_packet_length):
	decoder = {}
	decoder['working_byte'] = 0
	decoder['working_packet'] = zeros(max_packet_length)
	decoder['working_packet_byte_index'] = 0
	decoder['max_packet_length'] = max_packet_length
	decoder['min_packet_length'] = min_packet_length
	decoder['one_count'] = 0
	decoder['working_byte_bit_index'] = 0
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
				decoder['one_count'] += 1
				decoder['working_byte'] |= 0x80
				decoder['working_byte'] &= 0xFF
				decoder['working_byte_bit_index'] += 1
				if decoder['one_count'] > 6:
					# abort frame for invalid bit sequence
					decoder['working_byte_bit_index'] = 0
					decoder['working_packet_byte_index'] = 0
				elif decoder['working_byte_bit_index'] > 7:
					# Byte complete, do something with it
					decoder['working_byte_bit_index'] = 0
					decoder['working_packet'][
							decoder['working_packet_byte_index']
						] = decoder['working_byte']
					decoder['working_packet_byte_index'] += 1	
					if (
							decoder['working_packet_byte_index'] >
							decoder['max_packet_length']
					):
						# This packet exceeds max length
						decoder['working_packet_byte_index'] = 0
						# Don't treat the rest of the data before the next
						# flag as a valid packet
						decoder['stranded_data_flag'] = True
				else:
					decoder['working_byte'] >>= 1
			else:
				# this is a '0' bit
				if decoder['one_count'] < 5:
					decoder['working_byte'] &= 0x7F
					decoder['working_byte_bit_index'] += 1
					if decoder['working_byte_bit_index'] > 7:
						# Byte complete, do something with it
						decoder['working_byte_bit_index'] = 0
						decoder['working_packet'][
								decoder['working_packet_byte_index']
							] = decoder['working_byte']
						decoder['working_packet_byte_index'] += 1		
						if (
								decoder['working_packet_byte_index'] >
								decoder['max_packet_length']
						):
							# This packet exceeds max length
							decoder['working_packet_byte_index'] = 0
							# Don't treat the rest of the data before the next
							# flag as a valid packet
							decoder['stranded_data_flag'] = True
					else:
						decoder['working_byte'] >>= 1
				elif decoder['one_count'] == 5:
					# this is a stuffed zero, ignore
					pass
				elif decoder['one_count'] == 6:
					# This is a flag, check and save the packet
					print('flag ',end='')
					if (
							(
								decoder['working_packet_byte_index'] >=
								decoder['min_packet_length']
							) and (
								decoder['stranded_data_flag'] == False
							)
					):
						result.append(
							decoder['working_packet'][
								:decoder['working_packet_byte_index']
							]
						)
						print(" packet ")
					decoder['working_packet_byte_index'] = 0
					decoder['stranded_data_flag'] = False
				decoder['one_count'] = 0
			# shift input byte
			input_byte <<= 1
		# advance the working byte by one bit and bound in 8 bits
		decoder['working_byte'] <<= 1
		decoder['working_byte'] &= 0xFF
	return result
