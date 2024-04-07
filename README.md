# pymodem
Simple packet radio demodulators (and some day maybe modulators) written in Python. Intended to help people better understand some signal processing methods used in dsp-based packet radio.

Currently working:
- AFSK demodulator
- AX.25 decoder
- IL2P+CRC decoder

IL2P+CRC decoder is working but I have not fully tested and validated it for all header types and packet lengths yet. If you do, please give feedback!

I plan to add PSK, and transmit waveform generators.

Several sample audio files are included in AX.25, IL2P and IL2P+CRC format. The sample files have additive white gaussian noise at progressively increasing amplitude.

## Requirements:
- Python3
- NumPy
- SciPy

## Usage
```
python3 afsk300il2pc.py afsk_300_il2pc_noise.wav
python3 afsk300ax25.py afsk_300_ax25_noise.wav
python3 afsk1200ax25.py afsk_1200_ax25_noise.wav
python3 afsk1200il2p.py afsk_1200_il2p_noise.wav

```
