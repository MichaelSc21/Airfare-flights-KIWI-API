# %%
from importlib import reload
import data_getter_OOP
import data_analyser_OOP 

reload(data_getter_OOP)
reload(data_analyser_OOP)

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
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'flight_type': 'oneway',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit':1000}
    LTN_to_IAS_round = Data_getter(payload2, sanitise_data = True, delete_data = False)
    #LTN_to_IAS_round.using_threads2(dateEnd = '31/12/2023', max_workers=2, period = 16, max = 1)


    json_data = big_df(filename = LTN_to_IAS_round.filename, filter_data_bool = True)
    data_analyser = json_data.create_small_df(method = 'quantile', quantile = 0.15)
    data_analyser.plot_polynomial(degree = 7, ax=None, colour = 'red')

# %%
