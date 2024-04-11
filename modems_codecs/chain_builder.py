# Python3
# Functions for demodulating PSK
# Nino Carrillo
# 9 Apr 2024

import modems_codecs.psk
import modems_codecs.afsk
import modems_codecs.gfsk
import modems_codecs.lfsr
import modems_codecs.slicer
import modems_codecs.il2p
import modems_codecs.ax25

def ModemConfigurator(arg_sample_rate, input_args):
	new_object = []
	if input_args.get('type'):
		if input_args['type'] == 'bpsk':
			new_object = modems_codecs.psk.BPSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == 'gfsk':
			new_object = modems_codecs.gfsk.GFSKModem()
		elif input_args['type'] == 'afsk':
			new_object = modems_codecs.afsk.AFSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
	return new_object

def SlicerConfigurator(arg_sample_rate, input_args):
	new_object = []
	if input_args.get('type'):
		if input_args['type'] == 'binary':
			new_object = modems_codecs.slicer.BinarySlicer(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
	return new_object

def StreamConfigurator(input_args):
	new_object = []
	if input_args.get('type'):
		if input_args['type'] == 'lfsr':
			new_object = modems_codecs.lfsr.LFSR()
			new_object.StringOptionsRetune(input_args['options'])
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
	elif input_args['type'] == 'ax25' or input_args['type'] == 'AX25':
		new_object = modems_codecs.ax25.AX25Codec(ident=name)
	return new_object
