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

	modems = []
	modems.append(AFSKModem(sample_rate=input_sample_rate, config='1200'))
	modems.append(AFSKModem(sample_rate=input_sample_rate, config='1200'))
	modems[-1].retune(space_gain=2.11, correlator_span=1.5)
	# append more modems as desired

	demod_audios = []
	for modem in modems:
		demod_audios.append(modem.demod(input_audio))

	print("Slicing bits.")

	slicers = []
	sliced_datas = []
	for demod_audio in demod_audios:
		slicers.append(BinarySlicer(sample_rate=input_sample_rate, config='1200'))
		slicers[-1].retune(lock_rate=0.72)
		sliced_datas.append(slicers[-1].slice(demod_audio))

	print("IL2P Decoding.")

	il2p_codecs = []
	decoded_datas = []
	i = 0
	for sliced_data in sliced_datas:
		il2p_codecs.append(IL2PCodec(ident=i, crc=False))
		i += 1
		decoded_datas.append(il2p_codecs[-1].decode(sliced_data))

	print("Correlating results.")

	results = PacketMetaArray()
	for decoded_data in decoded_datas:
		results.add(decoded_data)

	results.CalcCRCs()
	results.Correlate(address_distance=input_sample_rate/4)

	# now print results
	good_count = 0
	for packet in results.unique_packet_array:
		#if packet.ValidCRC:
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
