import plotly.graph_objects as go  # root objects
from plotly.subplots import make_subplots  # to create multiple subplots
import pandas as pd


def get_subplot_configuration(show_stock_value: bool, show_account_value: bool, show_trades: bool) \
        -> (tuple, int):
    rows = []
    cols = 1

    if show_stock_value:
        rows.append("Stock Value")

    if show_account_value:
        rows.append("Account Value")

    if show_trades:
        rows.append("Trades")

    return tuple(rows), cols


def show_backtest(backtest, stock_symbol: str, start_date: str = "", end_date: str = "",
                  stock_df: pd.DataFrame = pd.DataFrame({"close": []}),
                  show_stock_value=True, show_account_value=True, show_trades=True):

    # only show stock_vale when there is data available
    if len(stock_df.index) == 0:
        show_stock_value = False

    rows, cols = get_subplot_configuration(show_stock_value, show_account_value, show_trades)

    backtest.history_and_returns["history"]["time"] = pd.to_datetime(
        backtest.history_and_returns["history"]["time"], unit="s")

    all_figs = make_subplots(rows=len(rows), cols=cols, row_titles=rows, shared_xaxes=True)

    row = 1
    if show_stock_value:
        all_figs.add_trace(go.Scatter(x=stock_df.index,
                                      y=stock_df["close"].values,
                                      name="Stock Value", mode="lines", showlegend=False), row=row, col=1)

        for colume in stock_df.columns:
            if colume not in ['open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap']:
                all_figs.add_trace(go.Scatter(x=stock_df.index,
                                              y=stock_df[colume].values,
                                              name=colume, mode="lines", showlegend=True), row=row, col=1)
        row += 1

    if show_account_value:
        # other possibility: backtest.history_and_returns["resampled_account_value"]
        all_figs.add_trace(go.Scatter(x=backtest.history_and_returns["history"]["time"].values,
                                      y=backtest.history_and_returns["history"]["Account Value (USD)"].values,
                                      name="Account Value", mode="lines", showlegend=False), row=row, col=1)
        row += 1

    if show_trades:
        all_figs.add_trace(go.Scatter(x=backtest.history_and_returns["history"]["time"].values,
                                      y=backtest.history_and_returns["history"][stock_symbol].values,
                                      name="Trades", mode="lines", showlegend=False), row=row, col=1)
        row += 1

    all_figs.show()
    print("\ninformation to", stock_symbol)

    # show dates when given
    if start_date != "":
        print(" " * 5, "start_date:", start_date)
    if end_date != "":
        print(" " * 5, "end_date:", end_date)
    print()

    m = backtest.get_metrics()
    for name in m:
        print(" " * 5, m[name]["display_name"] + ": " + str(m[name]["value"]))

