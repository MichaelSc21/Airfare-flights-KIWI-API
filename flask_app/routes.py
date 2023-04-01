from flask_app import app
from flask import render_template
import os


html_graph = os.path.abspath('../../Graphs/Plotly graphs/HTML_graph.html')



@app.route('/')
def home():
    return render_template(html_graph)