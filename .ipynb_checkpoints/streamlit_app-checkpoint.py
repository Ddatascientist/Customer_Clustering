import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

def wrangle(filepath):

  df = pd.read_excel(filepath, parse_dates=True) # Read data

  df = df.rename(columns={'Amount' : 'Total_Sales'})

  # list unwanted rows
  rtf = ['Custom Pack - Cone', 'Custom Pack - Sticker', 'Caramel Popcorn 30g Pieces', 'Custom Pack - Box']

  # filter out unwanted rows
  mask2 = ~df['Product Name'].isin(rtf)
  df  = df[mask2]

  # filtering out the zero sales
  mask = df['Total_Sales'] != 0
  df = df[mask]

  # convert date to pandas datetime obj
  df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)



  return df

df = wrangle('Soyum_data.xlsx')

clustered_df = pd.read_csv('clustered_df.csv')

app = dash.Dash(__name__)
# server = app.server
app.layout = html.Div([
    html.H1('Soyummy Customer Segmentation Dashboard', style={
        'text-align': 'center', 'color': 'white'
        }),

    html.Div([
        html.Label('Select Fiscal Year', style={'color': 'white', 'font-size': '20px'}),
            dcc.Dropdown(
                options = [{'label': i, 'value': i} for i in df['Date'].dt.year.unique()],
                id='fiscal_year'
                ),], style={'margin': 'auto','width': '50%','padding': '10px'}),
    html.Div([
        dcc.Graph(id='eda_bar1'),
        dcc.Graph(id='eda_bar2'),
    ], style={'padding': '50px'}),

    html.Br(),
    html.Br(),
    
    html.Div([
        html.H2('Cluster Result', style={'text-align': 'center', 'color': 'white'}),
        dcc.Graph(id='cluster_bar',),
        html.Br(),
        html.Label('Select Cluster Group', style={'color': 'white', 'font-size': '20px'}),
        dcc.Dropdown(
            options = [{'label': i, 'value': i} for i in clustered_df['Cluster_names_'].unique()],
            placeholder = 'Choose Cluster name',
            id='clusters', style = {'width': '40%', 'margin': "15px"}
        ),
        html.Div(id='table',)
    ], style={'padding': '10px'}),
])

def top10_sales_bar(df):
  df_top10 = (
    df.groupby(by='Customer_ID', as_index=False)['Total_Sales']
            .sum()
            .sort_values(by='Total_Sales', ascending=False)
            .head(10))
  
  plt.figure(figsize=(8, 5), dpi=80)
  fig = px.bar(df_top10,
              x=df_top10.Total_Sales,
              y=df_top10.Customer_ID,
              orientation='h', color='Total_Sales')
  fig.update_layout(xaxis_title='Total Sales', 
                    yaxis_title='Customer ID', 
                    title='Top 10 Customers in terms of Total Sales')

  return fig

def top10_selling_productline(df):
    top_prodctline = (
    df.groupby(by=['Customer_ID', 'Product Name'], as_index=False)['Product Name']
    .value_counts()
    .sort_values(by='count', ascending=False)
    .head(10)
    )

    fig2 = px.bar(top_prodctline,
             x='Customer_ID',
             y='count',
             color='Product Name',
             barmode='group')
    fig2.update_layout(title='Top 10 Selling Productlines',
                      xaxis_title='Customer ID',
                      yaxis_title='Productline Counts')
    return fig2



def cluster_bargraph(df):
    df = df
    cluster_count = df['Cluster_names_'].value_counts()

    fig3 = px.bar(
        cluster_count,
        x=cluster_count.index,
        y=cluster_count.values,
        color = 'count'
    )
    fig3.update_layout(title='Customer Cluster Visualization',
                      xaxis_title='Cluster',
                      yaxis_title='Cluster Counts')
    
    return fig3


@app.callback(
    Output('eda_bar2', 'figure'),
    Input('fiscal_year', 'value')
)
def update_eda_graph(value):
    data = df.copy()
    if value != None:
        mask = data['Date'].dt.year == value
        data_coy = data[mask]
        bar_1 = top10_selling_productline(data_coy)
        return bar_1
    else:
        bar_1 = top10_selling_productline(data)
        return bar_1


@app.callback(
    Output('eda_bar1', 'figure'),
    Input('fiscal_year', 'value')
)
def update_eda_graph(value):
    data = df.copy()
    if value != None:
        mask = data['Date'].dt.year == value
        data_coy = data[mask]
        bar_2 = top10_sales_bar(data_coy)
        return bar_2
    else:
        bar_2 = top10_sales_bar(data)
        return bar_2
        


@app.callback(
    Output('cluster_bar', 'figure'),
    Input('clusters', 'value')
)
def update_bar_graph(v):
    fig3_graph = cluster_bargraph(clustered_df)
    return fig3_graph


@app.callback(
    Output('table', 'children'),
    Input('clusters', 'value')
)
def update_scatter_graph(v):
    if v != None:
        mask = clustered_df['Cluster_names_'] == v
        df_table = clustered_df[mask]
        df_table_grp = (
            df_table
            .groupby(by='Customer_ID', as_index=False)[['Recency', 'Frequency', 'Monetary']]
            .mean()
            .sort_values(by='Recency', ascending=True)
        )
        return dash_table.DataTable(
            data=df_table_grp.to_dict('records'),
            columns=[{'name': i, "id": i} for i in df_table_grp.columns],
        )
    else:
        df_table_grp = (
            clustered_df
            .groupby(by='Customer_ID', as_index=False)[['Recency', 'Frequency', 'Monetary']]
            .mean()
            .sort_values(by='Recency', ascending=True)
            .head(10)
        )
        return dash_table.DataTable(
            data=df_table_grp.to_dict('records'),
            columns=[{'name': i, "id": i} for i in df_table_grp.columns],
        )




from logging import debug
if __name__ == '__main__':
    app.run_server(debug=True, port=8081)