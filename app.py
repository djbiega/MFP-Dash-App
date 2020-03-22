import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import user_data

from datetime import date, timedelta, datetime
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from dash_table import DataTable

from user_data import MFP_User

app = dash.Dash(__name__,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                external_stylesheets=[dbc.themes.BOOTSTRAP])

cols = ['Item', 'Protein', 'Carbohydrates', 'Fat', 'Fiber', 'Sugar', 'Calories']
app.layout = html.Div(
    [
        html.Div(
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
            ]
        ), 
        html.Div(

            [
                dbc.Container(
                    children = 
                    [
                        html.H4('MyFitnessPal User', style={'marginTop': '25px'}),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Input(
                                        placeholder='Enter MFP Username...',
                                        id='mfp-username', 
                                        value='', 
                                        type='text',
                                        ),
                                    width = 3),
                                dbc.Col(dbc.Button('Submit', id='submit-button', className='submit-button')),
                            ], justify='start'
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Alert(
                                        'Invalid Username',
                                        id='dbc-validate-username',
                                        color='primary',
                                        dismissable=False,
                                        fade=False,
                                        is_open=False,
                                    ), width = 3
                                )
                            ], justify='start'
                        ),
                    ]
                )
            ]
        ),
        html.Div(
            [
                dbc.Container(
                    [                       
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H4('Your Week at a Glance', style={'marginTop': 25}),
                                            html.Div(
                                                [
                                                    dcc.Graph(
                                                        id='weekly-pie-chart',
                                                        className='pie-chart',
                                                        config={'displayModeBar': False},
                                                        figure={}
                                                    )
                                                ],
                                            ),
                                            html.Div(
                                                [
                                                    dcc.Graph(
                                                        id='weekly-bar-chart',
                                                        config={'displayModeBar': False},
                                                        figure={}
                                                    )
                                                ],
                                            )
                                    ], width=6
                                ),
                                dbc.Col(
                                    [
                                        dbc.Container(
                                            [
                                                html.Div(id='calories-table'),
                                                html.Div(id='protein-table'),
                                                html.Div(id='carbs-table'),
                                                html.Div(id='fat-table'),
                                            ]
                                        )
                                    ], width=6, style={'marginTop': 25}
                                )
                            ]
                        )
                    ]
                )                
            ]
        ),
        html.Div(
            [
                dbc.Container(
                    [
                        dbc.Row(
                            dbc.Col(
                                [
                                    dcc.Graph(
                                        id='week-at-a-glance',
                                        config={
                                            'displayModeBar': False,
                                        },
                                        figure={}
                                    )
                                ]
                            )
                        ),
                    ]
                ),
                dbc.Container(
                    [
                        dbc.Row(
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        id='date-dropdown',
                                        options=[
                                            {
                                                'label': datetime.strftime(datetime.today()-timedelta(day), '%Y-%m-%d'), 
                                                'value': datetime.strftime(datetime.today()-timedelta(day), '%Y-%m-%d')
                                            } for day in range(7)
                                        ],
                                        multi=True
                                    ),
                                ], width=10
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    DataTable(
                                        id='data-table',
                                        style_data={
                                            'whiteSpace': 'normal',
                                            'height': 'auto'
                                        },
                                        columns=[{'name': i, 'id': i} for i in cols],
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
                                        sort_action='native',
                                    ),
                                ], width=12, style={'marginTop': '5px'}
                            )
                        ),
                        html.P(id='blank-space', style={'height': '50px'})
                    ]
                ), html.Div(id='hidden-data', style={'display': 'none'}),
            ]
        )
    ], style={'backgroundColor': 'white'}
)

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
            [Input('dbc-validate-username', 'children'),
            Input('submit-button', 'n_clicks')])
def load_data(username, click):
    # Load sample data when the app is loaded
    if not click:
        with open('data/sampleData.txt') as file:
            data=json.load(file)
        date_list = list(data['Dates'].keys())
        df_list = [pd.DataFrame(data['Dates'][date]['Items']).T for date in date_list]
        data_jsonified = {date: df_list[idx].to_json(orient='split') for idx, date in enumerate(date_list)}
        return json.dumps(data_jsonified)

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
        data = {date: df_list[idx].to_json(orient='split') for idx, date in enumerate(date_list)}
        return json.dumps(data)

def de_jsonify_data(jsonified_data):
    data = json.loads(jsonified_data)
    date_list = list(data.keys())
    df_list = [pd.read_json(data[i], orient='split') for i in date_list]
    return data, df_list, date_list

@app.callback(
    [Output('week-at-a-glance', 'figure'),
    Output('weekly-bar-chart', 'figure'),
    Output('weekly-pie-chart', 'figure')],
    [Input('hidden-data', 'children')])
def plot_data(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    _, df_list, date_list = de_jsonify_data(jsonified_data)

    # Convert any empty DataFrames into Dataframes of 0s
    for idx, df in enumerate(df_list):
        if df.empty:
            df_list[idx] = pd.DataFrame([[np.nan,0,0,0,0,0,0]], columns=cols).set_index('Item')

    # Add a line plot of Protein, Carbs, Fat, Fiber, Sugar, Calories
    fig = go.Figure()
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': [df_list[i]['Protein'].sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Protein',
                        'line': {'color': '#1C4E80'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': [df_list[i]['Carbohydrates'].sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Carbohydrates',
                        'line': {'color': '#A5D8DD'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': [df_list[i]['Fat'].sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Fat',
                        'line': {'color': '#EA6A47'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': [df_list[i]['Fiber'].sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Fiber',
                        'line': {'color': '#6AB187'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': [df_list[i]['Sugar'].sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Sugar',
                        'line': {'color': '#7E909A'}
                    }))
    fig.add_trace(go.Scatter({
                        'x': date_list, 
                        'y': [df_list[i]['Calories'].sum() for i in range(len(df_list))],
                        'type': 'scatter', 
                        'name': 'Calories', 
                        'yaxis': 'y2',
                        'line': {'color':'#202020'}
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
        'y': [df_list[i]['Protein'].sum() for i in range(len(df_list))],
        'name': 'Protein',
        'marker_color': '#1C4E80',
        'hovertemplate': '%{y} Grams<extra></extra>'
    }))
    fig2.add_trace(go.Bar({
        'x': date_list,
        'y': [df_list[i]['Carbohydrates'].sum() for i in range(len(df_list))],
        'name': 'Carbohydrates',
        'marker_color': '#A5D8DD',
        'hovertemplate': '%{y} Grams<extra></extra>'
    }))
    fig2.add_trace(go.Bar({
        'x': date_list,
        'y': [df_list[i]['Fat'].sum() for i in range(len(df_list))],
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
                np.sum([df_list[i]['Protein'].sum()*4 for i in range(len(df_list))]),
                np.sum([df_list[i]['Carbohydrates'].sum()*4 for i in range(len(df_list))]),    
                np.sum([df_list[i]['Fat'].sum()*9 for i in range(len(df_list))])
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
    Output('data-table', 'data'),
    [Input('hidden-data', 'children'),
    Input('date-dropdown', 'value')])
def display_tables(jsonified_data, selected_date):
    if jsonified_data is None or selected_date is None:
        raise PreventUpdate
    data, _, _ = de_jsonify_data(jsonified_data)
    # Create the tables. If there isn't any data, return a DataFrame of all 0's
    try:
        df = pd.concat([pd.read_json(data[i], orient='split').reset_index() for i in selected_date])
        df.rename(columns={'index': 'Item'}, inplace=True)
    except:
        df = pd.DataFrame([[np.nan,0,0,0,0,0,0]], columns=cols).set_index('Item')
    weekly_table = df.to_dict('records')
    return weekly_table
    
def generate_stats_tables(df, nutrient):
    table_header = [
        html.Thead(html.Tr([html.Th('Foods Highest in %s' % nutrient), html.Th('Value')]), style={'textAlign': 'center'})
    ]
    
    top_3 = df.nlargest(3, nutrient)[['Item', nutrient]]

    item_1 = top_3.iloc[[0]]
    item_2 = top_3.iloc[[1]]
    item_3 = top_3.iloc[[2]]

    row1 = html.Tr(
        [
        html.Td(str(item_1.loc[:, 'Item'].values[0]), style={'padding':'5px 5px 5px 0px'}),
        html.Td(str(item_1.loc[:, nutrient].values[0]), style={'textAlign': 'center'})      
        ]
    )
    row2 = html.Tr(
        [       
            html.Td(str(item_2.loc[:, 'Item'].values[0]), style={'padding':'5px 5px 5px 0px'}),
            html.Td(str(item_2.loc[:, nutrient].values[0]), style={'textAlign': 'center'})
        ]
    )
    row3 = html.Tr(
        [
            html.Td(str(item_3.loc[:, 'Item'].values[0]), style={'padding':'5px 5px 5px 0px'}), 
            html.Td(str(item_3.loc[:, nutrient].values[0]), style={'textAlign': 'center'})
        ]
    )
    
    table_body = [html.Tbody([row1, row2, row3])]

    return dbc.Table(
        table_header + table_body, 
        responsive=True,
        style={'width': 500, 'fontSize': '13px'},
        )

def concat_nutrition_stats_dfs(jsonified_data):
    _, df_list, date_list = de_jsonify_data(jsonified_data)
    try:
        df = pd.concat([(df_list[i]).reset_index() for i in range(len(date_list))])
        df.rename(columns={'index': 'Item'}, inplace=True)
    except:
        df = pd.DataFrame([[np.nan,0,0,0,0,0,0]], columns=cols).set_index('Item')
    return df

@app.callback(
    Output('calories-table', 'children'),
    [Input('hidden-data', 'children')])
def calories_table(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    df = concat_nutrition_stats_dfs(jsonified_data)
    return generate_stats_tables(df, 'Calories')

@app.callback(
    Output('protein-table', 'children'),
    [Input('hidden-data', 'children')])
def protein_table(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    df = concat_nutrition_stats_dfs(jsonified_data)
    return generate_stats_tables(df, 'Protein')

@app.callback(
    Output('carbs-table', 'children'),
    [Input('hidden-data', 'children')])
def carbs_table(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    df = concat_nutrition_stats_dfs(jsonified_data)
    return generate_stats_tables(df, 'Carbohydrates')

@app.callback(
    Output('fat-table', 'children'),
    [Input('hidden-data', 'children')])
def fat_table(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    df = concat_nutrition_stats_dfs(jsonified_data)
    return generate_stats_tables(df, 'Fat')


if __name__ == '__main__':
    app.run_server(debug=True)