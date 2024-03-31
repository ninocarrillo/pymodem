# crc_functions
# Python3
# Functions for calculating CRCs
# Nino Carrillo
# 31 Mar 2024

import numpy as np

def CheckCRC(packet, byte_count):
	packet_val = int(packet[byte_count - 1] * 256)
	packet_val += int(packet[byte_count - 2])
	# print(hex(packet_val))
	packet = packet[0:byte_count - 2] # slicing exludes the end index
	fcsval = np.uint16(0xFFFF)
	CRC_poly = np.uint16(0x8408)
	one = np.uint16(1)
	for byte in packet:
		byte = int(round(byte))
		for i in range(8):
			fcsbit = np.bitwise_and(fcsval, one)
			fcsval = np.right_shift(fcsval, 1)
			if np.bitwise_xor(fcsbit, np.bitwise_and(byte,one)) != 0:
				fcsval = np.bitwise_xor(fcsval, CRC_poly)
			byte = np.right_shift(byte, 1)
	fcs_val = np.bitwise_and(np.bitwise_not(fcsval), 0xFFFF)
	if packet_val == fcs_val:
		return [packet_val, fcs_val, 1]
	else:
		return [packet_val, fcs_val, 0]

def CalcCRC16(packet):
	fcsval = np.uint16(0xFFFF)
	CRC_poly = np.uint16(0x8408)
	one = np.uint16(1)
	for byte in packet:
		byte = int(byte)
		for i in range(8):
			fcsbit = np.bitwise_and(fcsval, one)
			fcsval = np.right_shift(fcsval, 1)
			if np.bitwise_xor(fcsbit, np.bitwise_and(byte,one)) != 0:
				fcsval = np.bitwise_xor(fcsval, CRC_poly)
			byte = np.right_shift(byte, 1)
	fcs_val = np.bitwise_and(np.bitwise_not(fcsval), 0xFFFF)
	return(hex(fcs_val))
