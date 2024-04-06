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
from lfsr import LFSR
from ax25 import AX25Codec
from packet_meta import PacketMeta, PacketMetaArray
import crc_functions

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


	modem_1 = AFSKModem(sample_rate=input_sample_rate, config='1200')
	modem_1.space_gain = 1.0
	modem_1.tune()
	demod_audio_1 = modem_1.demod(input_audio)
	
	modem_2 = AFSKModem(sample_rate=input_sample_rate, config='1200')
	modem_2.space_gain = 2.1
	modem_2.tune()
	demod_audio_2 = modem_2.demod(input_audio)

	slicer_1 = BinarySlicer(sample_rate=input_sample_rate, config='1200')
	sliced_data_1 = slicer_1.slice(demod_audio_1)
	
	slicer_2 = BinarySlicer(sample_rate=input_sample_rate, config='1200')
	sliced_data_2 = slicer_1.slice(demod_audio_2)

	#il2p_codec_1 = IL2PCodec(crc=True)
	#il2p_decoded_data = il2p_codec_1.decode(sliced_data)

	# Apply differential decoding through a linear feedback shift register.
	# The same method can be used for de-scrambling.
	# For simple differential decoding, the polynomial is x + 1 or 0b11 or 0x3
	# AX.25 invertes the bitstream as well
	# The G3RUH polynomial is 0x21001.
	# Sequential lfsr operations can be combined by multiplying the polynomials
	# together.
	# So G3RUH descrambling combined with differential decoding is equivalent
	# to lfsr polynomial 0x21001 * 0x3 = 0x63003

	LFSR_1 = LFSR(poly=0x3, invert=True)
	descrambled_data_1 = LFSR_1.stream_unscramble_8bit(sliced_data_1)
	
	LFSR_2 = LFSR(poly=0x3, invert=True)
	descrambled_data_2 = LFSR_2.stream_unscramble_8bit(sliced_data_2)

	# Attempt AX.25 packet decoding on the descrambled data.

	ax25_codec_1 = AX25Codec(ident=1)
	ax25_decoded_data_1 = ax25_codec_1.decode(descrambled_data_1)
	
	ax25_codec_2 = AX25Codec(ident=2)
	ax25_decoded_data_2 = ax25_codec_2.decode(descrambled_data_2)
	
	results = PacketMetaArray()
	results.add(ax25_decoded_data_1)
	results.add(ax25_decoded_data_2)
	#print(results.raw_packet_arrays)
	results.CalcCRCs()
	results.Correlate(address_distance=1000)

	# if il2p_codec_1.crc:
	#Check CRCs on each decoded packet.
		# good_count = 0
		# for packet in il2p_decoded_data:
			# crc_result = crc_functions.CheckCRC(packet)
			# if crc_result[2] == True:
				# good_count += 1
				# print("Packet number: ", good_count, " CRC: ", hex(crc_result[0]))
				# for byte in packet[:-2]:
					# byte = int(byte)
					# if (byte < 0x7F) and (byte > 0x1F):
						# print(chr(int(byte)), end='')
					# else:
						# print(f'<{byte}>', end='')
				# print(" ")
	# else:
		# good_count = 0
		# for packet in il2p_decoded_data:
				# good_count += 1
				# print("Packet number: ", good_count)
				# for byte in packet:
					# byte = int(byte)
					# if (byte < 0x7F) and (byte > 0x1F):
						# print(chr(int(byte)), end='')
					# else:
						# print(f'<{byte}>', end='')
				# print(" ")


	good_count = 0
	for packet in results.unique_packet_array:
		if packet.ValidCRC:
			good_count += 1
			print("Packet number: ", good_count, " CRC: ", hex(packet.CalculatedCRC), "bit address: ", packet.bitaddress)
			print("source decoders: ", packet.CorrelatedDecoders)
			for byte in packet.data[:-2]:
				byte = int(byte)
				if (byte < 0x7F) and (byte > 0x1F):
					print(chr(int(byte)), end='')
				else:
					print(f'<{byte}>', end='')
			print(" ")


if __name__ == "__main__":
	main()
