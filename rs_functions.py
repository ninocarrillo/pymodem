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
	result = 0
	return result
