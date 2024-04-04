# gf_functions
# Python3
# Functions for galois field arithmetic
# Nino Carrillo
# 4 Apr 2024

from numpy import zeros

def lfsr_step(gf):
	# utilize Galois configuration to implement LFSR
	if gf['lfsr'] & 1:
		feedback_bit = True
	else:
		feedback_bit = False
	gf['lfsr'] >>= 1
	if (feedback_bit):
		gf['lfsr'] ^= (gf['genpoly'] >> 1)
	return

def mul(gf, a, b):
	if ((a == 0) or (b == 0)):
		return 0
	result = gf['index'][a] + gf['index'][b]
	while result > (gf['order'] - 2):
		result -= (gf['order'] - 1)
	return gf['table'][int(result)]

def initialize(power, genpoly):
	gf = {}
	gf['genpoly'] = genpoly
	gf['order'] = 2**power
	gf['table'] = zeros(gf['order'] - 1)
	gf['index'] = zeros(gf['order'])
	gf['inverse'] = zeros(gf['order'])
	# generate the field table and index
	gf['lfsr'] = 1 # start with GF element a^0
	for i in range(gf['order'] - 2, -1, -1):
		lfsr_step(gf)
		gf['table'][i] = gf['lfsr']
		gf['index'][gf['lfsr']] = i
	for i in range(1, gf['order']):
		j = 1
		while (mul(gf, i, j) != 1):
			j += 1
		gf['inverse'][i] = j
	return gf
