# slicer
# Python3
# Functions for bit-slicing a sample stream
# Nino Carrillo
# 30 Mar 2024

from modems_codecs.data_classes import AddressedData
from matplotlib import pyplot as plot

class BinarySlicer:

	def __init__(self, **kwargs):

		self.definition = kwargs.get('config', '1200')
		self.sample_rate = kwargs.get('sample_rate', '8000')


		# lock_rate should be between 0 and 1.0
		# Lower numbers cause slicer to sync the bitstream faster,
		# but increase jitter. Higher values are more stable,
		# but sync the bitstream more slowly. Typically 0.65-0.95.

		if self.definition == '300':
			self.symbol_rate = 300
			self.lock_rate = 0.75
		elif self.definition == '9600':
			self.symbol_rate = 9600
			self.lock_rate = 0.88
		else:
			self.symbol_rate = 1200
			self.lock_rate = 0.75

		self.tune()

	def retune(self, **kwargs):
		self.symbol_rate = kwargs.get('symbol_rate', self.symbol_rate)
		self.lock_rate = kwargs.get('lock_rate', self.lock_rate)
		self.sample_rate = kwargs.get('sample_rate', self.sample_rate)
		self.tune()

	def StringOptionsRetune(self, options):
		self.symbol_rate = options.get('symbol_rate', self.symbol_rate)
		self.sample_rate = options.get('sample_rate', self.sample_rate)
		self.lock_rate = float(options.get('lock_rate', self.lock_rate))
		self.tune()

	def tune(self):
		self.phase_clock = 0.0
		self.samples_per_symbol = self.sample_rate / self.symbol_rate
		self.rollover_threshold = (self.samples_per_symbol / 2.0) - 0.5
		self.working_byte = 0
		self.working_bit_count = 0
		self.last_sample = 0.0
		self.streamaddress = 0


	def slice(self, samples):
		# This method will attempt to resynchronize a 2-level symbol stream,
		# make binary bit decisions at resynchronized symbol centers, and store the
		# resulting bitstream packed into an int array.
		#
		# phase_clock will be incremented every sample, by 1.0
		# when phase_clock meets or exceeds rollover_threshold:
		#    - evaluate the bit (this should be midpoint of the bit)
		#    - subtract samples_per_symbol from phase_clock
		# sample stream zero-crossings should happen when phase_clock = 0, if
		# it is synchronized. When zero-crossing is detected in sample stream,
		# multiply phase_clock by lock_rate (positive number less than 1.0)
		# this causes phase_clock to converge to synchronization
		result = []
		result_index = 0
		for sample in samples:
			self.streamaddress += 1
			# increment phase_clock
			self.phase_clock += 1.0
			# check for symbol center
			if self.phase_clock >= self.rollover_threshold:
				# at or past symbol center, reset phase_clock
				self.phase_clock -= self.samples_per_symbol
				# shift and bound the working byte
				self.working_byte = (self.working_byte << 1) & 0xFF
				# make a bit decision
				if sample >= 0:
					# this is a '1' bit
					self.working_byte |= 1
				else:
					# this is a '0' bit
					self.working_byte &= 0xFE
				# save this bit into the lsb of the working_byte
				self.working_bit_count += 1
				# after 8 bits, save this byte in the result array and reset bit
				# count
				if self.working_bit_count >= 8:
					self.working_bit_count = 0
					result.append(AddressedData(self.working_byte, self.streamaddress))
			# check for zero-crossing in sample stream
			if (
					(self.last_sample < 0.0 and sample >= 0.0)
					or (self.last_sample >= 0.0 and sample < 0.0)
				):
				# zero crossing detected, adjust phase_clock
				self.phase_clock = self.phase_clock * self.lock_rate
			# save this sample to compare with the next for zero-crossing detect
			self.last_sample = sample
		return result

class QuadratureSlicer:

	def __init__(self, **kwargs):
		self.sample_rate = kwargs.get('sample_rate', '8000')
		self.definition = kwargs.get('config', '600')

		# lock_rate should be between 0 and 1.0
		# Lower numbers cause slicer to sync the bitstream faster,
		# but increase jitter. Higher values are more stable,
		# but sync the bitstream more slowly. Typically 0.65-0.95.

		if self.definition == '600':
			self.symbol_rate = 300
			self.lock_rate = 0.9
		elif self.definition == '2400':
			self.symbol_rate = 1200
			self.lock_rate = 0.9
		elif self.definition == '4800':
			self.symbol_rate = 2400
			self.lock_rate = 0.99
		elif self.definition == '3600':
			self.symbol_rate = 1800
			self.lock_rate = 0.99
		else:
			self.symbol_rate = 1200
			self.lock_rate = 0.9

		self.demap = [3,2,1,0,1,3,0,2,2,0,3,1,0,1,2,3]

		self.tune()

	def retune(self, **kwargs):
		self.symbol_rate = kwargs.get('symbol_rate', self.symbol_rate)
		self.lock_rate = kwargs.get('lock_rate', self.lock_rate)
		self.sample_rate = kwargs.get('sample_rate', self.sample_rate)
		self.tune()

	def StringOptionsRetune(self, options):
		self.symbol_rate = options.get('symbol_rate', self.symbol_rate)
		self.sample_rate = options.get('sample_rate', self.sample_rate)
		self.lock_rate = float(options.get('lock_rate', self.lock_rate))
		self.tune()

	def tune(self):
		self.phase_clock = 0.0
		self.samples_per_symbol = self.sample_rate / self.symbol_rate
		self.rollover_threshold = (self.samples_per_symbol / 2.0) - 0.5
		self.working_byte = 0
		self.working_bit_count = 0
		self.last_i_sample = 0.0
		self.last_q_sample = 0.0
		self.streamaddress = 0
		self.state_register = 0

	def slice(self, iq_samples):
		result = []
		i_samples = []
		q_samples = []
		result_index = 0
		for i_sample, q_sample in zip(iq_samples.i_data, iq_samples.q_data):
			self.streamaddress += 1
			# increment phase_clock
			self.phase_clock += 1.0
			# check for symbol center
			if self.phase_clock >= self.rollover_threshold:
				i_samples.append(i_sample)
				q_samples.append(q_sample)
				# at or past symbol center, reset phase_clock
				self.phase_clock -= self.samples_per_symbol
				# make a bit decision
				self.state_register = (self.state_register << 2) & 0xF
				if i_sample >= 0:
					self.state_register |= 2
				if q_sample >= 0:
					self.state_register |= 1
				# shift the working byte
				self.working_byte = self.working_byte << 2
				self.working_byte |= self.demap[self.state_register]
				# save this bit into the lsb of the working_byte
				self.working_bit_count += 2
				# after 8 bits, save this byte in the result array and reset bit
				# count
				if self.working_bit_count >= 8:
					self.working_bit_count = 0
					self.working_byte &= 0xFF
					result.append(AddressedData(self.working_byte, self.streamaddress))
			# check for zero-crossing in sample stream
			if (
					(self.last_i_sample < 0.0 and i_sample >= 0.0)
					or (self.last_i_sample >= 0.0 and i_sample < 0.0)
				) or (
					(self.last_q_sample < 0.0 and q_sample >= 0.0)
					or (self.last_q_sample >= 0.0 and q_sample < 0.0)

				):
				# zero crossing detected, adjust phase_clock
				self.phase_clock = self.phase_clock * self.lock_rate
			# save this sample to compare with the next for zero-crossing detect
			self.last_i_sample = i_sample
			self.last_q_sample = q_sample
		plot.figure()
		plot.scatter(i_samples, q_samples,s=1)
		plot.show()
		return result

class FourLevelSlicer:

	def __init__(self, **kwargs):
		self.sample_rate = kwargs.get('sample_rate', '8000')
		self.definition = kwargs.get('config', '4800')

		if self.definition == '4800':
			self.symbol_rate = 4800
			self.lock_rate = 0.99
			self.threshold = 0.5
			
		self.symbol_map = [1, 3, -1, -3]

		self.tune()

	def retune(self, **kwargs):
		self.symbol_rate = kwargs.get('symbol_rate', self.symbol_rate)
		self.lock_rate = kwargs.get('lock_rate', self.lock_rate)
		self.sample_rate = kwargs.get('sample_rate', self.sample_rate)
		self.tune()

	def StringOptionsRetune(self, options):
		self.symbol_rate = options.get('symbol_rate', self.symbol_rate)
		self.sample_rate = options.get('sample_rate', self.sample_rate)
		self.lock_rate = float(options.get('lock_rate', self.lock_rate))
		self.tune()

	def tune(self):
		self.phase_clock = 0.0
		self.samples_per_symbol = self.sample_rate / self.symbol_rate
		self.rollover_threshold = (self.samples_per_symbol / 2.0) - 0.5
		self.working_byte = 0
		self.working_bit_count = 0
		self.last_sample = 0.0
		self.streamaddress = 0
		self.state_register = 0
		# create the symbol demap
		self.demap = [0,0,0,0]
		for index in range(4):
			value_number = 0
			if self.symbol_map[index] == -3:
				value_number = 0
			if self.symbol_map[index] == -1:
				value_number = 1
			if self.symbol_map[index] == 1:
				value_number = 2
			if self.symbol_map[index] == 3:
				value_number = 3
			self.demap[index] = value_number
		print("demap: ", self.demap)

	def slice(self, samples):
		# This method will attempt to resynchronize a 4-level symbol stream,
		# make symbol decisions at resynchronized symbol centers, and store the
		# resulting bitstream packed into an int array.
		#
		# phase_clock will be incremented every sample, by 1.0
		# when phase_clock meets or exceeds rollover_threshold:
		#    - evaluate the symbol (this should be midpoint of the symbol)
		#    - subtract samples_per_symbol from phase_clock
		# sample stream zero-crossings should happen when phase_clock = 0, if
		# it is synchronized. When zero-crossing is detected in sample stream,
		# multiply phase_clock by lock_rate (positive number less than 1.0)
		# this causes phase_clock to converge to synchronization
		result = []
		result_index = 0
		save_samples = []
		save_zeros = []
		for sample in samples:
			self.streamaddress += 1
			# increment phase_clock
			self.phase_clock += 1.0
			# check for symbol center
			if self.phase_clock >= self.rollover_threshold:
				# at or past symbol center, reset phase_clock
				self.phase_clock -= self.samples_per_symbol
				# shift and bound the working byte
				self.working_byte = (self.working_byte << 2) & 0xFF
				# This will determine the symbol value, from 0 at the lowest, to 3 at the highest.
				save_samples.append(sample)
				save_zeros.append(0)
				if sample > 0:
					if sample >= self.threshold:
						symbol = 3
					else:
						symbol = 2
				else:
					if sample <= -self.threshold:
						symbol = 0
					else:
						symbol = 1
				self.working_byte += self.demap[symbol]
				# save this bit into the lsb of the working_byte
				self.working_bit_count += 2
				# after 8 bits, save this byte in the result array and reset bit
				# count
				if self.working_bit_count >= 8:
					self.working_bit_count = 0
					result.append(AddressedData(self.working_byte, self.streamaddress))
			# check for zero-crossing in sample stream
			if (
					(self.last_sample < 0.0 and sample >= 0.0)
					or (self.last_sample >= 0.0 and sample < 0.0)
				):
				# zero crossing detected, adjust phase_clock
				self.phase_clock = self.phase_clock * self.lock_rate
			# save this sample to compare with the next for zero-crossing detect
			self.last_sample = sample
		#plot.figure()
		#plot.scatter(save_samples, save_zeros, s=1)
		#plot.show()
		return result