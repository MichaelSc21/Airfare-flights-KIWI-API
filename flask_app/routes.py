import sys 
import os
#sys.path.insert(0, os.getcwd())

from flask_wtf.csrf import CSRFProtect
from flask_app.forms import FlightRequestForm
from flask_app import app
from flask import render_template, request
import threading

import Getting_data.API_details as API_details
import Getting_data.data_getter_OOP as data_getter_OOP
import Getting_data.data_analyser_OOP as data_analyser_OOP 

Data_getter = data_getter_OOP.Data_getter
big_df= data_analyser_OOP.big_df
small_df = data_analyser_OOP.small_df




@app.route('/chart1')
def chart1():
    payload={
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'return_from': '08/04/2023',
    'return_to': '23/04/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'round',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit': 1000}
    small_df = big_df(payload = payload, filter_data_bool=True).create_small_df(method='quantile', quantile=0.15)
    small_df.plot_polynomial_plotly(12)
    json_graph1 = small_df.return_json()


    return render_template('chart1.html', json_graph1 = json_graph1)


@app.route('/form', methods=['GET', 'POST'])
def payload_form():
    payload={
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'return_from': '08/04/2023',
    'return_to': '23/04/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'round',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit': 1000}
    if request.method == 'POST':
        payload = request.form.to_dict()
        
        return "Thanks for submitting the form, {}!".format(payload)
    else:
        return render_template('payload_form.html', payload_format=payload)

app.secret_key = API_details.FORMS_KEY  # Set your own secret key for Flask app
csrf = CSRFProtect(app)
#app.config["CACHE_TYPE"] = "null"

@app.route('/flight_request', methods=['GET', 'POST'])
def flight_request():
    form = FlightRequestForm()

    if form.validate_on_submit():
        #Note: you have to sort out the passing of parameters into the functions
        payload = dict(form.data)
        del payload['submit']
        del payload['csrf_token']
        print(payload)
        t1 = threading.Thread(target=get_result)
        t1.start()
        return render_template('flight_request_data.html')

    return render_template('flight_request.html', form=form)


@app.route('/get_result')
def get_result():
    payload={
    'fly_from': 'LTN',
    'fly_to': 'IAS',
    'date_from': '01/04/2023',
    'date_to': '16/04/2023',
    'return_from': '08/04/2023',
    'return_to': '23/04/2023',
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 7,
    'flight_type': 'round',
    'adults': '4',
    'curr': 'GBP',
    'sort':'date',
    'selected_cabins': 'M',
    'limit': 1000}
    getter = Data_getter(payload, 
                        sanitise_data = True, 
                        delete_data = False,
                        dateStart = '01/04/2023',
                        dateEnd = '31/12/2023')
    print(getter.filename )
    print(f"""current directory in routes is: + {os.getcwd()}
    
    
    
    """)
    big_dfs= big_df(filename = getter.filename, 
                            filter_data_bool=True, 
                            payload = payload,
                            dateStart = '01/04/2023',
                            dateEnd = '31/12/2023')
    
    small_dfs = big_dfs.create_small_df(method = 'quantile', quantile =0.14)
    small_dfs.plot_polynomial_plotly(12)

    json_graph1 = small_dfs.return_json()
    print(json_graph1)
    return {"response": 'True', "data":json_graph1}