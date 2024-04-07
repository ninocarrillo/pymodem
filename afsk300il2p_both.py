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
from scipy.io.wavfile import write as writewav
from modems_codecs.afsk import AFSKModem
from modems_codecs.slicer import BinarySlicer
from modems_codecs.il2p import IL2PCodec
from modems_codecs.lfsr import LFSR
from modems_codecs.packet_meta import PacketMeta, PacketMetaArray
import numpy

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

	modems = []
	modems.append(AFSKModem(sample_rate=input_sample_rate, config='300'))
	# append more modems as desired

	demod_audios = []
	for modem in modems:
		demod_audios.append(modem.demod(input_audio))

	print("Slicing bits.")

	slicers = []
	sliced_datas = []
	for demod_audio in demod_audios:
		slicers.append(BinarySlicer(sample_rate=input_sample_rate, config='300'))
		slicers[-1].retune(lock_rate=0.90)
		sliced_datas.append(slicers[-1].slice(demod_audio))

	print("IL2P Decoding.")

	il2p_codecs = []

	il2p_codecs.append(IL2PCodec(ident='with CRC', crc=True, min_dist=0, disable_rs=False))
	il2p_codecs.append(IL2PCodec(ident='without CRC', crc=False, min_dist=0, disable_rs=False))

	decoded_datas = []
	for sliced_data in sliced_datas:
		for codec in il2p_codecs:
			decoded_datas.append(codec.decode(sliced_data))

	print("Correlating results.")

	results = PacketMetaArray()
	for decoded_data in decoded_datas:
		results.add(decoded_data)

	results.CalcCRCs()
	results.Correlate(address_distance=input_sample_rate/4)

	# now print results
	good_count = 0
	for packet in results.unique_packet_array:
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
