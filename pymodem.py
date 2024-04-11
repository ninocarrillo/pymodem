# Python3
# Demodulate, slice, and decode packets from an audio file.
# Nino Carrillo
# 29 Mar 2024
# Exit codes
# 1 Wrong Python version
# 2 Wrong argument count
# 3 Unable to open config file
# 4 Unable to open audio file

import sys
from scipy.io.wavfile import read as readwav
from scipy.io.wavfile import write as writewav

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
		print("Not enough arguments. Usage: python3 pymodem.py <config json> <sound file>")
		sys.exit(2)
	# try to open configuration json
	try:
		configfile = open(sys.argv[1], 'r')
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
		sys.exit(4)

	print("Building processing stacks from config json")

	demod_stack = []
	report_stack = []
	demod_stack_index = 0
	report_stack_index = 0
	line_number = 0
	for line in stack_plan:
		line_number += 1
		try:
			object_type = line.get('object_type')
			print(f"Found object_type: {object_type}")
		except:
			print(f"Missing 'object_type' in {sys.argv[1]} line {line_number}, skipping this chain.")
			continue

		if object_type == 'demod_chain':
			demod_stack.append([])
			try:
				demod_stack[demod_stack_index].append(line['object_name'])
				print(f"Line {line_number}: {demod_stack[demod_stack_index][0]}")
			except:
				print(f"Missing 'object_name' in {sys.argv[1]} line {line_number}, skipping this chain.")
				demod_stack_index += 1
				# go to the next iteration of the for loop
				continue
			# append the modem object to this chain
			try:
				modem = modems_codecs.chain_builder.ModemConfigurator(
					input_sample_rate,
					line['modem'],
				)
			except:
				print(f"Invalid or missing 'modem' in {line['object_name']}.")
				modem = []
			demod_stack[demod_stack_index].append(modem)
			try:
				slicer_sample_rate = demod_stack[demod_stack_index][1].output_sample_rate
			except:
				slicer_sample_rate = input_sample_rate
			try:
				slicer = modems_codecs.chain_builder.SlicerConfigurator(
					slicer_sample_rate,
					line['slicer']
				)
			except:
				print(f"Invalid or missing 'slicer' in {line['object_name']}.")
				slicer = []
			demod_stack[demod_stack_index].append(slicer)
			try:
				stream = modems_codecs.chain_builder.StreamConfigurator(line['stream'])
			except:
				print(f"Invalid or missing 'stream' in {line['object_name']}.")
				stream = []
			demod_stack[demod_stack_index].append(stream)
			try:
				codec = modems_codecs.chain_builder.CodecConfigurator(
					line['codec'],
					line['object_name']
				)
			except:
				print(f"Invalid or missing 'codec' in {line['object_name']}.")
				codec = []
			demod_stack[demod_stack_index].append(codec)
			demod_stack_index += 1
		elif object_type == 'report':
			report_stack.append([])
			try:
				report_stack[report_stack_index].append(line['object_name'])
				print(f"Line {line_number}: {report_stack[report_stack_index][0]}")
			except:
				print(f"Missing 'object_name' in {sys.argv[1]} line {line_number}, skipping this reporter.")
				report_stack_index += 1
				# go to the next iteration of the for loop
				continue
			# append the report style object to this chain
			try:
				report = modems_codecs.packet_meta.ReportStyle(line['options'])
			except:
				print(f"Invalid or missing 'style' in {line['object_name']}.")
				report = []
			report_stack[report_stack_index].append(report)

	print("Executing demod stack plan.")
	decoded_datas = []
	for chain in demod_stack:
		print(f"Processing chain: {chain[0]}")
		try:
			demod_audio = chain[1].demod(input_audio)
		except:
			print("skipped modem")
			pass
		try:
			sliced_data = chain[2].slice(demod_audio)
		except:
			print("skipped slicer")
			pass
		try:
			descrambled_data = chain[3].stream_unscramble_8bit(sliced_data)
		except:
			print("skipped stream")
			pass
		try:
			decoded_datas.append(chain[4].decode(descrambled_data))
		except:
			print("skipped codec")
			pass


	print("Correlating results.")

	results = PacketMetaArray()
	for decoded_data in decoded_datas:
		results.add(decoded_data)

	results.CalcCRCs()
	results.Correlate(address_distance=input_sample_rate/4)

	for report_order in report_stack:
		print(f"Generating {report_order[0]}")
		print(results.Report(report_order[1]))


if __name__ == "__main__":
	main()