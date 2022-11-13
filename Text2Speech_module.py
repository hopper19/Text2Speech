from os.path import splitext
import gc
import math
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import scipy.signal
from IPython.display import Audio, display
import re
import random
import os
import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
import glob
import datetime

def getAvailableWords(voiceLib):
    availableWords = []
    for file in os.listdir(voiceLib):
        if file.endswith(".wav"):
            availableWords.append(os.path.splitext(file)[0])
    return availableWords

def recordWord(voiceLib, word):
    fs = 48000  # Sample rate
    seconds = 3  # Duration of recording

    print("Please say the word: ", word)
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    write(voiceLib+'/'+word+'.wav', fs, myrecording)  # Save as WAV file 
    
def recordSentence():
    fs = 48000  # Sample rate
    seconds = 7  # Duration of recording

    print("Please say the sentence...")
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    filename = 'sentence-{date:%Y-%m-%d_%H%M%S}.wav'.format(date=datetime.datetime.now())
    write(filename, fs, myrecording)  # Save as WAV file 
    print("Thank you!")
    return filename
    
    
def playAvailableWords(voiceLib):
    root = voiceLib+'/'
    for file in os.listdir(voiceLib):
        if file.endswith(".wav"):
            # Extract data and sampling rate from file
            data, fs = sf.read(root+file, dtype='float32')  
            sd.play(data, fs)
            status = sd.wait()  # Wait until file is done playing
            
def play(x, fs, autoplay=False):
    ''' Output an audio player that allows participants to listen to their wav files '''
    display(Audio(x, rate=fs, autoplay=autoplay))
    
def norm(wav):
    ''' Normalization function '''
    return wav/np.max(np.abs(wav))

def dco(wav):
    ''' Remove DC offset and normalize the signal '''
    return norm(wav - np.mean(wav))

def extract(wav, t1, t2, fs):
    ''' Extract a portion of the input signal from t1 to t2 '''
    if isinstance(t1, str) and t1 == 'start':
        cut = wav[:math.floor(t2*fs)]
    elif isinstance(t2, str) and t2 == 'end':
            cut = wav[math.floor(t1*fs):]
    else:
        cut = wav[math.floor(t1*fs):math.floor(t2*fs)]
    tcut = np.arange(len(cut))*(1./fs)
    return cut, tcut

def crosscorrelate(signal, template, fs):
    '''Cross-correlate the template against the signal'''
    Rxy = scipy.signal.correlate(signal, template, mode='valid')
    t = np.arange(len(Rxy))*(1./fs)
    return Rxy, t

def plot_signal(time_vec,x_0,xlim=None,title=None):
    ''' Plot the signal in the time domain'''

    # This code add the very low level of white noise to the input
    # so that the specgram will continue display on zero input values

    minval = 1e-16
    x_1 = x_0

    for i in range(len(x_1)):
      # the random value must be greater than zero!
      v = x_1[i]
      if (v < 0) and (v > -minval):
        r = 1.0 - random.random() 
        x_1[i] = -minval * r
      elif (v >= 0) and (v < minval):
        r = 1.0 - random.random() 
        x_1[i] = minval * r
    
    fig = plt.figure(figsize=(15,12))
    ax = fig.add_subplot(2,1,1)
    ax.plot(time_vec,x_0)
    ax.set_xticklabels([])
    ax.set_ylabel('x(t)')
    ax.set_xlim(xlim)
    ax.set_title(title)

    ax = fig.add_subplot(2,1,2)
    samplerate = 1./(time_vec[1]-time_vec[0])
    # display the noise-added spectrum data instead of the given data
    ax.specgram(x_1,Fs=samplerate)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Hz')
    ax.set_xlim(xlim)
    #ax.set_ylim(0,5000)

    fig.tight_layout()
    plt.show()
    plt.close(fig)
    
    gc.collect()

def plot_correlation(tau, Rxy, title = None, return_figure=False):
    '''Plot cross-correlation values Rxy at time points tau.'''
    fig = plt.figure(figsize=(15,6))
    
    ax = fig.add_subplot(1,1,1)
    ax.plot(tau, Rxy)
    ax.set_xlabel('Tau [s]')
    ax.set_ylabel('$R_{XY}$')
    ax.set_title(title)
    
    plt.show()
    plt.close(fig)
    
    if return_figure:
        return fig
    
    gc.collect()

def plot_correlation_interactive(tau, Rxy, title = None):
    '''Plot cross-correlation interactively and highlight peaks.'''
    
    sample_rate = len(tau)/(tau[-1] - tau[0]) # assuming equally-spaced samples
    
    # require peaks that at at least .01 seconds apart (assuming sample rate is in seconds)
    indices = scipy.signal.find_peaks(Rxy, prominence=(np.max(Rxy)/4), distance=.01 * sample_rate)[0]
    R_peaks = [Rxy[i] for i in indices]
    t_peaks = [tau[i] for i in indices]
    print(f'Peaks found at {t_peaks}')
    
    fig = go.FigureWidget([go.Scatter(x=tau, y=Rxy, mode='lines'),
                          go.Scatter(x=t_peaks,
                                     y=R_peaks,
                                    mode='markers',
                                    marker=dict(size=8,color='red',symbol='cross'))])
    fig.layout.title = title
    fig.show()
    
    return R_peaks, t_peaks

def find_timing_of(template, signal, fs):
    '''Find the timing of the given test signal (template) in the given signal recording'''
    Rxy, tau = crosscorrelate(signal, template, fs)
    plot_correlation(tau, Rxy, 'cross-correlation plot generated by find')
    return np.where(np.abs(Rxy) == np.max(np.abs(Rxy)) )[0][0] * (1./fs)

# Allowed filename formats for submission to this festival
formats = [
    {
        "name": 'kristina',
        "human": "CALLSIGN_STATION_BAND_YYYY-MM-DD_HH-MM_(iq|am).wav",
        "re": r"(?P<callsign>[^_]+)_(?P<station>[^_]+)_(?P<band>[^_]+)_(?P<timestamp>\d{4}-\d{2}-\d{2}_\d{2}-\d{2})_(?P<type>am|iq).wav"
    },
    {
        "name": "N6GN",
        "human": "CALLSIGN_YYYYMMDDTHHMMSS_(iq|am)_BAND.wav",
        "re": r"(?P<callsign>[^_\n]+)_(?P<timestamp>\d{4}\d{2}\d{2}T\d{2}\d{2}\d{2})_(?P<type>am|iq)_(?P<band>[0-9]+).wav"
    },
    {
        "name": "W2NAF",
        "human": "CALLSIGN_YYYY-MM-DDTHH_MM_SSZ_FREQUENCY_iq.wav",
        "re": r"(?P<callsign>[^_\n]+)_(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}Z)_(?P<band>[\d.]+)_(?P<type>am|iq).wav"
    },
    {
        "name": 'jj1bdx',
        "human": "CALLSIGN_STATION_BAND_YYYY-MM-DD_HH-MM.wav",
        "re": r"(?P<callsign>[^_]+)_(?P<station>[^_]+)_(?P<band>[^_]+)_(?P<timestamp>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}).wav"
    }
]

def parse(filename: str):
    """Parse a filename for the sunrise festival and return a dictionary of the info therein"""
    found_matches = 0
    
    for fmt in formats:
        match = re.match(fmt['re'], filename)
                      
        if match is not None:
            print(f'filename matched format {fmt["name"]}')
            found_matches += 1
            temp = match.groupdict()
            
    if found_matches != 1:
        raise Exception('more than one match')
    
    return temp