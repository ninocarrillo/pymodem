# gf_functions
# Python3
# Functions for galois field arithmetic
# Nino Carrillo
# 4 Apr 2024

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
	result = gf['index'][int(a)] + gf['index'][int(b)]
	while result > (gf['order'] - 2):
		result -= (gf['order'] - 1)
	return gf['table'][int(result)]

def div(gf, a, b):
	if b == 0:
		return 0xFFFF
	if a == 0:
		return 0
	result = gf['index'][a] - gf['index'][b]
	while result < 0:
		result += (gf['order'] - 1)
	return gf['table'][result]

def convolve(gf, poly1, poly1len, poly2, poly2len):
	len = poly1len + poly2len - 1
	polyresult = []
	for i in range(len):
		polyresult.append(0)
	for i in range(poly1len):
		for j in range(poly2len):
			polyresult[i + j] = int(polyresult[i + j]) \
											^ int(mul(gf, poly1[i], poly2[j]))
	return polyresult

def initialize(power, genpoly):
	gf = {}
	gf['genpoly'] = genpoly
	gf['order'] = 2**power
	gf['table'] = []
	for i in range(gf['order']-1):
		gf['table'].append(0)
	gf['index'] = []
	for i in range(gf['order']):
		gf['index'].append(0)
	gf['inverse'] = []
	for i in range(gf['order']):
		gf['inverse'].append(0)
	# generate the field table and index
	gf['lfsr'] = 1 # start with GF element a^0
	for i in range(gf['order'] - 2, -1, -1):
		lfsr_step(gf)
		gf['table'][i] = gf['lfsr']
		gf['index'][gf['lfsr']] = i
	# generate the inverse table by brute force, using
	# multiplication to find the multiplicand that results in
	# product 1
	for i in range(1, gf['order']):
		j = 1
		while (mul(gf, i, j) != 1):
			j += 1
		gf['inverse'][i] = j
	return gf
