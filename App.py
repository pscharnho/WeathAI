import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import json
from Model import get_forecast
from Data import get_current_temperature

user_key = "afcd0a181f7c81d62b48495edd24cc61"


app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children='WeathAI'),

    html.Div(children='''
        Forecasting the weather with Machine Learning.
    '''),

    html.Label('City'),
    dcc.Dropdown(
        id='dropdown_1',
        options=[
            {'label': 'Magdeburg', 'value': 'Magdeburg'},
            {'label': 'Lausanne', 'value': 'Lausanne'},
            {'label': 'San Francisco', 'value': 'San Francisco'}
        ],
        value='Magdeburg'
    ),
    html.Label('Model'),
    dcc.Dropdown(
        id='dropdown_2',
        options=[
            {'label': 'OpenWeatherMap', 'value': 'OWM'},
            {'label': 'ML Model', 'value': 'MLM'}
        ],
        value='OWM'
    ),
    html.Div(id='output-container')

])

@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('dropdown_1', 'value'), dash.dependencies.Input('dropdown_2', 'value')])
def update_output(city, model):
    city_id = get_id(city) 
    (x, high, low) = get_forecast(city, model, city_id, user_key)
    if city_id == None:
        title = 'No current data'
    else:
        temp = get_current_temperature(city_id, user_key)
        title = 'Current Temperature: {}°C'.format(temp)
    return dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': x, 'y': low, 'type': 'line', 'name': 'low'},
                {'x': x, 'y': high, 'type': 'line', 'name': 'high'},
            ],
            'layout': {
                'title': title
            }
        }
    )


def get_id(city):
    with open('Data/city.list.json', encoding="utf8") as json_file:  
        data = json.load(json_file)
        for d in data:
            if d['name'] == city:
                return d['id']
    return None


if __name__ == '__main__':
    app.run_server(debug=True)