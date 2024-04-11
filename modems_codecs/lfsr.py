# lfsr
# Python3
# Descrambling through linear feedback shift registers
# Nino Carrillo
# 30 Mar 2024

from modems_codecs.data_classes import AddressedData

class LFSR:
	def __init__(self, **kwargs):

		self.polynomial = kwargs.get('poly', 0x1)
		self.invert = kwargs.get('invert', False)

		self.shift_register = 0

	def stream_unscramble_8bit(self, data):
		# this method creates one output byte for each input byte
		# The lfsr is free-running and arbitrarily initialized, so valid data
		# appears after the length of the polynomial.
		result = []
		# step through each input byte
		# and in each input byte, operate on each bit
		working_byte = int(0)
		for stream_byte in data:
			input_byte = int(stream_byte.data)
			# cycle through each bit in this byte
			for bit_index in range(8):
				# make room in working byte for a new bit
				working_byte <<= 1
				working_byte &= 0xFE
				# msb is first, sample it
				if input_byte & 0x80:
					# if the msb is 1, xor the polynomial into the shift register
					self.shift_register ^= self.polynomial
				working_byte |= (self.shift_register & 1)
				input_byte <<= 1
				# advance the lfsr shift register 1 bit
				self.shift_register >>= 1
			# 8 bits have been processed, save the byte

			if self.invert:
				result.append(AddressedData(0xFF ^ working_byte, stream_byte.address))

			else:
				result.append(AddressedData(working_byte, stream_byte.address))
		return result

class LFSRnoaddr:
	def __init__(self, **kwargs):

		self.polynomial = kwargs.get('poly', 0x3)
		self.invert = kwargs.get('invert', True)

		self.shift_register = 0

	def stream_unscramble_8bit(self, data):
		# this method creates one output byte for each input byte
		# The lfsr is free-running and arbitrarily initialized, so valid data
		# appears after the length of the polynomial.
		result = []
		# step through each input byte
		# and in each input byte, operate on each bit
		working_byte = int(0)
		for stream_byte in data:
			input_byte = int(stream_byte)
			# cycle through each bit in this byte
			for bit_index in range(8):
				# make room in working byte for a new bit
				working_byte <<= 1
				working_byte &= 0xFE
				# msb is first, sample it
				if input_byte & 0x80:
					# if the msb is 1, xor the polynomial into the shift register
					self.shift_register ^= self.polynomial
				working_byte |= (self.shift_register & 1)
				input_byte <<= 1
				# advance the lfsr shift register 1 bit
				self.shift_register >>= 1
			# 8 bits have been processed, save the byte

			if self.invert:
				result.append(0xFF ^ working_byte)

			else:
				result.append(working_byte)
		return result
