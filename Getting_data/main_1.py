# %%
from importlib import reload
import Getting_data.data_getter_OOP as data_getter_OOP
import Getting_data.data_analyser_OOP as data_analyser_OOP 
import Getting_data.email_sender as email_sender
import Getting_data.API_details as API_details
import time
reload(data_getter_OOP)
reload(data_analyser_OOP)
reload(email_sender)
reload(API_details)


Data_getter = data_getter_OOP.Data_getter
big_df= data_analyser_OOP.big_df
small_df = data_analyser_OOP.small_df
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
    
        
    data = Data_getter(payload2, sanitise_data = True, delete_data = False)
    data.using_threads2(dateStart = '20/03/2023',dateEnd = '31/12/2023', max_workers=2, period = 16, max = 1)


    json_data = big_df(payload = data.payload,filename = data.filename, filter_data_bool = True)
    data_analyser = json_data.create_small_df(method = 'quantile', quantile = 0.15)
    data_analyser.plot_polynomial_plotly(5)


    details_email = dict(        
        send_from = f"{API_details.EMAIL_USERNAME}", 
        send_to = f"{API_details.EMAIL_RECIPIENT}", 
        subject = 'Third attempt at sending an email',
        files=[data_analyser.file_graph_plotly],
        username =  f"{API_details.EMAIL_USERNAME}",
        password = f"{API_details.EMAIL_PASSWORD}",
        message = 'Lets see if this works',
        server = "smtp.gmail.com",
        port = 587
)


    email_sender.send_mail(**details_email)


 # %%
