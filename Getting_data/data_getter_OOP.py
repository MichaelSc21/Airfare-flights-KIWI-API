# %%
import sys
import requests
import json
import os
import sqlite3
import pandas as pd
import concurrent.futures
print("current directory in data_getter_OOP is:" + os.getcwd())
import Getting_data.API_details as API_details
import importlib
importlib.reload(API_details)
import time
import datetime


class Data_getter():
    # remember to find a proper way to assingn appropriate values to date_start and date_end
    def __init__(self, 
                 payload, 
                 sanitise_data=False, 
                 delete_data = False, 
                 date_start=None, 
                 date_end=None):  # noqa: E501
        self.payload = payload
        if payload['flight_type'] == 'oneway':
            self.oneway = True
            self.round = False
        else:
            self.oneway = False
            self.round = True

        self.date_start = self.payload['fly_from']
        if self.round:
            self.date_end = self.payload['return_to']
        else:
            self.date_end = self.payload['date_to']
        #self.date_start= date_start
        #self.date_end = date_end
        
        self.filename = f"{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}_{str(self.date_start).replace('/',  '-')}_to_{str(self.date_end).replace('/',  '-')}.parquet"
        self.filename = os.path.join(sys.path[0],API_details.DIR_DATA_PARQUET, self.filename)
        self.sanitise = sanitise_data
        self.delete_data = delete_data
        if self.delete_data:
            self.write_data("o")
        

    def get_data(self):
        url  = "https://api.tequila.kiwi.com/v2/search?"
        for key, value in self.payload.items():
            url += str(key) + '=' + str(value) + '&'

        url = url[:-1]

        headers = {
        'apikey': API_details.API_KEY,
        'accept': 'application/json',
        }

        response = requests.request("GET", url,headers=headers)
        return response.text
    
    def get_departure_duration(self, row):
        return row['departure'] / 3600
    
    def get_return_duration(self, row):
        return row['return'] / 3600
    
    def get_departure_date(self, row):
        for i in row:
            if i['flyTo'] == self.payload['fly_to']:
                return i['utc_arrival']

    def get_return_date(self, row):
        for i in row:
            if i['flyTo'] == self.payload['fly_from']:
                return i['utc_arrival']
    
    def get_availability(self, row):
        return row['seats']

    total_elem = 0
    def sanitise_data(self, data): 
        data = json.loads(data)
        try: 
            data = data['data']
        except Exception as err:
            print(err)
            print(data)
            
        usecols = ['id', 
                   'date_added', 
                   'quality', 
                   'price', 
                   'airlines', 
                   'departure_duration',
                   'return_duration', 
                   'routecount', 
                   'departure_date', 
                   'return_date', 
                   'seats_available']

        df = pd.DataFrame.from_dict(data)
        df['departure_duration'] = df['duration'].apply(lambda row: self.get_departure_duration(row))
        df['departure_date'] = df['route'].apply(lambda row: self.get_departure_date(row))

        if self.round == True:
            df['return_duration'] = df['duration'].apply(lambda row: self.get_return_duration(row))  # noqa: E501
            df['return_date'] = df['route'].apply(lambda row: self.get_return_date(row))
        

        df['date_added'] = pd.to_datetime('today')
        df['date_added'] = df['date_added'].dt.date
        df['routecount'] = df['route'].apply(lambda row: len(row))
        df['seats_available'] = df['availability'].apply(lambda row: self.get_availability(row))
        self.__class__.total_elem += df['price'].size
        print(f"We have {df['price'].size} elements from this response")

        for col in df.columns:
            if col not in usecols:
                df.drop(col, axis=1, inplace=True)
        #json_string = df.to_json(orient='records')
        return df
    
    def write_data(self, data):
        if data == "o":
            with open(self.filename, 'w') as f:
                pass
        else:
            data= json.loads(data)
            #data = data['data']
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=2)

    # writes the data to a file in chunks; It converts the existing data in the file to 
    # dataframe then concactenates the month_df and the file_df together
    def write_data_in_chunks(self, month_df):
        try: 
            file_df = pd.read_parquet(self.filename)

        except Exception as err: 
            print(err)


        try:
            file_df = pd.concat([file_df,month_df])
        except Exception as err:
            print(err)
            file_df = month_df
        file_df.to_parquet(self.filename)
            



    def return_dates(self, period, nights_in_dst):
        if self.date_start != None:
            self.payload['date_from'] = self.date_start
            self.payload['date_to'] = pd.to_datetime(self.date_start
            ,format="%d/%m/%Y") + pd.Timedelta(days=period-1) 
            self.payload['date_to']=self.payload['date_to'].strftime('%d/%m/%Y')

        if self.payload['flight_type'] == 'oneway':
            dates = [self.payload['date_from'], self.payload['date_to']]
        elif self.payload['flight_type'] == 'round':
            self.payload['return_from'] = pd.to_datetime(self.payload['date_from'] ,format="%d/%m/%Y") + pd.Timedelta(days=nights_in_dst)
            self.payload['return_from'] = self.payload['return_from'].strftime('%d/%m/%Y')
            self.payload['return_to'] = pd.to_datetime(self.payload['date_to'] ,format="%d/%m/%Y") + pd.Timedelta(days=nights_in_dst)
            self.payload['return_to'] = self.payload['return_to'].strftime('%d/%m/%Y')

            dates = [self.payload['date_from'], self.payload['date_to'], self.payload['return_from'], self.payload['return_to']]
        
        print(self.payload)
        print(self.date_end)
        self.list_dates = []
        date_end = pd.to_datetime(self.date_end,format="%d/%m/%Y")
        print(date_end)
        # Converts dates into pd.datetime
        for date in range(len(dates)):
            dates[date] = pd.to_datetime(dates[date],format="%d/%m/%Y")

        self.list_dates.append([date.strftime('%d/%m/%Y') for date in dates])
        # Loops over the dates until it gets to the date_end and adds them to self.list_dates in the format dd/mm/YYYY  # noqa: E501
        while dates[-1] < self.date_end:
            print(f"{dates[-1]} is smaller than {self.date_end}")
            for date in range(len(dates)):
                dates[date] = dates[date] + pd.Timedelta(days = period)
            self.list_dates.append([date.strftime('%d/%m/%Y') for date in dates])


    # this function is going to be called by the thread pool, and then the write_data_in_chunks function
    def middle_man(self, date):
        if self.payload['flight_type'] == 'oneway':
            self.payload['date_from'], self.payload['date_to'] = date
            temp_dict = self.get_data()
            #test_dict= json.loads(temp_dict)
            #print(test_dict['search_id'])

        elif self.payload['flight_type'] == 'round':
            self.payload['date_from'], self.payload['date_to'], self.payload['return_from'],self.payload['return_to'] = date
            temp_dict = self.get_data()
            
        if self.sanitise == True:
            temp_dict = self.sanitise_data(temp_dict)
        else:
            temp_dict= json.loads(temp_dict)
            temp_dict= json.dumps(temp_dict['data'])

        return temp_dict

    def insert_into_database(self):
        conn = sqlite3.connect('Data/Departure and destination.db')
        self.time_when_added = str(datetime.datetime.now().strftime('%d/%m/%Y %H:00'))
        try:
            conn.execute('''
                INSERT OR IGNORE INTO date_checked(date, depart_dest, filename, start_date, end_date)
                VALUES(?, ?, ?, ?, ?)
            ''', (self.time_when_added, 
                f"{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}",
                self.filename,
                self.date_start,
                self.date_end))
            print('got to here')
            depart_dest = f"""{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}"""
            conn.execute('''
                INSERT OR IGNORE INTO departure_destination_flight(id)
                VALUES(?)
            ''', (depart_dest,))
        except Exception as err:
            print(err)
            conn.rollback()
            
        conn.commit()
        conn.close()


    # this method is only to be for round flights as of 2/3/2023
    def using_threads2(self, max_workers, date_start
    =None, date_end=None, period=16,nights_in_dst=None, max = 1):
        self.return_dates(period=period, nights_in_dst=nights_in_dst)
        count = 1
        #looping_over = int(len(self.list_dates)/max) + (len(self.list_dates)%max_workers>0)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            dateidx= 0
            #for i in range(looping_over):
            worker_list = []
            worker_count =0
            
            while dateidx < len(self.list_dates):
                # The variable max makes sure that only a certain number of API calls can be done before the dictionaries with data have to be written to a file   # noqa: E501
                if worker_count<max*max_workers:
                    worker_count += 1
                    worker_list.append(executor.submit(self.middle_man, date=self.list_dates[dateidx]))
                    time.sleep(0.5)
                    print(dateidx)
                    dateidx += 1
                else:
                    worker_count +=1 
                if worker_count>max*max_workers or dateidx == len(self.list_dates):
                    for future in concurrent.futures.as_completed(worker_list):
                        temp_df= future.result()
                        if temp_df is None:
                            print('Temp dict is empty')
                        else:
                            self.write_data_in_chunks(month_df=temp_df)

                    print(f"We have written to the file {count} times")
                    count += 1
                    worker_list = []
                    worker_count =0

        self.insert_into_database()


                
        

# %% 
if __name__ == '__main__':
    #Note: Date is in the format: DD/MM/YYYY
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0,parent_dir)
    os.chdir(sys.path[0])
    print(os.getcwd())
    payload={
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/05/2023',
    'date_to': '16/05/2023',
    'return_from': '08/12/2023',
    'return_to': '23/12/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'round',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit': 1000}

    payload2= {
    'fly_from': 'OPO',
    'fly_to': 'BHX',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit':1000}

    getter = Data_getter(payload, 
                         sanitise_data = True, 
                         delete_data = False,
                         date_start = '01/04/2023',
                         date_end = '31/12/2023')

    #getter.using_threads2(max_workers=2, 
    #                      period = 16, 
    #                      nights_in_dst=7, 
    #                      max = 1)
    
    # Note: the period that is passed as an argument into the using_threads2 functions 
    # should be +1 more compared to the difference between 
    # date_from and date_to and the same when looking for round tickets
    getter.using_threads2(  max_workers=2, 
                        period = 16, 
                        nights_in_dst=7, 
                        max = 1)

