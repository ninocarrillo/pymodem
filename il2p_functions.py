# il2p_functions
# Python3
# Functions for decoding and encoding IL2P packets
# Nino Carrillo
# 1 Apr 2024

import lfsr_functions as lf
import crc_functions
import rs_functions

def ceil(arg):
	return int(arg) + (arg % 1 > 0)

def initialize_decoder():
	decoder = {}
	decoder['state'] = 'sync_search'
	decoder['working_word'] = int(0xFFFFFF)
	decoder['sync_tolerance'] = 1
	decoder['buffer'] = []
	for i in range(255):
		decoder['buffer'].append(0)
	decoder['working_packet'] = []
	for i in range(1200):
		decoder['working_packet'].append(0)
	decoder['bit_index'] = 0
	decoder['byte_index_a'] = 0
	decoder['byte_index_b'] = 0
	decoder['block_index'] = 0
	decoder['num_roots'] = 16
	# IL2P Polynomial x^9 + x^4 + 1
	lfsr_polynomial = 0x211
	lfsr_invert = False
	decoder['lfsr'] = lf.initialize(
		lfsr_polynomial,
		lfsr_invert
	)
	rs_firstroot = 0
	rs_numroots = 2
	rs_power = 8
	rs_poly = 0x11D
	decoder['header_rs'] = rs_functions.initialize(rs_firstroot, rs_numroots, rs_power, rs_poly)
	numroots = 16
	decoder['block_rs'] = rs_functions.initialize(rs_firstroot, rs_numroots, rs_power, rs_poly)
	decoder['bytes_corrected'] = 0
	decoder['block_fail'] = False
	return decoder

def hamming_decode(data):
	# Hamming(7,4) Decoding Table
	# Enter this table with 7-bit encoded value, high bit masked.
	# Returns 4-bit decoded value.
	hamming_decode_table = [
			0x0, 0x0, 0x0, 0x3, 0x0, 0x5, 0xe, 0x7,
			0x0, 0x9, 0xe, 0xb, 0xe, 0xd, 0xe, 0xe,
			0x0, 0x3, 0x3, 0x3, 0x4, 0xd, 0x6, 0x3,
			0x8, 0xd, 0xa, 0x3, 0xd, 0xd, 0xe, 0xd,
			0x0, 0x5, 0x2, 0xb, 0x5, 0x5, 0x6, 0x5,
			0x8, 0xb, 0xb, 0xb, 0xc, 0x5, 0xe, 0xb,
			0x8, 0x1, 0x6, 0x3, 0x6, 0x5, 0x6, 0x6,
			0x8, 0x8, 0x8, 0xb, 0x8, 0xd, 0x6, 0xf,
			0x0, 0x9, 0x2, 0x7, 0x4, 0x7, 0x7, 0x7,
			0x9, 0x9, 0xa, 0x9, 0xc, 0x9, 0xe, 0x7,
			0x4, 0x1, 0xa, 0x3, 0x4, 0x4, 0x4, 0x7,
			0xa, 0x9, 0xa, 0xa, 0x4, 0xd, 0xa, 0xf,
			0x2, 0x1, 0x2, 0x2, 0xc, 0x5, 0x2, 0x7,
			0xc, 0x9, 0x2, 0xb, 0xc, 0xc, 0xc, 0xf,
			0x1, 0x1, 0x2, 0x1, 0x4, 0x1, 0x6, 0xf,
			0x8, 0x1, 0xa, 0xf, 0xc, 0xf, 0xf, 0xf
		]
	result = hamming_decode_table[int(data) & 0x7F]
	return result

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
			5, 6, 6, 7, 6, 7, 7, 8
		]
	result = 0
	for index in range(3):
		a = data_a & 0xFF
		b = data_b & 0xFF
		data_a >>= 8
		data_b >>= 8
		result += Distance8[a ^ b]
	return result

def unpack_header(data):
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
		header['dest'][6] = (int(data[i]) & 0xF)

		# extract source callsign
		header['source'] = [0, 0, 0, 0, 0, 0, 0]
		for i in range(6):
			header['source'][i] = (int(data[i + 6]) & 0x3F) + 0x20
		header['source'][6] = ((int(data[i]) & 0xF) >> 4)

		# Extract IL2P PID data. This has meaning even if the AX.25 PID doesn't
		# exist.
		header['PID'] = 0
		for i in range(4):
			if int(data[i + 1]) & 0x40:
				header['PID'] |= 0x8 >> i

		header['control'] = 0
		for i in range(7):
			if (int(data[i + 5]) & 0x40):
				header['control'] |= 0x40 >> i

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

		header['PFbit'] = False
		header['Cbit'] = False
		header['NR'] = 0
		header['NS'] = 0
		header['opcode'] = 0
		# translate IL2P control field
		if header['type'] == 'AX25_I':
			if header['control'] & 0x40:
				header['PFbit'] = True
			header['NS'] = header['control'] & 0x7
			header['NR'] = (header['control'] >> 3) & 0x7
			header['CBit'] = True # all I frames are commands
		elif header['type'] == 'AX25_S':
			header['NR'] = (header['control'] >> 3) & 0x7
			if header['control'] & 0x4:
				header['Cbit'] = True
			header['opcode'] = header['control'] & 0x3
		elif (header['type'] == 'AX25_U') or (header['type'] == 'AX25_UI'):
			if (header['control'] >> 6) & 0x1:
				header['PFbit'] = True
			if header['control'] & 0x4:
				header['Cbit'] = True
			header['opcode'] = (header['control'] >> 3) & 0x7
	else:
		# transparent encapsulation
		pass
	return header

def reform_control_byte(header):
	control_byte = 0
	U_Control = [ 0x2F, 0x43, 0x0F, 0x63, 0x87, 0x03, 0xAF, 0xE3 ]
	if (header['type'] == 'AX25_U') or (header['type'] == 'AX25_UI'):
		control_byte = U_Control[header['opcode'] & 0x7]
		if header['PFbit']:
			control_byte |= 0x10
	elif header['AX25_PID'] == 'AX25_S':
		control_byte = 0x1
		control_byte |= header['opcode'] << 2
		control_byte |= header['NR'] << 5
		if header['PFbit']:
			control_byte |= 0x10
	elif header['AX25_PID'] == 'AX25_I':
		control_byte = header['NS'] << 1
		control_byte |= header['NR'] << 5
		if header['PFbit']:
			control_byte |= 0x10
	return control_byte

def get_a_bit(decoder, word_mask):
	decoder['working_word'] <<= 1
	decoder['working_word'] &= word_mask
	if decoder['input_byte'] & 0x80:
		decoder['working_word'] |= 1
	decoder['input_byte'] <<= 1
	decoder['bit_index'] += 1

def decode(decoder, data, collect_crc):
	result = []
	for input_byte in data:
		decoder['input_byte'] = int(input_byte)
		for input_bit_index in range(8):
			if decoder['state'] == 'sync_search':
				get_a_bit(decoder, 0xFFFFFF)
				if bit_distance_24(decoder['working_word'], 0xF15E48) <= \
													decoder['sync_tolerance']:
					decoder['bit_index'] = 0
					decoder['byte_index_b'] = 0
					decoder['state'] = 'rx_header'
			elif decoder['state'] == 'rx_header':
				get_a_bit(decoder, 0xFF)
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['buffer'][decoder['byte_index_a']] = \
														decoder['working_word']
					decoder['byte_index_a'] += 1
					if decoder['byte_index_a'] == 15:
						decoder['byte_index_a'] = 0

						# do reed-solomon error correction
						rs_result = rs_functions.decode(
								decoder['header_rs'],
								decoder['buffer'][:decoder['byte_index_a']]
						)
						if rs_result < 0:
							# RS decoding header failed
							decoder['block_fail'] = True
						else:
							decoder['bytes_corrected'] += rs_result

						# descramble header
						decoder['lfsr']['shift_register'] = 0x1F0
						decoder['buffer'][:13] = lf.stream_unscramble_8bit(
								decoder['lfsr'],
								decoder['buffer'][:13]
						)

						# Unpack IL2P header
						decoder['header'] = \
							unpack_header(decoder['buffer'][:13])

						decoder['block_index'] = 0
						decoder['block_byte_count'] = 0

						# re-assemble AX.25 header in working_packet:
						# First add the destination callsign and SSID
						for i in range(6):
							decoder['working_packet'][decoder['byte_index_b']] = \
											decoder['header']['dest'][i] << 1
							decoder['byte_index_b'] += 1
						# Now add the destination SSID and bits
						decoder['working_packet'][decoder['byte_index_b']] = \
											decoder['header']['dest'][6] << 1
						# Set RR bits
						decoder['working_packet'][decoder['byte_index_b']] += 0x60
						# Set C/R bit per AX.25 2.2
						# Command is indicated by Dest 1 Src 0
						# Response is indicated by Dest 0 Src 1
						if decoder['header']['Cbit'] == True:
							decoder['working_packet'][decoder['byte_index_b']] += 0x80
						decoder['byte_index_b'] += 1

						# Now add source callsign and SSID
						for i in range(6):
							decoder['working_packet'][decoder['byte_index_b']] = \
											decoder['header']['source'][i] << 1
							decoder['byte_index_b'] += 1
						# Now add the destination SSID and bits
						decoder['working_packet'][decoder['byte_index_b']] = \
											decoder['header']['source'][6] << 1
						# Set RR bits
						decoder['working_packet'][decoder['byte_index_b']] += 0x60
						# Set C/R bit per AX.25 2.2
						# Command is indicated by Dest 1 Src 0
						# Response is indicated by Dest 0 Src 1
						if decoder['header']['Cbit'] == False:
							decoder['working_packet'][decoder['byte_index_b']] += 0x80
						# Set callsign extension bit
						decoder['working_packet'][decoder['byte_index_b']] += 1
						decoder['byte_index_b'] += 1

						# add the Control byte:
						decoder['working_packet'][decoder['byte_index_b']] = \
										reform_control_byte(decoder['header'])
						decoder['byte_index_b'] += 1

						# add the PID byte, if applicable
						if (decoder['header']['type'] == 'AX25_I') or \
								(decoder['header']['type'] == 'AX25_UI'):
							decoder['working_packet'][decoder['byte_index_b']] = \
												decoder['header']['AX25_PID']
							decoder['byte_index_b'] += 1

						# print(decoder['header'])
						# for byte in decoder['working_packet'][:decoder['byte_index_b']]:
						# 	print(hex(int(byte)), end = ' ')

						if decoder['block_fail']:
							decoder['block_fail'] = False
							decoder['state'] = 'sync_search'
						elif decoder['header']['count'] > 0:
							decoder['block_count'] = int(ceil(
									decoder['header']['count'] / 239
								))
							decoder['block_size'] = int(
									decoder['header']['count']
									/ decoder['block_count']
								)
							decoder['big_blocks'] = \
								int(decoder['header']['count'] - (
									decoder['block_count']
									* decoder['block_size']
								))
							if decoder['big_blocks'] > 0:
								# there are big blocks in this frame, collect those first.
								decoder['block_size'] += 1
								decoder['bit_index'] = 0
								decoder['state'] = 'rx_bigblocks'
							else:
								decoder['bit_index'] = 0
								# there are only small blocks in this frame, collect.
								decoder['state'] = 'rx_smallblocks'

						else:
							# this frame is only a header, dispose of it
							#print(decoder['working_packet'][decoder['byte_index_b']])
							if collect_crc:
								decoder['state'] = 'rx_trailing_crc'
							else:
								result.append(
									decoder['working_packet'] \
									[:decoder['byte_index_b']].copy()
								)
								decoder['state'] = 'sync_search'

			elif decoder['state'] == 'rx_bigblocks':
				get_a_bit(decoder, 0xFF)
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['buffer'][decoder['byte_index_a']] = \
					 									decoder['working_word']
					decoder['byte_index_a'] += 1
					if decoder['byte_index_a'] == decoder['block_size'] + decoder['num_roots']:
						# this block is completely collected
						# do reed-solomon error correction
						rs_result = rs_functions.decode(
								decoder['block_rs'],
								decoder['buffer'][:decoder['byte_index_a']]
						)
						if rs_result < 0:
							# RS decoding failed
							decoder['block_fail'] = True
						else:
							decoder['bytes_corrected'] += rs_result

						# de-scramble
						decoder['lfsr']['shift_register'] = 0x1F0
						decoder['buffer'][:decoder['byte_index_a']] = \
							lf.stream_unscramble_8bit(
								decoder['lfsr'],
								decoder['buffer'][:decoder['byte_index_a']]
							)
						decoder['byte_index_a'] = 0

						for i in range(decoder['block_size']):
							decoder['working_packet'][decoder['byte_index_b']] = \
								decoder['buffer'][i]
							decoder['byte_index_b'] += 1


						decoder['block_index'] += 1

						# for byte in decoder['buffer'][:decoder['block_size']]:
						# 	byte = int(byte)
						# 	if (byte < 0x7F) and (byte > 0x1F):
						# 		print(chr(int(byte)), end='')
						# print("")

						if decoder['block_fail']:
							decoder['block_fail'] = False
							decoder['state'] = 'sync_search'
						elif decoder['block_index'] == decoder['big_blocks']:
							if decoder['block_count'] > decoder['block_index']:
								decoder['block_size'] -= 1
								decoder['state'] = 'rx_smallblocks'
							elif collect_crc:
								decoder['state'] = 'rx_trailing_crc'
							else:
								result.append(
									decoder['working_packet'] \
									[:decoder['byte_index_b']].copy()
								)
								decoder['state'] = 'sync_search'

			elif decoder['state'] ==  'rx_smallblocks':
				get_a_bit(decoder, 0xFF)
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['buffer'][decoder['byte_index_a']] = decoder['working_word']
					decoder['byte_index_a'] += 1
					if decoder['byte_index_a'] == decoder['block_size'] + decoder['num_roots']:
						# do reed-solomon error correction
						rs_result = rs_functions.decode(
								decoder['block_rs'],
								decoder['buffer'][:decoder['byte_index_a']]
						)
						if rs_result < 0:
							# RS decoding failed
							decoder['block_fail'] = True
						else:
							decoder['bytes_corrected'] += rs_result

						# de-descramble
						decoder['lfsr']['shift_register'] = 0x1F0
						decoder['buffer'][:decoder['byte_index_a']] = \
							lf.stream_unscramble_8bit(
								decoder['lfsr'],
								decoder['buffer'][:decoder['byte_index_a']]
							)

						decoder['block_index'] += 1

						for i in range(decoder['block_size']):
							decoder['working_packet'][decoder['byte_index_b']] = \
								decoder['buffer'][i]
							decoder['byte_index_b'] += 1

						decoder['byte_index_a'] = 0

						# for byte in decoder['buffer'][:decoder['block_size']]:
						# 	byte = int(byte)
						# 	if (byte < 0x7F) and (byte > 0x1F):
						# 		print(chr(int(byte)), end='')
						# print("")

						if decoder['block_fail']:
							decoder['block_fail'] = False
							decoder['state'] = 'sync_search'
						elif decoder['block_index'] == decoder['block_count']:
							if collect_crc:
								decoder['state'] = 'rx_trailing_crc'
							else:
								result.append(
									decoder['working_packet'] \
									[:decoder['byte_index_b']].copy()
								)
								decoder['state'] = 'sync_search'
			elif decoder['state'] == 'rx_trailing_crc':
				get_a_bit(decoder, 0xFF)
				if decoder['bit_index'] == 8:
					decoder['bit_index'] = 0
					decoder['buffer'][decoder['byte_index_a']] = \
														decoder['working_word']
					decoder['byte_index_a'] += 1
					if decoder['byte_index_a'] == 4:
						decoder['byte_index_a'] = 0
						# complete trailing crc has been received
						# Apply hamming correction and compute CRC
						trailing_crc = 0
						for i in range(4):
							trailing_crc += \
									hamming_decode(decoder['buffer'][i]) << \
																(12 - (i * 4))
						decoder['working_packet'][decoder['byte_index_b']] = \
															trailing_crc & 0xFF
						decoder['byte_index_b'] += 1
						decoder['working_packet'][decoder['byte_index_b']] = \
															trailing_crc >> 8
						decoder['byte_index_b'] += 1
						result.append(
							decoder['working_packet'] \
											[:decoder['byte_index_b']].copy()
						)
						decoder['state'] = 'sync_search'
	return result
