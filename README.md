# Airfare-flights-KIWI-API

<h1> Airfare-flights API caller using KIWI API </h1>

<h2> How does it all work? </h2>

<h3> Data getter OOP </h3>

<p> It does a few things to retrieve the data from the API and then write into a file in the desired format. </p>
<p> It receives a JSON format from the KIWI API, sanitises the data received using pandas and then writes into a dictionary </p>
<p> Main functions of the program: </p>
<ul>
<li> get_data(): it makes the call to the API</li>
<li> using_threads2(): It makes the right get_data() calls by passing the right dates. These dates are found in a list of dates.</li>
<li> middle_man(): It is called by using_threads2() and makes the calls get_data() and then sanitise_data()
</ul>



<h3> Data analyser OOP </h3>
<p> This file is a half failed attempt of mine to analyse data.</p>
<p> There is 2 ways in which I tried to implement a line of best fit of price against date of the data. </p>
<p> plot_graph_fourier() either is going to need a lot more work or become deprecated. </p>
<p> plot_polynomial() is right now the best method I have right now for creating a line of best fit. </p>
<p> Main functions of the program </p>
<ul>
<li> The create_big_df() class is going to create a class for the main dataframe from which we are going to get data from </p>
<li> The create_small_df() class creates a class which stores a df which we are going to use for data analysation. The class contains the methods used to make a line of best fit and plot the dat.</p>
</ul>


<p> *Note: The other versions of the data_getter and data_analyser are just kept here to just have a refference of a non OOP approach of creating a solution </p>
