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


#NOTE: Update the database to use a composite key of the date and the depart_dest fieldnames

# this class is modified to be able handle request from the flight_request endpoint
# this class is not optimised to handle requests that require 1 API call but rather 2 or more
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

        self.date_start = self.payload['date_from']
        if self.round:
            self.date_end = self.payload['return_to']
        else:
            self.date_end = self.payload['date_to']
        #self.date_start= date_start
        #self.date_end = date_end

        # The time when it is added is in the format dd/mm/yy HH:00
        # When converted so that it is added to the filepath, it will be: dd_mm_yy HH_00
        self.time_when_added = str(datetime.datetime.now().strftime('%d/%m/%Y %H:00'))
        self.time_when_added_filepath = self.time_when_added.replace(':', '_').replace('/', '-')
        
        self.filename = f"{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}_{str(self.date_start).replace('/',  '-')}_to_{str(self.date_end).replace('/',  '-')}.parquet"
        self.absolute_path = os.path.join(sys.path[0],
                                        API_details.DIR_DATA_PARQUET,
                                        self.time_when_added_filepath)
        self.absolute_path_with_filename = os.path.join(self.absolute_path, self.filename)
        self.sanitise = sanitise_data

        # If the filepath for that certain time is not existent, it will be created
        # It fhe filepath exists, however if the same file is changed at the same hour,
        # it will be updated with the newer data rather than have the old data
        if not os.path.exists(self.absolute_path):
            os.makedirs(self.absolute_path)
        else:
            if os.path.exists(self.absolute_path_with_filename):
                os.remove(self.absolute_path_with_filename)

        


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
        try:
            return row['departure'] / 3600
        except Exception as err:
            print(err)
            return 'N/A'
    
    def get_return_duration(self, row):
        try:
            return row['return'] / 3600
        except Exception as err:
            print(err)
            return 'N/A'
    
    def get_departure_date(self, row):
        try:
            for i in row:
                if i['flyTo'] == self.payload['fly_to']:
                    return i['utc_arrival']
        except Exception as err:
            print(err)
            return 'N/A'

    def get_return_date(self, row):
        try:
            for i in row:
                if i['flyTo'] == self.payload['fly_from']:
                    return i['utc_arrival']
        except Exception as err:
            print(err)
            return 'N/A'

    
    def get_availability(self, row):
        try:
            return row['seats']
        except Exception as err:
            print(err)
            return 'N/A'


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
        try:
            df['departure_duration'] = df['duration'].apply(lambda row: self.get_departure_duration(row))
        except Exception as err:
            print(err)
            print(data)
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
    
    # this way of writing to the file is deprecated
    def write_data(self, data):
        if data == "o":
            with open(self.absolute_path_with_filename, 'w') as f:
                pass
        else:
            data= json.loads(data)
            #data = data['data']
            with open(self.absolute_path_with_filename, 'w') as f:
                json.dump(data, f, indent=2)

    # writes the data to a file in chunks; It converts the existing data in the file to 
    # dataframe then concactenates the month_df and the file_df together
    def write_data_in_chunks(self, month_df):
        try: 
            file_df = pd.read_parquet(self.absolute_path_with_filename)
        except Exception as err: 
            print(err)

        try:
            file_df = pd.concat([file_df,month_df])
        except Exception as err:
            print(err)
            file_df = month_df
        file_df.to_parquet(self.absolute_path_with_filename)
            


    
    # This function creates a list of all of the dates that are going to be iterated through with the using_thread_2 function to the arguments: date_from & date_to (and return_from & return_to if flight_type == 'round')
    # this function is optimised to only work with flight_requests for multiple API calls rather than a single one
    # NOTE: I have still have to figure out how dates are going to be iterated through for round and oneway flights
    def return_dates(self, period, nights_in_dst):
        if self.date_start != None:
            date_from = self.date_start
            date_to = pd.to_datetime(self.date_start, format="%d/%m/%Y") + pd.Timedelta(days=period-1) 
        if self.payload['flight_type'] == 'oneway':
            dates = [date_from, date_to]
        # putting the dates in the format dd/mm/yyyy
        elif self.payload['flight_type'] == 'round':
            return_from = pd.to_datetime(self.date_start ,format="%d/%m/%Y") + pd.Timedelta(days=nights_in_dst)
            return_from = return_from.strftime('%d/%m/%Y')
            return_to = pd.to_datetime(date_to ,format="%d/%m/%Y") + pd.Timedelta(days=nights_in_dst)
            return_to = return_to.strftime('%d/%m/%Y')

            dates = [date_from, date_to, return_from, return_to]

        self.list_dates = []
        self.date_end = pd.to_datetime(self.date_end,format="%d/%m/%Y")
        # Converts dates into pd.datetime
        for date in range(len(dates)):
            dates[date] = pd.to_datetime(dates[date],format="%d/%m/%Y")

        self.list_dates.append([date.strftime('%d/%m/%Y') for date in dates])
        # Loops over the dates until it gets to the date_end and adds them to self.list_dates in the format dd/mm/YYYY  # noqa: E501
        print(type(dates[-1]))
        print(dates)
        print(type(self.date_end))
        print(self.date_end)
        while dates[-1] < self.date_end:
            print(f"{dates[-1]} is smaller than {self.date_end}")
            for date in range(len(dates)):
                dates[date] = dates[date] + pd.Timedelta(days = period)
            self.list_dates.append([date.strftime('%d/%m/%Y') for date in dates])
        print(self.list_dates)
        # date_end is made into a string because it is needed when it is inserted into the database
        # date_start doesn't need to be converted because it is already a string datatype
        if self.payload['flight_type'] == 'oneway':
            self.date_end = self.payload['date_to']
        else:
            self.date_end = self.payload['return_to']

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
        
        try:
            conn = sqlite3.connect('Data/Departure and destination.db')
            conn.execute('''
                INSERT OR IGNORE INTO date_checked(date, depart_dest, filename, start_date, end_date, JSON_payload)
                VALUES(?, ?, ?, ?, ?, ?)
            ''', (self.time_when_added, 
                f"{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}",
                self.filename,
                self.date_start,
                self.date_end,
                json.dumps(self.payload)))
            print('got to here')
            depart_dest = f"""{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}"""
            conn.execute('''
                INSERT OR IGNORE INTO departure_destination_flight(id)
                VALUES(?)
            ''', (depart_dest,))
        except Exception as err:
            print(err)
            conn.rollback()
            raise "There was a problem when connecting ot the database with the data_getter_OOP"
        conn.commit()
        conn.close()

    # *NOTE: the variable nights_in_dst is only needed if the flight request is round
    def using_threads2(self, max_workers, date_start
    =None, date_end=None, period=16,nights_in_dst=None, max = 1):
        if 'nights_in_dst_to' in self.payload.keys():
            nights_in_dst = self.payload['nights_in_dst_to']
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

