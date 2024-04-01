# crc_functions
# Python3
# Functions for calculating CRCs
# Nino Carrillo
# 31 Mar 2024

# CRC-CCIT Polynomial x^16+x^12+x^5+1

def CheckCRC(packet):
	packet_crc = int((packet[-1] * 256) + packet[-2])
	fcs = 0xFFFF
	CRC_poly = 0x8408
	for byte in packet[:-2]:
		byte = int(byte)
		for i in range(8):
			if (fcs & 1) != (byte & 1):
				fcs = (fcs >> 1) ^ CRC_poly
			else:
				fcs >>= 1
			byte >>= 1
	fcs ^= 0xFFFF
	if packet_crc == fcs:
		return [packet_crc, fcs, True]
	else:
		return [packet_crc, fcs, False]
