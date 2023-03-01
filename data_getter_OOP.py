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
        print(url)

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

        for col in df.columns:
            if col not in usecols:
                df.drop(col, axis=1, inplace=True)
        df
        json_string = df.to_json(orient='records')

        #json_string = json.loads(json_string)
        
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
        if self.round == False:
            self.payload['date_from'] = f'{stringDayResume}/{stringMonth}/2023'
            self.payload['date_to'] = f'{stringDayEnd}/{stringMonth}/2023'
            month_dict = self.get_data()
            if self.sanitise == True:
                month_dict = self.sanitise_data(month_dict)


        else:
            self.payload['date_from'] = f'{stringDayResume}/{stringMonth}/2023'
            self.payload['date_to'] = f'{stringDayEnd}/{stringMonth}/2023'
            
            self.payload['date_from'] = f'{stringDayResume}/{stringMonth}/2023'
            self.payload['date_to'] = f'{stringDayEnd}/{stringMonth}/2023'

            
            month_dict = self.get_data()
            if self.sanitise == True:
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

    def return_dates(self, dateEnd, period):
        self.listDates = []
        dateEnd = pd.to_datetime(dateEnd,format="%d/%m/%Y")
        dates = [self.payload['date_from'], self.payload['date_to'], self.payload['return_from'], self.payload['return_to']]

        for date in range(len(dates)):
            dates[date] = pd.to_datetime(dates[date],format="%d/%m/%Y")
        self.listDates.append([date.strftime('%d/%m/%Y') for date in dates])

        while dates[0] <= dateEnd:
            dates[0] = dates[0] + pd.Timedelta(days=period)
            dates[1] = dates[1] + pd.Timedelta(days=period)
            dates[2] = dates[2] + pd.Timedelta(days=period)
            dates[2] = dates[2] + pd.Timedelta(days=period)

            self.listDates.append([date.strftime('%d/%m/%Y') for date in dates])

        print(self.listDates)

    def using_thread2(self, max_workers, dateEnd='31/12/2023', period=15):

        self.return_dates(dateEnd, period)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            worker_list = []
            dates_index=[i for i in range(max_workers)]
            for date in self.listDates:

                worker_list.append(executor.submit(self.rotate_date_kiwi,  payload =payload, dates=dates))
        
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
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M'}

    payload2= {
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '05/04/2023',
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M'}

    
    LTN_to_IAS_round = Data_getter(payload2, sanitise_data = True)
    """data = LTN_to_IAS_round.get_data()
    data = LTN_to_IAS_round.sanitise_data(data)
    LTN_to_IAS_round.write_data(data)
    """
    #LTN_to_IAS_round.using_threads(payload = payload2, months= [3, 4, 5, 6, 7, 8, 9, 10, 11, 12], period = 15)
# %%
LTN_to_IAS_round = Data_getter(payload, sanitise_data = True)
LTN_to_IAS_round.return_dates('31/12/2023', period = 15)


# %%
dateStart = "04/04/2023"
dateEnd = "31/12/2023"
period = 15

payload={
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'return_from': '17/04/2023',
    'return_to': '01/05/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M'}


def iterate(payload, dateStart, dateEnd, period):
    dateStart = pd.to_datetime(dateStart)
    dateEnd = pd.to_datetime(dateEnd)
    payload['date_from'] = pd.to_datetime(payload['date_from'],format="%d/%m/%Y")
    payload['date_to'] = pd.to_datetime(payload['date_to'],format="%d/%m/%Y")
    payload['return_from'] = pd.to_datetime(payload['return_from'],format="%d/%m/%Y")
    payload['return_to'] = pd.to_datetime(payload['return_to'],format="%d/%m/%Y")

    print(payload['date_from'])
    print(payload['date_to'])
    print(payload['return_from'])
    print(payload['return_to'])


    while payload['date_from'] <= dateEnd:
        payload['date_from'] = payload['date_from'] + pd.Timedelta(days=period)
        payload['date_to'] = payload['date_to'] + pd.Timedelta(days=period)
        payload['return_from'] = payload['return_from'] + pd.Timedelta(days=period)
        payload['return_to'] = payload['return_to'] + pd.Timedelta(days=period)
        print(payload['date_from'])
        print(payload['date_to'])
        print(payload['return_from'])
        print(payload['return_to'])

        print("""
        
        
        """)


iterate(payload, dateStart, dateEnd, period)
# %%
