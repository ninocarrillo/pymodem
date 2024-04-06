# Python3
# class definition for packet data with metadata
# Nino Carrillo
# 6 Apr 2024

import crc_functions

class PacketMeta:

	def __init__(self):
		# the array of bytes that make up the packet
		self.data = []
		# the reference point in the bitstream where this packet was decoded
		# it is measured to the last bit of the closing flag in the packet.
		# this is used for comparing age of packets in multi-decoder systems
		self.bitaddress = 0
		# the calculated CRC for the packet data
		self.CalculatedCRC = 0
		self.CarriedCRC = 0
		self.ValidCRC = False
		
	def CalcCRC(self):
		# Assume the CRC encoded in the packet is in the highest two positions of the data list
		result = crc_functions.CheckCRC(self.data)
		self.CarriedCRC = result[0]
		self.CalculatedCRC = result[1]
		self.ValidCRC = result[2]
		return self.ValidCRC

