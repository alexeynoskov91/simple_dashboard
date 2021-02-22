import pandas as pd
from typing import List, Union
import random
import plotly.express as px
import plotly.graph_objects as go

# dash specific imports
import dash_core_components as dcc
import dash_html_components as html
import dash.dependencies
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# 0. inputs

# data processing
data = pd.read_csv(r'C:\Programming\sales_dashboard\aggregated_data.csv')
category_sales = pd.read_csv(r'C:\Programming\sales_dashboard\category_sales.csv')
categories = category_sales['category'].unique()
shops = category_sales['shop_name'].unique()

# constant variables
PLOTLY_THEME = 'plotly_dark'
APP_theme = dbc.themes.CYBORG

# 1. selectors
controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Shop:", id='shop-selector-header'),
                dcc.Dropdown(
                    id="shop-selector",
                    options=[{"label": col, "value": col} for col in shops],
                    value="",
                    multi=True
                ),
                dbc.Tooltip('Select shop.',
                            target="shop-selector-header"),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Category:", id='category-selector-header'),
                dcc.Dropdown(
                    id="category-selector",
                    options=[{"label": col, "value": col} for col in categories],
                    value="",
                    multi=True
                ),
                dbc.Tooltip('Select category.',
                            target="category-selector-header"),
            ]
        ),
        html.Div(id='params-store', style={'display': 'none'}),  # тут хранятся параметры
        dcc.Store(id='data-store', data=[data.to_dict('records'),
                                         category_sales.to_dict('records')]),  # тут хранится наш датасет в виде словаря
    ],
    body=True,
)

# 2. graph objects
category_sales_graph = dcc.Graph(id='category-sales-graph')
plan_graph = dcc.Graph(id='plan-graph')


# 3. running the app
app = dash.Dash(name='basic_sales', external_stylesheets=[dbc.themes.FLATLY])
server = app.server


# 4. describing how it should look like
app.layout = dbc.Container(
    [
     html.H1("Basic sales dashboard", style={'textAlign': 'center'}),
     html.Hr(),
     dbc.Row([dbc.Col(controls, width=3),
              dbc.Col(plan_graph, width=7),
              dbc.Tooltip('A basic graph - plan vs total sales.', target="plan-graph"),
              ], justify="right", align="center"),
     dbc.Row([
              dbc.Col(category_sales_graph, width={"size": 7, "offset": 3}),
              dbc.Tooltip('Category sales depending on selected shops.',
                          target="category-sales-graph"),
              ], justify="right", align="center")
    ], fluid=True
)

# 5. additional functions and callbacks


def stringify(x: Union[str, int]) -> str:
    return "'"+str(x)+"'"


@app.callback(Output(component_id='params-store', component_property='children'),
              [Input(component_id='shop-selector', component_property='value'),
               Input(component_id='category-selector', component_property='value')])
def collect_params(shop_list: str, category_list: str):

    shop_list = shop_list if shop_list == 'all' else ', '.join([stringify(i)for i in shop_list])
    category_list = category_list if category_list == 'all' else ', '.join([stringify(i) for i in category_list])
    params = shop_list, category_list
    print(params)
    return params

# построить 2 графика - 1) разбивка по продажам по магазинам с мультиселектором 2) статичный продажи против плана


@app.callback(Output(component_id='plan-graph', component_property='figure'),
              [Input(component_id='params-store', component_property='children'),
               Input(component_id='data-store', component_property='data')])
def draw_plan_graph(selected_params: List, df: pd.DataFrame):

    df = pd.DataFrame(df[0])

    global shops
    shop_list, category_list = selected_params
    shop_list = [] if shop_list == '' else [i.strip("''") for i in shop_list.split(', ')]

    if shop_list == []:
        cleaned_df = df
    else:
        cleaned_df = df[df['shop_name'].isin(shop_list)][['month', 'shop_name', 'sold', 'plan']]
        cleaned_df = cleaned_df.reset_index()

    grouped_df = cleaned_df.groupby(['month'])[['sold', 'plan']].sum()
    grouped_df = grouped_df.reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=grouped_df['month'].values, y=grouped_df['sold'].values, fill=None,
                   mode='lines+markers', name='sales', line={'color': 'indigo'}))
    fig.add_trace(
        go.Scatter(x=grouped_df['month'].values, y=grouped_df['plan'].values, fill=None,
                   mode='lines+markers', name='plan', line={'color': 'orange'}))

    fig.update_traces(opacity=0.75)

    fig.update_layout(template=PLOTLY_THEME, title_text="Total sales vs. plan", xaxis_title="month",
                      yaxis_title="pieces", barmode='overlay', legend=dict(x=.02, y=.99),
                      xaxis=dict(tickmode='linear', tick0=0, dtick=1)
                      )
    return fig


@app.callback(Output(component_id='category-sales-graph', component_property='figure'),
              [Input(component_id='params-store', component_property='children'),
               Input(component_id='data-store', component_property='data')])
def draw_category_sales_graph(selected_params: List, df: pd.DataFrame):

    df = pd.DataFrame(df[1])


    global shops, categories
    shop_list, category_list = selected_params
    shop_list = [] if shop_list == '' else [i.strip("''") for i in shop_list.split(', ')]

    if shop_list == []:
        cleaned_df = df
    else:
        cleaned_df = df[df['shop_name'].isin(shop_list)][['month', 'shop_name', 'category','sold']]
        cleaned_df = cleaned_df.reset_index()


    grouped_df = cleaned_df.groupby(['month', 'category'])[['sold']].sum()
    grouped_df = grouped_df.reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=grouped_df[grouped_df['category'] == 'shirts']['month'].values,
                   y=grouped_df[grouped_df['category'] == 'shirts']['sold'].values, fill=None,
                   mode='lines+markers', name='shirts', line={'color': 'green'}))
    fig.add_trace(
        go.Scatter(x=grouped_df[grouped_df['category'] == 'sneakers']['month'].values,
                   y=grouped_df[grouped_df['category'] == 'sneakers']['sold'].values, fill=None,
                   mode='lines+markers', name='sneakers', line={'color': 'blue'}))

    fig.update_traces(opacity=0.75)

    fig.update_layout(template=PLOTLY_THEME, title_text="Monthly shop sales by category", xaxis_title="month",
                      yaxis_title="pieces", barmode='overlay', legend=dict(x=.02, y=.99),
                      xaxis=dict(tickmode='linear', tick0=0, dtick=1)
                      )
    return fig

# 6. python file runner expression


if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8887)