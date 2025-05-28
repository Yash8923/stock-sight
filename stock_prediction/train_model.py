from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Dense, LSTM
from tensorflow.keras.callbacks import EarlyStopping
import joblib

# Step 1: Fetch Data using Alpha Vantage
api_key = "IMX52D8BMBPYMHJP"
symbol = "INFY.BSE"

ts = TimeSeries(key=api_key, output_format='pandas')
data, _ = ts.get_daily(symbol=symbol, outputsize='full')  # 'full' = long history

# Reverse to chronological order
data = data[::-1]

if data.empty:
    raise ValueError("No data fetched for the symbol.")

# Step 2: Preprocess
close_prices = data["4. close"].values.reshape(-1, 1)
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(close_prices)

X, y = [], []
for i in range(50, len(scaled_data)):
    X.append(scaled_data[i-50:i, 0])
    y.append(scaled_data[i, 0])

X, y = np.array(X), np.array(y)
X = X.reshape((X.shape[0], X.shape[1], 1))

# Step 3: Build LSTM model
model = Sequential()
model.add(Input(shape=(X.shape[1], 1), name='input_layer'))
model.add(LSTM(64, return_sequences=True))
model.add(LSTM(32))
model.add(Dense(1))

model.compile(optimizer='adam', loss='mean_squared_error')

# Step 4: Train model
model.fit(X, y, epochs=10, batch_size=32, callbacks=[EarlyStopping(patience=3)])

# Step 5: Save model and scaler
model.save("stock_prediction_model.h5")
joblib.dump(scaler, "scaler.pkl")

print("Model training complete and saved.")