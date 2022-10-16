from rtlsdr import RtlSdr
from scipy import signal
import numpy as np
from scipy.io import wavfile
import sounddevice
import itertools as it

sdr = RtlSdr()
Fs =  2.4e6
F_offset = 250000
sdr.sample_rate = Fs
sdr.gain = 'auto'

def get_samples(Freq, hold_time_sec):
    # tune device to desired frequency
    Fc = Freq - F_offset
    sdr.center_freq = Fc

    samples_to_read = (Fs * hold_time_sec) // 1024
    return sdr.read_samples(samples_to_read * 1024) 

def filter_samples(samples, bandwidth=200000, n_taps=64):
    x1 = np.array(samples).astype("complex64")
    fc1 = np.exp(-1.0j*2.0*np.pi* F_offset/Fs*np.arange(len(x1))) 
    x2 = x1 * fc1

    
    # Use Remez algorithm to design filter coefficients
    lpf = signal.remez(n_taps, [0, bandwidth, bandwidth+(Fs/2-bandwidth)/4, Fs/2], [1,0], Hz=Fs)  
    x3 = signal.lfilter(lpf, 1.0, x2)
    dec_rate = int(Fs / bandwidth)
    x4 = x3[0::dec_rate]
    Fs_y = Fs/dec_rate
    f_bw = 200000 
    dec_rate = int(Fs / f_bw)  
    x4 = signal.decimate(x2, dec_rate) 
    # Calculate the new sampling rate
    # Fs_y = Fs/dec_rate  

    
    y5 = x4[1:] * np.conj(x4[:-1])
    x5 = np.angle(y5)
    
    # The de-emphasis filter
    # Given a signal 'x5' (in a numpy array) with sampling rate Fs_y
    d = Fs_y * 75e-6   # Calculate the # of samples to hit the -3dB point  
    x = np.exp(-1/d)   # Calculate the decay between each sample  
    b = [1-x]          # Create the filter coefficients  
    a = [1,-x]  
    x6 = signal.lfilter(b,a,x5)  
    audio_freq = 48100.0 
    dec_audio = int(Fs_y/audio_freq)  
    Fs_audio = Fs_y / dec_audio
    x7 = signal.decimate(x6, dec_audio) 
    
    # sounddevice.play(x7,Fs_audio) 
    x7 *= 10000 / np.max(np.abs(x7))
    return x7, Fs_audio

def play_samples(Freq, hold_time_sec=1):
    # from https://witestlab.poly.edu/blog/capture-and-decode-fm-radio/ 
    print(Freq/1e6)

    samples = get_samples(Freq, hold_time_sec)

    # print(samples)
    # print(samples.shape)
    # print(np.max(samples))
    #continue
    
    filtered_samples, Fs_audio = filter_samples(samples)
    
    #sounddevice.play(x7,Fs_audio)
    # x7.astype("int16").tofile("wbfm-mono.raw")  #Raw file.
    # wavfile.write('wav.wav',int(Fs_audio), x7.astype("int16"))
    # print('playing...')
    sounddevice.play(filtered_samples.astype("int16"), Fs_audio)


if __name__ == '__main__':
    start_freq = 88e6
    end_freq = 108e6
    step_freq = 0.2e6
    # endless sweep frequencies
    try:
        for freq in it.cycle(np.arange(start_freq, end_freq, step_freq)):
            play_samples(freq, 0.5)
    finally:
        sdr.close()