# slicer
# Python3
# Functions for bit-slicing a sample stream
# Nino Carrillo
# 30 Mar 2024

from data_classes import AddressedData

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
		else:
			self.symbol_rate = 1200
			self.lock_rate = 0.75

		self.tune()

	def tune(self):
		self.phase_clock = 0.0
		self.samples_per_symbol = self.sample_rate / self.symbol_rate
		self.rollover_threshold = self.samples_per_symbol / 2.0
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
