import base64
import datetime
import json
import os

import dash
import dash_core_components as dcc
import dash_html_components as html

from Data import get_current_temperature
from Model import get_forecast

user_key =   # Enter your OWM user key


app = dash.Dash()

image_filename = os.getcwd() + '/img/WeathAI.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

app.layout = html.Div(children=[
    html.Div([
        html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
                 style={'width': '40%'})
    ], style={'textAlign': 'center', 'padding': 10}),

    html.Div(children='''
        Forecasting the weather with Machine Learning.
    ''', style={'textAlign': 'center', 'padding': 10}),

    html.Div(children=[
        html.Label('City', style={'width': '48%', 'display': 'inline-block'}),
        html.Label('Model', style={'width': '48%', 'display': 'inline-block'}),
        dcc.Dropdown(
            id='dropdown_1',
            options=[
                {'label': 'Berlin', 'value': 'Berlin'},
                {'label': 'Hamburg', 'value': 'Hamburg'},
                {'label': 'Magdeburg', 'value': 'Magdeburg'},
                {'label': 'München', 'value': 'Muenchen'}
            ],
            value='Magdeburg',
            style={'width': '48%', 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='dropdown_2',
            options=[
                {'label': 'OpenWeatherMap', 'value': 'OWM'},
                {'label': 'Bayesian Ridge Regressor', 'value': 'Bayesian Ridge'},
                {'label': 'ElasticNet Regressor', 'value': 'ElasticNet'},
                {'label': 'Lasso Regressor', 'value': 'Lasso'},
                {'label': 'Neural Net Regressor', 'value': 'Neural Net'},
                {'label': 'Ridge Regressor', 'value': 'Ridge'}
            ],
            value='OWM',
            style={'width': '48%', 'display': 'inline-block'})
    ], style={'textAlign': 'center'}),
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
    if city == 'Muenchen':
        city = 'Landkreis München'
    with open('Data/city.list.json', encoding="utf8") as json_file:
        data = json.load(json_file)
        for d in data:
            if d['name'] == city and d['country'] == 'DE':
                return d['id']
    return None


if __name__ == '__main__':
    app.run_server(debug=True)
