# il2p
# Python3
# Functions for decoding and encoding IL2P packets
# Nino Carrillo
# 1 Apr 2024

from modems_codecs.data_classes import AddressedData
from modems_codecs.packet_meta import PacketMeta
from modems_codecs.lfsr import LFSRnoaddr
import modems_codecs.rs_functions as rs_functions
from modems_codecs.crc_functions import AppendCRC
from modems_codecs.string_ops import check_boolean
import copy


def ceil(arg):
	return int(arg) + (arg % 1 > 0)

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


def reform_control_byte(header):
	control_byte = 0
	U_Control = [ 0x2F, 0x43, 0x0F, 0x63, 0x87, 0x03, 0xAF, 0xE3 ]
	if (header['AX25_type'] == 'AX25_U') or (header['AX25_type'] == 'AX25_UI'):
		control_byte = U_Control[header['control_opcode']]
		if header['AX25_PFbit']:
			control_byte |= 0x10
	elif header['AX25_type'] == 'AX25_S':
		control_byte = 0x1
		control_byte |= header['control_opcode'] << 2
		control_byte |= header['AX25_NR'] << 5
		if header['AX25_PFbit']:
			control_byte |= 0x10
	elif header['AX25_type'] == 'AX25_I':
		control_byte = header['AX25_NS'] << 1
		control_byte |= header['AX25_NR'] << 5
		if header['AX25_PFbit']:
			control_byte |= 0x10
	return control_byte

class IL2PCodec:
	def __init__(self, **kwargs):

		self.collect_trailing_crc = kwargs.get('crc', True)
		self.identifier = kwargs.get('ident', 1)
		self.min_distance = kwargs.get('min_dist', 0)
		self.disable_rs = kwargs.get('disable_rs', False)
		self.sync_tolerance = kwargs.get('sync_tol', 0)

		self.state = 'sync_search'
		self.working_word = int(0xFFFFFF)
		self.buffer = []
		for i in range(255):
			self.buffer.append(0)
		self.working_packet = PacketMeta()
		self.bit_index = 0
		self.byte_index_a = 0
		self.block_index = 0
		self.num_roots = 16
		# IL2P Scrambling Polynomial x^9 + x^4 + 1
		self.lfsr = LFSRnoaddr(poly=0x211, invert=False)
		rs_firstroot = 0
		rs_header_numroots = 2
		rs_block_numroots = 16
		rs_gf_power = 8
		rs_gf_poly = 0x11D
		self.header_rs = rs_functions.initialize(rs_firstroot, rs_header_numroots, rs_gf_power, rs_gf_poly)
		self.block_rs = rs_functions.initialize(rs_firstroot, rs_block_numroots, rs_gf_power, rs_gf_poly)
		self.bytes_corrected = 0
		self.block_fail = False

	def StringOptionsRetune(self, options):
		self.collect_trailing_crc = check_boolean(options.get('crc', 'yes'))
		self.disable_rs = check_boolean(options.get('disable_rs', 'no'))
		self.min_distance = int(options.get('min_dist', self.min_distance))
		self.sync_tolerance = int(options.get('sync_tol', self.sync_tolerance))
		# print("sync tolerance", self.sync_tolerance)

	def get_a_bit(self, word_mask):
		self.working_word <<= 1
		self.working_word &= word_mask
		if self.input_byte & 0x80:
			self.working_word |= 1
		self.input_byte <<= 1
		self.bit_index += 1

	def dump_block(self):
		for i in range(self.byte_index_a):
			print(hex(self.buffer[i]), end=' ')
		print("\nend block")

	def block_unscramble(self):
		self.lfsr.shift_register = 0x1F0
		self.buffer[:self.byte_index_a] = \
			self.lfsr.stream_unscramble_8bit(self.buffer[:self.byte_index_a])

	def block_rs_decode(self):
		if self.disable_rs:
			rs_result = 0
		else:
			rs_result = rs_functions.decode(
					self.block_rs,
					self.buffer,
					self.byte_index_a,
					self.min_distance
			)
		if rs_result < 0:
			# RS decoding failed
			self.block_fail = True
		else:
			if rs_result > 0:
				print("Successful RS block decode with corrected errors: ", rs_result)
			self.bytes_corrected += rs_result

	def dump_header_hex(self):	
		for i in range(13):
			print(hex(self.buffer[i]), end=' ')
		print("end header")

	def header_rs_decode(self):
		if self.disable_rs:
			rs_result = 0
		else:
			rs_result = rs_functions.decode(
					self.header_rs,
					self.buffer,
					self.byte_index_a,
					self.min_distance
			)
		if rs_result < 0:
			# RS decoding failed
			self.block_fail = True
		else:
			self.bytes_corrected += rs_result

	def write_n_search(self, result):
		self.working_packet.BytesCorrected = self.bytes_corrected
		result.append(
			copy.copy(self.working_packet)
		)
		print("IL2P packet complete. Bytes Corrected: ", self.bytes_corrected)
		self.bytes_corrected = 0;
		self.working_packet = PacketMeta()
		self.state = 'sync_search'

	def unpack_il2p_header(self):
		self.header = {}
		# get reserved bit
		self.header['IL2P_reserved_subfield'] = (int(self.buffer[0]) & 0x80) >> 7
		# get header type
		self.header['IL2P_type_subfield'] = (int(self.buffer[1]) & 0x80) >> 7
		# get byte count
		self.header['IL2P_count_subfield'] = 0
		for i in range(10):
			if int(self.buffer[i + 2]) & 0x80:
				self.header['IL2P_count_subfield'] |= 0x200 >> i

		self.header['IL2P_PID_subfield'] = 0
		for i in range(4):
			if int(self.buffer[i + 1]) & 0x40:
				self.header['IL2P_PID_subfield'] |= 0x8 >> i

		self.header['IL2P_control_subfield'] = 0
		for i in range(7):
			if (int(self.buffer[i + 5]) & 0x40):
				self.header['IL2P_control_subfield'] |= 0x40 >> i

		# extract destination callsign
		self.header['dest'] = [0, 0, 0, 0, 0, 0, 0]
		for i in range(6):
			self.header['dest'][i] = (int(self.buffer[i]) & 0x3F) + 0x20
		self.header['dest'][6] = int(self.buffer[12]) >> 4

		# extract source callsign
		self.header['source'] = [0, 0, 0, 0, 0, 0, 0]
		for i in range(6):
			self.header['source'][i] = (int(self.buffer[i + 6]) & 0x3F) + 0x20
		self.header['source'][6] = int(self.buffer[12]) & 0xF

		self.header['AX25_type'] = 'unknown'
		# extract UI frame indicator
		if int(self.buffer[0]) & 0x40:
			# This is a UI frame
			self.header['AX25_type'] = 'AX25_UI'
			# UI frames have a PID
		else:
			# this is either an I frame, S frame, or Unnumbered (non-UI) frame
			if self.header['IL2P_PID_subfield'] == 0x0:
				# AX.25 Supervisory Frame, no PID
				self.header['AX25_type'] = 'AX25_S'
			elif self.header['IL2P_PID_subfield'] == 0x1:
				# AX.25 Unnumbered Frame (non-UI), no PID
				self.header['AX25_type'] = 'AX25_U'
			else:
				# this frame defaults to an Information frame, has PID
				self.header['AX25_type'] = 'AX25_I'

		# returns 0 to signal "omit PID byte"
		IL2P_to_AX25_PID_table = [0, 0, 0x10, 0x01, 0x06, 0x07, 0x08, 0xC3, 0xC4, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF, 0xF0]
		self.header['AX25_PID_byte'] = IL2P_to_AX25_PID_table[self.header['IL2P_PID_subfield']]

		self.header['AX25_PFbit'] = False
		self.header['AX25_Cbit'] = False
		self.header['AX25_NR'] = 0
		self.header['AX25_NS'] = 0
		self.header['control_opcode'] = 0
		# translate IL2P control field
		if self.header['IL2P_control_subfield'] & 0x40:
			self.header['AX25_PFbit'] = True
		if self.header['AX25_type'] == 'AX25_I':
			self.header['AX25_NS'] =self.header['IL2P_control_subfield'] & 0x7
			self.header['AX25_NR'] = (self.header['IL2P_control_subfield'] >> 3) & 0x7
			self.header['AX25_Cbit'] = True # all I frames are commands
		elif self.header['AX25_type'] == 'AX25_S':
			self.header['AX25_NR'] = (self.header['IL2P_control_subfield'] >> 3) & 0x7
			if self.header['IL2P_control_subfield'] & 0x4:
				self.header['AX25_Cbit'] = True
			self.header['control_opcode'] =self.header['IL2P_control_subfield'] & 0x3
		elif (self.header['AX25_type'] == 'AX25_U') or (self.header['AX25_type'] == 'AX25_UI'):
			if self.header['IL2P_control_subfield'] & 0x4:
				self.header['AX25_Cbit'] = True
			self.header['control_opcode'] = (self.header['IL2P_control_subfield'] >> 3) & 0x7

	def construct_ax25_header(self):
		if self.header['IL2P_type_subfield'] == 1:
			# re-assemble AX.25 header in working_packet:
			# First add the destination callsign and SSID
			for i in range(6):
				self.working_packet.data.append(
								self.header['dest'][i] << 1
				)
			# Now add the destination SSID and bits
			self.working_packet.data.append(
								self.header['dest'][6] << 1
			)
			# Set RR bits
			self.working_packet.data[-1] += 0x60
			# Set C/R bit per AX.25 2.2
			# Command is indicated by Dest 1 Src 0
			# Response is indicated by Dest 0 Src 1
			if self.header['AX25_Cbit'] == True:
				self.working_packet.data[-1] += 0x80

			# Now add source callsign and SSID
			for i in range(6):
				self.working_packet.data.append(
								self.header['source'][i] << 1
				)
			# Now add the destination SSID and bits
			self.working_packet.data.append(
								self.header['source'][6] << 1
			)
			# Set RR bits
			self.working_packet.data[-1] += 0x60
			# Set C/R bit per AX.25 2.2
			# Command is indicated by Dest 1 Src 0
			# Response is indicated by Dest 0 Src 1
			if self.header['AX25_Cbit'] == False:
				self.working_packet.data[-1] += 0x80
			# Set callsign extension bit
			self.working_packet.data[-1] += 1

			# add the Control byte:
			self.working_packet.data.append(
							reform_control_byte(self.header)
			)

			# add the PID byte, if applicable
			if (self.header['AX25_PID_byte'] != 0):
				self.working_packet.data.append(
									self.header['AX25_PID_byte']
				)
		else:
			print("IL2P Transparent")
			# Type 0 Transparent Encapsulation
			pass

	def calc_big_small_blocks(self):
		self.block_count = int(ceil(
				self.header['IL2P_count_subfield'] / 239
			))
		self.block_size = int(
				self.header['IL2P_count_subfield']
				/ self.block_count
			)
		self.big_blocks = \
			int(self.header['IL2P_count_subfield'] - (
				self.block_count
				* self.block_size
			))

	def decode(self, data):
		result = []
		for stream_byte in data:
			self.input_byte = int(stream_byte.data)
			self.working_packet.streamaddress = stream_byte.address
			self.working_packet.SourceDecoder = self.identifier
			for input_bit_index in range(8):
				if self.state == 'sync_search':
					self.get_a_bit(0xFFFFFF)
					if ( \
							(bit_distance_24(self.working_word, 0xF15E48) <= self.sync_tolerance) \
							or \
							(bit_distance_24(self.working_word, 0x57DF7F) <= self.sync_tolerance) \
					):
						print("Syncword: ", hex(self.working_word))
						self.bit_index = 0
						self.state = 'rx_header'
				elif self.state == 'rx_header':
					self.get_a_bit(0xFF)
					if self.bit_index == 8:
						self.bit_index = 0
						self.buffer[self.byte_index_a] = self.working_word
						self.byte_index_a += 1
						if self.byte_index_a == 15:
							self.header_rs_decode()

							# Set the byte index to the end of intentional data,
							# just before the two RS bytes. block_unscramble
							# needs byte_index_a to know how many bytes to un-
							# scramble.
							self.byte_index_a = 13
							self.block_unscramble()
							self.byte_index_a = 0


							#self.dump_header_hex()

							# Unpack IL2P header
							self.unpack_il2p_header()

							self.block_index = 0
							self.block_byte_count = 0

							self.construct_ax25_header()

							if self.block_fail:
								print("IL2P Header Decode Fail")
								self.block_fail = False
								self.state = 'sync_search'
								self.working_packet = PacketMeta()
							elif self.header['IL2P_count_subfield'] > 0:

								self.calc_big_small_blocks()

								if self.big_blocks > 0:
									# there are big blocks in this frame, collect those first.
									self.block_size += 1
									self.bit_index = 0
									self.state = 'rx_bigblocks'
								else:
									self.bit_index = 0
									# there are only small blocks in this frame, collect.
									self.state = 'rx_smallblocks'

							else:
								# this frame is only a header
								if self.collect_trailing_crc:
									self.state = 'rx_trailing_crc'
								else:
									# put a calculated CRC here
									# this facilitates handling this packet
									# elsewhere
									AppendCRC(self.working_packet.data)
									self.write_n_search(result)

				elif self.state == 'rx_bigblocks':
					self.get_a_bit(0xFF)
					if self.bit_index == 8:
						self.bit_index = 0
						self.buffer[self.byte_index_a] = self.working_word
						self.byte_index_a += 1
						if self.byte_index_a == self.block_size + self.num_roots:
							# this block is completely collected
							#self.dump_block()
							self.block_rs_decode()
							self.block_unscramble()

							for i in range(self.block_size):
								self.working_packet.data.append(self.buffer[i])

							self.block_index += 1
							self.byte_index_a = 0

							if self.block_fail:
								print("IL2P BigBlock Decode Fail")
								self.block_fail = False
								self.working_packet = PacketMeta()
								self.state = 'sync_search'
							elif self.block_index == self.big_blocks:
								if self.block_count > self.block_index:
									self.block_size -= 1
									self.state = 'rx_smallblocks'
								elif self.collect_trailing_crc:
									self.state = 'rx_trailing_crc'
								else:
									# put a calculated CRC here
									# this facilitates handling this packet
									# elsewhere
									AppendCRC(self.working_packet.data)
									self.write_n_search(result)

				elif self.state ==  'rx_smallblocks':
					self.get_a_bit(0xFF)
					if self.bit_index == 8:
						self.bit_index = 0
						self.buffer[self.byte_index_a] = self.working_word
						self.byte_index_a += 1
						if self.byte_index_a == self.block_size + self.num_roots:
							#self.dump_block()
							self.block_rs_decode()
							self.block_unscramble()

							self.block_index += 1
							self.byte_index_a = 0

							for i in range(self.block_size):
								self.working_packet.data.append(self.buffer[i])


							if self.block_fail:
								print("IL2P SmallBlock Decode Fail")
								self.block_fail = False
								self.working_packet = PacketMeta()
								self.state = 'sync_search'
							elif self.block_index == self.block_count:
								if self.collect_trailing_crc:
									self.state = 'rx_trailing_crc'
								else:
									# put a calculated CRC here
									# this facilitates handling this packet
									# elsewhere
									AppendCRC(self.working_packet.data)
									self.write_n_search(result)
				elif self.state == 'rx_trailing_crc':
					self.get_a_bit(0xFF)
					if self.bit_index == 8:
						self.bit_index = 0
						self.buffer[self.byte_index_a] = self.working_word
						self.byte_index_a += 1
						if self.byte_index_a == 4:
							self.byte_index_a = 0
							# complete trailing crc has been received
							# Apply hamming correction and compute CRC
							trailing_crc = 0
							for i in range(4):
								trailing_crc += hamming_decode(self.buffer[i]) << (12 - (i * 4))
							self.working_packet.data.append(trailing_crc & 0xFF)
							self.working_packet.data.append(trailing_crc >> 8)
							self.write_n_search(result)
		return result
