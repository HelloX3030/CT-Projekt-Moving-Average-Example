from blankly import Alpaca, Interface, Strategy, StrategyState

from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

import blankly_comfort_functions
from blankly_comfort_functions import show_backtest

import pandas as pd
from datetime import datetime, timedelta


# variables
SMA1 = 10
SMA2 = 50  # SMA2 needs to be bigger than SMA1
STOCK_SYMBOL = "MSFT"
START_DATE = "2019-06-01 0:0:0"
END_DATE = "2022-01-06 0:0:0"

start_date_plot = datetime.strptime(START_DATE, "%Y-%m-%d %H:%M:%S") - timedelta(days=int(SMA2 * 1.44))
START_DATE_PLOT = start_date_plot.strftime("%Y-%m-%d %H:%M:%S")


def get_stock_df() -> pd.DataFrame:
    stock_client = StockHistoricalDataClient(blankly_comfort_functions.alpaca_api_key,
                                             blankly_comfort_functions.alpaca_secret_api_key)
    request_params = StockBarsRequest(
        symbol_or_symbols=[STOCK_SYMBOL],
        timeframe=TimeFrame.Day,
        start=START_DATE_PLOT,
        end=END_DATE,
        # adjustment="all"
        # Huge Problem of blankly: Back-tests don´t use the adjusted close price of a stock!
        # this can cause completely different behaviour when a stock split happens
        # (and also don´t represent dividends)
        # There is no esy way around this problem, the only way would be to call the alpaca-api
        # manually and use the adjusted prices of a stock from them, but this would not simulate the
        # correct behaviour of the number of stocks owned by the user, only his return would be right
        # and his account value
        # also you would need to program manually a big part of the backtesting process, and when you
        # want to deploy it than on blankly you would again need to implement your algorithm completely
        # new

        # last: maybe they will add this feature later to there api
    )

    # get historical data
    new_stock_df = stock_client.get_stock_bars(request_params).df
    new_stock_df = new_stock_df.loc[(STOCK_SYMBOL,)]

    new_stock_df["SMA " + str(SMA1)] = new_stock_df["close"].rolling(SMA1).mean()
    new_stock_df["SMA " + str(SMA2)] = new_stock_df["close"].rolling(SMA2).mean()

    new_stock_df.dropna(inplace=True)
    return new_stock_df


# Bot Functions
def init(symbol, state: StrategyState):
    interface: Interface = state.interface
    # resolution: float = state.resolution
    variables = state.variables
    # initialize the historical data
    df = interface.history(symbol, start_date=START_DATE_PLOT, end_date=START_DATE)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    variables["history"] = df["close"]
    variables["has_bought"] = False


def price_event(price, symbol, state: StrategyState):
    interface: Interface = state.interface
    # resolution: float = state.resolution
    variables = state.variables
    variables["history"] = pd.concat([variables["history"], pd.Series([price])], ignore_index=True)
    variables["history"].drop(variables["history"].index[0], inplace=True)

    # calculate the sma (simple moving average)
    sma1 = variables["history"].iloc[-SMA1:].mean()
    sma2 = variables["history"].iloc[-SMA2:].mean()

    # process the price events

    # buy
    if sma2 > sma1 and not variables["has_bought"]:
        interface.market_order(symbol, 'buy', int(interface.cash / price))  # round the amount down
        variables["has_bought"] = True

    # sell
    elif sma2 < sma1 and variables["has_bought"]:
        interface.market_order(symbol, 'sell', int(interface.account[symbol].available))
        variables["has_bought"] = False


if __name__ == "__main__":
    # initialize strategy
    alpaca = Alpaca()
    strategy = Strategy(alpaca)
    strategy.add_price_event(price_event, symbol=STOCK_SYMBOL, resolution='1d', init=init)

    # backtest strategy
    backtest = strategy.backtest(initial_values={'USD': 10000},
                                 start_date=START_DATE, end_date=END_DATE)

    # get historical stock data
    stock_df = get_stock_df()

    # show backtest result
    show_backtest.show_backtest(backtest, STOCK_SYMBOL, START_DATE, END_DATE, stock_df)
