import sys 
import os
#sys.path.insert(0, os.getcwd())
from flask_app.forms import FlightRequestForm
from flask_app import app
from flask import render_template, request, session, redirect, url_for, jsonify
import sqlite3

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


#app.secret_key = API_details.FORMS_KEY  # Set your own secret key for Flask app
#csrf = CSRFProtect(app)


@app.route('/flight_request', methods=['GET', 'POST'])
def flight_request():
    form = FlightRequestForm()

    
    print(session)
    if form.validate_on_submit():
        #Note: you have to sort out the passing of parameters into the functions
        payload = dict(form.data)
        del payload['submit']
        del payload['csrf_token']

        if payload['limit'] == None:
            payload['limt'] = 1000
        if payload['flight_type'] == 'One-way':
            payload['flight_type'] = 'oneway'
        else:
            payload['flight_type'] = 'round'
        payload1 = {}
        for key, value in payload.items():
            if  payload[key] == None or  payload[key] == "":
                pass
            else:
                print(payload[key])
                payload1[key] = value
        payload = payload1
        #if 'json_graph' in session:
        #    print(session['json_graph'])
        #   del session['json_graph']
        session['payload'] = payload
        return render_template('flight_request_data.html', )

    return render_template('flight_request.html', form=form)


@app.route('/get_result')
def get_result():
    """payload={
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
    'limit': 1000}"""
    payload = session.get('payload')
    getter = Data_getter(payload, 
                        sanitise_data = True, 
                        delete_data = False,
                        dateStart = '01/04/2023',
                        dateEnd = '16/05/2023')
    #getter.using_threads2(max_workers=2, 
     #                   period = 16, 
      #                  nights_in_dst=7, 
       #                 max = 1)
    big_dfs = big_df(filename = getter.filename, 
                                filter_data_bool=True, 
                                payload = payload)
    small_dfs = big_dfs.create_small_df(method = 'quantile', quantile =0.14)
    small_dfs.plot_polynomial_plotly(12)

    json_graph1 = small_dfs.return_json()
    session['json_graph'] = json_graph1
    print('rendered graph')
    return {"ok": True, "data":json_graph1}

@app.route('/available_data', methods=['GET', 'POST'])
def get_available_data():
    if request.is_json:
        

        metadata_for_graph = request.json
        print(metadata_for_graph)
        print("""
        
        
        
        
        """)
        big_dfs = big_df(filename = metadata_for_graph['filename'], 
                                filter_data_bool=True)
        small_dfs = big_dfs.create_small_df(method = 'quantile', quantile =0.14)
        small_dfs.plot_polynomial_plotly(12)

        json_graph1 = small_dfs.return_json()
        #session['json_graph'] = json_graph1
        #return render_template('get_available_data_back.html', json_graph = json_graph1)    
        #return redirect('/get_available_data')
        return jsonify(json_graph1)
        

    # It is going to display the destinations that have available data
    data_analysing_functions= ['Plot graph', 'Plot graph with line of best fit', 'Compare data from 2 files']

    # Getting the departures and destinations which I ahve available
    try:
        conn = sqlite3.connect('Data/Departure and destination.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM departure_destination_flight')
        depart_dest = cursor.fetchall()

    except Exception as err:
        print(err)
        conn.rollback()
    conn.commit()
    conn.close()


    # Getting the dates that have been checked for the departures and destinations
    try:
        conn = sqlite3.connect('Data/Departure and destination.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM date_checked')
        dates_checked_list = cursor.fetchall()
    except Exception as err:
        print(err)
        conn.rollback()

    # Converting this dates_checked list into a dictionary that is accessible by the primary key depart_dest of the databse
    dates_checked = {}
    for row in dates_checked_list:
        row = list(row)
        depart_dest_column = row.pop(1)
        if depart_dest_column in dates_checked:
            dates_checked[depart_dest_column].append(row)
        else:
            dates_checked[depart_dest_column] = []
            dates_checked[depart_dest_column].append(row)

    # after departure and destinations are shown;
    # you can click on one of them which will load a table via JS
    # which will show for that respective destination and departure, the dates 
    # when data was retrieved

    # This will then have a dropdown menu, of either show_graph, or compare graph
    return render_template('available_data.html', 
                        data_analysing_functions = data_analysing_functions,
                        depart_dest = depart_dest,
                        dates_checked = dates_checked)

# NOTEE
# As of thursday 11/5/2023, this format is going to be changed when I change the format of the database
@app.route('/get_available_data')
def get_available_data_back():
    """metadata_for_graph = {'filename': request.args.get('filename'),
                          'date_id': request.args.get('date_id')}
    print(metadata_for_graph['filename'])
    print("""
    
    
    
    
    """)
    big_dfs = big_df(filename = metadata_for_graph['filename'], 
                                filter_data_bool=True)
    small_dfs = big_dfs.create_small_df(method = 'quantile', quantile =0.14)
    small_dfs.plot_polynomial_plotly(12)

    json_graph1 = small_dfs.return_json()
    """
    return render_template('get_available_data_back.html', json_graph = session['json_graph'])

