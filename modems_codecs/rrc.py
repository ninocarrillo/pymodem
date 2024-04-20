# Python3
# Functions for generating RRC FIR taps
# Nino Carrillo
# 19 Apr 2024

import numpy as np
import math

class RRC:
	def __init__(self, **kwargs):
		self.sample_rate = kwargs.get('sample_rate', 8000)
		self.symbol_span = kwargs.get('symbol_span', 5)
		self.symbol_rate = kwargs.get('symbol_rate', 300)
		self.rolloff_rate = kwargs.get('rolloff_rate', 0.3)
		self.window = kwargs.get('window', "tukey")
		self.tune()

	def tune(self):
		self.oversample = self.sample_rate / self.symbol_rate
		self.tap_count = int(round(self.symbol_span * self.oversample, 0)) + 1
		self.time_step = 1 / self.sample_rate
		self.symbol_time = 1 / self.symbol_rate
		self.time = np.arange(0, self.tap_count * self.time_step, self.time_step) - (self.tap_count * self.time_step / 2) + (self.time_step / 2)
		self.taps = []
		i = 0
		try:
			asymptote = self.symbol_time / (4 * self.rolloff_rate)
		except:
			asymptote = False
		for time in self.time:
			if math.isclose(time, -asymptote) or math.isclose(time, asymptote):
				numerator = self.rolloff_rate * ((1 + 2 / np.pi) * np.sin(np.pi/(4 * self.rolloff_rate)) + (1 - (2 / np.pi)) * np.cos(np.pi / (4 * self.rolloff_rate)))
				denominator = self.symbol_time * pow(2, 0.5)
				try:
					self.taps.append(numerator / denominator)
				except:
					self.taps.append(0)
			else:
				numerator = np.sin(np.pi * time * (1 - self.rolloff_rate) / self.symbol_time) + 4 * self.rolloff_rate * time * np.cos(np.pi * time * (1 + self.rolloff_rate) / self.symbol_time) / self.symbol_time
				denominator = np.pi * time * (1 - pow(4 * self.rolloff_rate * time / self.symbol_time, 2)) / self.symbol_time
				try:
					self.taps.append(numerator / (denominator * self.symbol_time))
				except:
					self.taps.append(0)
		self.taps = self.taps / np.linalg.norm(self.taps)
		self.rc = np.convolve(self.taps, self.taps, 'same')

		self.filter_window = []
		N = self.tap_count - 1
		if self.window == 'hann':
			for index in range(self.tap_count):
				self.filter_window.append(np.power(np.sin(np.pi * index / N),2))
		elif self.window == 'rect':
			for index in range(self.tap_count):
				self.filter_window.append(1)
		elif self.window == 'blackmann':
			a0 = 0.355768
			a1 = 0.487396
			a2 = 0.144232
			a3 = 0.012604
			for index in range(self.tap_count):
				self.filter_window.append(a0 - (a1 * np.cos(2 * np.pi * index / N)) + (a2 * np.cos(4 * np.pi * index / N)) - (a3 * np.cos(6 * np.pi * index / N)))
		elif self.window == 'blackmann-harris':
			a0 = 0.35875
			a1 = 0.48829
			a2 = 0.14128
			a3 = 0.01168
			for index in range(self.tap_count):
				self.filter_window.append(a0 - (a1 * np.cos(2 * np.pi * index / N)) + (a2 * np.cos(4 * np.pi * index / N)) - (a3 * np.cos(6 * np.pi * index / N)))
		elif self.window == 'flattop':
			a0 = 0.21557895
			a1 = 0.41663158
			a2 = 0.277263158
			a3 = 0.083578947
			a4 = 0.006947368
			for index in range(self.tap_count):
				self.filter_window.append(a0 - (a1 * np.cos(2 * np.pi * index / N)) + (a2 * np.cos(4 * np.pi * index / N)) - (a3 * np.cos(6 * np.pi * index / N)) + (a4  * np.cos(8 * np.pi * index / N)))
		elif self.window == 'tukey':
			a = 0.25
			index = 0
			while index < a * N / 2:
				self.filter_window.append(0.5 * (1 - np.cos(2 * np.pi * index / (a * N))))
				index += 1
			while index <= N // 2:
				self.filter_window.append(1)
				index += 1
			while index <= N:
				self.filter_window.append(self.filter_window[N - index])
				index += 1

		self.taps = np.multiply(self.taps, self.filter_window)
		self.windowed_rc = np.convolve(self.taps, self.taps, 'same')
		self.windowed_rc = self.windowed_rc * max(self.taps) / max(self.windowed_rc)
