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

def decode(rs, data, block_size, min_distance):
	error_count = 0
	# calculate one syndrome for each root of genpoly:
	syndromes = []
	for i in range(rs['num_roots']):
		syndromes.append(0)
		x = rs['gf']['table'][rs['first_root'] + i]
		for j in range(block_size - 1):
			syndromes[i] = gf_functions.mul(rs['gf'], syndromes[i] ^ data[j], x)
		syndromes[i] ^= data[block_size - 1]
	# Berlekamp's Algorithm
	# calculate the error locator
	error_locator = []
	correction_poly = []
	next_error_locator = []
	error_locations = []
	error_magnitudes = []
	for i in range(rs['num_roots']):
		error_locator.append(0)
		next_error_locator.append(0)
		error_locations.append(0)
		error_magnitudes.append(0)
	for i in range(rs['num_roots'] + 1):
		correction_poly.append(0)
	error_locator[0] = 1
	correction_poly[1] = 1
	order_tracker = 0
	for step_factor in range(1, rs['num_roots'] + 1):
		# calculate error locator
		y = step_factor - 1
		e = syndromes[y]
		for i in range(1, order_tracker + 1):
			x = y - i
			e ^= gf_functions.mul(rs['gf'], error_locator[i], syndromes[x])
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
	for j in range(block_size):
		x = 0
		y = j + rs['gf']['order'] - block_size
		for i in range(1, (rs['num_roots'] // 2) + 1):
			if error_locator[i]:
				z = (y * i) + rs['gf']['index'][error_locator[i]]
				while z > (rs['gf']['order'] - 2):
					z -= (rs['gf']['order'] - 1)
				x ^= rs['gf']['table'][z]
		x ^= error_locator[0]
		if x == 0:
			# found an error here
			error_locations[error_count] = j
			error_count += 1
	if (error_count <= (rs['num_roots'] // 2) - min_distance):
		# Forney algorithm to determine error values
		for i in range(error_count):
			correction_poly[i] = syndromes[rs['first_root'] + i]
			for j in range(1, i + 1):
				correction_poly[i] ^= gf_functions.mul(
						rs['gf'],
						syndromes[rs['first_root'] + i - j],
						error_locator[j]
				)
		for i in range(error_count):
			e = block_size - error_locations[i] - 1
			z = correction_poly[0]
			for j in range(1, error_count):
				x = e * j
				while x > (rs['gf']['order'] - 2):
					x -= (rs['gf']['order'] - 1)
				x = rs['gf']['order'] - x - 1
				while x > (rs['gf']['order'] - 2):
					x -= (rs['gf']['order'] - 1)
				z ^= gf_functions.mul(
						rs['gf'],
						correction_poly[j],
						rs['gf']['table'][x]
				)
			z = gf_functions.mul(rs['gf'], z, rs['gf']['table'][e])
			y = error_locator[1]
			for j in range(3, (rs['num_roots'] // 2) + 1, 2):
				x = e * (j - 1)
				while x > (rs['gf']['order'] - 2):
					x -= (rs['gf']['order'] - 1)
				x = rs['gf']['order'] - x - 1
				while x > (rs['gf']['order'] - 2):
					x -= (rs['gf']['order'] - 1)
				y ^= gf_functions.mul(rs['gf'], error_locator[j], rs['gf']['table'][x])
			y = rs['gf']['index'][y]
			y = rs['gf']['order'] - y - 1
			if y == (rs['gf']['order'] - 1):
				y = 0
			y = rs['gf']['table'][y]
			error_magnitudes[i] = gf_functions.mul(rs['gf'], y, z)
			data[error_locations[i]] ^= error_magnitudes[i]
		# error correction is complete, now check for success by calculating syndromes on the corrected data
		for i in range(rs['num_roots']):
			syndromes[i] = 0
			x = rs['gf']['table'][rs['first_root'] + i]
			for j in range(block_size - 1):
				syndromes[i] = gf_functions.mul(rs['gf'], syndromes[i] ^ data[j], x)
			syndromes[i] ^= data[block_size - 1]
			if syndromes[i] != 0:
				error_count = -1
	return error_count
