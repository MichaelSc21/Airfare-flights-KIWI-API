# %%
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import sys
from scipy.optimize import curve_fit, leastsq

# %%

class create_big_df(pd.DataFrame):
    def __init__(self, filename): 
        self.filename = filename
        super().__init__(pd.read_json(self.filename))
        print(type(self))

    def filter_data(self):    
        mean = self['price'].mean()
        std = self['price'].std()
        lower_range = mean - 2*std
        upper_range = mean + 2*std
        mask = (self['price'] >= lower_range) & (self['price'] <= upper_range)
        print(len(self['price']))
        self = self.loc[mask]
        print(len(self['price']))

        self['departure'] = pd.to_datetime(self['departure'].str[:10])

        self.index = self['departure']
    
    def create_small_df(self, method, quantile=None, ):
        return create_small_df(self,method, quantile, self.filename)
    
class create_small_df(pd.DataFrame):
    def __init__(self, big_df, method, quantile, filename):
        super().__init__(pd.DataFrame(index=big_df.index.unique(), columns=['price']))
        
        if method == 'mean':
            for i in big_df.index.unique():
                self.loc[i] = pd.Series(big_df.loc[i, 'price']).mean()
        elif method == 'min':
            for i in big_df.index.unique():
                self.loc[i] = pd.Series(big_df.loc[i, 'price']).min()
        elif method == 'quantile':
            if quantile == None:
                raise TypeError("The method selected is quantile which means you also need to pass a value for the quantile")
            else: 
                for i in big_df.index.unique():
                    self.loc[i] = pd.Series(big_df.loc[i, 'price']).quantile(q=quantile)
        else:
            raise TypeError("Invalid method selected")
        
        self.y = self['price']
        self.x = self.index
        self.x_line = np.array(self.x.astype(int) / 10**9)
        # Finding the amplitude of the sin waves
        self.amp = abs(np.fft.fft(self.y))
        #Sorting the indices of the amplitudes in descending order
        self.indices = np.flip(np.argsort(self.amp))
        # Finding the frequency of the sin waves
        self.freq = np.fft.fftfreq(len(self.x_line), (self.x_line[1]-self.x_line[0]))
        self.guess_amp = np.std(self.y) * 2**0.5
        self.guess_freq = abs(self.freq[np.argmax(self.amp[1:])+1])
        self.phase = 0
        self.guess_offset = np.mean(self.y) * 2**0.5
        self.guess = [self.guess_amp, 2*np.pi*self.guess_freq, self.phase,  self.guess_offset]
        self.filename = filename

    def sinfunc(x, a, w, p):
        return a * np.sin(x*w+p)
    
    def est_param(self):
        self.est_amps = np.empty(len(self.amp))
        self.est_freq = np.empty(len(self.amp))
        self.est_phase = np.empty(len(self.amp))
        for i in self.indices:
            popt, pcov= curve_fit(self.sinfunc, self.x_line, self.y,  p0 = [self.amp[i], self.freq[i], self.phase])
            self.est_amps[i] = popt[0]
            self.est_freq[i] = popt[1]
            self.est_phase[i] = popt[2]
        
        self.est_values = [self.est_amps, self.est_freq, self.est_phase]

    def model_based_on_param(self,degree):
        self.x_line_dense = np.linspace(self.x_line.min(), self.x_line.max(), 4*len(self.x_line))
        self.x_dense = pd.to_datetime(self.x_line_dense, unit='s')
        self.y_dense = np.zeros(shape=len(self.x_line_dense))

        ind = np.argpartition(self.est_values[0], -degree)[-degree:]
        for i in ind:
            self.y_dense += self.sinfunc(self.x_line_dense, self.est_values[0][i], self.est_values[1][i],self.est_values[2][i]) 

    def plot_graph_fourier(self, ax, a=1, b=0, colour='blue'):
    
        ax.plot(self.x_line,self.y_line*a+b, label = df_name, color = colour)
        ax.scatter(self.x, self.y, color = colour, marker='.',label = self.filename)
        
        ax.legend(fontsize=12)
        ax.set_title('Price of flights in the bottom 15% for 4 adults')





# %%
df_names = ['BHX_to_IAS','MAN_to_IAS']
dict_df = {}
small_df = {}
for df_name in df_names:
    
    dict_df[df_name] = create_big_df(df_name+'.json')
    print(type(dict_df[df_name]))
    dict_df[df_name].filter_data()
    small_df[df_name] = dict_df[df_name].create_small_df(method = 'quantile', quantile = 0.1)
    small_df[df_name].est_param()
    small_df[df_name].model_based_on_param(8)
    fig, ax = plt.subplots(figsize = (12, 6))
    small_df[df_name].plot_graph_fourrier(ax, a= 0.5, b = 0, colour = 'red')


# %%
