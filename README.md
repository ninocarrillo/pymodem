# pymodem
Simple packet radio demodulators (and maybe modulators) written in Python. Intended to help people better understand the signal processing used in packet radio.

Only an AFSK AX.25 demodulator is implemented now. Plans include PSK, IL2P+CRC, and transmit waveform generators. 

A sample audio file is included that contains 50 short AFSK 1200 bps packets encoded in AX.25 format, with additive white gaussian noise at progressively increasing amplitude.

## Requirements:
- Python3
- NumPy
- SciPy

## Usage
```
python3 afsk1200.py afsk_1200_noise.wav
```
