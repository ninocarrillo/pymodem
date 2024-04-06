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
		self.SourceDecoder = 0
		self.CorrelatedDecoders = []
		
	def CalcCRC(self):
		# Assume the CRC encoded in the packet is in the highest two positions of the data list
		result = crc_functions.CheckCRC(self.data)
		self.CarriedCRC = result[0]
		self.CalculatedCRC = result[1]
		self.ValidCRC = result[2]
		return self.ValidCRC
		
class PacketMetaArray:

	def __init__(self):
		self.raw_packet_arrays = []
		self.unique_packet_array =[]
		
	def add(self, array):
		self.raw_packet_arrays.append(array)
		
	def CalcCRCs(self):
		for array in self.raw_packet_arrays:
			for packet in array:
				packet.CalcCRC()
		
	def Correlate(self, **kwargs):
		self.address_distance = kwargs.get('address_distance', 50)
		# Identify unique and duplicate packets based on bitaddress and CalculatedCRC
		for raw_packet_array in self.raw_packet_arrays:
			for raw_packet in raw_packet_array:
				if raw_packet.ValidCRC:
					# only check packets with a valid CRC
					# assume this packet is unique
					is_unique = True
					# compare this packet with the existing unique packets, flag false if matched
					for unique_packet in self.unique_packet_array:
						if (
							(abs(raw_packet.bitaddress - unique_packet.bitaddress) < self.address_distance)
							and
							(raw_packet.CalculatedCRC == unique_packet.CalculatedCRC)
						):
							is_unique = False
							unique_packet.CorrelatedDecoders.append(raw_packet.SourceDecoder)
							break
					if is_unique:
						print("unique", raw_packet.bitaddress, raw_packet.CalculatedCRC)
						raw_packet.CorrelatedDecoders.append(raw_packet.SourceDecoder)
						# this packet is unique, add it to the list.
						self.unique_packet_array.append(raw_packet)
		# now sort the unique list:
		self.unique_packet_array = sorted(self.unique_packet_array, key=lambda packet: packet.bitaddress)

						
			

