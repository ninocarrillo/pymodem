# rs_functions
# Python3
# Functions for Reed Solomon block codes
# Nino Carrillo
# 4 Apr 2024

import gf_functions

def initialize(first_root, num_roots, gf_power, gf_poly):
	rs = {}
	rs['gf'] = gf_functions.initialize(gf_power, gf_poly)
	rs['first_root'] = first_root
	rs['num_roots'] = num_roots
	# Generate Reed Solomon generator polynomial through convolution of
	# polynomials.
	# rs->genpoly = (x + a^b)(x + a^b+1)...(x + a^b+r-1)
	# start with rs->genpoly = x + a^b
	# lowest order coefficient in lowest index of array
	rs['genpoly'] = [rs['gf']['table'][first_root], 1]
	# preload the x^1 coefficient in the factor polynomial
	rs['factorpoly'] = [0, 1]
	for i in range(first_root + 1, first_root + num_roots, 1):
		rs['factorpoly'][0] = rs['gf']['table'][i]
		rs['genpoly'] = gf_functions.convolve(
			rs['gf'],
			rs['genpoly'],
			i + 1 - first_root,
			rs['factorpoly'],
			2
		)
	return rs

def decode(rs, data):
	error_count = 0
	# calculate one syndrome for each root of genpoly:
	syndromes = []
	for i in range(rs['num_roots']):
		syndromes.append(0)
		x = rs['gf']['table'][rs['first_root'] + i]
		for j in range(len(data) - 1):
			syndromes[i] = gf_functions.mul(rs['gf'], syndromes[i] ^ data[j], x)
		syndromes[i] ^= data[-1]
	print(syndromes)

	# Berlekamp's Algorithm
	# calculate the error locator
	error_locator = []
	correction_poly = []
	next_error_locator = []
	for i in range(rs['num_roots']):
		error_locator.append(0)
		next_error_locator.append(0)
	for i in range(rs['num_roots'] + 1):
		correction_poly.append(0)
	error_locator[0] = 1
	correction_poly[1] = 1
	order_tracker = 1
	for step_factor in range(1, rs['num_roots'] + 1, 1):
		# calculate error locator
		y = step_factor - 1
		e = syndromes[y]
		for i in range(1, order_tracker + 1, 1):
			x = y - i
			e = e ^ gf_functions.mul(rs['gf'], error_locator[i], syndromes[x])
		# update estimate of next_error_locator
		if (e != 0):
			for i in range(order_tracker + 1):
				next_error_locator[i] = error_locator[i] \
							^ gf_functions.mul(rs['gf'], e, correction_poly[i])
			e = rs['gf']['inverse'][e]
			for i in range((rs['num_roots'] // 2) + 1):
				correction_poly[i] = \
								gf_functions.mul(rs['gf'], error_locator[i], e)
			for i in range((rs['num_roots'] // 2) + 1):
				error_locator[i] = next_error_locator[i]
		if (2 * order_tracker) < step_factor:
			order_tracker = step_factor - order_tracker
		for i in range(rs['num_roots'], 0, -1):
			correction_poly[i] = correction_poly[i - 1]
		correction_poly[0] = 0
	# now solve the error locator polynomial to find the error positions
	# by using the Chien Search
	print(correction_poly)
	return error_count
