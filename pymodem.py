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
from modems_codecs.lfsr import LFSR
from modems_codecs.packet_meta import PacketMeta, PacketMetaArray
import modems_codecs.chain_builder
import json


import matplotlib.pyplot as plt

def main():
	# check correct version of Python
	if sys.version_info < (3, 0):
		print("Python version should be 3.x, exiting")
		sys.exit(1)
	# check correct number of parameters were passed to command line
	if len(sys.argv) != 3:
		print("Not enough arguments. Usage: python3 decode.py <config json> <sound file>")
		sys.exit(2)
	# try to open configuration json
	try:
		configfile = open(sys.argv[1], 'r')
		#stack_plan = json.load(configfile)
		stack_plan = []
		for line in configfile:
			stack_plan.append(json.loads(line))
		configfile.close()
	except:
		print('Unable to open config json file.')
		sys.exit(3)
	# try to open audio file
	try:
		input_sample_rate, input_audio = readwav(sys.argv[2])
	except:
		print('Unable to open audio file.')
		sys.exit(3)

	print("Building stack from config json")

	stack = []
	i = 0
	for line in stack_plan:
		stack.append([])
		try:
			stack[i].append(line['chain_name'])
			print(f"Line {i+1}: {stack[i][0]}.")
		except:
			print(f"Missing 'chain_name' in {sys.argv[1]} line {i+1}, skipping this chain.")
			i += 1
			# go to the next iteration of the for loop
			continue

		# append the modem object to this chain
		stack[i].append(
			modems_codecs.chain_builder.ModemConfigurator(
				input_sample_rate,
				line['modem'],
			)

		)
		stack[i].append(
			modems_codecs.chain_builder.SlicerConfigurator(
				stack[i][1].output_sample_rate,
				line['slicer']
			)
		)
		stack[i].append(
			modems_codecs.chain_builder.LFSRConfigurator(line['lfsr'])
		)
		stack[i].append(
			modems_codecs.chain_builder.CodecConfigurator(
				line['codec'],
				line['chain_name']
			)
		)
		i += 1


	print("Executing stack plan.")
	decoded_datas = []
	for chain in stack:
		print(chain[0])
		demod_audio = chain[1].demod(input_audio)
		sliced_data = chain[2].slice(demod_audio)
		descrambled_data = chain[3].stream_unscramble_8bit(sliced_data)
		decoded_datas.append(chain[4].decode(descrambled_data))



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
