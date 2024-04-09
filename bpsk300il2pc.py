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

from modems_codecs.psk import BPSKModem
from modems_codecs.slicer import BinarySlicer
from modems_codecs.il2p import IL2PCodec
from modems_codecs.packet_meta import PacketMeta, PacketMetaArray


import matplotlib.pyplot as plt

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
	modems.append(BPSKModem(sample_rate=input_sample_rate, config='300'))
	# append more modems as desired

	demod_audios = []
	for modem in modems:
		demod_audios.append(modem.demod(input_audio))


	

	print("Slicing bits.")

	slicers = []
	sliced_datas = []
	i = 0
	for demod_audio in demod_audios:
		plt.figure()
		plt.plot(demod_audios[0])
		plt.plot(modems[i].AGC.envelope_buffer)
		plt.plot(modems[i].i_oscillator_output)
		plt.plot(modems[i].q_oscillator_output)
		#plt.plot(modems[i].original_sample_buffer)
		plt.show()
		writewav(f"FilteredSignal_{i}.wav", input_sample_rate, demod_audio / 10000)
		slicers.append(BinarySlicer(sample_rate=input_sample_rate, config='300'))
		slicers[-1].retune(lock_rate=0.90)
		sliced_datas.append(slicers[-1].slice(demod_audio))
		i += 1

	print("IL2P Decoding.")

	il2p_codecs = []
	decoded_datas = []
	i = 0
	for sliced_data in sliced_datas:
		il2p_codecs.append(IL2PCodec(ident=i, crc=True, min_dist=0, disable_rs=False))
		i += 1
		decoded_datas.append(il2p_codecs[-1].decode(sliced_data))

	print("Correlating results.")

	results = PacketMetaArray()
	for decoded_data in decoded_datas:
		results.add(decoded_data)

	results.CalcCRCs()

	# Look for CRC saves
	bad_count = 0
	for packet_array in results.raw_packet_arrays:
		for packet in packet_array:
			if packet.ValidCRC == False:
				bad_count += 1
				print("Valid IL2P Decode with Invalid CRC:")
				print("Packet number: ", bad_count, "Calc CRC: ", hex(packet.CalculatedCRC), "Carried CRC: ", hex(packet.CarriedCRC), "stream address: ", packet.streamaddress)
				print("source decoder: ", packet.SourceDecoder)
				for byte in packet.data[:-2]:
					byte = int(byte)
					if (byte < 0x7F) and (byte > 0x1F):
						print(chr(int(byte)), end='')
					else:
						print(f'<{byte}>', end='')
				print("")
				for byte in packet.data[:-2]:
					print(hex(int(byte)), end=" ")
				print(" ")


	results.Correlate(address_distance=input_sample_rate/4)

	# now print results
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
			for byte in packet.data[:-2]:
				print(hex(int(byte)), end=" ")
			print(" ")


if __name__ == "__main__":
	main()
