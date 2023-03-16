# %%
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import sys
from scipy.optimize import curve_fit, leastsq
from mplcursors import cursor
import plotly.express as px
import plotly.graph_objects as go
%matplotlib qt

class big_df():
    def __init__(self, filename, filter_data_bool = False): 
        self.filename = filename
        self.df = pd.read_json(self.filename)

        if filter_data_bool == True:
            self.filter_data()



    def filter_data(self):    
        mean = self.df['price'].mean()
        std = self.df['price'].std()
        lower_range = mean - 2*std
        upper_range = mean + 2*std
        mask = (self.df['price'] >= lower_range) & (self.df['price'] <= upper_range)
        print(len(self.df['price']))
        self.df = self.df.loc[mask]
        print(len(self.df['price']))

        self.df['departure_date'] = pd.to_datetime(self.df['departure_date'].str[:10])
        self.df = self.df.sort_values(by=['departure_date', 'price'])

        self.df.index = self.df['departure_date']
    
    def create_small_df(self, method, quantile=None, ):
        self.method = method
        self.quantile = quantile
        return small_df(self.df,self.method, self.quantile, self.filename)
    
class small_df():
    def __init__(self, big_df, method, quantile, filename):
        self.df = pd.DataFrame(columns=['departure_date', 'price', 'seats_available'])
        unique_dates = big_df['departure_date'].unique()
        if method == 'mean':
            for i in big_df['departure_date'].unique():
                self.df.loc[i] = pd.Series(big_df.loc[i, 'price']).mean()
        elif method == 'min':
            for i in big_df['departure_date'].unique():
                self.df.loc[i] = pd.Series(big_df.loc[i, 'price']).min()
        elif method == 'quantile':
            if quantile == None:
                raise TypeError("The method selected is quantile which means you also need to pass a value for the quantile")
            else: 
                for i in range(len(unique_dates)):
                    quantile_val = pd.Series(big_df.loc[unique_dates[i], 'price']).quantile(q=quantile, interpolation = 'lower')
                    idx = np.where(quantile_val == big_df.loc[unique_dates[i], 'price'])[0][0]
                    new_row = {'departure_date':unique_dates[i], 'price': quantile_val, 'seats_available': big_df.loc[unique_dates[i], 'seats_available'][idx]}
                    self.df.loc[i] = new_row
                self.df.index = self.df['departure_date']
        else:
            raise TypeError("Invalid method selected")
        
        self.big_df = big_df
        self.y = self.df['price']
        self.x = self.df.index
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
        
        self.x_line_dense = np.linspace(self.x_line.min(), self.x_line.max(), 1*len(self.x_line))
        self.x_dense = pd.to_datetime(self.x_line_dense, unit='s')
        self.y_dense = np.zeros(shape=len(self.x_line_dense))


    def sinfunc(self,x, a, w, p):
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
        
        ind = np.argpartition(self.est_values[0], -degree)[-degree:]
        for i in ind:
            self.y_dense += self.sinfunc(self.x_line_dense, self.est_values[0][i], self.est_values[1][i],self.est_values[2][i]) 

    def plot_graph_fourier(self, ax, a=1, b=0, colour='blue'):
        ax.plot(self.x_dense,self.y_dense*a+b, label = df_name, color = colour)
        ax.scatter(self.x, self.y, color = colour, marker='.',label = self.filename)
        ax.legend(fontsize=12)
        ax.set_title('Price of flights in the bottom 15% for 4 adults')
        

    def plot_polynomial(self,degree,  ax, colour):
        if ax== None:
            fig, ax = plt.subplots(figsize = (12, 6))
        y = self.y.astype(int)
        p= np.polyfit(self.x_line, y, degree)
        self.y_line = np.polyval(p,self.x_line_dense)
        ax.plot(self.x_dense, self.y_line, label=self.filename, color=colour)

        ax.set_ylabel('Price in GBP')
        #ax.set_yticks(np.arange(0, np.max(y)+1, 100))
        ax.set_xlabel('Date')
        ax.set_title('The price of a Oneway flight on each of the day of the year for 4 adults( adult > 12y/o)')
        ax.scatter(self.x, self.y, marker ='.', color=colour, label=self.filename)
        ax.legend(fontsize=12)
        plt.savefig('test3.svg')
        
    # This is still a work in progress
    def add_dfs(self, instance, offset = 0):
        # Aligining the 2 dataframes together
        #sorting the beginning of the np array
        for i in range(len(self.x)):
            if self.x[i] == instance.x[0]:
                print(i)
                break
        #sorting the end of the np array
        for j in range(len(self.x), 0, -1):
            if self.x[j] == instance.x[len(instance.x)-offset-1]:
                break

        y2=instance.y
        new_x = self.x[i:j]
        new_y = self.y[i:j]
        y2 = y2[i:j]


        
        x_dense2 = instance.x_dense
        for i in range(len(y2)):
            y2[i+offset] = y2[i+offset] + self.y[i]

    
    # Plotting a graph with plotly rather than matplotlib since I want to create interactive graphs which can be shown on the internet. Matplotlib doesn't have that functionality
    def plot_graph_plotly(self):
        customdata = np.stack((self.df['seats_available']), axis=-1)

        hovertemplate = ('Seats available: %{customdata}<br>' + 
            'price: %{y} <br>' + 
            'date: %{x}' + 
            '<extra></extra>')
        fig = px.scatter(self.df, x=self.x, y=self.y)
        
        fig.update_traces(customdata=customdata, hovertemplate=hovertemplate)
        fig.write_html('D:\COding\Python\Python web scraping\Flight tickets\Airfare-flights KIWI API\Graphs\Plotly graphs\Test1 Interactive plot.html')

    def plot_polynomial_plotly(self, degree):
        customdata = np.stack((self.df['seats_available']), axis=-1)
        hovertemplate = ('Seats available: %{customdata}<br>' + 
            'price: %{y} <br>' + 
            'date: %{x}' + 
            '<extra></extra>')
        self.y = self.y.astype(int)
        p= np.polyfit(self.x_line, self.y, degree)
        self.y_line = np.polyval(p,self.x_line)

        trace1 = go.Scatter(x=self.x, y=self.y, mode='markers', name='line')
        trace2 = go.Scatter(x=self.x, y=self.y_line, mode='lines', name='scatter')
        data = [trace1, trace2]
        layout = go.Layout(title='Flights oneway from OPO to BHX for 4 adults ')

        fig = go.Figure(data = data, layout=layout)

        fig.update_traces(customdata=customdata, hovertemplate=hovertemplate)
        fig.write_html('D:\COding\Python\Python web scraping\Flight tickets\Airfare-flights KIWI API\Graphs\Plotly graphs\Test1 Interactive plot.html')

# %%
if __name__ == '__main__':
    df_names = ['OPO_to_BHX_oneway']
    big_dfs = {}
    small_dfs = {}
    for df_name in df_names:
        
        big_dfs[df_name] = big_df(filename = df_name+'.json', filter_data_bool=True)

        temp_df = big_dfs[df_name].df
        small_dfs[df_name] = big_dfs[df_name].create_small_df(method = 'quantile', quantile = 0.15)
        #fig, ax = plt.subplots(figsize = (12, 6))
        df = small_dfs[df_name].df

        small_dfs[df_name].plot_polynomial_plotly(12)


# %%
"""
TO DO as of 2/3/2023:
Sort out the fourier curve fitting


"""


