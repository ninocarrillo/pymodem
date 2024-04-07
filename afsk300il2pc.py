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
		print("Not enough arguments. Usage: python3 decode.py <sound file>")
		sys.exit(2)
	# try to open audio file
	try:
		input_sample_rate, input_audio = readwav(sys.argv[1])
	except:
		print('Unable to open audio file.')
		sys.exit(3)

	print("Demodulating audio.")

	modem_1 = AFSKModem(sample_rate=input_sample_rate, config='300')
	demod_audio_1 = modem_1.demod(input_audio)

	modem_2 = AFSKModem(sample_rate=input_sample_rate, config='300')
	modem_2.retune(correlator_offset=-10)
	demod_audio_2 = modem_2.demod(input_audio)

	modem_3 = AFSKModem(sample_rate=input_sample_rate, config='300')
	modem_3.retune(correlator_offset=+10)
	demod_audio_3 = modem_3.demod(input_audio)


	print("Slicing bits.")

	slicer_1 = BinarySlicer(sample_rate=input_sample_rate, config='300')
	sliced_data_1 = slicer_1.slice(demod_audio_1)

	slicer_2 = BinarySlicer(sample_rate=input_sample_rate, config='300')
	sliced_data_2 = slicer_2.slice(demod_audio_2)

	slicer_3 = BinarySlicer(sample_rate=input_sample_rate, config='300')
	sliced_data_3 = slicer_3.slice(demod_audio_3)

	print("IL2P Decoding.")

	il2p_codec_1 = IL2PCodec(ident='il2pc 300 +0', crc=True)
	il2p_decoded_data_1 = il2p_codec_1.decode(sliced_data_1)

	il2p_codec_2 = IL2PCodec(ident='il2pc 300 -10', crc=True)
	il2p_decoded_data_2 = il2p_codec_2.decode(sliced_data_2)

	il2p_codec_3 = IL2PCodec(ident='il2pc 300 +10', crc=True)
	il2p_decoded_data_3 = il2p_codec_3.decode(sliced_data_3)

	print("Correlating results.")

	results = PacketMetaArray()
	results.add(il2p_decoded_data_1)
	results.add(il2p_decoded_data_2)
	results.add(il2p_decoded_data_3)
	results.CalcCRCs()
	results.Correlate(address_distance=input_sample_rate/4)


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
