import sys 
import os
import logging 
from logging.handlers import RotatingFileHandler
#sys.path.insert(0, os.getcwd())
from flask_app.forms import FlightRequestForm
from flask_app import app
from flask import render_template, request, session, redirect, url_for, jsonify
import sqlite3

import Getting_data.API_details as API_details
import Getting_data.data_getter_OOP as data_getter_OOP
import Getting_data.data_analyser_OOP as data_analyser_OOP
import Getting_data.data_analyser_OOP2 as analyser

Data_getter = data_getter_OOP.Data_getter
big_df= data_analyser_OOP.big_df
small_df = data_analyser_OOP.small_df


logging.basicConfig(filename='logging.txt', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
 
# setting up the format of the logger within the routes module
"""logger = logging.getLogger('routes_logger')
fileHandlerRoutes = logging.FileHandler('logging.txt')

fmt = logging.Formatter(
    "%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(process)d >>> /n%(message)s"
)
fileHandlerRoutes.setFormatter(fmt)
fileHandlerRoutes.setLevel(logging.DEBUG)
app.logger.addHandler(fileHandlerRoutes)"""

# Exceptions will be written to my logging file
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical('Uncaught exception', stack_info=True)

sys.excepthook = handle_exception


logging.info("this is a test")
print('asfsf')

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

#NOTE: Update this endpoint so that when there is text in the return_to and return_from 
# fieldnames, they are delted if the flight_type is "oneway" because it creates an 
# error in the data_getter_OOP module
@app.route('/flight_request', methods=['GET', 'POST'])
def flight_request():
    logging.info("""The flight_request template has been requeste
    
    
    """)
    form = FlightRequestForm()
    if form.validate_on_submit():
        #Note: you have to sort out the passing of parameters into the functions
        payload = dict(form.data)
        del payload['submit']
        del payload['csrf_token']

        if payload['limit'] == None:
            payload['limit'] = 1000
        if payload['flight_type'] == 'One-way':
            payload['flight_type'] = 'oneway'
        else:
            payload['flight_type'] = 'round'
        
        filtered_dict = {key: value for key, value in payload.items() if value != "" and value is not None}
        #print(filtered_dict)
        logging.debug("a POST request has been sent with the information for the payload for the data_getter_OOP module")
        logging.debug(f"This is the dictionary passed: \n {filtered_dict}")
        logging.debug(f"Compare to the dictoinary of the session: \n {session['payload']}")
        
        session['payload'] = filtered_dict


        return render_template('flight_request_data.html', )

    return render_template('flight_request.html', form=form)


@app.route('/get_result')
def get_result():
    # Example of the format the payload should be like
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
                        delete_data = False,)
    getter.using_threads2(max_workers=2, 
                        period = 16, 
                        max = 1)
    df = analyser.small_df(filename = getter.filename,
                    absolute_path_with_filename=getter.absolute_path_with_filename,
                    filter_data_bool=True, 
                    payload = payload)
    df.create_small_df(method = 'quantile', quantile =0.14)
    no_parameters_polynomial = 12
    df.plot_polynomial_plotly(no_parameters_polynomial)

    json_graph1 = df.return_json()
    #session['json_graph'] = json_graph1
    print('rendered graph')
    logging.debug("""the data that was passed as a payload via the POST request allows data_getter_OOP 
                        to fetch the data from KIWI API.""")
    logging.debug("""A line of best fit is created with %(no_parameters_polynomial)d  paramaters""")
    return {"ok": True, "data":json_graph1}

@app.route('/available_data', methods=['GET', 'POST'])
def get_available_data():
    logging.debug("The available_data template has been requested")
    # This template does not support POST requests
    if request.method == 'POST':
        # Only data from 2 files can be shown and compared to each other, or data of a single file is shown
        metadata_for_graph = request.json
        logging.debug("A POST request has been made with the data needed that is wanted to be shown on the available_data webpage")
        logging.debug("This is the graphs requested: %(metadata_for_graph)s")
        big_dfs = big_df(filename = metadata_for_graph['filename'], 
                                filter_data_bool=True)
        small_dfs = big_dfs.create_small_df(method = 'quantile', quantile =0.14)
        no_parameters_polynomial = 12
        small_dfs.plot_polynomial_plotly(no_parameters_polynomial)
        json_graph1 = small_dfs.return_json()
        logging.debug("A graph has been drawn and the json data for the graph will be rendered on the html template with %(no_parameters_polynomial)d parameters for the polynomial shown")
        #session['json_graph'] = json_graph1
        return render_template('templates/get_available_data_back.html', json_graph = json_graph1)    
        #return redirect('/get_available_data')
        
        

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

    # Converting this dates_checked list into a dictionary that is accessible by the 
    # primary key depart_dest of the databse
    #  Each row after this for loop will be like this: 
    # ['21-06-2023 18:00', 'LTN_to_IAS_oneway_01-07-2023_to_31-07-2023.parquet', '01/07/2023', '31/07/2023']
    logging.debug("The files available in the SQL database are displayed on the available_data template")
    dates_checked = {}
    for row in dates_checked_list:
        row = list(row)
        depart_dest_column = row.pop(1)
        #Only showing the filename and not the whole path
        #index = row[1].find('Parquet_files\\')
        #row[1] = row[1][index + len('Parquet_files\\'):]
        #Changin the format of the date
        print(row[1])
        row[0] = row[0].replace('/', '-')
        #row[0] = row[0].replace(' ', '_')
        print(row[0])
        if depart_dest_column in dates_checked:
            dates_checked[depart_dest_column].append(row)
        else:
            dates_checked[depart_dest_column] = []
            dates_checked[depart_dest_column].append(row)
    print("""
    
    
    
    """)
    print(dates_checked)
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

#@app.get('/get_available_data_back/date_id1=<path:date_id1>&filename1=<path:filename1>&date_id2=<path:date_id2>&filename2=<path:filename2>')
@app.get('/get_available_data_back/date_id0=<date_id0>&filename0=<filename0>&date_id1=<date_id1>&filename1=<filename1>&graph_type=<graph_type>')
def get_available_data_back(date_id0, filename0, date_id1, filename1, graph_type):
    metadata_for_graph = {
        'date_id0': date_id0,
        'filename0': filename0,
        'date_id1': date_id1,
        'filename1': filename1,
                          }
    logging.debug(f"This is the metadata for the graph based on what the user requested on the available_data template: {metadata_for_graph}")
    logging.debug("The available_data template has been accessed and now the data from the file is going to be shown on a graph")

    if date_id1 == 'NA':
        logging.debug("Plotting a graph for a single file")
        df = analyser.small_df(filename =metadata_for_graph['filename0'], 
                                filter_data_bool = True,
                                date_id=metadata_for_graph['date_id0'])
        # the function select_graph type creates the dataframe for the graph and 
        # creates a suitable graph based graph_type value and 
        # then it returns a json dictionary that has the data for the graph to be rendered 
        # on the webpage
        json_graph1 = df.select_graph_type(method = 'quantile', 
                                           quantile = 0.2, 
                                           graph_type=graph_type, 
                                           degree=12)
    else:
        logging.debug
        df = analyser.small_df(filename = metadata_for_graph['filename0'], 
                                filter_data_bool = True,
                                date_id=metadata_for_graph['date_id0'])
        json_graph1 = df.select_graph_type(method = 'quantile', 
                                           quantile = 0.2, 
                                           graph_type=graph_type, 
                                           degree=12, 
                                           other_date_df_filename=metadata_for_graph['filename1'],
                                           other_date_df_id=metadata_for_graph['date_id1'])

          
    
    

    print(json_graph1)
    return render_template('get_available_data_back.html', json_graph = json_graph1)

