import json
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import flask
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from datetime import timedelta, datetime, date
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from dash_table import DataTable

from webscraper import only_public_profiles
from webscraper.user_data import MFP_User
from db import update_db

server = flask.Flask(__name__)
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                server=server)
server = app.server

from constants import *

def build_banner():
    return  html.Div(
        className='banner',
        children=
            [
                dbc.Container(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H2('MyFitnessPal Weekly Dashboard'), 
                                    html.H6('To access MyFitnessPal Data, Diary settings must be set to public'),
                                ], width=11, style={'height': '100%', 'textAlign': 'center'}
                            ),
                            dbc.Col(
                                html.Img(
                                    src=app.get_asset_url('mfp-logo.png'),
                                    style={
                                        'width': '65px',
                                        'marginTop': 0,
                                        'marginRight': 0,
                                        'marginBottom': 0
                                        }
                                ), width=1, style={'height': '100%'}
                            )
                        ]
                    )                
                )
            ])

def build_input_container():
    return html.Div(
        dbc.Container(
            [
                html.H4('MyFitnessPal User', style={'marginTop': '25px'}),
                dbc.Row(
                    dbc.Col(
                        dbc.Input(
                            placeholder='Enter MFP Username...',
                            id='mfp-username', 
                            value='', 
                            type='text',
                            className='input-field'
                            ),
                    ),
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Alert(
                            'Invalid Username',
                            id='dbc-validate-username',
                            color='primary',
                            dismissable=False,
                            fade=False,
                            is_open=False,
                            className='input-field'
                        ), width = 4
                    )
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=datetime(2017,1,1),
                            max_date_allowed=date.today(),
                            minimum_nights=2,
                            initial_visible_month=datetime(2020, 1, 1),
                            start_date=datetime(2020, 1, 4),
                            end_date=datetime(2020, 1, 10),
                            clearable=True
                        ), width=4
                    ), style={'marginTop': '10px'}
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Button(
                            'Submit', 
                            id='submit-button', 
                            className='submit-button'
                        ), 
                    width = 1), 
                style={'marginTop': '10px'}
                ),
            ]
        )
    )

def build_pie_chart():
    return html.Div(
        children = [
            dcc.Loading(id='loading-pie-chart', children = [
                dcc.Graph(
                    id='weekly-pie-chart',
                    className='pie-chart',
                    config={'displayModeBar': False},
                    figure={}
                )
            ],
            type='default'
            ) 
        ], className='pretty_container')

def build_bar_chart():
    return html.Div(
        children=[
            dcc.Loading(id='loading-bar-chart', children = [
                dcc.Graph(
                    id='weekly-bar-chart',
                    config={'displayModeBar': False},
                    figure={}
                )
            ],
            type='default'
            )
        ], className='pretty_container')

def build_calories_table():
    return html.Div(
        dcc.Loading(
            id='loading-calories-table', 
            children = [html.Div(id='calories-table')], 
            type='default')
        )
def build_protein_table():
    return html.Div(
        dcc.Loading(
            id='loading-protein-table', 
            children = [html.Div(id='protein-table')], 
            type='default')
        )
def build_carbs_table():
    return html.Div(
        dcc.Loading(
            id='loading-carbs-table', 
            children = [html.Div(id='carbs-table')], 
            type='default')
        )
def build_fat_table():
    return html.Div(
        dcc.Loading(
            id='loading-fat-table', 
            children = [html.Div(id='fat-table')], 
            type='default')
        )

def build_nutrition_container():
    return html.Div(
            [
                dbc.Container(
                    [   
                        dbc.Row(
                            dbc.Col(
                                html.H4('Your Week at a Glance', style={'marginTop': 25}),
                            )
                        ),                    
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        build_pie_chart(),
                                        build_bar_chart()
                                    ], width=6
                                ),
                                dbc.Col(
                                    [
                                        dbc.Container(
                                            [
                                                build_calories_table(),
                                                build_protein_table(),
                                                build_carbs_table(),
                                                build_fat_table()
                                            ], className='pretty_container',
                                        )
                                    ], width=6
                                )
                            ]
                        )
                    ]
                )                
            ]
        )

def build_line_plot_container():
    return dbc.Container(
        dbc.Row(
            dbc.Col(
                html.Div(
                    dcc.Loading(id='loading-scatter-chart', 
                        children = [
                            dcc.Graph(
                                id='week-at-a-glance',
                                config={'displayModeBar': False},
                                figure={}
                            )
                        ], type='default'
                    )
                )
            )
        ), className='line_pretty_container',
    )

def build_data_table_container():
    return dbc.Container(
        [
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(id='date-dropdown', multi=True),
                width=10
            )
        ),
        dbc.Row(
            dbc.Col(
                html.Div(id='data-table'), 
                width=12, 
                className='line_pretty_container'  
            )
        )], className='line_pretty_container',
    )

app.layout = html.Div(
    style={'backgroundColor': '#F2F2F2'},
    children = [
        build_banner(),
        build_input_container(),
        build_nutrition_container(),
        html.Div(
            [
                build_line_plot_container(),
                build_data_table_container(), 
                html.P(id='blank-space', style={'height': '300px'}),
                html.Div(id='hidden-data', style={'display': 'none'})
            ]
        )
    ]
)

@app.callback(
    [Output('dbc-validate-username', 'children'),
    Output('dbc-validate-username', 'is_open')],
    [Input('submit-button', 'n_clicks')],
    state=[State('mfp-username', 'value')]
)
def check_username(click, username):
    if not click or not username:
        raise PreventUpdate
    valid = only_public_profiles.check_username(username)
    if valid:
        return username, False
    return 'Invalid Username', True


@app.callback(
    Output('hidden-data', 'children'),
    [Input('dbc-validate-username', 'children'),
    Input('submit-button', 'n_clicks')],
    state=[
        State('date-picker-range', 'start_date'),
        State('date-picker-range', 'end_date')
    ]
)
def load_data(username, click, start_date, end_date):
    # Load sample data when the app is loaded
    if not click:
        raise PreventUpdate

    if username != 'Invalid Username' and username != None:
        # Convert ISO-8601 inputs to Strings
        start_date = datetime.strftime(
           datetime.fromisoformat(start_date), '%Y-%m-%d'
        )
        end_date = datetime.strftime(
           datetime.fromisoformat(end_date), '%Y-%m-%d'
        )

        user_exists, last_updated = update_db.db_check_user(username)
        if user_exists:
            if (last_updated != YESTERDAY and last_updated != TODAY):
                print("last updated: %s" % last_updated)
                # Update the database with the most recent entries
                update_db.insert_nutrition([username], last_updated)
        else:
            # Update the database with all entries
            print("Scraping all of it: %s" % username)
            update_db.insert_nutrition([username], START_SCRAPE_DATE)
        print("user_data:")
        user_data = update_db.return_data(username, start_date, end_date)
        print("done scraping")
        json_out=user_data.to_json(orient='records', date_format='iso')
        return json_out


@app.callback(
    [Output('week-at-a-glance', 'figure'),
    Output('weekly-bar-chart', 'figure'),
    Output('weekly-pie-chart', 'figure')],
    [Input('hidden-data', 'children')]
)
def plot_data(json_in):
    if json_in is None:
        raise PreventUpdate
    df_data = pd.read_json(json_in)
    df_data['entry_date'] = pd.to_datetime(df_data['entry_date']).dt.date   
    date_list = sorted(df_data['entry_date'].unique())

    # Add a line plot of Protein, Carbs, Fat, Fiber, Sugar, Calories
    fig = go.Figure()
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': df_data.groupby('entry_date')['protein'].sum(),
                        'type': 'scatter', 
                        'name': 'Protein',
                        'line': {'color': '#1C4E80'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': df_data.groupby('entry_date')['carbohydrates'].sum(),
                        'type': 'scatter', 
                        'name': 'Carbohydrates',
                        'line': {'color': '#A5D8DD'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': df_data.groupby('entry_date')['fat'].sum(),
                        'type': 'scatter', 
                        'name': 'Fat',
                        'line': {'color': '#EA6A47'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': df_data.groupby('entry_date')['fiber'].sum(),
                        'type': 'scatter', 
                        'name': 'Fiber',
                        'line': {'color': '#6AB187'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': df_data.groupby('entry_date')['sugar'].sum(),
                        'type': 'scatter', 
                        'name': 'Sugar',
                        'line': {'color': '#7E909A'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': df_data.groupby('entry_date')['calories'].sum(),
                        'type': 'scatter', 
                        'name': 'Calories', 
                        'yaxis': 'y2',
                        'line': {'color': '#202020'}
                    }))
    fig.update_layout(
                yaxis={'title': 'Grams'}, 
                yaxis2={
                    'title':'Calories', 
                    'overlaying': 'y', 
                    'side': 'right',
                    'showgrid': False
                    },
                xaxis={'showgrid': False},
                legend={
                    'orientation': 'h',
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'x': 0.5,
                    'y': 1.1
                    },
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin={'t': 50},
                hovermode='x'
    )

    # Add a Bar plot of Protein, Carbs, Fat
    fig2 = go.Figure()
    fig2.add_trace(go.Bar({
        'x': date_list,
        'y': df_data.groupby('entry_date')['protein'].sum(),
        'name': 'Protein',
        'marker_color': '#1C4E80',
        'hovertemplate': '%{y} Grams<extra></extra>'
    }))
    fig2.add_trace(go.Bar({
        'x': date_list,
        'y': df_data.groupby('entry_date')['carbohydrates'].sum(),
        'name': 'Carbohydrates',
        'marker_color': '#A5D8DD',
        'hovertemplate': '%{y} Grams<extra></extra>'
    }))
    fig2.add_trace(go.Bar({
        'x': date_list,
        'y': df_data.groupby('entry_date')['fat'].sum(),
        'name': 'Fat',
        'marker_color': '#EA6A47',
        'hovertemplate': '%{y} Grams<extra></extra>'
    }))
    fig2.update_layout(
        yaxis={'title': 'Grams'},
        legend={
            'orientation': 'h',
            'xanchor': 'center',
            'yanchor': 'top',
            'x': 0.5,
            'y': 1.1
            },
        showlegend=False,
        height=350,
        width=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin={
            'l': 50, 
            'r': 150,
            't': 0,
            'b': 0
            },
    )

    # Add a pie chart of Protein, Carbs, Fat percentages
    fig3 = go.Figure()
    fig3.add_trace(go.Pie(
        labels=['Protein', 'Carbohydrates', 'Fat'], 
        values=[
                np.sum(df_data.groupby('entry_date')['protein'].sum()*4),
                np.sum(df_data.groupby('entry_date')['carbohydrates'].sum()*4),
                np.sum(df_data.groupby('entry_date')['fat'].sum()*4),
        ], 
        textinfo='label+percent', 
        insidetextorientation='radial',
        hovertemplate='%{value} Calories of %{label}<extra></extra>',
        marker_colors=['#1C4E80', '#A5D8DD', '#EA6A47'])
    )
    fig3.update_layout(
        showlegend=False,
        height=375,
        width=375,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin={
            'l': 125, 
            'r': 0,
            't': 0,
            'b': 0
            })
    return fig, fig2, fig3


@app.callback(
    Output('date-dropdown', 'options'),
    [Input('submit-button', 'n_clicks')],
    state=[
        State('date-picker-range', 'start_date'),
        State('date-picker-range', 'end_date')
    ]
)
def dropdown(click, start_date, end_date):
    if not click:
        raise PreventUpdate
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)
    date_range = (end_date - start_date).days + 1
    options=[
        {
            'label': datetime.strftime(end_date-timedelta(day), '%Y-%m-%d'), 
            'value': datetime.strftime(end_date-timedelta(day), '%Y-%m-%d')
        } for day in range(date_range)
    ]

    return options


@app.callback(
    Output('data-table', 'children'),
    [Input('hidden-data', 'children'),
    Input('date-dropdown', 'value')]
)
def display_tables(json_in, selected_date):
    if json_in is None or selected_date is None:
        raise PreventUpdate

    df_data = pd.read_json(json_in)
    df_data['entry_date'] = pd.to_datetime(df_data['entry_date']).dt.date
    try:
        out_data = pd.concat(df_data.loc[df_data['entry_date']==datetime.strptime(day, '%Y-%m-%d').date()] for day in selected_date)
    except:
        out_data = df_data.loc[df_data['entry_date']==datetime.strptime(selected_date[0], '%Y-%m-%d').date()]


    out_data = out_data[[col for col in out_data.columns if col not in DB_ONLY_COLS]]

    return DataTable(
        data=out_data.to_dict('rows'), 
        columns=[{'name': i, 'id': i} for i in out_data.columns],
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_as_list_view=True,
        style_cell={'textAlign': 'center'},
        style_header={
            'backgroundColor': '#F1F1F1',
            'fontWeight': 'bold'
        },
        style_cell_conditional=[
            {
                'if': {'column_id': 'Item'},
                'textAlign': 'left'
            }
        ],
        sort_action='native'
    )
    
def generate_stats_tables(json_in, nutrient):
    df_data = pd.read_json(json_in)
    df_data['entry_date'] = pd.to_datetime(df_data['entry_date']).dt.date
    table_header = [
        html.Thead(html.Tr([html.Th('Foods Highest in %s' % nutrient), html.Th('Value')]), style={'textAlign': 'center'})
    ]
    
    top_3 = df_data.nlargest(3, nutrient)[['item', nutrient]]

    item_1 = top_3.iloc[[0]]
    item_2 = top_3.iloc[[1]]
    item_3 = top_3.iloc[[2]]

    row1 = html.Tr(
        [
        html.Td(str(item_1.loc[:, 'item'].values[0]), style={'padding':'5px 5px 5px 0px'}),
        html.Td(str(item_1.loc[:, nutrient].values[0]), style={'textAlign': 'center'})      
        ]
    )
    row2 = html.Tr(
        [       
            html.Td(str(item_2.loc[:, 'item'].values[0]), style={'padding':'5px 5px 5px 0px'}),
            html.Td(str(item_2.loc[:, nutrient].values[0]), style={'textAlign': 'center'})
        ]
    )
    row3 = html.Tr(
        [
            html.Td(str(item_3.loc[:, 'item'].values[0]), style={'padding':'5px 5px 5px 0px'}), 
            html.Td(str(item_3.loc[:, nutrient].values[0]), style={'textAlign': 'center'})
        ]
    )
    
    table_body = [html.Tbody([row1, row2, row3])]

    return dbc.Table(
        table_header + table_body, 
        responsive=True,
        style={'width': 500, 'fontSize': '13px'},
        )

@app.callback(
    Output('calories-table', 'children'),
    [Input('hidden-data', 'children')]
)
def calories_table(json_in):
    if json_in is None:
        raise PreventUpdate
    return generate_stats_tables(json_in, 'calories')

@app.callback(
    Output('protein-table', 'children'),
    [Input('hidden-data', 'children')]
)
def protein_table(json_in):
    if json_in is None:
        raise PreventUpdate
    return generate_stats_tables(json_in, 'protein')

@app.callback(
    Output('carbs-table', 'children'),
    [Input('hidden-data', 'children')]
)
def carbs_table(json_in):
    if json_in is None:
        raise PreventUpdate
    return generate_stats_tables(json_in, 'carbohydrates')

@app.callback(
    Output('fat-table', 'children'),
    [Input('hidden-data', 'children')]
)
def fat_table(json_in):
    if json_in is None:
        raise PreventUpdate
    return generate_stats_tables(json_in, 'fat')


if __name__ == '__main__':
    server.run()