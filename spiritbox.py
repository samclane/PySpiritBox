import io
from rtlsdr import RtlSdr
from scipy import signal
import scipy
import numpy as np
import sounddevice
import itertools as it
import speech_recognition as sr

class SpiritBox:
    def __init__(self):
        self.sdr = RtlSdr()
        self.Fs =  2.4e6
        self.F_offset = 250000
        
        self.sdr.sample_rate = self.Fs
        self.sdr.gain = 'auto'

        self._looping = False
        self._text_buffer = ""

    def get_samples(self, Freq, hold_time_sec):
        # tune device to desired frequency
        Fc = Freq - self.F_offset
        self.sdr.center_freq = Fc

        samples_to_read = (self.Fs * hold_time_sec) // 1024
        return self.sdr.read_samples(samples_to_read * 1024) 

    def filter_samples(self, samples, bandwidth=200000, n_taps=64):
        # from https://witestlab.poly.edu/blog/capture-and-decode-fm-radio/ 
        x1 = np.array(samples).astype("complex64")
        fc1 = np.exp(-1.0j*2.0*np.pi* self.F_offset/self.Fs*np.arange(len(x1))) 
        x2 = x1 * fc1

        # Use Remez algorithm to design filter coefficients
        lpf = signal.remez(n_taps, [0, bandwidth, bandwidth+(self.Fs/2-bandwidth)/4, self.Fs/2], [1,0], Hz=self.Fs)  
        x3 = signal.lfilter(lpf, 1.0, x2)
        dec_rate = int(self.Fs / bandwidth)
        x4 = x3[0::dec_rate]
        Fs_y = self.Fs/dec_rate
        f_bw = bandwidth 
        dec_rate = int(self.Fs / f_bw)  
        x4 = signal.decimate(x2, dec_rate) 
        # Calculate the new sampling rate
        
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
        
        x7 *= 10000 / np.max(np.abs(x7))
        return x7, Fs_audio

    def speech_recognition(self, samples, Fs_audio):
        byte_io = io.BytesIO(bytes())
        scipy.io.wavfile.write(byte_io, int(Fs_audio), samples.astype("int16"))
        result_bytes = byte_io.read()
        audio_data = sr.AudioData(result_bytes, int(Fs_audio), 2)
        r = sr.Recognizer()
        text = r.recognize_sphinx(audio_data)
        if text:
            self._text_buffer += text
            print("You said: {}".format(text))

    def run(self, start_freq, end_freq, step_freq, hold_time_sec):
        self._looping = True
        try:
            for Freq in it.cycle(np.arange(start_freq, end_freq, step_freq)):
                # print(Freq/1e6)

                samples = self.get_samples(Freq, hold_time_sec)
                
                filtered_samples, Fs_audio = self.filter_samples(samples)

                self.speech_recognition(filtered_samples, Fs_audio)
                
                sounddevice.play(filtered_samples.astype("int16"), Fs_audio)

                if not self._looping:
                    break
        finally:
            self.stop()

    def stop(self):
        self._looping = False

    @property
    def looping(self):
        return self._looping

    @property
    def text_buffer(self):
        b = self._text_buffer
        self._text_buffer = ""
        return b

if __name__ == '__main__':
    sb = SpiritBox()
    start_freq = 88e6
    end_freq = 108e6
    step_freq = 0.2e6
    # endless sweep frequencies
    sb.run(start_freq, end_freq, step_freq, 0.1)
