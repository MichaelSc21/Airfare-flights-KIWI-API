# %%|
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import sys
from scipy.optimize import curve_fit, leastsq
# %%

def create_df(filename):
    df= pd.read_json(filename)
    return df

def filter_data(df):    
    mean = df['price'].mean()
    std = df['price'].std()
    lower_range = mean - 2*std
    upper_range = mean + 2*std
    mask = (df['price'] >= lower_range) & (df['price'] <= upper_range)

    df['price'] = df['price'][mask]
    df['duration'] = df['duration'][mask]

    df['departure'] = pd.to_datetime(df['departure'].str[:10])

    df.index = df['departure']
    return df
    
def sort_by_date(df):
    df2 = pd.DataFrame(index=df.index.unique(), columns=['price'])

    for i in df.index.unique():
        df2.loc[i] = df.loc[i, 'price'].quantile(q=0.25)
    return df2



# %% 
def hist(df, bin):

    x = df['price']
    fig, ax = plt.subplots(figsize = (12, 6))
    ax.legend(['The price density of flights from BHX to IAS'])
    ax.set_xlabel('price')
    ax.set_ylabel('density')
    ax.set_xticks(np.arange(0, np.max(x)+1, 100))
    ax.hist(x, bins=bin)

def model(x, a, b):
    return a *  np.sin(x) + b


def plot(df):
    y = df['price']
    x = df.index
    x_line= (x - pd.Timestamp("01/01/1970")) // pd.Timedelta('1s')
    popt, pcov = curve_fit(model, x_line, y)
    y_line = model(x_line, *popt)
    print(popt)

    fig, ax = plt.subplots(figsize = (12, 6))
    ax.set_ylabel('Price in GBP')
    #ax.set_yticks(np.arange(0, np.max(y)+1, 100))
    ax.set_xlabel('departure')

    ax.plot(x, y_line, color = 'red')
    ax.scatter(x, y, marker ='.')


def fit_sin(df2):
    y = df2['price']
    x = df2.index

    x_line= (x - pd.Timestamp("01/01/1970")) // pd.Timedelta('1s')

    # Finding the amplitude 
    amp = abs(np.fft.fft(y))
    print(len(amp))
    # Finding the frequency
    freq = np.fft.fftfreq(len(x_line), (x_line[1]-x_line[0]))
    print(len(freq))
    guess_amp = np.std(y) * 2**0.5
    guess_freq = abs(freq[np.argmax(amp[1:])+1])
    print(guess_freq)
    phase = 0
    guess_offset = np.mean(y)
    guess = [guess_amp, 2*np.pi*guess_freq, phase,  guess_offset]
    #print(guess)
    #print(freq)

    def sinfunc(x, a, w, p, c):
        return a * np.sin(x*w+p) + c

    def combine_funcs(x_line, y, a, w, p, c):
        total = np.zeros(shape=len(x_line))
        print(total)
        highest_amps = np.empty(len(a))
        for i in range(len(a)):
            popt, pcov= curve_fit(sinfunc, x_line, y,  p0 = [a[i], w[i], p, c])
            highest_amps[i] = popt[0]
            #total += sinfunc(x_line, popt[0], popt[1], popt[2], 0)
        
        ind = np.argpartition(highest_amps, -4)[-4:]
        print(ind)


        return total+ c
    
    popt, pcov= curve_fit(sinfunc, x_line, y,  p0 = guess)
    print(popt)

    y_line = sinfunc(x_line, *popt)
    y_line2 = combine_funcs(x_line, y, amp, freq, popt[2], popt[3])

    return x_line, y_line2



# %%
df = create_df('file1.json')
df = filter_data(df)
df2 = sort_by_date(df)


x_line, y_line2 = fit_sin(df2)
# %%
y = df2['price']
x = df2.index
fig, ax = plt.subplots(figsize = (12, 6))
ax.scatter(x, y, color = 'red', marker='.')
ax.plot(x, y_line2/12)




# %%

# %%
