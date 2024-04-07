# crc_functions
# Python3
# Functions for calculating CRCs
# Nino Carrillo
# 31 Mar 2024

# CRC-CCIT Polynomial x^16+x^12+x^5+1

def CheckCRC(packet):
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
	if packet_crc == calculated_crc:
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
