# il2p_functions
# Python3
# Functions for decoding and encoding IL2P packets
# Nino Carrillo
# 1 Apr 2024

from numpy import zeros, append, rint

def initialize_decoder():
	decoder = {}
	decoder['state'] = 'sync_search'
	decoder['working_word'] = int(0xFFFFFF)
	decoder['sync_tolerance'] = 1
	decoder['rx_buffer'] = zeros(1200)
	decoder['bit_index'] = 0
	decoder['byte_index'] = 0
	return decoder

def bit_distance_24(data_a, data_b):
	Distance8 = [
    0, 1, 1, 2, 1, 2, 2, 3,
    1, 2, 2, 3, 2, 3, 3, 4,
    1, 2, 2, 3, 2, 3, 3, 4,
    2, 3, 3, 4, 3, 4, 4, 5,
    1, 2, 2, 3, 2, 3, 3, 4,
    2, 3, 3, 4, 3, 4, 4, 5,
    2, 3, 3, 4, 3, 4, 4, 5,
    3, 4, 4, 5, 4, 5, 5, 6,
    1, 2, 2, 3, 2, 3, 3, 4,
    2, 3, 3, 4, 3, 4, 4, 5,
    2, 3, 3, 4, 3, 4, 4, 5,
    3, 4, 4, 5, 4, 5, 5, 6,
    2, 3, 3, 4, 3, 4, 4, 5,
    3, 4, 4, 5, 4, 5, 5, 6,
    3, 4, 4, 5, 4, 5, 5, 6,
    4, 5, 5, 6, 5, 6, 6, 7,
    1, 2, 2, 3, 2, 3, 3, 4,
    2, 3, 3, 4, 3, 4, 4, 5,
    2, 3, 3, 4, 3, 4, 4, 5,
    3, 4, 4, 5, 4, 5, 5, 6,
    2, 3, 3, 4, 3, 4, 4, 5,
    3, 4, 4, 5, 4, 5, 5, 6,
    3, 4, 4, 5, 4, 5, 5, 6,
    4, 5, 5, 6, 5, 6, 6, 7,
    2, 3, 3, 4, 3, 4, 4, 5,
    3, 4, 4, 5, 4, 5, 5, 6,
    3, 4, 4, 5, 4, 5, 5, 6,
    4, 5, 5, 6, 5, 6, 6, 7,
    3, 4, 4, 5, 4, 5, 5, 6,
    4, 5, 5, 6, 5, 6, 6, 7,
    4, 5, 5, 6, 5, 6, 6, 7,
    5, 6, 6, 7, 6, 7, 7, 8]
	result = 0
	for index in range(3):
		a = data_a & 0xFF
		b = data_b & 0xFF
		data_a >>= 8
		data_b >>= 8
		result += Distance8[a ^ b]
	return result

def decode(decoder, data):
	count = 0
	for input_byte in data:
		input_byte = int(input_byte)
		for bit_index in range(8):
			if decoder['state'] == 'sync_search':
				decoder['working_word'] <<= 1
				decoder['working_word'] &= 0xFFFFFF
				if input_byte & 0x80:
					decoder['working_word'] |= 1
				input_byte <<= 1
				if bit_distance_24(decoder['working_word'], 0xF15E48) <= decoder['sync_tolerance']:
					count += 1
					print('sync', count)
					decoder['state'] = 'rx_header'
			elif decoder['state'] == 'rx_header':
				decoder['bit_index'] += 1
				decoder['working_word'] <<= 1
				decoder['working_word'] &= 0xFF
				if input_byte & 0x80:
					decoder['working_word'] |= 1
				input_byte <<= 1
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['rx_buffer'][decoder['byte_index']] = decoder['working_word']
					decoder['byte_index'] += 1
					if decoder['byte_index'] == 15:
						decoder['byte_index'] = 0
						print('header: ', decoder['rx_buffer'][:15])
						decoder['state'] = 'sync_search'
			elif decoder['state'] == 'rx_bigblocks':
				pass
			elif decoder['state'] ==  'rx_smallblocks':
				pass
			elif decoder['state'] == 'rx_trailing_crc':
				pass
