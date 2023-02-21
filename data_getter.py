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

    url= f"https://api.tequila.kiwi.com/v2/search?fly_from={payload['fly_from']}&fly_to={payload['fly_to']}&date_from={payload['date_from']}&date_to={payload['date_to']}&flight_type={payload['flight_type']}&adults={payload['adults']}&children=0&curr={payload['curr']}&vehicle_type=aircraft&limit=1000&sort={payload['sort']}"




    headers = {
    'apikey': API_details.API_KEY,
    'accept': 'application/json',
    }

    response = requests.request("GET", url,headers=headers)

    return response.text

def get_duration(row):
    return row['total'] / 3600

def get_departure(row):
    return row[0]['utc_arrival']

def get_availability(row):
    return row['seats']

def sanitise_data(data): 
    data = json.loads(data)
    try: 
        data = data['data']
    except Exception as err:
        print(err)
        print(data)

    usecols = ['id', 'quality', 'price', 'airlines', 'duration', 'routecount', 'departure', 'seats_available']

    df = pd.DataFrame.from_dict(data)
    df['duration'] = df['duration'].apply(lambda row: get_duration(row))
    df['routecount'] = df['route'].apply(lambda row: len(row))
    df['departure'] = df['route'].apply(lambda row: get_departure(row))
    df['seats_available'] = df['availability'].apply(lambda row: get_availability(row))

    for col in df.columns:
        if col not in usecols:
            df.drop(col, axis=1, inplace=True)
    df
    json_string = df.to_json(orient='records')

    #json_string = json.loads(json_string)
    
    return json_string

def write_data(data):
    
    data= json.loads(data)
    #data = data['data']
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
            month_dict = json.loads(month_dict)
            file_json = file_json+month_dict
        except Exception as err:
            print(err)
            file_json = month_dict
        #print(f"Month_dict is of the type: {type(month_dict)}")
        
        json.dump(file_json, f, indent = 2)



def rotate_date(payload, month=None, dayResume = 1, period=40):
    month_dict = {}
    months_list = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    if month< 10:
        string_month = '0'+str(month)
    else:
        string_month = month


    dayEnd = dayResume + period
    if dayEnd > months_list[month-1]:
        dayEnd =months_list[month-1]
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


#This function will rotate dates by taking advanteage of the date_from and date_to parameters which are passed into the API call
#So, instead of making an API call for each date like this 02/03/2023, 03/03/2023, 04/03/2023
# It will make these calls all in one go by using date_from=02/03/2023 and date_to=04/03/2023


def rotate_date_kiwi(payload, month=None, dayResume = 1, period=40):
    months_list = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_dict=[]
    if month < 10:
        stringMonth = '0'+str(month)
    else:
        stringMonth = month

    dayEnd = dayResume + period
    if dayResume > months_list[month-1]:
        return None, None
    if dayEnd > months_list[month-1]:
        dayEnd =months_list[month-1]

    if dayResume< 10:
        stringDayResume = '0'+str(dayResume)
    else:
        stringDayResume = dayResume
    if dayEnd < 10:
        stringDayEnd = '0'+str(dayEnd)
    else:
        stringDayEnd = dayEnd

    print(f"The day start is: {stringDayResume}/{stringMonth}/2023")
    print(f"The day end is: {stringDayEnd}/{stringMonth}/2023")
    print("""
    
    
    """)

    payload['date_from'] = f'{stringDayResume}/{stringMonth}/2023'
    payload['date_to'] = f'{stringDayEnd}/{stringMonth}/2023'

    month_dict = get_data(payload)
    month_dict = sanitise_data(month_dict)

    
    return month_dict, dayEnd+1




def using_threads(payload=None, max_workers = 3, period=4, loop_over=3, months=None, filename=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        dayResume = 1
        
        for _ in range(loop_over):
            print(f"The dayResume is: {dayResume}")
            print("""
        
        
            """)
            worker_list = []
            for month in months:
                worker_list.append(executor.submit(rotate_date_kiwi,  payload =payload, month=month,dayResume=dayResume, period = period))
                time.sleep(0.5)

        
            for future in concurrent.futures.as_completed(worker_list):
                
                month_dict,dayResume = future.result()
                if month_dict == None:
                    pass
                else:
                    write_data_in_chunks(month_dict=month_dict, filename = filename)
    




# %%
if __name__ == '__main__':
    #Note: Date is in the format: DD/MM/YYYY
    payload={
    'fly_from': 'BHX',
    'fly_to': 'IAS',
    'date_from': '01%2F04%2F2023',
    'date_to': '16%2F04%2F2023',
    'return_from': '10/04/2023',
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date'}

    filename = payload['fly_from']+'_to_'+ payload['fly_to']
    using_threads(payload = payload, max_workers = 2, period = 15, months=[3, 4, 5, 6, 7, 8, 9, 10, 11, 12], filename=filename)
    



# %%
