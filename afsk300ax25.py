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
	modems.append(AFSKModem(sample_rate=input_sample_rate, config='300'))
	modems[-1].retune(correlator_offset=-10)
	modems.append(AFSKModem(sample_rate=input_sample_rate, config='300'))
	modems.append(AFSKModem(sample_rate=input_sample_rate, config='300'))
	modems[-1].retune(correlator_offset=10)
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
		
	# Apply differential decoding through a linear feedback shift register.
	# The same method can be used for de-scrambling.
	# For simple differential decoding, the polynomial is x + 1 or 0b11 or 0x3
	# AX.25 inverts the bitstream as well
	# The G3RUH polynomial is 0x21001.
	# Sequential lfsr operations can be combined by multiplying the polynomials
	# together.
	# So G3RUH descrambling combined with differential decoding is equivalent
	# to lfsr polynomial 0x21001 * 0x3 = 0x63003

	print("Applying LFSR.")

	Descramblers = []
	descrambled_datas = []
	for sliced_data in sliced_datas:
		Descramblers.append(LFSR(poly=0x3, invert=True))
		descrambled_datas.append(Descramblers[-1].stream_unscramble_8bit(sliced_data))

	# Attempt AX.25 packet decoding on the descrambled data.

	print("AX25 Decoding.")

	ax25_codecs = []
	decoded_datas = []
	i = 0
	for descrambled_data in descrambled_datas:
		ax25_codecs.append(AX25Codec(ident=i))
		i += 1
		decoded_datas.append(ax25_codecs[-1].decode(descrambled_data))

	print("Correlating results.")

	results = PacketMetaArray()
	for decoded_data in decoded_datas:
		results.add(decoded_data)

	results.CalcCRCs()
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


if __name__ == "__main__":
	main()
