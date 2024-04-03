# il2p_functions
# Python3
# Functions for decoding and encoding IL2P packets
# Nino Carrillo
# 1 Apr 2024

from numpy import zeros, append, rint, ceil, floor
import lfsr_functions as lf

def initialize_decoder():
	decoder = {}
	decoder['state'] = 'sync_search'
	decoder['working_word'] = int(0xFFFFFF)
	decoder['sync_tolerance'] = 1
	decoder['buffer_a'] = zeros(255)
	decoder['buffer_b'] = zeros(1200)
	decoder['bit_index'] = 0
	decoder['byte_index_a'] = 0
	decoder['byte_index_b'] = 0
	decoder['block_index'] = 0
	decoder['num_roots'] = 16
	decoder['lfsr'] = lf.initialize(
		0x211,
		False
	)
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

def decode_header(data):
	header = {}
	# get header type
	header['type'] = (int(data[1]) & 0x80) >> 7
	# get reserved bit
	header['reserved'] = (int(data[0]) & 0x80) >> 7
	# get byte count
	header['count'] = 0
	for i in range(10):
		if int(data[i + 2]) & 0x80:
			header['count'] |= 0x200 >> i

	if header['type'] == 1:
		# translated AX.25
		# extract destination callsign
		header['dest'] = [0, 0, 0, 0, 0, 0, 0]
		for i in range(6):
			header['dest'][i] = (int(data[i]) & 0x3F) + 0x20
		header['dest'][6] = (int(data[i]) & 0xF) + 0x30

		# extract source callsign
		header['source'] = [0, 0, 0, 0, 0, 0, 0]
		for i in range(6):
			header['source'][i] = (int(data[i + 6]) & 0x3F) + 0x20
		header['source'][6] = ((int(data[i]) & 0xF) >> 4) + 0x30

		# Extract IL2P PID data. This has meaning even if the AX.25 PID doesn't
		# exist.
		header['PID'] = 0
		for i in range(4):
			if int(data[i + 1]) & 0x40:
				header['PID'] |= 0x8 >> i

		header['control'] = 0
		for i in range(7):
			if (int(data[i + 5]) & 0x80):
				header['control'] |= 0x80 >> i

		header['type'] = 'unknown'
		# extract UI frame indicator
		if int(data[i]) & 0x40:
			# This is a UI frame
			header['type'] = 'AX25_UI'
			# UI frames have a PID
		else:
			# this is either an I frame, S frame, or Unnumbered (non-UI) frame
			if header['PID'] == 0x0:
				# AX.25 Supervisory Frame, no PID
				header['type'] = 'AX25_S'
			elif header['PID'] == 0x1:
				# AX.25 Unnumbered Frame (non-UI), no PID
				header['type'] = 'AX25_U'
			else:
				# this frame defaults to an Information frame, has PID
				header['type'] = 'AX25_I'

		# convert IL2P PID to AX.25 PID, if applicable
		header['AX25_PID'] = 0
		if header['type'] == 'AX25_UI' or header['type'] == 'AX25_I':
			if header['PID'] == 0x2:
				header['AX25_PID'] = 0x20
			elif header['PID'] == 0x3:
				header['AX25_PID'] = 0x01
			elif header['PID'] == 0x4:
				header['AX25_PID'] = 0x06
			elif header['PID'] == 0x5:
				header['AX25_PID'] = 0x07
			elif header['PID'] == 0x6:
				header['AX25_PID'] = 0x08
			elif header['PID'] == 0xB:
				header['AX25_PID'] = 0xCC
			elif header['PID'] == 0xC:
				header['AX25_PID'] = 0xCD
			elif header['PID'] == 0xD:
				header['AX25_PID'] = 0xCE
			elif header['PID'] == 0xE:
				header['AX25_PID'] = 0xCF
			elif header['PID'] == 0xF:
				header['AX25_PID'] = 0xF0

		header['PFbit'] = 0
		header['Cbit'] = 0
		header['NR'] = 0
		header['NS'] = 0
		header['opcode'] = 0
		# translate IL2P control field
		if header['type'] == 'AX25_I':
			if header['control'] & 0x40:
				header['PFbit'] = 1
			header['NS'] = header['control'] & 0x7
			header['NR'] = (header['control'] >> 3) & 0x7
			header['CBit'] = 1 # all I frames are commands
		elif header['type'] == 'AX25_S':
			header['NR'] = (header['control'] >> 3) & 0x7
			header['Cbit'] = 1
			header['opcode'] = header['control'] & 0x3
		elif header['type'] == 'AX25_U':
			header['PFbit'] = (header['control'] >> 6) & 0x1
			header['Cbit'] = (header['control'] >> 2) & 0x1
			header['opcode'] = (header['control'] >> 3) & 0x7



	else:
		# transparent encapsulation
		pass
	return header

def get_a_bit(decoder, word_mask):
	decoder['working_word'] <<= 1
	decoder['working_word'] &= word_mask
	if decoder['input_byte'] & 0x80:
		decoder['working_word'] |= 1
	decoder['input_byte'] <<= 1
	decoder['bit_index'] += 1

def decode(decoder, data):
	count = 0
	for input_byte in data:
		decoder['input_byte'] = int(input_byte)
		for input_bit_index in range(8):
			if decoder['state'] == 'sync_search':
				get_a_bit(decoder, 0xFFFFFF)
				if bit_distance_24(decoder['working_word'], 0xF15E48) <= decoder['sync_tolerance']:
					count += 1
					print('sync', count)
					decoder['bit_index'] = 0
					decoder['state'] = 'rx_header'
			elif decoder['state'] == 'rx_header':
				get_a_bit(decoder, 0xFF)
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['buffer_a'][decoder['byte_index_a']] = decoder['working_word']
					decoder['byte_index_a'] += 1
					if decoder['byte_index_a'] == 15:
						decoder['byte_index_a'] = 0
						# do reed-solomon error correction

						# descramble header
						decoder['lfsr']['shift_register'] = 0x1F0
						decoder['buffer_a'][:13] = lf.stream_unscramble_8bit(
								decoder['lfsr'],
								decoder['buffer_a'][:13]
							)

						# decode header
						header = decode_header(decoder['buffer_a'][:13])

						decoder['block_index'] = 0
						decoder['block_byte_count'] = 0
						if header['count'] > 0:
							decoder['block_count'] = int(ceil(
									header['count'] / 239
								))
							decoder['block_size'] = int(floor(
									header['count'] / decoder['block_count']
								))
							decoder['big_blocks'] = int(header['count'] - (
									decoder['block_count']
									* decoder['block_size']
								))
							if decoder['big_blocks'] > 0:
								# there are big blocks in this frame, collect those first.
								decoder['block_size'] += 1
								print(header)
								decoder['bit_index'] = 0
								decoder['state'] = 'rx_bigblocks'
							else:
								print(header)
								decoder['bit_index'] = 0
								# there are only small blocks in this frame, collect.
								decoder['state'] = 'rx_smallblocks'

						else:
							# this frame is only a header, dispose of it
							print('count: ', header['count'])
							for byte in header['dest']:
								byte = int(byte)
								if (byte < 0x7F) and (byte > 0x1F):
									print(chr(int(byte)), end='')
							print("")
							for byte in header['source']:
								byte = int(byte)
								if (byte < 0x7F) and (byte > 0x1F):
									print(chr(int(byte)), end='')
							print("")
							print(header)
							decoder['state'] = 'sync_search'

			elif decoder['state'] == 'rx_bigblocks':
				get_a_bit(decoder, 0xFF)
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['buffer_a'][decoder['byte_index_a']] = decoder['working_word']
					decoder['byte_index_a'] += 1
					if decoder['byte_index_a'] == decoder['block_size'] + decoder['num_roots']:
						# reed-solomon

						# de-scramble
						decoder['lfsr']['shift_register'] = 0x1F0
						decoder['buffer_a'][:decoder['byte_index_a']] = lf.stream_unscramble_8bit(
								decoder['lfsr'],
								decoder['buffer_a'][:decoder['byte_index_a']]
							)
						decoder['byte_index_a'] = 0
						decoder['block_index'] += 1
						for byte in decoder['buffer_a'][:decoder['block_size']]:
							byte = int(byte)
							if (byte < 0x7F) and (byte > 0x1F):
								print(chr(int(byte)), end='')
						print("")
						if decoder['block_index'] == decoder['big_blocks']:
							if decoder['block_count'] > decoder['block_index']:
								decoder['block_size'] -= 1
								decoder['state'] = 'rx_smallblocks'
							else:
								decoder['state'] = 'sync_search'
			elif decoder['state'] ==  'rx_smallblocks':
				get_a_bit(decoder, 0xFF)
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['buffer_a'][decoder['byte_index_a']] = decoder['working_word']
					decoder['byte_index_a'] += 1
					if decoder['byte_index_a'] == decoder['block_size'] + decoder['num_roots']:
						# reed-solomon

						# de-descramble
						decoder['lfsr']['shift_register'] = 0x1F0
						decoder['buffer_a'][:decoder['byte_index_a']] = lf.stream_unscramble_8bit(
								decoder['lfsr'],
								decoder['buffer_a'][:decoder['byte_index_a']]
							)

						decoder['block_index'] += 1
						decoder['byte_index_a'] = 0
						for byte in decoder['buffer_a'][:decoder['block_size']]:
							byte = int(byte)
							if (byte < 0x7F) and (byte > 0x1F):
								print(chr(int(byte)), end='')
						print("")
						if decoder['block_index'] == decoder['block_count']:
							decoder['state'] = 'sync_search'
			elif decoder['state'] == 'rx_trailing_crc':
				pass
