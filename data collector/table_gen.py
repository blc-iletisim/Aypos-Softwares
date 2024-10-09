"""Create a tidied up csv file. Get data from json files and merge them to a csv file."""
import pandas as pd
import os

files = os.listdir('./data')
print(files)

initialdf = pd.DataFrame()

for jso in files:

    if jso.startswith('reg_gain'):

        df = pd.read_json(f'data/{jso}',)
        print(df)
        initialdf = pd.concat([initialdf,df],ignore_index=True)

    else:
        continue

# pd.options.display.max_columns = None

print(initialdf)
print(initialdf.describe())