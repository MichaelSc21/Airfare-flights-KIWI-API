# %%
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
from scipy.optimize import curve_fit, leastsq
from mplcursors import cursor
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import sqlite3

from importlib import reload

import Getting_data.API_details as API_details
#from Getting_data.data_getter_OOP import Data_getter
reload(API_details)

#%matplotlib qt

class small_df:
    # Specific filename can be passed in if needed
    # big_df is created in the __init__
    def __init__(self, 
                 filename=None, 
                 payload = None, 
                 filter_data_bool = False,  
                 date_start = None, 
                 date_end = None,
                 date_id = None,
                 absolute_path_with_filename=None,
                 other_df_instance = False): 
        self.payload = payload
        self.date_start = date_start
        self.date_end = date_end
        if filename == None:
            self.filename = f"{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}_{str(self.date_start).replace('/',  '-')}_to_{str(self.date_end).replace('/',  '-')}.parquet"
            #self.filename = os.path.join(sys.path[0],API_details.DIR_DATA_PARQUET, self.filename)
        else:
            self.filename = filename
        #self.filename = os.path.join(sys.path[0],API_details.DIR_DATA_PARQUET, self.filename)
  
        self.date_id = date_id
        if absolute_path_with_filename == None:
            self.absolute_path_with_filename = self.create_absolute_path_with_filename(self.date_id, self.filename)
            
            print(self.absolute_path_with_filename)
            print(len(self.absolute_path_with_filename))
            print("\n\n\n\n\n")
        else:
            self.absolute_path_with_filename = absolute_path_with_filename
        self.big_df = pd.read_parquet(self.absolute_path_with_filename)

        if filter_data_bool == True:
            self.filter_data()
    
    def create_absolute_path_with_filename(self, date_when_checked, filename):
        self.time_when_added_filepath = date_when_checked.replace('_', ' ').replace(':', '_').replace('/', '_')
        print(self.time_when_added_filepath)
        absolute_path_with_filename = os.path.join(sys.path[0],
                                                        API_details.DIR_DATA_PARQUET,
                                                        self.time_when_added_filepath,
                                                        filename)
        return absolute_path_with_filename



    #Big_df is filtered and we get rid of any data outside of 2 standard deviations
    def filter_data(self):    
        mean = self.big_df['price'].mean()
        std = self.big_df['price'].std()
        lower_range = mean - 2*std
        upper_range = mean + 2*std
        mask = (self.big_df['price'] >= lower_range) & (self.big_df['price'] <= upper_range)
        print(len(self.big_df['price']))
        self.big_df = self.big_df.loc[mask]
        print(len(self.big_df['price']))

        self.big_df['departure_date'] = pd.to_datetime(self.big_df['departure_date'].str[:10])
        self.big_df = self.big_df.sort_values(by=['departure_date', 'price'])

        self.big_df.index = self.big_df['departure_date']


    # We create a small df which we can visualise better on a graph
    def create_small_df(self, method=None, quantile=None):
        self.method = method
        print(self.method)
        self.quantile = quantile
        self.df = pd.DataFrame(columns=['departure_date', 'price', 'seats_available'])
        unique_dates = self.big_df['departure_date'].unique()
        #For the mean
        if self.method == 'mean':
            for i in range(len(unique_dates)):
                mean = pd.Series(self.big_df.loc[unique_dates[i], 'price']).mean()
                idx = self.big_df.loc[unique_dates[i], 'price'].gt(mean).argmax()-1
                new_row = {
                    'departure_date':unique_dates[i], 
                    'price': pd.Series(self.big_df.loc[unique_dates[i], 'price'])[idx], 
                    'seats_available': pd.Series(self.big_df.loc[unique_dates[i], 'seats_available'])[idx]}
                #print(new_row)
                self.df.loc[i] = new_row
        # for the smallest value
        elif self.method == 'min':
            for i in range(len(unique_dates)):
                self.df.loc[i] = pd.Series(self.big_df.loc[unique_dates[i], 'price']).min()
                new_row = {
                    'departure_date':unique_dates[i], 
                    'price': pd.Series(self.big_df.loc[unique_dates[i], 'price'])[0], 
                    'seats_available': pd.Series(self.big_df.loc[unique_dates[i], 'seats_available'])[0]}
                self.df.loc[i] = new_row
        # For the quantile
        elif self.method == 'quantile':
            if quantile == None:
                raise TypeError("The method selected is quantile which means you also need to pass a value for the quantile")
            else: 
                for i in range(len(unique_dates)):
                    quantile_val = pd.Series(self.big_df.loc[unique_dates[i], 'price']).quantile(q=quantile, interpolation = 'lower')
                    idx = np.where(quantile_val == self.big_df.loc[unique_dates[i], 'price'])[0][0]
                    #idx2 = self.big_df.loc[unique_dates[i], 'price'].eq(quantile_val).argmax()
                    new_row = {
                        'departure_date':unique_dates[i], 
                        'price': quantile_val, 
                        'seats_available': pd.Series(self.big_df.loc[unique_dates[i], 'seats_available'])[idx]}
                    self.df.loc[i] = new_row
                #self.df.index = self.df['departure_date']
        else:
            raise TypeError("Invalid method selected")
        
        self.df.index = self.df['departure_date']
        self.df = self.df.drop('departure_date', axis=1)

        self.y = self.df['price']
        self.x = self.df.index
        self.x_line = np.array(self.x.astype(int) / 10**9)
        
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
    # just use this function if you want to create a line of best fit based on a fourier transformer
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
        

    def plot_polynomial(self, degree, ax, colour):
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
    #this only plots the points
    def plot_graph_plotly(self):
        customdata = np.stack((self.df['seats_available']), axis=-1)

        hovertemplate = ('Seats available: %{customdata}<br>' + 
            'price: %{y} <br>' + 
            'date: %{x}' + 
            '<extra></extra>')
        fig = px.scatter(self.df, x=self.x, y=self.y,
                         title = f"Flights {self.payload['flight_type']} from {self.payload['fly_from']} to {self.payload['fly_to']} for {self.payload['adults']} adults")

        layout = go.Layout(title=f"Flights {self.payload['flight_type']} from {self.payload['fly_from']} to {self.payload['fly_to']} for {self.payload['adults']} adults",
                           yaxis_title=f"Price in {self.payload['curr']}", 
                           xaxis_title='Date',
                           showlegend=False)
        fig.update_layout(layout) 
        fig.update_traces(customdata=customdata, hovertemplate=hovertemplate,)
        
        #fig.write_html(self.file_graph_plotly)
        self.fig = fig

    #this plots the points with a polynomial line of best fit
    def plot_polynomial_plotly(self, degree):
        customdata = np.stack((self.df['seats_available']), axis=-1)
        hovertemplate = ('Seats available: %{customdata}<br>' + 
            'price: %{y} <br>' + 
            'date: %{x}' + 
            '<extra></extra>')
        self.y = self.y.astype(int)
        p= np.polyfit(self.x_line, self.y, degree)
        self.y_line = np.polyval(p,self.x_line)

        trace1 = go.Scatter(x=self.x, y=self.y, mode='markers')
        trace2 = go.Scatter(x=self.x, y=self.y_line, mode='lines')
        data = [trace1, trace2]

        layout = go.Layout(title=f"Flights {self.payload['flight_type']} from {self.payload['fly_from']} to {self.payload['fly_to']} for {self.payload['adults']} adults",
                           yaxis_title=f"Price in {self.payload['curr']}", 
                           xaxis_title='Date',
                           showlegend=False)
        
        fig = go.Figure(data = data)
        fig.update_layout(layout)
        fig.update_traces(customdata=customdata, hovertemplate=hovertemplate)
        #fig.write_html(self.file_graph_plotly)
        self.fig = fig

    def fetch_from_database(self, date_id, filename):
        # changing the format of the date_id from the one which was suitable as a classname
        # in the HTML template to one which can be used for quering the database
        date_id = date_id.replace('_', ' ')
        date_id = date_id.replace('-', '/')

        print(f"""We are fetching records that have the
              date_id:{date_id};
              filename:{filename}""")

        try:
            conn = sqlite3.connect('Data/Departure and destination.db')
            cursor = conn.cursor()
            cursor.execute("""
            SELECT *
            FROM date_checked
            WHERE date LIKE ? AND filename LIKE ? 
            """, (date_id, filename,))
            
            rows = cursor.fetchall()
            rows= rows[0]
            print(rows)
            print(len(rows))
            return_dict={'date':rows[0],
                         'depart_dest':rows[1],
                         'filename':rows[2],
                         'start_date':rows[3],
                         'end_date':rows[4],
                         'payload': rows[5]}
        except Exception as err:
            print(err)
            conn.rollback()
        conn.commit()
        conn.close()
        print("queried the database for the paylaod")
        # we create an instance of another small_df class, and we use it to get the small df
        # this is used to compare against the small_df form the instance it is created from
        return return_dict

    def compare_data_small_df_plotly(self, other_date_df_filename=None, 
                                     other_date_df_payload=None,):

        self.other_date_df_filename = other_date_df_filename
        self.other_date_df = small_df(absolute_path_with_filename=self.other_date_df_absolute_path_with_filename, 
                                        filter_data_bool=True,
                                        payload=self.other_date_df_payload)


        self.other_date_df.create_small_df(method = self.method, quantile = self.quantile)
        self.other_date_df = self.other_date_df.df

        # subtracting one df from the other
        def subtraction(row):
            index = row.name
            if row['matching_index']:
                return self.df.loc[index]['price'] - self.other_date_df.loc[index]['price']
            else:
                if index in self.df.index:
                    return self.df.loc[index]['price']
                elif index in self.other_date_df.index:
                    return self.other_date_df.loc[index]['price']
                else:
                    print(' There is some missing data')

        # adding a colours for the data points on the scatter plot
        def adding_colours(row):
            if row['matching_index']:
                if row['price'] == 0 :
                    price_change_text.append('No price change')
                    return 'blue'
                elif row['price']> 0: 
                    #Price is higher now compared to the last time it was checked
                    price_change_text.append('Price increased by £'+ str(row['price']))
                    return 'red'
                    
                elif row['price'] < 0:
                    #Price is lower now compared to the last time it was checked
                    x = -row['price']
                    price_change_text.append('Price decreased by £'+ str(x))    
                    return 'green'
                    
            # If the indices don't match, this will happen
            else:
                price_change_text.append('Data unavailable')
                return 'grey'
           
        price_change_text=[]

        # Creating a df that has a union for the indices of the 2 dfs
        indices = self.df.index.union(self.other_date_df.index)
        self.calc_df = pd.DataFrame(index=indices)
        self.calc_df['matching_index'] = self.calc_df.index.isin(self.df.index) & self.calc_df.index.isin(self.other_date_df.index)
    
        
        self.calc_df['price'] = self.calc_df.apply(lambda row: subtraction(row), axis=1)
        self.calc_df['colour'] = self.calc_df.apply(lambda row: adding_colours(row), axis=1)


        customdata = np.stack((price_change_text), axis=-1)
        hovertemplate = (#'Seats available: %{customdata[0]}<br>' + 
            '%{customdata}<br>' + 
            'price: %{y} <br>' + 
            'date: %{x}' + 
            '<extra></extra>')
        trace1 = go.Scatter(x=self.calc_df.index, y=self.calc_df['price'], mode='markers',name='line')
        data = [trace1]
        layout = go.Layout(title=f"Flights {self.payload['flight_type']} from {self.payload['fly_from']} to {self.payload['fly_to']} for {self.payload['adults']} adults<br>minus Flights {other_date_df_payload['flight_type']} from {other_date_df_payload['fly_from']} to {other_date_df_payload['fly_to']} for {other_date_df_payload['adults']} adults",
                           yaxis_title=f"Price in {self.payload['curr']}", 
                           xaxis_title='Date',
                           showlegend=False     )

        fig = go.Figure(data = data)
        fig.update_traces(customdata=customdata, hovertemplate=hovertemplate)
        fig.update_layout(layout)
        fig.update_traces(marker=dict(color=self.calc_df['colour']))
        #fig.write_html(self.file_graph_plotly)
        self.fig = fig


    def return_json(self):
        #self.json_file_plotly_graph = json.dumps(self.fig, cls = plotly.utils.PlotlyJSONEncoder
        self.json_file_plotly_graph = self.fig.to_json()
        print('this is the json graph that is going to be rendered on the website when the available_data endpoint is accessed')
        return self.json_file_plotly_graph
    
    def select_graph_type(self, 
                          graph_type=None, 
                          method = 'quantile', 
                          quantile = 0.2, 
                          degree=None,
                          other_date_df_filename=None,
                          other_date_df_id=None):
        SQL_query_dict = self.fetch_from_database(self.date_id, self.filename)
        self.payload = json.loads(SQL_query_dict['payload'])

        self.other_date_df_id = other_date_df_id
        self.other_date_df_filename = other_date_df_filename

        if graph_type == 'Plot graph':
            self.create_small_df(method=method, quantile=quantile)
            self.plot_graph_plotly()
            return self.return_json()
        elif graph_type == 'Plot graph with line of best fit':
            self.create_small_df(method=method, quantile=quantile)
            self.plot_polynomial_plotly(degree=degree)
            return self.return_json()
        elif graph_type == 'Compare data from 2 files':
            self.create_small_df(method=method, quantile=quantile)
            SQL_query_dict_other_date_df = self.fetch_from_database(self.other_date_df_id, self.other_date_df_filename)
            self.other_date_df_payload = json.loads(SQL_query_dict_other_date_df['payload'])
            self.other_date_df_filename =   SQL_query_dict_other_date_df['filename']

            self.other_date_df_absolute_path_with_filename = self.create_absolute_path_with_filename(self.other_date_df_id, self.other_date_df_filename)
            
            print(f"Absolute file path: {self.absolute_path_with_filename}")
            print(f"Absolute file path for other df: {self.other_date_df_absolute_path_with_filename}")
            
            # Arguments don't need to be passed as they are already variable that belong to the instance
            # however, it shows the variables this function needs
            self.compare_data_small_df_plotly(other_date_df_filename=self.other_date_df_absolute_path_with_filename,
                                              other_date_df_payload=self.other_date_df_payload)
            return self.return_json()
        
        


# %%
if __name__ == '__main__':
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0,parent_dir)
    os.chdir(sys.path[0])
    print(os.getcwd())

    payload={  
    'fly_from': 'OPO',
    'fly_to': 'BHX',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'return_from': '08/04/2023',
    'return_to': '23/04/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit': 1000}
    
    analyser = small_df(payload = payload, 
                        filter_data_bool = True, 
                        date_start = '01/04/2023', date_end = '16/05/2023')
    analyser.create_small_df(method = 'quantile', quantile = 0.3)
    analyser.compare_data_small_df_plotly('LTN_to_IAS_round_01-04-2023_to_31-12-2023.parquet')
    checking_df = analyser.df
    

# %%
# *NOTE: I have to add the ability to compare 2 graphs properly, however, I have to make a plan to make everything organised