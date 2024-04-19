# Python3
# Functions for generating RRC FIR taps
# Nino Carrillo
# 9 Apr 2024

class RRC:
	def __init__(self, **kwargs):
		
def InitRRCFilter(this):
	this['Oversample'] = this['sample rate'] // this['symbol rate']
	this['TapCount'] = this['symbol span'] * this['Oversample'] + 1
	this['TimeStep'] = 1 / this['sample rate']
	this['SymbolTime'] = 1 / this['symbol rate']
	this['Time'] = np.arange(0, this['TapCount'] * this['TimeStep'], this['TimeStep']) - (this['TapCount'] * this['TimeStep'] / 2) + (this['TimeStep'] / 2)
	this['SymbolTicks'] = np.arange(this['Time'][0] - (this['TimeStep'] / 2), this['Time'][this['TapCount'] - 1], this['SymbolTime'])
	this['Taps'] = np.zeros(this['TapCount'])
	# discontinuity:
	# print(this['TimeStep'] / (4 * this['rolloff rate']))
	index = 0
	try:
		asymptote = this['SymbolTime'] / (4 * this['rolloff rate'])
	except:
		asymptote = False
	for time in this['Time']:
		if math.isclose(time,-asymptote) or math.isclose(time, asymptote):
			numerator = this['rolloff rate'] * ((1 + 2 / np.pi) * np.sin(np.pi/(4 * this['rolloff rate'])) + (1 - (2 / np.pi)) * np.cos(np.pi / (4 * this['rolloff rate'])))
			denominator = this['SymbolTime'] * pow(2, 0.5)
			this['Taps'][index] = numerator / denominator
		else:
			numerator = np.sin(np.pi * time * (1 - this['rolloff rate']) / this['SymbolTime']) + 4 * this['rolloff rate'] * time * np.cos(np.pi * time * (1 + this['rolloff rate']) / this['SymbolTime']) / this['SymbolTime']
			denominator = np.pi * time * (1 - pow(4 * this['rolloff rate'] * time / this['SymbolTime'], 2)) / this['SymbolTime']
			try:
				this['Taps'][index] = numerator / (denominator * this['SymbolTime'])
			except:
				pass
		index += 1
	this['Taps'] = this['Taps'] / np.linalg.norm(this['Taps'])
	this['RC'] = np.convolve(this['Taps'], this['Taps'], 'same')

	this['FilterWindow'] = np.zeros(this['TapCount'])

	N = this['TapCount'] - 1
	if this['window'] == 'hann':
		for index in range(this['TapCount']):
			this['FilterWindow'][index] = np.power(np.sin(np.pi * index / N),2)
	elif this['window'] == 'rect':
		for index in range(this['TapCount']):
			this['FilterWindow'][index] = 1
	elif this['window'] == 'blackmann':
		a0 = 0.355768
		a1 = 0.487396
		a2 = 0.144232
		a3 = 0.012604
		for index in range(this['TapCount']):
			this['FilterWindow'][index] = a0 - (a1 * np.cos(2 * np.pi * index / N)) + (a2 * np.cos(4 * np.pi * index / N)) - (a3 * np.cos(6 * np.pi * index / N))
	elif this['window'] == 'blackmann-harris':
		a0 = 0.35875
		a1 = 0.48829
		a2 = 0.14128
		a3 = 0.01168
		for index in range(this['TapCount']):
			this['FilterWindow'][index] = a0 - (a1 * np.cos(2 * np.pi * index / N)) + (a2 * np.cos(4 * np.pi * index / N)) - (a3 * np.cos(6 * np.pi * index / N))
	elif this['window'] == 'flattop':
		a0 = 0.21557895
		a1 = 0.41663158
		a2 = 0.277263158
		a3 = 0.083578947
		a4 = 0.006947368
		for index in range(this['TapCount']):
			this['FilterWindow'][index] = a0 - (a1 * np.cos(2 * np.pi * index / N)) + (a2 * np.cos(4 * np.pi * index / N)) - (a3 * np.cos(6 * np.pi * index / N)) + (a4  * np.cos(8 * np.pi * index / N))
	elif this['window'] == 'tukey':
		a = 0.25
		index = 0
		while index < a * N / 2:
			this['FilterWindow'][index] = 0.5 * (1 - np.cos(2 * np.pi * index / (a * N)))
			index += 1
		while index <= N // 2:
			this['FilterWindow'][index] = 1
			index += 1
		while index <= N:
			this['FilterWindow'][index] = this['FilterWindow'][N - index]
			index += 1


	this['Taps'] = np.multiply(this['Taps'], this['FilterWindow'])
	this['WindowedRC'] = np.convolve(this['Taps'], this['Taps'], 'same')
	this['WindowedRC'] = this['WindowedRC'] * max(this['Taps']) / max(this['WindowedRC'])
	return this
