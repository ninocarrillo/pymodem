# Python3
# Functions for executing signal processing chains
# Nino Carrillo
# 17 Apr 2024

import traceback

def process_chain(chain, input_audio):
	print(f"{chain[0]} process start")
	decoded_data = []
	try:
		demod_audio = chain[1].demod(input_audio)
		sliced_data = chain[2].slice(demod_audio)
		descrambled_data = chain[3].stream_unscramble_8bit(sliced_data)
		decoded_data = chain[4].decode(descrambled_data)
	except Exception:
		print(f"{chain[0]} failed:")
		traceback.print_exc()
	return decoded_data

def multiprocess_chain(chain, input_audio, queue):
	# Always feed the queue, even on failure: the parent does a blocking
	# get() per chain and would otherwise wait forever on a chain that
	# raised. Report the real exception instead of silently skipping the
	# remaining stages.
	decoded_data = []
	try:
		demod_audio = chain[1].demod(input_audio)
		sliced_data = chain[2].slice(demod_audio)
		descrambled_data = chain[3].stream_unscramble_8bit(sliced_data)
		decoded_data = chain[4].decode(descrambled_data)
	except Exception:
		print(f"{chain[0]} failed:")
		traceback.print_exc()
	queue.put(decoded_data)
	return
