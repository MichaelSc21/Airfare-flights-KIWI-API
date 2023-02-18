# %%|
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
# %%
def create_df(filename):
    df = pd.read_json(filename)
    df

create_df('file1.json')
# %%

# %%
