import dash
from dash import dcc
from dash import html
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
# model
from model import prediction
from sklearn.svm import SVR
import matplotlib.pyplot as plt

def get_stock_price_fig(df):
    # Reset index to make 'Date' a column
    df.reset_index(inplace=True)

    # Flatten multi-index columns if they exist
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [' '.join(col).strip() for col in df.columns]

    print(df.columns)  # Optional: to check what's inside

    # Try to find Close columns dynamically
    close_cols = [col for col in df.columns if "Close" in col]

    fig = px.line(df, x="Date", y=close_cols, title="Stock Price")
    return fig

def get_more(df):
    # Flatten multi-level columns if they exist
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [' '.join(col).strip() for col in df.columns]

    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    fig = px.scatter(df,
                     x="Date",
                     y="EMA_20",
                     title="Exponential Moving Average vs Date")
    fig.update_traces(mode='lines+markers')
    return fig


app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
    ])
server = app.server

# html layout of site
app.layout = html.Div(
    [
        html.Div(
            [
                # Navigation
                html.P("Welcome to Vector Stocks", className="start"),
                html.Div([ 
                    html.P("Input stock code: "),
                    html.Div([
                        dcc.Input(id="dropdown_tickers", type="text"),
                        html.Button("Submit", id='submit'),
                    ],
                             className="form")
                ],
                         className="input-place"),
                html.Div([ 
                    dcc.DatePickerRange(id='my-date-picker-range',
                                        min_date_allowed=dt(1995, 8, 5),
                                        max_date_allowed=dt.now(),
                                        initial_visible_month=dt.now(),
                                        end_date=dt.now().date()),
                ],
                         className="date"),
                html.Div([ 
                    html.Button(
                        "Stock Price", className="stock-btn", id="stock"),
                    dcc.Input(id="n_days",
                              type="text",
                              placeholder="number of days"),
                    html.Button(
                        "Forecast", className="forecast-btn", id="forecast")
                ],
                         className="buttons"),
            ],
            className="nav"),

        # content
        html.Div(
            [
                html.Div(
                    [  # header
                        html.Img(id="logo"),
                        html.P(id="ticker")
                    ],
                    className="header"),
                html.Div(id="description", className="decription_ticker"),
                html.Div([], id="graphs-content"),
                html.Div([], id="main-content"),
                html.Div([], id="forecast-content")
            ],
            className="content"),
    ],
    className="container")

# callback for company info
@app.callback([ 
    Output("description", "children"),
    Output("logo", "src"),
    Output("ticker", "children"),
    Output("stock", "n_clicks"),
    Output("forecast", "n_clicks")
], [Input("submit", "n_clicks")], 
   [State("dropdown_tickers", "value")]
)
def update_company_info(n_clicks, selected_ticker):
    if n_clicks is None or selected_ticker is None:
        return (
            "Hey there! Please enter a legitimate stock code to get details.",
            "https://cdn5.vectorstock.com/i/1000x1000/56/94/bull-and-bear-symbols-stock-market-trends-vector-32005694.jpg",
            "Vector Stocks Pvt. Ltd",
            None,
            None
        )
    else:
        ticker = yf.Ticker(selected_ticker)
        info = ticker.info
        logo_url = info.get('logo_url', None)
        short_name = info.get('shortName', '')
        long_summary = info.get('longBusinessSummary', '')
        
        return (
            long_summary,
            logo_url,
            short_name,
            None,
            None
        )

# callback for stocks graphs
@app.callback([ 
    Output("graphs-content", "children"),
], [
    Input("stock", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])
def stock_price(n, start_date, end_date, val):
    if n == None:
        return [""]
    if val == None:
        raise PreventUpdate
    else:
        if start_date != None:
            df = yf.download(val, str(start_date), str(end_date))
        else:
            df = yf.download(val)

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig)]


# callback for forecast
@app.callback([Output("forecast-content", "children")],
              [Input("forecast", "n_clicks")],
              [State("n_days", "value"),
               State("dropdown_tickers", "value")])
def forecast(n, n_days, val):
    if n == None:
        return [""]
    if val == None:
        raise PreventUpdate
    fig = prediction(val, int(n_days) + 1)
    return [dcc.Graph(figure=fig)]

if __name__ == "__main__":
    app.run(debug=True)
