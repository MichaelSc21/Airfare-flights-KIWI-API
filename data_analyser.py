# %%|
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
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
    print(df['price'].quantile(q=0.15))

def format_date(df):
    df['departure'] = df['departure'].to_datetime()


# %% 
def hist(df):
    x = df['price']
    fig, ax = plt.subplots(figsize = (12, 6))
    ax.hist(x, bins=1000)

def plot(df):
    x = df['price']
    y = df['duration']
    fig, ax = plt.subplots(figsize = (12, 6))
    ax.set_xlabel('Price in GBP')
    ax.set_xticks(np.arange(0, np.max(x)+1, 100))
    ax.set_ylabel('Duration')
    ax.scatter(x, y, marker ='.')

df = create_df('file1.json')
df
filter_data(df)
format_date(df)



# %%
