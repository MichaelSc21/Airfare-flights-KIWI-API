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
    def __init__(self, payload, sanitise_data=False):
        self.payload = payload
        if payload['flight_type'] == 'oneway':
            self.oneway = True
            self.round = False
        else:
            self.oneway = False
            self.round = True

        self.filename = f"{self.payload['fly_from']}_to_{self.payload['fly_to']}_{self.payload['flight_type']}.json"
        self.sanitise = sanitise_data

    def get_data(self):
        url  = "https://api.tequila.kiwi.com/v2/search?"
        for key, value in self.payload.items():
            url += str(key) + '=' + str(value) + '&'

        url = url[:-1]
        #print(url)

        headers = {
        'apikey': API_details.API_KEY,
        'accept': 'application/json',
        }

        response = requests.request("GET", url,headers=headers)
        return response.text
    
    @staticmethod
    def get_departure_duration(row):
        return row['departure'] / 3600
    
    @staticmethod
    def get_return_duration(row):
        return row['return'] / 3600
    
    def get_departure_date(self, row):
        for i in row:
            if i['flyTo'] == self.payload['fly_to']:
                return i['utc_arrival']

    def get_return_date(self, row):
        for i in row:
            if i['flyTo'] == self.payload['fly_from']:
                return i['utc_arrival']
    
    @staticmethod
    def get_availability(row):
        return row['seats']

    total_elem = 0
    def sanitise_data(self, data): 
        data = json.loads(data)
        try: 
            data = data['data']
        except Exception as err:
            print(err)
            print(data)

        usecols = ['id', 'quality', 'price', 'airlines', 'departure_duration','return_duration', 'routecount', 'departure_date', 'return_date', 'seats_available']

        df = pd.DataFrame.from_dict(data)
        df['departure_duration'] = df['duration'].apply(lambda row: self.get_departure_duration(row))
        df['departure_date'] = df['route'].apply(lambda row: self.get_departure_date(row))

        if self.round == True:
            df['return_duration'] = df['duration'].apply(lambda row: self.get_return_duration(row))
            df['return_date'] = df['route'].apply(lambda row: self.get_return_date(row))


        df['routecount'] = df['route'].apply(lambda row: len(row))
        df['seats_available'] = df['availability'].apply(lambda row: self.get_availability(row))
        self.__class__.total_elem += df['price'].size
        print(f"We have {df['price'].size} elements from this response")

        for col in df.columns:
            if col not in usecols:
                df.drop(col, axis=1, inplace=True)
        json_string = df.to_json(orient='records')
        return json_string
    
    def write_data(self, data):
        data= json.loads(data)
        #data = data['data']
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

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



    def return_dates(self, dateEnd, period):
        if self.payload['flight_type'] == 'oneway':
            dates = [self.payload['date_from'], self.payload['date_to']]
        elif self.payload['flight_type'] == 'round':
            dates = [self.payload['date_from'], self.payload['date_to'], self.payload['return_from'], self.payload['return_to']]

        self.listDates = []
        dateEnd = pd.to_datetime(dateEnd,format="%d/%m/%Y")
        
        # Converts dates into pd.datetime
        for date in range(len(dates)):
            dates[date] = pd.to_datetime(dates[date],format="%d/%m/%Y")

        # Loops over the dates until it gets to the dateEnd and adds them to self.listDates in the format dd/mm/YYYY
        while dates[0] <= dateEnd:
            self.listDates.append([date.strftime('%d/%m/%Y') for date in dates])
            for date in range(len(dates)):
                dates[date] = dates[date] + pd.Timedelta(days = period)

    def middle_man(self, date):

        if self.payload['flight_type'] == 'oneway':
            self.payload['date_from'], self.payload['date_to'] = date
            temp_dict = self.get_data()
            #test_dict= json.loads(temp_dict)
            #print(test_dict['search_id'])
            if self.sanitise == True:
                temp_dict = self.sanitise_data(temp_dict)

        elif self.payload['flight_type'] == 'round':
            self.payload['date_from'], self.payload['date_to'], self.payload['return_from'],self.payload['return_to'] = date
            temp_dict = self.get_data()
            if self.sanitise == True:
                temp_dict = self.sanitise_data(temp_dict)

        return temp_dict

    # this method is only to be for round flights as of 2/3/2023
    def using_threads2(self, max_workers, dateEnd='31/12/2023', period=15, max = 1):
        self.return_dates(dateEnd, period)
        print(len(self.listDates))
        count = 1
        #looping_over = int(len(self.listDates)/max) + (len(self.listDates)%max_workers>0)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            dateidx= 0
            #for i in range(looping_over):
            worker_list = []
            worker_count =0
            
            while dateidx < len(self.listDates):
                # The variable max makes sure that only a certain number of API calls can be done before the dictionaries with data have to be written to a file 
                if worker_count<max*max_workers:
                    worker_count += 1
                    worker_list.append(executor.submit(self.middle_man, date=self.listDates[dateidx]))
                    time.sleep(0.5)
                    print(dateidx)
                    dateidx += 1
                else:
                    worker_count +=1 
                
                if worker_count>max*max_workers or dateidx == len(self.listDates):
                    for future in concurrent.futures.as_completed(worker_list):
                        temp_dict= future.result()
                        if temp_dict == None:
                            print('Temp dict is empty')
                        else:
                            self.write_data_in_chunks(month_dict=temp_dict)
                    #print(f"Completed these dates: {self.listDates[i]}")
                    #print(f"Completed these dates: {date}")
                    print(f"We have written to the file {count} times")
                    count += 1
                    worker_list = []
                    worker_count =0


                
        

# %% 
if __name__ == '__main__':
    #Note: Date is in the format: DD/MM/YYYY
    payload={
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'return_from': '17/04/2023',
    'return_to': '01/05/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'round',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit': 1000}

    payload2= {
    'fly_from': 'IAS',
    'fly_to': 'LTN',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit':1000}

    IAS_to_LTN_round = Data_getter(payload2, sanitise_data = True)

    IAS_to_LTN_round.using_threads2(dateEnd = '31/12/2023', max_workers=2, period = 16, max = 2)
    # Note: the period that is passed as an argument into the using_threads2 functions should be +1 more compared to the difference between date_from and date_to and the same when looking for round tickets


# %%
