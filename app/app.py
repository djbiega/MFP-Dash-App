import dash
import dash_table
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
from dash.exceptions import PreventUpdate
import plotly
from user_data import MFP_User
import user_data
from datetime import date, timedelta, datetime
import json
import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children = [
        html.H4('To analyze your My fitness Pal Data, your Diary settings must be set to Public'),
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
                html.Div(id='validate-username'),
            ]),
        html.Div(
            children = [
                html.H4('See Daily Breakdown'),]),
        html.Div([
            dcc.Graph(id='week-at-a-glance'),
            dcc.Dropdown(
                id='date-dropdown',
                options=[
                    {'label': datetime.strftime(datetime.today()-timedelta(i), '%Y-%m-%d'), 
                    'value': datetime.strftime(datetime.today()-timedelta(i), '%Y-%m-%d')} \
                        for i in range(7)
                    ],
                    multi=True),
            dash_table.DataTable(
            id='data-table',
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto'
            },
            columns=[{'name': i, 'id': i} for i in ['Item', 'Protein', 'Carbohydrates',\
                 'Fat', 'Fiber', 'Sugar', 'Calories']]               
        ),]),
        html.Div(id='hidden-data', style={'display': 'none'}),
    ])


@app.callback(Output('validate-username', 'children'),
            [Input('button', 'n_clicks')],
            state=[State('mfp-username', 'value')])
def check_username(click, username):
    if click == 0:
        raise PreventUpdate
    valid = user_data.check_username(username)
    if valid:
        return username
    return 'Invalid username'


@app.callback(Output('hidden-data', 'children'),
            [Input('validate-username', 'children')])
def load_data(username):
    if username != ("This User's Diary settings are set to private" or 'This user does not exist'):
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

def de_jsonify_data(jsonified_data):
    datasets = json.loads(jsonified_data)
    df_list = [pd.read_json(datasets[i], orient='split') for i in datasets.keys()]
    date_list = list(datasets.keys())
    return datasets, df_list, date_list

@app.callback(
    Output('week-at-a-glance', 'figure'),
    [Input('hidden-data', 'children')])
def plot_data(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    try:
        _, df_list, date_list = de_jsonify_data(jsonified_data)
        weekly_nutrition = [
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
                    ]
        return {'data': weekly_nutrition}
    except:
        return {'data': [{'x': [0], 'y': [0], 'type': 'scatter', 'showlegend': False}]}                


@app.callback(
    Output('data-table', 'data'),
    [Input('hidden-data', 'children'),
    Input('date-dropdown', 'value')])
def display_tables(jsonified_data, selected_date):
    if jsonified_data is None or selected_date is None:
        raise PreventUpdate
    datasets, _, _ = de_jsonify_data(jsonified_data)
    df = pd.concat([pd.read_json(datasets[i], orient='split').reset_index() for i in selected_date])
    df.rename(columns={'index': 'Item'}, inplace=True)
    return df.to_dict('records')
    

if __name__ == '__main__':
    app.run_server(debug=True)