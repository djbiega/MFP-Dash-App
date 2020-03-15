import dash
import dash_table
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
from dash.exceptions import PreventUpdate
import plotly
from user_data import MFP_User
from datetime import date, timedelta, datetime
import json
import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children = [
        html.H4('To analyze your My fitness Pal Data, your Diary settings must be set to Public'),
        dcc.Store(id='memory-output'),
        html.Div(
            children = [
                dcc.Input(
                    placeholder='Enter MFP Username...',
                    id='mfp-username', 
                    value='', 
                    type='text',
                    required=True),
                html.Button(
                    id='button', 
                    children='Submit',
                    n_clicks=0),
                dcc.Loading(id='loading-1', 
                            children=[html.Div(id='loading-button-1')], 
                            type='circle'),
            ]),
        html.Div(
            id='output-graph'),
        html.Div(
            children = [
                html.H4('See Daily Breakdown'),
                dcc.Dropdown(
                    id='dates',
                    options=[
                        {'label': datetime.strftime(datetime.today()-timedelta(i), '%Y-%m-%d'), 
                        'value': datetime.strftime(datetime.today()-timedelta(i), '%Y-%m-%d')} \
                            for i in range(7)
                    ],
                    multi=True,
                    value='today')]),
                dash_table.DataTable(
                    id='data-table'                    
                ),
                html.Div(id='hidden-data', style={'display': 'none'}),
    ])

@app.callback(Output('hidden-data', 'children'),
            [Input('button', 'n_clicks')],
            state=[State('mfp-username', 'value')])
def load_data(click, username):
    if click == 0:
        return None
    user = MFP_User(username)
    date_list = list(user.data['Dates'].keys())        
    df_list = []
    for date in date_list:
        df_list.append(pd.DataFrame.from_dict(user.data['Dates'][date]['Items'], orient='index'))
    
    # Sort by Date
    idx = np.argsort(date_list)
    date_list = [date_list[i] for i in idx]
    df_list = [df_list[i].applymap(np.int64) for i in idx]
    
    # return JSON of the aggregated data
    datasets = {date: df_list[idx].to_json(orient='split') for idx, date in enumerate(date_list)}
    return json.dumps(datasets)

@app.callback(
    Output('output-graph', 'children'),
    [Input('hidden-data', 'children')])
def mfp_login(jsonified_data):
    if jsonified_data is None:
        return None
    datasets = json.loads(jsonified_data)
    df_list = [pd.read_json(datasets[i], orient='split') for i in datasets.keys()]
    date_list = list(datasets.keys())
    return dcc.Graph(
        id='week-at-a-glance',
        figure={
                'data': [
                            {
                                'x': date_list, 
                                'y': [df_list[i].Protein.sum() for i in range(len(df_list))],
                                'type': 'scatter', 'name': 'Protein'
                            },
                            {
                                'x': date_list, 
                                'y': [df_list[i].Carbohydrates.sum() for i in range(len(df_list))],
                                'type': 'scatter', 'name': 'Carbohydrates'
                            },
                            {
                                'x': date_list, 
                                'y': [df_list[i].Fat.sum() for i in range(len(df_list))],
                                'type': 'scatter', 'name': 'Fat'
                            },
                            {
                                'x': date_list, 
                                'y': [df_list[i].Fiber.sum() for i in range(len(df_list))],
                                'type': 'scatter', 'name': 'Fiber'
                            },
                            {
                                'x': date_list, 
                                'y': [df_list[i].Sugar.sum() for i in range(len(df_list))],
                                'type': 'scatter', 'name': 'Sugar'
                            },
                        ],
                'layout': {
                    'title': 'Your Week at a Glance'
                }})

if __name__ == '__main__':
    app.run_server(debug=True)