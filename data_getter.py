# %%
import requests
import json
import sys

def get_data(payload):

    url = f"https://api.tequila.kiwi.com/v2/search?fly_from={payload['fly_from']}&fly_to={payload['fly_to']}&date_from ={payload['date_from']}&adults={payload['adults']}&curr={payload['curr']}"
    

    headers = {
    'apikey': 'daatPIgsDN_cPqUdFLoobJ0Qjco__3mE',
    'accept': 'application/json',
    }

    response = requests.request("GET", url,headers=headers)

    return response.text

payload={
    'fly_from': 'BHX',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'flight-type': 'oneway',
    'adults': '4',
    'curr': 'GBP'}




data = get_data(payload)
# %%
def write_data(data):
    data = json.loads(data)
    data = data['data']
    with open('file1.json', 'w') as f:
        json.dump(data, f, indent=2)

write_data(data)
 # %%
sys.getsizeof(data)
# %%
