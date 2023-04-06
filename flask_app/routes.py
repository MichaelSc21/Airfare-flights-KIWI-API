import sys 
sys.path.insert(0, 'D:\OneDrive\Coding\A-level\Airfare-flights KIWI API')
import os
#sys.path.insert(0, 'D:\OneDrive\Coding\A-level\Airfare-flights KIWI API\Getting_data')
from Getting_data.data_analyser_OOP import *
import Getting_data.API_details as API_details

from flask_wtf.csrf import CSRFProtect
from flask_app.forms import FlightRequestForm
from flask_app import app
from flask import render_template, request



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


@app.route('/flight_request', methods=['GET', 'POST'])
def flight_request():
    form = FlightRequestForm()
    if form.validate_on_submit():
        # Access form data using form.field_name.data
        fly_from = form.fly_from.data
        fly_to = form.fly_to.data
        # Extract other form data in a similar manner
        
        # Process the form data and make the flight request
        # ...

        # Redirect to another page or return a response
        return 'Form submitted successfully!'
    return render_template('flight_request.html', form=form)
# %%
