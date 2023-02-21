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
        print(df.loc[i, 'price'])
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
    ax.set_xlim
    ax.hist(x, bins=bin)

def model(x, a, b):
    return a *  np.sin(x) + b


def plot(df,):
    x = df.index
    y = df['price']
    #x_line= (x - pd.Timestamp("01/01/1970")) // pd.Timedelta('1s')

    fig, ax = plt.subplots(figsize = (12, 6))
    ax.set_ylabel('Price in GBP')
    #ax.set_yticks(np.arange(0, np.max(y)+1, 100))
    ax.set_xlabel('Date')

    ax.scatter(x, y, marker ='.')




# %%
df = create_df('BHX_to_IAS.json')
df = filter_data(df)
df2 = sort_by_date(df)
df

plot(df2)



# %%

# %%
