# ax25_functions
# Python3
# Functions for manipulating an ax.25 bitstream
# Nino Carrillo
# 30 Mar 2024

from packet_meta import PacketMeta
import copy

class AX25Codec:

	def __init__(self, **kwargs):

		self.min_packet_length = kwargs.get('min_packet_length', 18)
		self.max_packet_length = kwargs.get('max_packet_length', 1023)

		self.working_byte = 0
		self.working_packet = PacketMeta()
		self.byte_index = 0
		self.one_count = 0
		self.bit_index = 0
		self.absolute_bit_index = 0

	def decode(self, data):
		# create an empty list to collect decoded packets
		result = []
		for input_byte in data:
			input_byte = int(input_byte)
			for bit_index in range(8):
				self.absolute_bit_index += 1
				if input_byte & 0x80:
					# this is a '1' bit
					self.working_byte |= 0x80
					self.one_count += 1
					self.bit_index += 1
					if self.one_count > 6:
						# abort frame for invalid bit sequence
						self.bit_index = 0
						self.byte_index = 0
					if self.bit_index == 8:
						# Byte complete, do something with it
						self.bit_index = 0
						self.working_packet.data.append(self.working_byte)
						self.byte_index += 1
						if (
								self.byte_index >
								self.max_packet_length
						):
							# This packet exceeds max length
							self.byte_index = 0
							self.one_count = 0
					self.working_byte >>= 1
				else:
					# this is a '0' bit
					if self.one_count < 5:
						self.bit_index += 1
						if self.bit_index == 8:
							# Byte complete, do something with it
							self.bit_index = 0
							self.working_packet.data.append(self.working_byte)
							self.byte_index += 1
							if (
									self.byte_index >
									self.max_packet_length
							):
								# This packet exceeds max length
								self.byte_index = 0
						self.working_byte >>= 1
					elif self.one_count == 5:
						#ignore stuffed zero
						pass
					elif self.one_count == 6:
						# This is a flag, check and save the packet
						if (
								(
									self.byte_index >=
									self.min_packet_length
								) and (
									self.bit_index == 7
								)
						):
							self.working_packet.bitaddress = self.absolute_bit_index
							result.append(
								copy.copy(self.working_packet)
							)
						self.working_packet = PacketMeta()
						self.byte_index = 0
						self.bit_index = 0
					self.one_count = 0
				# shift input byte
				input_byte <<= 1
		return result
