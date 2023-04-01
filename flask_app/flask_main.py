# %%
from flask import Flask, render_template
import os
html_graph = os.path.abspath('../Graphs/Plotly graphs/HTML_graph.html')

print(html_graph)
app = Flask(__name__)


@app.route('/')
def home():
    return 'Hello world'

if __name__ == '__main__':
    app.run(debug=True, port=8080)
# %%
