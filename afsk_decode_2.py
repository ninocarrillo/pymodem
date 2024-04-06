# afsk_decode
# Python3
# Demodulate, slice, and decode packets from an audio file.
# Nino Carrillo
# 29 Mar 2024
# Exit codes
# 1 Wrong Python version
# 2 Wrong argument count
# 3 Unable to open audio file

import sys
from scipy.io.wavfile import read as readwav
from afsk import AFSKModem
from slicer import BinarySlicer
from il2p import IL2PCodec
import lfsr_functions
import ax25_functions
import crc_functions
import rs_functions
import gf_functions

def main():
	# check correct version of Python
	if sys.version_info < (3, 0):
		print("Python version should be 3.x, exiting")
		sys.exit(1)
	# check correct number of parameters were passed to command line
	if len(sys.argv) != 2:
		print("Not enough arguments. Usage: python3 afsk1200.py <sound file>")
		sys.exit(2)
	# try to open audio file
	try:
		input_sample_rate, input_audio = readwav(sys.argv[1])
	except:
		print('Unable to open audio file.')
		sys.exit(3)


	modem_1 = AFSKModem(input_sample_rate, config='300')
	demod_audio = modem_1.demod(input_audio)

	# Slice demodulated audio into bitstream.
	slicer_1 = BinarySlicer(input_sample_rate, config='300')
	sliced_data = slicer_1.slice(demod_audio)

	il2p_codec_1 = IL2PCodec(crc=True)
	il2p_decoded_data = il2p_codec_1.decode(sliced_data)

	if il2p_codec_1.crc:
	# Check CRCs on each decoded packet.
		good_count = 0
		for packet in il2p_decoded_data:
			crc_result = crc_functions.CheckCRC(packet)
			if crc_result[2] == True:
				good_count += 1
				print("Packet number: ", good_count, " CRC: ", hex(crc_result[0]))
				for byte in packet[:-2]:
					byte = int(byte)
					if (byte < 0x7F) and (byte > 0x1F):
						print(chr(int(byte)), end='')
					else:
						print(f'<{byte}>', end='')
				print(" ")
	else:
		good_count = 0
		for packet in il2p_decoded_data:
				good_count += 1
				print("Packet number: ", good_count)
				for byte in packet:
					byte = int(byte)
					if (byte < 0x7F) and (byte > 0x1F):
						print(chr(int(byte)), end='')
					else:
						print(f'<{byte}>', end='')
				print(" ")

	# Apply differential decoding through a linear feedback shift register.
	# The same method can be used for de-scrambling.
	# For simple differential decoding, the polynomial is x + 1 or 0b11 or 0x3
	# AX.25 invertes the bitstream as well
	# The G3RUH polynomial is 0x21001.
	# Sequential lfsr operations can be combined by multiplying the polynomials
	# together.
	# So G3RUH descrambling combined with differential decoding is equivalent
	# to lfsr polynomial 0x21001 * 0x3 = 0x63003
	polynomial = 0x3
	invert = True
	lfsr = lfsr_functions.initialize(
		polynomial,
		invert
	)

	descrambled_data = lfsr_functions.stream_unscramble_8bit(lfsr, sliced_data)

	# Attempt AX.25 packet decoding on the descrambled data.
	min_packet_length = 18
	max_packet_length = 1023
	ax25_decoder = ax25_functions.initialize_decoder(
		min_packet_length,
		max_packet_length
	)

	ax25_decoded_data = ax25_functions.decode(ax25_decoder, descrambled_data)

	# Check CRCs on each decoded packet.
	good_count = 0
	for packet in ax25_decoded_data:
		crc_result = crc_functions.CheckCRC(packet)
		if crc_result[2] == True:
			good_count += 1
			print("Packet number: ", good_count, " CRC: ", hex(crc_result[0]))
			for byte in packet[:-2]:
				byte = int(byte)
				if (byte < 0x7F) and (byte > 0x1F):
					print(chr(int(byte)), end='')
				else:
					print(f'<{byte}>', end='')
			print(" ")


if __name__ == "__main__":
	main()
