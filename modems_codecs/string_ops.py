# Python3
# Functions for interpreting strings
# Nino Carrillo
# 9 Apr 2024

def check_boolean(input_string):
	input_string = input_string.lower()
	if (
		(input_string == "yes")
		or (input_string == "true")
		or (input_string == "1")
	):
		return True
	else:
		return False
