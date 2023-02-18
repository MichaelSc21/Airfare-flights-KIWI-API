# %%|
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
# %%
"""def sanitise_data(filename):
    with open(filename, 'r') as f:
        data = json.dumps(f)
    data['duratipon'] = 
"""

def get_duration(row):
    return row['total'] / 3600

def create_df(filename):
    usecols = ['id', 'quality', 'price', 'fare', 'price_dropdown', 'airlines', 'duration', 'routecount']

    df = pd.read_json(filename)
    df['duration'] = df['duration'].apply(lambda row: get_duration(row))
    df['routecount'] = df['route'].apply(lambda row: len(row))

    for col in df.columns:
        if col not in usecols:
            df.drop(col, axis=1, inplace=True)
        else:
            print(col)

    """
    df.drop(['flyFrom', 'flyTo', 'cityFrom', 'cityCodeFrom', 'cityTo', 'cityCodeTo', 'countryFrom', 'countryTo', 'distance', 'conversion', 'fare','baglimit', 'route', ], axis=1, inplace =True)
    """
    return df



df = create_df('file1.json')
# %%
def plot(df):
    x = df['price']
    y = df['duration']
    fig, ax = plt.subplots(figsize = (12, 6))
    ax.set_xlabel('Price in GBP')
    ax.set_xticks(np.arange(0, np.max(x)+1, 100))
    ax.set_ylabel('Duration')
    ax.scatter(x, y, marker ='.')
    ax.scatter(x, df['routecount'])

plot(df)



# %%
