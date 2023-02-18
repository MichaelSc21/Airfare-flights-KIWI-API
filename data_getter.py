# %%
import requests
import json
import sys
import matplotlib.pyplot as plt
import pandas as pd
import concurrent.futures
import API_details
import time

# %%
def get_data(payload):

    url = f"https://api.tequila.kiwi.com/v2/search?fly_from={payload['fly_from']}&fly_to={payload['fly_to']}&date_from ={payload['date_from']}&adults={payload['adults']}&curr={payload['curr']}"
    

    headers = {
    'apikey': API_details.API_KEY,
    'accept': 'application/json',
    }

    response = requests.request("GET", url,headers=headers)

    return response.text

def get_duration(row):
    return row['total'] / 3600

def sanitise_data(data): 
    data = json.loads(data)    
    data = data['data']
    usecols = ['id', 'quality', 'price', 'airlines', 'duration', 'routecount']

    df = pd.DataFrame.from_dict(data)
    df['duration'] = df['duration'].apply(lambda row: get_duration(row))
    df['routecount'] = df['route'].apply(lambda row: len(row))

    for col in df.columns:
        if col not in usecols:
            df.drop(col, axis=1, inplace=True)
    df
    json_string = df.to_json(orient='table')

    json_string = json.loads(json_string)
    json_string = json_string['data']
    return json_string

def write_data(data):
    #data= json.loads(data)

    with open('file1.json', 'w') as f:
        json.dump(data, f, indent=2)


def write_data_in_chunks(month_dict, filename):
    try: 
        with open(filename, 'r') as f:
            file_json = json.load(f)
    except: 
        pass

    with open(filename, 'w') as f:
        try:
            file_json = file_json|month_dict
        except Exception as err:
            print(err)
            file_json = month_dict
        json.dump(file_json, f, indent = 2)



def rotate_date(payload, month=None, dayResume = 1, period=40):
    month_dict = {}
    months_list = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    if month< 10:
        string_month = '0'+str(month)
    else:
        string_month = month


    dayEnd = dayResume + period
    if dayEnd > months_list[month-1]+1:
        dayEnd =months_list[month-1] +1
    for day in range(dayResume, dayEnd):
        if day < 10:
            string_day = '0'+str(day)
        else:
            string_day = day

        print(f"The date is {string_day}/{string_month}/2023")
        payload['date_from'] = f'{string_day}/{string_month}/2023'
        
        data = get_data(payload)
        data = sanitise_data(data)

        month_dict[payload['date_from']] = data
    return month_dict, day+1




def using_threads(payload=None, max_workers = 3, period=11, loop_over=3, months=None, filename=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        dayResume = 1
        
        for _ in range(loop_over):
            print(f"The dayResume is: {dayResume}")
            print("""
        
        
            """)
            worker_list = []
            for month in months:
                worker_list.append(executor.submit(rotate_date,  payload =payload, month=month,dayResume=dayResume, period = period))
                time.sleep(0.5)

        
            for future in concurrent.futures.as_completed(worker_list):
                
                month_dict,dayResume = future.result()
                write_data_in_chunks(month_dict=month_dict, filename = filename)
    




# %%
if __name__ == '__main__':
    #Note: Date is in the format: DD/MM/YYYY
    payload={
    'fly_from': 'BHX',
    'fly_to': 'IAS',
    'date_from': 'N/a',
    'flight-type': 'oneway',
    'adults': '4',
    'curr': 'GBP'}

    """month_dict, day = rotate_date(payload=payload,month=3, dayResume=1, period=7)
    write_data_in_chunks(month_dict, 'file1.json')"""
    filename = 'file1.json'
    using_threads(payload = payload, max_workers = 6, period = 11, months=[3, 4, 5], filename=filename)



# %%
