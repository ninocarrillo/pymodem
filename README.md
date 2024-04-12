# pymodem
Pymodem is a packet radio decoding program which can demodulate and decode a variety of packet formats from audio files. This is a work in progress! I plan to add more modems (including QPSK), more report options, the ability to save binary or kiss packet data to an output file, and the ability to save correlated packet audio to inidividual output audio files.

All signal processing blocks in Pymodem are implemented in plain Python code. This is done for ease of understanding as well as ease of modification. Because of this, Pymodem isn't the *fastest* offline packet radio decoder. Faster execution would be possible by porting Pymodem to a compiler-based language and compiling for each platform. However, this approach makes Pymodem easy to modify, analyze, and adapt. 

The operation of Pymodem is specified at runtime by a config file. The config file specifies details about the modems and decoders to be used to process the audio file. It also includes instructions for generating reports after processing is complete. Config files are composed of json objects, stored one-object-per-line in the file.

## Requirements
- Python3
- NumPy
- SciPy

## Modems
- AFSK in 1200 bps and 300 bps formats
- BPSK in 1200 bps and 300 bps formats
- FSK in 9600 and 4800 bps formats

Arbitrary modes can be described for all modems in the configuration .json passed at program start.

## Decoders
- AX.25
- IL2P with CRC

IL2P decoder options can be specified in the configuration .json as well.

## Program Architecture
Pymodem is modular and configurable.

Pymodem reads the configuration file to build any number of signal processing chains. Each line in the config.json file is one json object. Signal processing chains are identified as 'demod_chain' objects, and consist of the following obects in order:
### 'demod_chain' object composition
Every demod chain is arranged the same way, and consists of four blocks in this order:

{'modem', 'slicer', 'stream', 'codec'}
- 'modem' object processes audio samples into a baseband signal
- 'slicer' object processes baseband signal into a bitstream
- 'stream' object manipulates the bitstream with a linear feedback shift register, which can be configured for differential descrambling, unmodified passthrough, or a combination of these processes
- 'codec' object detects and decodes packets from the manipulated bitstream
After all 'demod_chain' objects have been processed, Pymodem correlates the results of each to identify duplicate and unique packets. Uniqueness is determined by the streamaddress, or the sample index of the last input audio sample processed to create the last bit used to generate each decoded packet.
### Omitted blocks in subsequent 'demod_chain' objects
The first line the .json file should be a 'demod_chain' object that defines all four blocks. Subsequent lines may omit any of the leading blocks in the chain. When leading blocks are omitted, the rest of the chain in that line resumes processing with the product from the applicable block in the previous chain. This is demonstrated in configs/fsk_9600_il2pc.json.
## 'report' object
The last line(s) of the config .json should be a 'report' object. This object describes how to dispose of the decoder output. Multiple 'report' objects are allowed.

## Sample Audio
Several sample audio files are included in AX.25, IL2P and IL2P+CRC format. The sample files have additive white gaussian noise at progressively increasing amplitude.

## Usage
```
python3 pymodem.py <config.json> <audio.wav>

```
Example:
```
python3 pymodem.py configs/bpsk_300_il2pc.json audio_samples/bpsk_300_il2pc_noise.wav
```
