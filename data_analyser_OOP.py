# %%
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import sys
from scipy.optimize import curve_fit, leastsq
from mplcursors import cursor

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

        self.df.index = self.df['departure_date']
    
    def create_small_df(self, method, quantile=None, ):
        self.method = method
        self.quantile = quantile
        return small_df(self.df,self.method, self.quantile, self.filename)
    
class small_df():
    def __init__(self, big_df, method, quantile, filename):
        self.df = pd.DataFrame(index=big_df.index.unique(), columns=['price'])
        
        if method == 'mean':
            for i in big_df.index.unique():
                self.df.loc[i] = pd.Series(big_df.loc[i, 'price']).mean()
        elif method == 'min':
            for i in big_df.index.unique():
                self.df.loc[i] = pd.Series(big_df.loc[i, 'price']).min()
        elif method == 'quantile':
            if quantile == None:
                raise TypeError("The method selected is quantile which means you also need to pass a value for the quantile")
            else: 
                for i in big_df.index.unique():
                    self.df.loc[i] = pd.Series(big_df.loc[i, 'price']).quantile(q=quantile)
        else:
            raise TypeError("Invalid method selected")
        
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

    def plot_with_hover(self):
        c = np.random.randint(1,5,size=15)
        norm = plt.Normalize(1,4)
        cmap = plt.cm.RdYlGn
        names = np.array(list("ABCDEFGHIJKLMNO"))

        fig,ax = plt.subplots(figsize = (12, 6))
        sc = plt.scatter(self.x,self.y)

        annot = ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        def update_annot(ind):
            
            pos = sc.get_offsets()[ind["ind"][0]]
            annot.xy = pos
            text = "{}".format(" ".join(list(map(str,self.y[ind["ind"]]))))
            annot.set_text(text)
            #annot.get_bbox_patch().set_facecolor(cmap(norm(c[ind["ind"][0]])))
            #annot.get_bbox_patch().set_alpha(0.4)
            

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                cont, ind = sc.contains(event)
                if cont:
                    update_annot(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)
        plt.show()





# %%
if __name__ == '__main__':
    df_names = ['OPO_to_BHX_oneway']
    big_dfs = {}
    small_dfs = {}
    for df_name in df_names:
        
        big_dfs[df_name] = big_df(filename = df_name+'.json', filter_data_bool=True)

        temp_df = big_dfs[df_name].df
        small_dfs[df_name] = big_dfs[df_name].create_small_df(method = 'quantile', quantile = 0.1)
        #fig, ax = plt.subplots(figsize = (12, 6))
        #small_dfs[df_name].plot_polynomial(degree = 7, ax=ax, colour='red')

        small_dfs[df_name].plot_with_hover()


# %%
"""
TO DO as of 2/3/2023:
Sort out the fourier curve fitting


"""


