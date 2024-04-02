# pymodem
Simple packet radio demodulators (and some day maybe modulators) written in Python. Intended to help people better understand some signal processing methods used in dsp-based packet radio.

Only an AFSK AX.25 demodulator is implemented now. I plan to add PSK, IL2P+CRC, and transmit waveform generators.

A sample audio file is included that contains 50 short AFSK 1200 bps packets encoded in AX.25 format, with additive white gaussian noise at progressively increasing amplitude.

afsk1200.py can be used to decode any wav file containing AFSK 1200 AX.25 samples. The sample rate will be automatically detected from the wav file.

## Requirements:
- Python3
- NumPy
- SciPy

## Usage
```
python3 afsk1200.py afsk_1200_ax25_noise.wav
```
