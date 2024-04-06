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

	print("Demodulating audio.")

	modem_1 = AFSKModem(sample_rate=input_sample_rate, config='300')
	modem_1.tune()
	demod_audio_1 = modem_1.demod(input_audio)
	
	modem_2 = AFSKModem(sample_rate=input_sample_rate, config='1200')
	modem_2.tune()
	demod_audio_2 = modem_2.demod(input_audio)

	print("Slicing bits.")

	slicer_1 = BinarySlicer(sample_rate=input_sample_rate, config='300')
	sliced_data_1 = slicer_1.slice(demod_audio_1)
	
	slicer_2 = BinarySlicer(sample_rate=input_sample_rate, config='1200')
	sliced_data_2 = slicer_2.slice(demod_audio_2)

	print("IL2P Decoding.")

	il2p_codec_1 = IL2PCodec(ident='il2pc 300', crc=True)
	il2p_decoded_data_1 = il2p_codec_1.decode(sliced_data_1)
	
	il2p_codec_2 = IL2PCodec(ident='il2pc 1200', crc=True)
	il2p_decoded_data_2 = il2p_codec_2.decode(sliced_data_2)
	
	il2p_codec_3 = IL2PCodec(ident='il2p 1200', crc=False)
	il2p_decoded_data_3 = il2p_codec_3.decode(sliced_data_2)

	# Apply differential decoding through a linear feedback shift register.
	# The same method can be used for de-scrambling.
	# For simple differential decoding, the polynomial is x + 1 or 0b11 or 0x3
	# AX.25 invertes the bitstream as well
	# The G3RUH polynomial is 0x21001.
	# Sequential lfsr operations can be combined by multiplying the polynomials
	# together.
	# So G3RUH descrambling combined with differential decoding is equivalent
	# to lfsr polynomial 0x21001 * 0x3 = 0x63003

	print("Applying LFSR.")

	LFSR_1 = LFSR(poly=0x3, invert=True)
	descrambled_data_1 = LFSR_1.stream_unscramble_8bit(sliced_data_1)
	
	LFSR_2 = LFSR(poly=0x3, invert=True)
	descrambled_data_2 = LFSR_2.stream_unscramble_8bit(sliced_data_2)

	# Attempt AX.25 packet decoding on the descrambled data.

	print("AX25 Decoding.")

	ax25_codec_1 = AX25Codec(ident='ax25 300')
	ax25_decoded_data_1 = ax25_codec_1.decode(descrambled_data_1)
	
	ax25_codec_2 = AX25Codec(ident='ax25 1200')
	ax25_decoded_data_2 = ax25_codec_2.decode(descrambled_data_2)

	print("Correlating results.")

	results = PacketMetaArray()
	results.add(ax25_decoded_data_1)
	results.add(ax25_decoded_data_2)
	results.add(il2p_decoded_data_1)
	results.add(il2p_decoded_data_2)
	results.CalcCRCs()
	results.Correlate(address_distance=input_sample_rate/4)

	# print the non-CRC IL2P results first
	good_count = 0
	for packet in il2p_decoded_data_3:
			good_count += 1
			print("Packet number: ", good_count, " CRC: ", hex(packet.CalculatedCRC), "stream address: ", packet.streamaddress)
			for byte in packet.data[:-2]:
				byte = int(byte)
				if (byte < 0x7F) and (byte > 0x1F):
					print(chr(int(byte)), end='')
				else:
					print(f'<{byte}>', end='')
			print(" ")

	# now print the IL2P+CRC results
	good_count = 0
	for packet in results.unique_packet_array:
		if packet.ValidCRC:
			good_count += 1
			print("Packet number: ", good_count, " CRC: ", hex(packet.CalculatedCRC), "stream address: ", packet.streamaddress)
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
