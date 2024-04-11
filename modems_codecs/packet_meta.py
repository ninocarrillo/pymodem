# Python3
# class definition for packet data with metadata
# Nino Carrillo
# 6 Apr 2024

import modems_codecs.crc_functions as crc_functions


# I found this 'print_to_string' function on stack overflow
# https://stackoverflow.com/questions/39823303/python3-print-to-string
import io
def print_to_string(*args, **kwargs):
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents
# end found on stack overflow

def print_ax25_header_to_string(frame, delimiter):
	string_output = ''
	count = len(frame)
	index = 0
	if (count > 15):
		valid_header = 1
		address_extension_bit = 0
		index = 1
		subfield_character_index = 0
		subfield_index = 0
		# Print address information
		while address_extension_bit == 0:
			working_character = int(frame[index])
			if (working_character & 0b1) == 1:
				address_extension_bit = 1
			working_character = working_character >> 1
			subfield_character_index = subfield_character_index + 1
			if (subfield_character_index == 1):
				if (subfield_index == 0):
					string_output += print_to_string("To:", end='')
				elif (subfield_index == 1):
					string_output += print_to_string(delimiter, end='')
					string_output += print_to_string("From:", end='')
				else:
					string_output += print_to_string(delimiter, end='')
					string_output += print_to_string("Via:", end='')
			if subfield_character_index < 7:
				# This is a callsign character
				if (working_character != 0) and (working_character != 0x20):
					string_output += print_to_string(chr(working_character), end='')
			elif subfield_character_index == 7:
				# This is the SSID characters
				# Get bits
				string_output += print_to_string('-', end='')
				string_output += print_to_string(working_character & 0b1111, end='')
				if (working_character & 0b10000000):
					# C or H bit is set
					string_output += print_to_string('*', end=' ')
				# This field is complete
				subfield_character_index = 0
				subfield_index = subfield_index + 1
			index = index + 1
			if index > count:
				address_extension_bit = 1
		# Control and PID fields
		working_character = frame[index]
		string_output += print_to_string(delimiter, end='')
		string_output += print_to_string("Control: ", end='')
		string_output += print_to_string(f'{hex(working_character)} ', end='')
		poll_final_bit = (working_character & 0x10) >> 4
		# determine what type of frame this is
		if (working_character & 1) == 1:
			# either a Supervisory or Unnumbered frame
			frame_type = working_character & 3
		else:
			# Information frame
			frame_type = 0
			ax25_ns = (working_character >> 1) & 7
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 1:
			# Supervisory frame
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 3:
			# Unnumbered frame, determine what type
			ax25_u_control_field_type = working_character & 0xEF
		else:
			ax25_u_control_field_type = 0

		if (ax25_u_control_field_type == 0x6F):
			string_output += print_to_string("SABME", end='')
		elif (ax25_u_control_field_type == 0x2F):
			string_output += print_to_string("SABM", end='')
		elif (ax25_u_control_field_type == 0x43):
			string_output += print_to_string("DISC", end='')
		elif (ax25_u_control_field_type == 0x0F):
			string_output += print_to_string("DM", end='')
		elif (ax25_u_control_field_type == 0x63):
			string_output += print_to_string("UA", end='')
		elif (ax25_u_control_field_type == 0x87):
			string_output += print_to_string("FRMR", end='')
		elif (ax25_u_control_field_type == 0x03):
			string_output += print_to_string("UI", end='')
		elif (ax25_u_control_field_type == 0xAF):
			string_output += print_to_string("XID", end='')
		elif (ax25_u_control_field_type == 0xE3):
			string_output += print_to_string("TEST", end='')

		if (frame_type == 0) or (ax25_u_control_field_type == 3):
			# This is an Information frame, or an Unnumbered Information frame, so
			# there is a PID byte.
			index = index + 1
			working_character = frame[index]
			string_output += print_to_string(delimiter, end='')
			string_output += print_to_string("PID: ", end='')
			string_output += print_to_string(f'{hex(working_character)} ', end='')
			if (working_character == 1):
				string_output += print_to_string("ISO 8208", end='')
			if (working_character == 6):
				string_output += print_to_string("Compressed TCP/IP", end='')
			if (working_character == 7):
				string_output += print_to_string("Uncompressed TCP/IP", end='')
			if (working_character == 8):
				string_output += print_to_string("Segmentation Fragment", end='')
			if (working_character == 0xC3):
				string_output += print_to_string("TEXNET", end='')
			if (working_character == 0xC4):
				string_output += print_to_string("Link Quality Protocol", end='')
			if (working_character == 0xCA):
				string_output += print_to_string("Appletalk", end='')
			if (working_character == 0xCC):
				string_output += print_to_string("ARPA Internet Protocol", end='')
			if (working_character == 0xCD):
				string_output += print_to_string("ARPA Address Resolution", end='')
			if (working_character == 0xCF):
				string_output += print_to_string("TheNET (NET/ROM)", end='')
			if (working_character == 0xF0):
				string_output += print_to_string("No Layer 3", end='')
			if (working_character == 0xFF):
				string_output += print_to_string("Escape", end='')

		index = index + 1

		# return the index of the start of payload data and the printed string
		string_output += print_to_string(" ")
	return [index, string_output]



class ReportStyle:
	def __init__(self, options):
		self.destination = options.get('destination', 'std_out')
		self.style = options.get('style', 'raw')

class PacketMeta:

	def __init__(self):
		# the array of bytes that make up the packet
		self.data = []
		# the reference point in the bitstream where this packet was decoded
		# it is measured to the last bit of the closing flag in the packet.
		# this is used for comparing age of packets in multi-decoder systems
		self.streamaddress = 0
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
		self.address_distance = kwargs.get('address_distance', 10000)
		# Identify unique and duplicate packets based on stream address and CalculatedCRC
		first_array = True
		for raw_packet_array in self.raw_packet_arrays:
			for raw_packet in raw_packet_array:
				# only check validated packets
				if raw_packet.ValidCRC:
					# assume this packet is unique
					is_unique = True
					# everything in the first array is unique
					if first_array == False:
						# compare this packet with the existing unique packets, flag false if matched
						for unique_packet in self.unique_packet_array:
							# don't check packets from the same decoder
							if (unique_packet.SourceDecoder != raw_packet.SourceDecoder):
								if (
									(abs(raw_packet.streamaddress - unique_packet.streamaddress) < self.address_distance)
									and
									(raw_packet.CalculatedCRC == unique_packet.CalculatedCRC)
								):
									is_unique = False
									unique_packet.CorrelatedDecoders.append(raw_packet.SourceDecoder)
									break
					if is_unique:
						raw_packet.CorrelatedDecoders.append(raw_packet.SourceDecoder)
						# this packet is unique, add it to the list.
						self.unique_packet_array.append(raw_packet)
			first_array = False
		# now sort the unique list:
		self.unique_packet_array = sorted(self.unique_packet_array, key=lambda packet: packet.streamaddress)
	
	def CountBad(self):
		self.bad_count = 0
		for packet_array in self.raw_packet_arrays:
			for packet in packet_array:
				if packet.ValidCRC == False:
					self.bad_count += 1
		return self.bad_count
	
	def PrintRawBad(self):
		string_output = ''
		self.bad_count = 0
		for packet_array in self.raw_packet_arrays:
			for packet in packet_array:
				if packet.ValidCRC == False:
					self.bad_count += 1
					string_output += print_to_string("Valid IL2P Decode with Invalid CRC:")
					string_output += print_to_string("Packet number: ", self.bad_count, "Calc CRC: ", hex(packet.CalculatedCRC), "Carried CRC: ", hex(packet.CarriedCRC), "stream address: ", packet.streamaddress)
					string_output += print_to_string("source decoder: ", packet.SourceDecoder)
					for byte in packet.data[:-2]:
						byte = int(byte)
						if (byte < 0x7F) and (byte > 0x1F):
							string_output += print_to_string(chr(int(byte)), end='')
						else:
							string_output += print_to_string(f'<{byte}>', end='')
					string_output += print_to_string("")
					for byte in packet.data[:-2]:
						string_output += print_to_string(hex(int(byte)), end=" ")
					string_output += print_to_string(" ")
		return string_output
	
	def CountGood(self):
		# now print results
		self.good_count = 0
		for packet in self.unique_packet_array:
			if packet.ValidCRC:
				self.good_count += 1
		return self.good_count
	
	def PrintRawGood(self):
		string_output = ''
		# now print results
		self.good_count = 0
		for packet in self.unique_packet_array:
			if packet.ValidCRC:
				self.good_count += 1
				string_output += print_to_string("Packet number: ", self.good_count, " CRC: ", hex(packet.CalculatedCRC), "stream address: ", packet.streamaddress)
				string_output += print_to_string("source decoders: ", packet.CorrelatedDecoders)
				for byte in packet.data[:-2]:
					byte = int(byte)
					if (byte < 0x7F) and (byte > 0x1F):
						string_output +=print_to_string(chr(int(byte)), end='')
					else:
						string_output += print_to_string(f'<{byte}>', end='')
				string_output += print_to_string(" ")
				for byte in packet.data[:-2]:
					string_output += print_to_string(hex(int(byte)), end=" ")
				string_output += print_to_string(" ")
		return string_output

	def Report(self, order):
		string_output = ''
		count = 0
		if order.style == 'raw':
			string_output += self.PrintRawBad()
			string_output += self.PrintRawGood()
			string_output += print_to_string("Valid packets: ", self.CountGood())
			string_output += print_to_string("CRC saves: ", self.CountBad())
		elif order.style == 'decoded_headers':
			for packet in self.unique_packet_array:
				if packet.ValidCRC:
					count += 1
					string_output += print_to_string("Packet number: ", count, " CRC: ", hex(packet.CalculatedCRC), "stream address: ", packet.streamaddress)
					string_output += print_to_string("source decoders: ", packet.CorrelatedDecoders)
					string_output += print_to_string("Packet byte count: ", len(packet.data))
					header_info = print_ax25_header_to_string(packet.data, ', ')
					string_output += header_info[1]
					for i in range(header_info[0], len(packet.data)-2):
						byte = packet.data[i]
						string_output +=print_to_string(chr(int(byte)), end='')
			string_output += print_to_string("Valid packets: ", self.CountGood())
			string_output += print_to_string("CRC saves: ", self.CountBad())
		return string_output
