# data_classes
# Python3
# classes to support data handling through modems
# Nino Carrillo
# 6 Apr 2024

class AddressedData:
	def __init__(self, data, address, *args):
		# a place to hold the data output and
		# a unique address for later use
		self.data = data
		self.address = address

class IQData:
	def __init__(self):
		self.i_data = []
		self.q_data = []
