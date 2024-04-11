# Python3
# Functions for demodulating PSK
# Nino Carrillo
# 9 Apr 2024

import modems_codecs.psk
import modems_codecs.afsk
import modems_codecs.gfsk
import modems_codecs.lfsr
import modems_codecs.slicer

def ModemConfigurator(arg_sample_rate, input_args):
	new_object = []
	if input_args['type'] == 'bpsk':
		new_object = modems_codecs.psk.BPSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
		new_object.StringOptionsRetune(input_args['options'])
	elif input_args['type'] == 'gfsk':
		new_object = modems_codecs.gfsk.GFSKModem()
	elif input_args['type'] == 'afsk':
		new_object = modems_codecs.afsk.AFSKModem()
	return new_object

def SlicerConfigurator(arg_sample_rate, input_args):
	new_object = []
	if input_args['type'] == 'binary':
		new_object = modems_codecs.slicer.BinarySlicer(sample_rate=arg_sample_rate, config=input_args['config'])
		new_object.StringOptionsRetune(input_args['options'])
	return new_object

def LFSRConfigurator(input_args):
	new_object = modems_codecs.lfsr.LFSR()
	try:
		poly = int(input_args.get('poly'), 16)
	except:
		try:
			poly = int(input_args.get('poly'), 10)
		except:
			try:
				poly = int(input_args.get('poly'), 2)
			except:
				poly = 1
	invert = input_args.get('invert')
	if poly:
		new_object.polynomial = poly
	if invert:
		new_object.invert = True
	else:
		new_object.invert = False
	return new_object

def CodecConfigurator(input_args, name):
	new_object = []
	if input_args['type'] == 'il2p' or input_args['type'] == 'IL2P':
		new_object = modems_codecs.il2p.IL2PCodec(ident=name)
		crc = input_args.get('crc', True)
		disable_rs = input_args.get('disable_rs')
		if crc:
			new_object.collect_trailing_crc = True
		else:
			new_object.collect_trailing_crc = False
		if disable_rs:
			new_object.disable_rs = True
		else:
			new_object.disable_rs = False
	return new_object
