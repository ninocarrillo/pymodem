# Python3
# Functions for demodulating PSK
# Nino Carrillo
# 9 Apr 2024

from scipy.signal import firwin
from scipy.signal import remez
from math import ceil, sin, pi, atan2
from numpy import convolve, zeros
from modems_codecs.agc import AGC
from modems_codecs.rrc import RRC
from modems_codecs.data_classes import IQData
from modems_codecs.pi_control import PI_control
from modems_codecs.iir import IIR_1
from modems_codecs.nco import NCO
from modems_codecs.hilbert import Hilbert
from modems_codecs.complexmath import ComplexNumber
from modems_codecs.phase_detector import PhaseDetector
from matplotlib import pyplot as plot

class BPSKModem:

	def __init__(self, **kwargs):
		self.definition = kwargs.get('config', '300')
		self.sample_rate = kwargs.get('sample_rate', 8000.0)

		if self.definition == '300':
			# set some default values for 300 bps BPSK:
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1.0	# sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 300.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 1200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 1800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 1.5		# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.rrc_rolloff_rate = 0.6
			self.rrc_span = 6
			self.max_freq_offset = 37.5
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=250.0,
				gain=1.0
			)
			self.FeedbackController = PI_control(
				p= 0.05,
				i= 0.0001,
				i_limit=self.max_freq_offset,
				gain= 7031.0
			)
		elif self.definition == '1200':
			# set some default values for 1200 bps BPSK:
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1.0	# sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 1200.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 2800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 4.80			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.max_freq_offset = 87.5
			self.rrc_rolloff_rate = 0.9
			self.rrc_span = 6
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=150.0,
				gain=1.0
			)
			self.FeedbackController = PI_control(
				p= 0.24,
				i= 0.0003,
				i_limit=self.max_freq_offset,
				gain= 7031.0
			)

		self.oscillator_amplitude = 1.0



		self.tune()

	def retune(self, **kwargs):
		self.symbol_rate = kwargs.get('symbol_rate', self.symbol_rate)
		self.input_bpf_low_cutoff = kwargs.get('input_bpf_low_cutoff', self.input_bpf_low_cutoff)
		self.input_bpf_high_cutoff = kwargs.get('input_bpf_high_cutoff', self.input_bpf_high_cutoff)
		self.input_bpf_span = kwargs.get('input_bpf_span', self.input_bpf_span)
		self.sample_rate = kwargs.get('sample_rate', self.sample_rate)
		self.carrier_freq = kwargs.get('carrier_freq', self.carrier_freq)
		self.tune()

	def StringOptionsRetune(self, options):
		self.symbol_rate = float(options.get('symbol_rate', self.symbol_rate))
		self.input_bpf_low_cutoff = float(options.get('input_bpf_low_cutoff', self.input_bpf_low_cutoff))
		self.input_bpf_high_cutoff = float(options.get('input_bpf_high_cutoff', self.input_bpf_high_cutoff))
		self.input_bpf_span = float(options.get('input_bpf_span', self.input_bpf_span))
		self.sample_rate = float(options.get('sample_rate', self.sample_rate))
		self.carrier_freq = float(options.get('carrier_freq', self.carrier_freq))
		self.tune()

	def tune(self):
		self.input_bpf_tap_count = round(
			self.sample_rate * self.input_bpf_span / self.symbol_rate
		)

		# Use scipy.signal.firwin to generate taps for input bandpass filter.
		# Input bpf is implemented as a Finite Impulse Response filter (FIR).
		self.input_bpf = firwin(
			self.input_bpf_tap_count,
			[ self.input_bpf_low_cutoff, self.input_bpf_high_cutoff ],
			pass_zero='bandpass',
			fs=self.sample_rate,
			scale=True
		)

		# print("Sample Rate: ", self.sample_rate)
		# print("Input BPF Tap Count: ", len(self.input_bpf))
		# print("Input BPF Taps: ")
		# for tap in self.input_bpf:
		# 	print(int(round(tap * 32768,0)), end=', ')
		# print(" ")

		# print("Output LPF Tap Count: ", len(self.output_lpf))
		# print("Output LPF Taps: ")
		# for tap in self.input_bpf:
		# 	print(int(round(tap * 32768,0)), end=', ')
		# print(" ")

		self.AGC = AGC(
			sample_rate = self.sample_rate,
			attack_rate = self.agc_attack_rate,
			sustain_time = self.agc_sustain_time,
			decay_rate = self.agc_decay_rate,
			target_amplitude = self.oscillator_amplitude,
			record_envelope = False
		)

		self.NCO = NCO(
			sample_rate = self.sample_rate,
			amplitude = self.oscillator_amplitude,
			set_frequency = self.carrier_freq,
			wavetable_size = 256
		)
		self.rrc = RRC(
			sample_rate = self.sample_rate,
			symbol_rate = self.symbol_rate,
			symbol_span = self.rrc_span,
			rolloff_rate = self.rrc_rolloff_rate
		)
		self.output_sample_rate = self.sample_rate

	def demod(self, input_audio):
		# Apply the input filter.
		audio = convolve(input_audio, self.input_bpf, 'valid')

		# perform AGC on the audio samples, saving over the original samples
		self.AGC.apply(audio)

		self.loop_output = []
		demod_audio = []
		# This is a costas loop
		for sample in audio:
			self.NCO.update()
			# mix the in phase oscillator output with the input signal
			#i_mixer = sample * self.NCO.sine_output
			i_mixer = sample * self.NCO.ComplexOutput.real
			# The branch low-pass filters might not be needed when using a
			# matched channel filter before slicing, like RRC.
			# mix the quadrature phase oscillator output with the input signal
			#q_mixer = sample * self.NCO.cosine_output
			q_mixer = sample * self.NCO.ComplexOutput.imag
			loop_mixer = i_mixer * q_mixer
			# low pass filter this product
			self.Loop_LPF.update(loop_mixer)
			# use a P-I control feedback arrangement to update the oscillator frequency
			self.NCO.control = self.FeedbackController.update_saturate(self.Loop_LPF.output)
			self.loop_output.append(self.NCO.control)
			demod_audio.append(i_mixer)

		# Apply the output filter:
		#demod_audio = convolve(demod_audio, self.output_lpf, 'valid')
		demod_audio = convolve(demod_audio, self.rrc.taps, 'valid')
		#print(self.rrc)
		# plt.figure()
		# plt.plot(self.loop_output)
		# plt.show()
		return demod_audio

class QPSKModem:

	def __init__(self, **kwargs):
		self.definition = kwargs.get('config', '600')
		self.sample_rate = kwargs.get('sample_rate', 44100.0)

		if self.definition == '600':
			# set some default values for 300 bps BPSK:
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1.0	# sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 300.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 1200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 1800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 1.5			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.output_lpf_cutoff = 200.0		# low pass filter cutoff frequency for
											# output signal after I/Q demodulation
			self.output_lpf_span = 1.5			# Number of symbols to span with the output
			self.rrc_rolloff_rate = 0.6
			self.rrc_span = 6
			self.max_freq_offset = 37.5
			self.Cosine_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=300.0,
				gain=1.0
			)
			self.Sine_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=300.0,
				gain=1.0
			)
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=100.0,
				gain=1.0
			)
			self.FeedbackController = PI_control(
				p= 0.020,
				i= 0.000031,
				i_limit=self.max_freq_offset,
				gain= 858
			)
		elif self.definition == '3600':
			# set some default values for 3600 bps QPSK:
			self.agc_attack_rate = 5000.0		# Normalized to full scale / sec
			self.agc_sustain_time = 0.1 # sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 1800			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 300.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 3000.0	# high cutoff frequency for input filter
			self.input_bpf_span = 5			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.carrier_freq = 1650.0				# carrier tone frequency
			self.output_lpf_cutoff = 900.0		# low pass filter cutoff frequency for
											# output signal after I/Q demodulation
			self.output_lpf_span = 1.5			# Number of symbols to span with the output
			self.max_freq_offset = 50
			self.rrc_rolloff_rate = 0.3
			self.rrc_span = 8
			self.Cosine_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=1450.0,
				gain=1.0
			)
			self.Sine_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=1450.0,
				gain=1.0
			)
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=200.0,
				gain=1.0
			)
			pi_p = 0.15
			pi_i = pi_p /1000
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= 1350.0
			)
		elif self.definition == '2400':
			# set some default values for 2400 bps QPSK:
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1	# sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 1200.0			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 2800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 4.8			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.carrier_freq = 1800.0				# carrier tone frequency
			self.output_lpf_cutoff = 900.0		# low pass filter cutoff frequency for
											# output signal after I/Q demodulation
			self.output_lpf_span = 1.5			# Number of symbols to span with the output
			self.max_freq_offset = 87.5
			self.rrc_rolloff_rate = 0.9
			self.rrc_span = 3
			branch_cutoff = 1200.0
			self.Cosine_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=branch_cutoff,
				gain=1.0
			)
			self.Sine_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=branch_cutoff,
				gain=1.0
			)
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=200.0,
				gain=1.0
			)
			pi_p = .1
			pi_i = pi_p / 500
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= 450.0
			)

		self.oscillator_amplitude = 1.0



		self.tune()

	def retune(self, **kwargs):
		self.symbol_rate = kwargs.get('symbol_rate', self.symbol_rate)
		self.input_bpf_low_cutoff = kwargs.get('input_bpf_low_cutoff', self.input_bpf_low_cutoff)
		self.input_bpf_high_cutoff = kwargs.get('input_bpf_high_cutoff', self.input_bpf_high_cutoff)
		self.input_bpf_span = kwargs.get('input_bpf_span', self.input_bpf_span)
		self.output_lpf_cutoff = kwargs.get('output_lpf_cutoff', self.output_lpf_cutoff)
		self.output_lpf_span = kwargs.get('output_lpf_span', self.output_lpf_span)
		self.sample_rate = kwargs.get('sample_rate', self.sample_rate)
		self.carrier_freq = kwargs.get('carrier_freq', self.carrier_freq)
		self.tune()

	def StringOptionsRetune(self, options):
		self.symbol_rate = float(options.get('symbol_rate', self.symbol_rate))
		self.input_bpf_low_cutoff = float(options.get('input_bpf_low_cutoff', self.input_bpf_low_cutoff))
		self.input_bpf_high_cutoff = float(options.get('input_bpf_high_cutoff', self.input_bpf_high_cutoff))
		self.input_bpf_span = float(options.get('input_bpf_span', self.input_bpf_span))
		self.output_lpf_cutoff = float(options.get('output_lpf_cutoff', self.output_lpf_cutoff))
		self.output_lpf_span = float(options.get('output_lpf_span', self.output_lpf_span))
		self.sample_rate = float(options.get('sample_rate', self.sample_rate))
		self.carrier_freq = float(options.get('carrier_freq', self.carrier_freq))
		self.tune()

	def tune(self):
		self.input_bpf_tap_count = round(
			self.sample_rate * self.input_bpf_span / self.symbol_rate
		)
		self.output_lpf_tap_count = round(
			self.sample_rate * self.output_lpf_span / self.symbol_rate
		)

		# Use scipy.signal.firwin to generate taps for input bandpass filter.
		# Input bpf is implemented as a Finite Impulse Response filter (FIR).
		self.input_bpf = firwin(
			self.input_bpf_tap_count,
			[ self.input_bpf_low_cutoff, self.input_bpf_high_cutoff ],
			pass_zero='bandpass',
			fs=self.sample_rate,
			scale=True
		)

		# print('Input BPF tap count: ', len(self.input_bpf))
		# print('Sample rate: ', self.sample_rate)
		# print('Span: ', self.input_bpf_span)
		# print('Symbol rate: ', self.symbol_rate)
		# for tap in self.input_bpf:
			# print(int(round(tap*32768)), end = ', ')

		# Use scipy.signal.firwin to generate taps for output low pass filter.
		# Output lpf is implemented as a Finite Impulse Response filter (FIR).
		# firwin defaults to hamming window if not specified.
		self.output_lpf = firwin(
			self.output_lpf_tap_count,
			self.output_lpf_cutoff,
			fs=self.sample_rate,
			scale=True
		)
		self.AGC = AGC(
			sample_rate = self.sample_rate,
			attack_rate = self.agc_attack_rate,
			sustain_time = self.agc_sustain_time,
			decay_rate = self.agc_decay_rate,
			target_amplitude = self.oscillator_amplitude,
			record_envelope = False
		)

		self.NCO = NCO(
			sample_rate = self.sample_rate,
			amplitude = self.oscillator_amplitude,
			set_frequency = self.carrier_freq,
			wavetable_size = 256
		)
		self.rrc = RRC(
			sample_rate = self.sample_rate,
			symbol_rate = self.symbol_rate,
			symbol_span = self.rrc_span,
			rolloff_rate = self.rrc_rolloff_rate
		)
		self.output_sample_rate = self.sample_rate

	def demod(self, input_audio):
		# Apply the input filter.
		audio = convolve(input_audio, self.input_bpf, 'valid')

		# perform AGC on the audio samples, saving over the original samples
		self.AGC.apply(audio)

		self.loop_output = zeros(len(audio))
		self.pi_i = zeros(len(audio))
		demod_audio = IQData()
		index = 0
		# This is a costas loop
		for sample in audio:
			self.NCO.update()
			# mix the in phase oscillator output with the input signal
			i_mixer = sample * self.NCO.cosine_output
			# low pass filter this product
			self.Cosine_LPF.update(i_mixer)
			# The branch low-pass filters might not be needed when using a
			# matched channel filter before slicing, like RRC.
			# mix the quadrature phase oscillator output with the input signal
			if self.Cosine_LPF.output >= 0:
				cosine_sgn = 1
			else:
				cosine_sgn = -1
			q_mixer = sample * self.NCO.sine_output
			# low pass filter this product
			self.Sine_LPF.update(q_mixer)
			demod_audio.i_data.append(self.Sine_LPF.output)
			demod_audio.q_data.append(self.Cosine_LPF.output)
			# mix the I and Q products to create the phase detector
			if self.Sine_LPF.output >= 0:
				sine_sgn = 1
			else:
				sine_sgn = -1
			loop_mixer = (self.Cosine_LPF.output * sine_sgn) - (self.Sine_LPF.output * cosine_sgn)
			# low pass filter this product
			self.Loop_LPF.update(loop_mixer)
			# use a P-I control feedback arrangement to update the oscillator frequency
			self.NCO.control = self.FeedbackController.update_saturate(self.Loop_LPF.output)
			self.loop_output[index] = self.NCO.control
			self.pi_i[index] = self.FeedbackController.integral
			index += 1

		# Apply the output filter:
		demod_audio.i_data = convolve(demod_audio.i_data, self.rrc.taps, 'valid')
		demod_audio.q_data = convolve(demod_audio.q_data, self.rrc.taps, 'valid')
		plot.figure()
		plot.plot(self.loop_output)
		plot.plot(self.pi_i)
		plot.show()
		return demod_audio


class MPSKModem:

	def __init__(self, **kwargs):
		self.definition = kwargs.get('config', 'qpsk_3600')
		self.sample_rate = kwargs.get('sample_rate', 44100.0)

		if self.definition == 'qpsk_3600':
			self.constellation_id = 'qpsk'
			# set some default values for 3600 bps QPSK:
			self.agc_attack_rate = 5000.0		# Normalized to full scale / sec
			self.agc_sustain_time = 0.1 # sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 1800			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 300.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 3000.0	# high cutoff frequency for input filter
			self.input_bpf_span = 2.7			# milliseconds spanned by input filter
			self.hilbert_span = 2.7		# milliseconds spanned by hilbert transformer
			self.carrier_freq = 1650.0				# carrier tone frequency
			self.max_freq_offset = 37.5
			self.rrc_rolloff_rate = 0.3
			self.rrc_span = 8
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=350.0,
				gain=1.0
			)
			pi_p = 1
			pi_i = pi_p /1000
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= 0.675
			)
		elif self.definition == "qpsk_600":
			self.constellation_id = 'qpsk'
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1 # sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 300			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 1200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 1800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 2.7			# milliseconds spanned by input filter
			self.hilbert_span = 2.7			# milliseconds spanned by hilbert transformer
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.max_freq_offset = 25
			self.rrc_rolloff_rate = 0.6
			self.rrc_span = 6
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff= 350.0,
				gain=1/8
			)
			pi_p = 0.2731
			pi_i = pi_p /1100
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= (14400/65536)
			)
		elif self.definition == "qpsk_2400":
			self.constellation_id = 'qpsk'
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1 # sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 1200			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 2800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 2.7			# milliseconds spanned by input filter
			self.hilbert_span = 2.7			# milliseconds spanned by hilbert transformer
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.max_freq_offset = 37.5
			self.rrc_rolloff_rate = 0.9
			self.rrc_span = 6
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=350.0,
				gain=1.0
			)
			pi_p = 0.15
			pi_i = pi_p /850
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= 3.5
			)
		elif self.definition == "bpsk_300":
			self.constellation_id = 'bpsk'
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1 # sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 300			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 1200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 1800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 2.7			# milliseconds spanned by input filter
			self.hilbert_span = 2.7			# milliseconds spanned by hilbert transformer
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.max_freq_offset = 50
			self.rrc_rolloff_rate = 0.6
			self.rrc_span = 6
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=250.0,
				gain=1.0
			)
			pi_p = 0.15
			pi_i = pi_p /1000
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= 1.5 * (500)
			)
		elif self.definition == "bpsk_1200":
			self.constellation_id = 'bpsk'
			self.agc_attack_rate = 500.0		# Normalized to full scale / sec
			self.agc_sustain_time = 1 # sec
			self.agc_decay_rate = 50.0			# Normalized to full scale / sec
			self.symbol_rate = 1200			# symbols per second (or baud)
			self.input_bpf_low_cutoff = 200.0	# low cutoff frequency for input filter
			self.input_bpf_high_cutoff = 2800.0	# high cutoff frequency for input filter
			self.input_bpf_span = 4.8			# Number of symbols to span with the input
											# filter. This is used with the sampling
											# rate to determine the tap count.
											# more taps = shaper cutoff, more processing
			self.hilbert_span = 2			# number of symbols to span with hilbert transformer
			self.carrier_freq = 1500.0				# carrier tone frequency
			self.max_freq_offset = 87.5
			self.rrc_rolloff_rate = 0.9
			self.rrc_span = 6
			self.Loop_LPF = IIR_1(
				sample_rate=self.sample_rate,
				filter_type='lpf',
				cutoff=200.0,
				gain=1.0
			)
			pi_p = 0.15
			pi_i = pi_p /1000
			self.FeedbackController = PI_control(
				p= pi_p,
				i= pi_i,
				i_limit=self.max_freq_offset,
				gain= 5
			)

		self.oscillator_amplitude = 1.0
		self.pd_gain = 32
		self.tune()

	def StringOptionsRetune(self, options):
		self.symbol_rate = float(options.get('symbol_rate', self.symbol_rate))
		self.sample_rate = float(options.get('sample_rate', self.sample_rate))
		self.carrier_freq = float(options.get('carrier_freq', self.carrier_freq))
		self.tune()

	def tune(self):
		self.input_bpf_tap_count = round(
			self.sample_rate * self.input_bpf_span / 1000
		)


		self.hilbert_tap_count = round(
			self.sample_rate * self.hilbert_span / 1000
		)

		self.input_bpf = firwin(
			self.input_bpf_tap_count,
			[ self.input_bpf_low_cutoff, self.input_bpf_high_cutoff ],
			pass_zero='bandpass',
			fs=self.sample_rate,
			scale=True
		)

		if self.hilbert_tap_count % 2:
			pass
		else:
			# make hilbert tap count odd
			self.hilbert_tap_count += 1

		self.Hilbert = Hilbert(tap_count=self.hilbert_tap_count)

		print("hilbert tap count: ", self.Hilbert.tap_count)
		print("hilbert delay count: ", self.Hilbert.delay)


		#plot.figure()
		#plot.stem(self.Hilbert.taps)
		#plot.title("Hilbert Filter Taps")
		#plot.show()

		#
		self.AGC = AGC(
			sample_rate = self.sample_rate,
			attack_rate = self.agc_attack_rate,
			sustain_time = self.agc_sustain_time,
			decay_rate = self.agc_decay_rate,
			target_amplitude = self.oscillator_amplitude,
			record_envelope = False
		)

		self.NCO = NCO(
			sample_rate = self.sample_rate,
			amplitude = self.oscillator_amplitude,
			set_frequency = self.carrier_freq,
			wavetable_size = 256
		)
		self.rrc = RRC(
			sample_rate = self.sample_rate,
			symbol_rate = self.symbol_rate,
			symbol_span = self.rrc_span,
			rolloff_rate = self.rrc_rolloff_rate
		)
		self.output_sample_rate = self.sample_rate

	def demod(self, input_audio):

		pd = PhaseDetector(self.constellation_id,64,self.pd_gain)

		# Apply the input filter.
		audio = convolve(input_audio, self.input_bpf, 'valid')

		# perform AGC on the audio samples, saving over the original samples
		self.AGC.apply(audio)
		imag_audio = convolve(audio, self.Hilbert.taps, 'valid')
		real_audio = convolve(audio, self.Hilbert.delay_taps, 'valid')
		real_audio = real_audio[:-self.Hilbert.delay]
		#plot.figure()
		#plot.scatter(real_audio, imag_audio, s=1)
		#plot.show()
		#plot.figure()
		#plot.plot(real_audio)
		#plot.plot(imag_audio)
		#plot.show()
		#print("len real", len(real_audio))
		#print("len imag", len(imag_audio))

		demod_audio = IQData()

		angle = []
		angle_error = []
		control = []
		integral = []

		for real,imag in zip(real_audio, imag_audio):
			sample = ComplexNumber(real,imag)
			self.NCO.update()
			sample.multiply(self.NCO.ComplexOutput)
			# Low pass filter the angle error
			self.Loop_LPF.update(pd.get_angle_error2(sample.imag,sample.real))
			self.NCO.control = self.FeedbackController.update_saturate(self.Loop_LPF.output)
			demod_audio.i_data.append(sample.real)
			demod_audio.q_data.append(sample.imag)

			angle.append(sample.angle)
			angle_error.append(pd.angle_error)
			control.append(self.NCO.control)
			integral.append(self.FeedbackController.integral)

		# Apply the output filter:
		demod_audio.i_data = convolve(demod_audio.i_data, self.rrc.taps, 'valid')
		demod_audio.q_data = convolve(demod_audio.q_data, self.rrc.taps, 'valid')


		# plot.figure()
		# plot.subplot(221)
		# plot.plot(angle)
		# plot.title("Output Phase")
		# plot.subplot(222)
		# plot.plot(angle_error)
		# plot.title("Angle Error")
		# plot.subplot(223)
		# plot.plot(control)
		# plot.title("NCO Control")
		# plot.subplot(224)
		# plot.plot(integral)
		# plot.title("PI Integral")
		# plot.show()
		# plot.figure()
		# plot.plot(demod_audio.i_data)
		# plot.plot(demod_audio.q_data)
		# plot.legend(["I", "Q"])
		# plot.show()
		return demod_audio
