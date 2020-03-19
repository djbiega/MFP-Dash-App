import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash_table import DataTable
from dash.exceptions import PreventUpdate
import plotly
import plotly.graph_objects as go
from user_data import MFP_User
import user_data
from datetime import date, timedelta, datetime
import json
import pandas as pd
import numpy as np


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

cols = ['Item', 'Protein', 'Carbohydrates', 'Fat', 'Fiber', 'Sugar', 'Calories']

app.layout = html.Div(
    children = [
        html.Div(
            id='banner',
            className='banner',
            children=[
                html.Div(
                    id='banner-text',
                    children=[
                        html.H4('MyFitnessPal Weekly Dashboard'),
                        html.H6('To access MyFitnessPal Data, Diary settings must be set to public')
                    ],
                ),
            ],
        ),
        html.Div(
            children = [
                dbc.Row([
                    dbc.Col(
                        dbc.Input(
                            placeholder='Enter MFP Username...',
                            id='mfp-username', 
                            value='', 
                            type='text',
                            ),
                        width = 3),
                    dbc.Col(dbc.Button('Submit', id='submit-button')),
                ], justify='start'),
                dbc.Row([
                    dbc.Col(
                        dbc.Alert(
                            'Invalid Username',
                            id='dbc-validate-username',
                            color='primary',
                            dismissable=False,
                            fade=False,
                            is_open=False,
                        ),
                    width = 3)
                ], justify='start'),
            ]),
        html.Div(
            children = [
                html.H4('See Daily Breakdown'),]),
        html.Div(
            id = 'display-div',
            children = [
                html.Div(id='test-div',children=[
                    dcc.Graph(
                        id='week-at-a-glance',
                        config={
                            'displayModeBar': False,
                        },
                        figure={}
                        )]),
                html.Div([
                    dcc.Dropdown(
                        id='date-dropdown',
                        options=[
                            {'label': datetime.strftime(datetime.today()-timedelta(i), '%Y-%m-%d'), 
                            'value': datetime.strftime(datetime.today()-timedelta(i), '%Y-%m-%d')} \
                                for i in range(7)
                            ],
                            multi=True),
                    DataTable(
                        id='data-table',
                        style_data={
                            'whiteSpace': 'normal',
                            'height': 'auto'
                        },
                        columns=[{'name': i, 'id': i} for i in cols]               
                    )])
                ],
            ),
        html.Div(id='hidden-data', style={'display': 'none'}),
    ])


@app.callback([Output('dbc-validate-username', 'children'),
            Output('dbc-validate-username', 'is_open')],
            [Input('submit-button', 'n_clicks')],
            state=[State('mfp-username', 'value')])
def check_username(click, username):
    if click == 0:
        raise PreventUpdate
    valid = user_data.check_username(username)
    if valid:
        return username, False
    return 'Invalid Username', True


@app.callback(Output('hidden-data', 'children'),
            [Input('dbc-validate-username', 'children')])
def load_data(username):
    if username != 'Invalid Username' and username != None:

        # Scrape weekly data as a list of DataFrames
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
    _, df_list, date_list = de_jsonify_data(jsonified_data)

    # Convert any empty DataFrames into Dataframes of 0s
    for idx, df in enumerate(df_list):
        if df.empty:
            df_list[idx] = pd.DataFrame([[np.nan,0,0,0,0,0,0]], columns=cols).set_index('Item')

    weekly_nutrition = [
                    {
                        'x': date_list, 
                        'y': [df_list[i].Protein.sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Protein',
                        'line': {'color': 'D44D30'}
                    },
                    {
                        'x': date_list, 
                        'y': [df_list[i].Carbohydrates.sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Carbohydrates',
                        'line': {'color': 'D7E321'}
                    },
                    {
                        'x': date_list, 
                        'y': [df_list[i].Fat.sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Fat',
                        'line': {'color': '4F28C7'}
                    },
                    {
                        'x': date_list, 
                        'y': [df_list[i].Fiber.sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Fiber',
                        'line': {'color': '0C8A26'}
                    },
                    {
                        'x': date_list, 
                        'y': [df_list[i].Sugar.sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Sugar',
                        'line': {'color': 'D77BDD'}
                    },
                    {
                        'x': date_list, 
                        'y': [df_list[i].Calories.sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Calories', 
                        'yaxis': 'y2',
                        'line': {'color':'#000000'}
                    },
                ]
    return {'data': weekly_nutrition,
            'layout': go.Layout(title='Your Week at a Glance', 
                                yaxis={'title': 'Grams'}, 
                                yaxis2={'title':'Calories', 
                                        'overlaying': 'y', 
                                        'side': 'right',
                                        'showgrid': False},
                                legend={'orientation': 'h',
                                        'xanchor': 'center',
                                        'yanchor': 'top',
                                        'x': 0.5,
                                        'y': 1.1},
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)')}


@app.callback(
    Output('data-table', 'data'),
    [Input('hidden-data', 'children'),
    Input('date-dropdown', 'value')])
def display_tables(jsonified_data, selected_date):
    if jsonified_data is None or selected_date is None:
        raise PreventUpdate
    datasets, _, _ = de_jsonify_data(jsonified_data)
    try:
        df = pd.concat([pd.read_json(datasets[i], orient='split').reset_index() for i in selected_date])
        df.rename(columns={'index': 'Item'}, inplace=True)
    except:
        df = pd.DataFrame([[np.nan,0,0,0,0,0,0]], columns=cols).set_index('Item')
    return df.to_dict('records')
    

if __name__ == '__main__':
    app.run_server(debug=True)