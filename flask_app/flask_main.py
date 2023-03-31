# %%
from flask import Flask, render_template
import os
html_graph = os.path.abspath('../Graphs/Plotly graphs/HTML_graph.html')

print(html_graph)
app = Flask(__name__)


@app.route('/')
def home():
    return render_template(html_graph)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
# %%
