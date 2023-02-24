# %%
import requests
import json
import sys
import matplotlib.pyplot as plt
import pandas as pd
import concurrent.futures
import API_details
import time



class Data_getter():
    def __init__(self, payload):
        self.payload = payload
        if payload['flight_type'] == 'oneway':
            self.oneway = True
            self.round = False

        self.filename = self.payload['fly_from'] + '_to_' + self.payload['fly_to'] + '.json'

    def get_data(self):
        url  = "https://api.tequila.kiwi.com/v2/search?"
        for key, value in self.payload.items():
            url += str(key) + '=' + str(value) + '&'

        url = url[:-1]
        print(url)

        headers = {
        'apikey': API_details.API_KEY,
        'accept': 'application/json',
        }

        response = requests.request("GET", url,headers=headers)

        return response.text
    
    @staticmethod
    def get_duration(row):
        return row['total'] / 3600
    @staticmethod
    def get_departure(row):
        return row[0]['utc_arrival']
    @staticmethod
    def get_availability(row):
        return row['seats']


    def sanitise_data(self, data): 
        data = json.loads(data)
        try: 
            data = data['data']
        except Exception as err:
            print(err)
            print(data)

        usecols = ['id', 'quality', 'price', 'airlines', 'duration', 'routecount', 'departure', 'seats_available']

        df = pd.DataFrame.from_dict(data)
        df['duration'] = df['duration'].apply(lambda row: self.get_duration(row))
        df['routecount'] = df['route'].apply(lambda row: len(row))
        df['departure'] = df['route'].apply(lambda row: self.get_departure(row))
        df['seats_available'] = df['availability'].apply(lambda row: self.get_availability(row))

        for col in df.columns:
            if col not in usecols:
                df.drop(col, axis=1, inplace=True)
        df
        json_string = df.to_json(orient='records')

        #json_string = json.loads(json_string)
        
        return json_string
    
    def write_data_in_chunks(self, month_dict):
        try: 
            with open(self.filename, 'r') as f:
                file_json = json.load(f)
        except: 
            pass

        with open(self.filename, 'w') as f:
            try:
                month_dict = json.loads(month_dict)
                file_json = file_json+month_dict
            except Exception as err:
                print(err)
                file_json = month_dict
            #print(f"Month_dict is of the type: {type(month_dict)}")
            
            json.dump(file_json, f, indent = 2)



    def rotate_date_kiwi(self, payload, month=None, dayResume = 1, period=40):
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

        self.payload['date_from'] = f'{stringDayResume}/{stringMonth}/2023'
        self.payload['date_to'] = f'{stringDayEnd}/{stringMonth}/2023'
        month_dict = self.get_data()
        month_dict = self.sanitise_data(month_dict)

        
        return month_dict, dayEnd+1


    def using_threads(self,payload=None, max_workers = 3, period=4, loop_over=3, months=None):
        print(self)
        print(self.__class__.__name__)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            dayResume = 1
            
            for _ in range(loop_over):
                print(f"The dayResume is: {dayResume}")
                print("""
            
            
                """)
                worker_list = []
                for month in months:
                    worker_list.append(executor.submit(self.rotate_date_kiwi,  payload =payload, month=month,dayResume=dayResume, period = period))
                    time.sleep(0.5)

            
                for future in concurrent.futures.as_completed(worker_list):
                    
                    month_dict,dayResume = future.result()
                    if month_dict == None:
                        pass
                    else:
                        self.write_data_in_chunks(month_dict=month_dict)
        
# %%
if __name__ == '__main__':
    #Note: Date is in the format: DD/MM/YYYY
    payload={
    'fly_from': 'MAN',
    'fly_to': 'IAS',
    'date_from': '01%2F04%2F2023',
    'date_to': '16%2F04%2F2023',
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date'}
    
    BHX_to_IAS = Data_getter(payload)
    BHX_to_IAS.using_threads(max_workers = 2, period = 15, months=[3, 4, 5, 6 ,7, 8, 9, 10 , 11, 12])

# %%
