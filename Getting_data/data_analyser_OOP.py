# %%
import sys 
import os

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
from scipy.optimize import curve_fit, leastsq
from mplcursors import cursor
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from importlib import reload
import Getting_data.API_details as API_details
from Getting_data.data_getter_OOP import Data_getter
reload(API_details)

#%matplotlib qt

class big_df():
    def __init__(self, 
                 filename=None, 
                 payload = None, 
                 filter_data_bool = False, 
                 date_start = None, 
                 date_end = None): 
        self.date_start = date_start
        self.date_end = date_end
        if filename == None:
            self.filename = f"{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}_{str(self.date_start).replace('/',  '-')}_to_{str(self.date_end).replace('/',  '-')}.parquet"
            self.filename = os.path.join(sys.path[0],API_details.DIR_DATA_PARQUET, self.filename)
        else:
            self.filename = filename
        self.payload = payload
        self.df = pd.read_parquet(self.filename)

        if filter_data_bool == True:
            self.filter_data()


    # we get rid of all data outside of 2 standard deviations
    # We sort out the dataframe in ascending order
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
        return small_df(big_df =self.df,
                        method = self.method, 
                        quantile =self.quantile, 
                        filename =self.filename, 
                        payload = self.payload)

# For each unique date, we only show a record, based on some criteria
class small_df():
    def __init__(self, big_df, method, quantile, filename, payload):
        self.method = method
        self.df = pd.DataFrame(columns=['departure_date', 'price', 'seats_available'])
        unique_dates = big_df['departure_date'].unique()
        if self.method == 'mean':
            for i in range(len(unique_dates)):
                mean = pd.Series(big_df.loc[unique_dates[i], 'price']).mean()
                idx = big_df.loc[unique_dates[i], 'price'].gt(mean).argmax()-1
                new_row = {
                    'departure_date':unique_dates[i], 
                    'price': pd.Series(big_df.loc[unique_dates[i], 'price'])[idx], 
                    'seats_available': pd.Series(big_df.loc[unique_dates[i], 'seats_available'])[idx]}
                #print(new_row)
                self.df.loc[i] = new_row
        elif self.method == 'min':
            for i in range(len(unique_dates)):
                self.df.loc[i] = pd.Series(big_df.loc[unique_dates[i], 'price']).min()
                new_row = {
                    'departure_date':unique_dates[i], 
                    'price': pd.Series(big_df.loc[unique_dates[i], 'price'])[0], 
                    'seats_available': pd.Series(big_df.loc[unique_dates[i], 'seats_available'])[0]}
                self.df.loc[i] = new_row

        elif self.method == 'quantile':
            if quantile == None:
                raise TypeError("The method selected is quantile which means you also need to pass a value for the quantile")
            else: 
                for i in range(len(unique_dates)):
                    quantile_val = pd.Series(big_df.loc[unique_dates[i], 'price']).quantile(q=quantile, interpolation = 'lower')
                    idx = np.where(quantile_val == big_df.loc[unique_dates[i], 'price'])[0][0]
                    #idx2 = big_df.loc[unique_dates[i], 'price'].eq(quantile_val).argmax()
                    new_row = {
                        'departure_date':unique_dates[i], 
                        'price': quantile_val, 
                        'seats_available': pd.Series(big_df.loc[unique_dates[i], 'seats_available'])[idx]}
                    self.df.loc[i] = new_row
                #self.df.index = self.df['departure_date']
        else:
            raise TypeError("Invalid method selected")
        
        self.df.index = self.df['departure_date']
        self.df = self.df.drop('departure_date', axis=1)
        
        self.big_df = big_df
        self.y = self.df['price']
        self.x = self.df.index
        self.x_line = np.array(self.x.astype(int) / 10**9)
        self.payload = payload
        self.filename = filename
        self.small_df_filename = self.filename[:-5] + '_small_df' + '.json'
        self.file_graph_plotly = os.path.join(API_details.DIR_GRAPH, API_details.FILE_GRAPH_PLOTLY)

    def sinfunc(self,x, a, w, p):
        return a * np.sin(x*w+p)
    
    def est_param_fourier(self):
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

        
        self.x_line_dense = np.linspace(self.x_line.min(), self.x_line.max(), 1*len(self.x_line))
        self.x_dense = pd.to_datetime(self.x_line_dense, unit='s')
        self.y_dense = np.zeros(shape=len(self.x_line_dense))



        self.est_amps = np.empty(len(self.amp))
        self.est_freq = np.empty(len(self.amp))
        self.est_phase = np.empty(len(self.amp))
        for i in self.indices:
            popt, pcov= curve_fit(self.sinfunc, self.x_line, self.y,  p0 = [self.amp[i], self.freq[i], self.phase])
            self.est_amps[i] = popt[0]
            self.est_freq[i] = popt[1]
            self.est_phase[i] = popt[2]
        
        self.est_values = [self.est_amps, self.est_freq, self.est_phase]

    def model_based_on_param_fourier(self,degree):
        self.est_param_fourier()
        ind = np.argpartition(self.est_values[0], -degree)[-degree:]
        for i in ind:
            self.y_dense += self.sinfunc(self.x_line_dense, self.est_values[0][i], self.est_values[1][i],self.est_values[2][i]) 

    def plot_graph_fourier(self, ax= None, a=1, b=0, colour='blue'):
        if ax == None:
            fig, ax = plt.subplots(figzie = (12, 6))
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
        fig.write_html(self.file_graph_plotly)

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
        fig.write_html(self.file_graph_plotly)
        self.fig = fig

    def write_data_to_file_small_df(self):
        self.small_df_filename = self.filename[:-5] + '_small_df' + '.json'
        self.df.to_json(orient='split', path_or_buf=self.small_df_filename)
    
    


    def compare_data_small_df_plotly(self, other_small_df=None):
        
        #self.json_df = pd.read_json(orient='split', path_or_buf=self.small_df_filename)
        mask = self.big_df['date_added'] == pd.to_datetime(date, format="%d/%m/%Y")
        self.other_date_df = small_df(big_df=self.big_df[mask],method=self.method, quantile=0.14, payload = self.payload, filename=self.filename).df  # noqa: E501
        price_change_mask = self.df['price'] - self.other_date_df['price']

        colour_series =[]
        price_change_text = []

        for i in price_change_mask:
            # Nothing will be added to the grpah if the data is unavailable
            if i == 0 or i == np.nan:
                colour_series.append('blue')
                price_change_text.append('No price change')
            elif i> 0: 
                #Price is higher now compared to the last time it was checked
                colour_series.append('red')
                price_change_text.append('Price increased by £'+ str(i))
            elif i < 0:
                #Price is lower now compared to the last time it was checked
                i = -i

                colour_series.append('green')
                price_change_text.append('Price decreased by £'+ str(i))

        customdata = np.stack((self.df['seats_available'], price_change_text), axis=-1)
        hovertemplate = ('Seats available: %{customdata[0]}<br>' + 
            '%{customdata[1]}<br>' + 
            'price: %{y} <br>' + 
            'date: %{x}' + 
            '<extra></extra>')
        trace1 = go.Scatter(x=self.x, y=self.y, mode='markers',name='line')
        data = [trace1]
        layout = go.Layout(title=f"Flights {self.payload['flight_type']} from {self.payload['fly_from']} to {self.payload['fly_to']} for {self.payload['adults']} adults")

        fig = go.Figure(data = data, layout=layout)
        fig.update_traces(customdata=customdata, hovertemplate=hovertemplate)
        fig.update_traces(marker=dict(color=colour_series))
        fig.write_html(self.file_graph_plotly)
        self.fig = fig

    def return_json(self):

        #self.json_file_plotly_graph = json.dumps(self.fig, cls = plotly.utils.PlotlyJSONEncoder
        self.json_file_plotly_graph = self.fig.to_json()
        return self.json_file_plotly_graph



if __name__ == '__main__':
    df_names = ['LTN_to_IAS_round']
    big_dfs = {}
    small_dfs = {}
    payload={  
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'return_from': '08/04/2023',
    'return_to': '23/04/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'round',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit': 1000}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0,parent_dir)
    os.chdir(sys.path[0])
    print(os.getcwd())
    for df_name in df_names:
        getter = Data_getter(payload, 
                        sanitise_data = True, 
                        delete_data = False,
                        dateStart = '01/04/2023',
                        dateEnd = '31/12/2023')
        print(getter.filename)
        big_dfs[df_name] = big_df(filename = getter.filename, 
                                filter_data_bool=True, 
                                payload = payload,
                                dateStart = '01/04/2023',
                                dateEnd = '31/12/2023')
        
        temp_df = big_dfs[df_name].df
        small_dfs[df_name] = big_dfs[df_name].create_small_df(method = 'quantile', quantile =0.14)

        #fig, ax = plt.subplots(figsize = (12, 6))
        df = small_dfs[df_name].df

        small_dfs[df_name].plot_polynomial_plotly(12)
        #small_dfs[df_name].write_data_to_file_small_df()
        #small_dfs[df_name].compare_data_small_df_plotly(date='30/03/2023')

# %%
"""
TO DO as of 2/3/2023:
Sort out the fourier curve fitting


"""
"""
TO DO as of 30/3/2023:
Sort out the function that compares one dataframe from the past and one from the present;
Make sure that they line up on the dates

"""
# %% 
date = '30/03/2023'
print(pd.to_datetime(date, format="%d/%m/%Y"))
print(pd.to_datetime('today'))
# %%
