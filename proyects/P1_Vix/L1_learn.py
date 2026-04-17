import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

load_dotenv()

api_key = os.getenv("APCA_API_KEY_ID")
secret_key = os.getenv("APCA_API_SECRET_KEY")

print(api_key)
client = StockHistoricalDataClient(api_key, secret_key)


# gets the dara from alpaca and stores it in a df
def get_data():
    bars = client.get_stock_bars(request_params)
    df = bars.df.reset_index()
    return df


# with a df get the values that we want to analize and give us X and y to train the model
def clean_data(df):
    df["return"] = df["close"].pct_change()
    df["volatility"] = df["return"].rolling(5).std()
    df["ma_5"] = df["close"].rolling(5).mean()
    df["ma_10"] = df["close"].rolling(10).mean()
    df["ma_20"] = df["close"].rolling(20).mean()

    df["target"] = df["close"].shift(-1)
    df = df.dropna()
    print(df.head())

    features = [
        "close",
        "return",
        "volatility",
        "ma_5",
        "ma_10",
        "ma_20",
    ]

    X = df[features]
    y = df["target"]

    return X, y


# trains a model based on data already given and cleaned X, y, and prints it
def train_model_clean_data(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"Mean Absolute Error: of {i} is ${mae:.2f}")

    plt.plot(y_test.values, label="Actual price")
    plt.plot(preds, label="predicted price")
    plt.title(f"{i} price prediction")
    plt.xlabel("time")
    plt.ylabel("price")


SYMBOLS = ["NVDA", "AAPL", "AMZN", "SONO", "NCLH"]

for i in SYMBOLS:
    SYMBOL = i
    START_DATE = "2022-01-01"
    END_DATE = "2026-02-20"
    client = StockHistoricalDataClient(api_key, secret_key)

    request_params = StockBarsRequest(
        symbol_or_symbols=SYMBOL,
        timeframe=TimeFrame.Day,
        start=START_DATE,
        end=END_DATE,
    )
    df = get_data()
    X, y = clean_data(df)
    train_model_clean_data(X, y)

plt.legend()
plt.show()
