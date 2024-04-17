# Python3
# Functions for executing signal processing chains
# Nino Carrillo
# 17 Apr 2024

def process_chain(chain, input_audio):
	print(f"{chain[0]} process start")
	try:
		demod_audio = chain[1].demod(input_audio)
	except:
		print(f"{chain[0]} skipped modem")
		pass
	try:
		sliced_data = chain[2].slice(demod_audio)
	except:
		print(f"{chain[0]} skipped slicer")
		pass
	try:
		descrambled_data = chain[3].stream_unscramble_8bit(sliced_data)
	except:
		print(f"{chain[0]} skipped stream")
		pass
	try:
		decoded_data = chain[4].decode(descrambled_data)
	except:
		print(f"{chain[0]} skipped codec")
		pass
	return decoded_data

def process_chain_thread(chain, input_audio, queue):
	print(f"{chain[0]} process start")
	try:
		demod_audio = chain[1].demod(input_audio)
	except:
		print(f"{chain[0]} skipped modem")
		pass
	try:
		sliced_data = chain[2].slice(demod_audio)
	except:
		print(f"{chain[0]} skipped slicer")
		pass
	try:
		descrambled_data = chain[3].stream_unscramble_8bit(sliced_data)
	except:
		print(f"{chain[0]} skipped stream")
		pass
	try:
		decoded_data = chain[4].decode(descrambled_data)
	except:
		print(f"{chain[0]} skipped codec")
		pass
	queue.put(decoded_data)
	return
