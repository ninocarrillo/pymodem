# Python3
# Functions for assembling signal processing chains
# Nino Carrillo
# 9 Apr 2024

import modems_codecs.psk
import modems_codecs.afsk
import modems_codecs.fsk
import modems_codecs.lfsr
import modems_codecs.slicer
import modems_codecs.il2p
import modems_codecs.ax25
import modems_codecs.afsk_pll
from modems_codecs.string_ops import check_boolean


def ModemConfigurator(arg_sample_rate, input_args):
	new_object = []
	if input_args.get('type'):
		if input_args['type'] == 'qpsk':
			new_object = modems_codecs.psk.QPSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == 'mpsk':
			new_object = modems_codecs.psk.MPSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == 'bpsk':
			new_object = modems_codecs.psk.BPSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == 'fsk':
			new_object = modems_codecs.fsk.FSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == 'afsk':
			new_object = modems_codecs.afsk.AFSKModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == 'afsk_pll':
			new_object = modems_codecs.afsk_pll.AFSKPLLModem(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
	return new_object

def SlicerConfigurator(arg_sample_rate, input_args):
	new_object = []
	if input_args.get('type'):
		if input_args['type'] == 'quadrature':
			new_object = modems_codecs.slicer.QuadratureSlicer(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == 'binary':
			new_object = modems_codecs.slicer.BinarySlicer(sample_rate=arg_sample_rate, config=input_args['config'])
			new_object.StringOptionsRetune(input_args['options'])
		elif input_args['type'] == '4level':
			new_object = modems_codecs.slicer.FourLevelSlicer(sample_rate=arg_sample_rate, config=input_args['config'])
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
	if input_args['type'].lower() == 'il2p':
		new_object = modems_codecs.il2p.IL2PCodec(ident=name)
		new_object.StringOptionsRetune(input_args['options'])
	elif input_args['type'].lower() == 'ax25':
		new_object = modems_codecs.ax25.AX25Codec(ident=name)
	return new_object
