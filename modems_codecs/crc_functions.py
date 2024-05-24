# crc_functions
# Python3
# Functions for calculating CRCs
# Nino Carrillo
# 31 Mar 2024

# CRC-CCIT Polynomial x^16+x^12+x^5+1

def CheckCRC(packet):
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
	packet_crc = int((packet[-1] * 256) + packet[-2])
	calculated_crc = 0xFFFF
	CRC_poly = 0x8408
	for byte in packet[:-2]:
		byte = int(byte)
		for i in range(8):
			if (calculated_crc & 1) != (byte & 1):
				calculated_crc = (calculated_crc >> 1) ^ CRC_poly
			else:
				calculated_crc >>= 1
			byte >>= 1
	calculated_crc ^= 0xFFFF
	crc_distance = Distance8[(calculated_crc & 0xFF)^(packet_crc & 0xFF)]
	crc_distance += Distance8[(calculated_crc>>8)^(packet_crc>>8)]
	if crc_distance <= 0:
		return [packet_crc, calculated_crc, True]
	else:
		return [packet_crc, calculated_crc, False]

def AppendCRC(packet):
	calculated_crc = 0xFFFF
	CRC_poly = 0x8408
	for byte in packet:
		byte = int(byte)
		for i in range(8):
			if (calculated_crc & 1) != (byte & 1):
				calculated_crc = (calculated_crc >> 1) ^ CRC_poly
			else:
				calculated_crc >>= 1
			byte >>= 1
	calculated_crc ^= 0xFFFF
	packet.append(calculated_crc & 0xFF)
	packet.append(calculated_crc >> 8)
