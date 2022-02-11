from binance import Client
import pandas as pd
import ta
import numpy as np
import time
import pandas_ta

api_secret = 'kqo5vCzqaQUjhsIsdeqrbawKPFUd6TYVvaqcPggxDZWfPZTWfAB4SVXuHWRymRXo'
api_key = 'oicPKWPW9v7UfaFUOj7H9yZB8oO5EbTdicm1KXZI4M0D2ory42Ic6E3lsAUwZYcP'
client = Client(api_key, api_secret)

def GetMinuteData(symbol, interval, lookback):
	frame = pd.DataFrame(client.futures_historical_klines(symbol, interval, lookback + ' min ago UTC'))
	frame = frame.iloc[:,:6]
	frame.columns = ['Time','Open','High','Low','Close','Volume']
	frame = frame.set_index('Time')
	frame.index = pd.to_datetime(frame.index, unit='ms')
	frame = frame.astype(float)
	return frame
	
def applytechnicals(df):
	df['ema8'] = ta.trend.ema_indicator(df.Close, window=8)
	df['ema13'] = ta.trend.ema_indicator(df.Close, window=13)
	df['ema50'] = ta.trend.ema_indicator(df.Close, window=50)
	df['ATR'] = ta.volatility.average_true_range(df.High, df.Low, df.Close)
	df['rsi'] = ta.momentum.rsi(df.Close)
	df['macd'] = ta.trend.macd_diff(df.Close, window_slow=50, window_fast=8, window_sign=8)
	df.dropna(inplace=True)

class Signals:
	def __init__(self, df):
		self.df = df	
	def decide(self):
		self.df['Buy'] = np.where((self.df.Close.iloc[-2] > self.df.ema8[-2])
							   & (self.df.ema8[-2] > self.df.ema50[-2])
		                       & (self.df.Close[-2] > self.df.ema50[-2])
		                       & ((self.df.Close[-2] - self.df.Open[-2]) < (self.df.ATR[-2] * 2))
		                       & (self.df.Open.iloc[-2] < self.df.Close.iloc[-2])
		                       & (self.df.Open.iloc[-3] < self.df.Low.iloc[-2])
		                       & (self.df.macd > 0), 1, 0)
		self.df['Sell'] = np.where((self.df.ema8[-2] > self.df.Close.iloc[-2])
		                       & (self.df.Open[-2] < self.df.ema50)
		                       & (self.df.ema8[-2] < self.df.ema50[-2])
		                       & ((self.df.Open[-2] - self.df.Close[-2]) < (self.df.ATR[-2] * 2))
		                       & (self.df.Open.iloc[-2] > self.df.Close.iloc[-2])
		                       & (self.df.Open.iloc[-3] > self.df.High.iloc[-2])
		                       & (self.df.macd < 0), 1, 0)
	                          	
'''df = GetMinuteData('ETHUSDT', '1m', '100')
applytechnicals(df)
inst = Signals(df)
inst.decide()
print(df.to_string())'''
#dfx = df.loc[(df.index > pd.to_datetime('1639953910', unit='s')) > (df.index > pd.to_datetime('1639951210', unit='s'))]
#print(dfx.to_string())

	                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          	
def strategy(pair, qty):
	df = GetMinuteData('ETHUSDT', '5m', '1000')
	applytechnicals(df)
	inst = Signals(df)
	inst.decide()
	print(f'Current Close is '+str(df.Close.iloc[-1]))

	if df.Buy.iloc[-1]:
		buyprice = df.Close.iloc[-1]
		order = client.futures_create_order(symbol=pair, 
		                            side='BUY',
		                            type='MARKET',
		                            quantity=qty)
		print(order)
		while True:
			time.sleep(1)
			df = GetMinuteData('ETHUSDT', '5m', '1000')
			applytechnicals(df)
			inst = Signals(df)
			inst.decide()
			print(f'Current Close is '+str(df.Close.iloc[-1]))
			if (buyprice + (df.ATR.iloc[-1] * 0.7)) < df.Close.iloc[-1]:
				order = client.futures_create_order(symbol=pair, 
		                            side='SELL',
		                            type='MARKET',
		                            quantity=qty)
				print(order)
				while True:
					time.sleep(5)
					df = GetMinuteData('ETHUSDT', '5m', '1000')
					applytechnicals(df)
					inst = Signals(df)
					inst.decide()
					if df.rsi.iloc[-2] < 50:
						break
				break
			if (buyprice - (df.ATR.iloc[-1] * 0.7)) > df.Close.iloc[-1]:
				order = client.futures_create_order(symbol=pair, 
		                            side='SELL',
		                            type='MARKET',
		                            quantity=qty)
				print(order)
				while True:
					time.sleep(5)
					df = GetMinuteData('ETHUSDT', '5m', '1000')
					applytechnicals(df)
					inst = Signals(df)
					inst.decide()
					if df.rsi.iloc[-2] < 50:
						break	
				break
	if df.Sell.iloc[-1]:
		sellprice = df.Close.iloc[-1]
		order = client.futures_create_order(symbol=pair, 
		                           side='SELL',
		                            type='MARKET',
		                            quantity=qty)
		print(order)
		while True:
			time.sleep(1)
			df = GetMinuteData('ETHUSDT', '5m', '1000')
			applytechnicals(df)
			inst = Signals(df)
			inst.decide()
			print(f'Current Close is '+str(df.Close.iloc[-1]))
			if (sellprice - (df.ATR.iloc[-1] * 0.7)) > df.Close.iloc[-1]:
				order = client.futures_create_order(symbol=pair, 
		                            side='BUY',
		                            type='MARKET',
		                            quantity=qty)
				print(order)
				while True:
					time.sleep(5)
					df = GetMinuteData('ETHUSDT', '5m', '3000')
					applytechnicals(df)
					inst = Signals(df)
					inst.decide()
					if df.rsi.iloc[-2] > 50:
						break
				break
			if sellprice + (df.ATR.iloc[-1] * 0.7) < df.Close.iloc[-1]:
				order = client.futures_create_order(symbol=pair, 
		                            side='BUY',
		                            type='MARKET',
		                            quantity=qty)
				print(order)
				while True:
					time.sleep(5)
					df = GetMinuteData('ETHUSDT', '5m', '3000')
					applytechnicals(df)
					inst = Signals(df)
					inst.decide()
					if df.rsi.iloc[-2] > 50:
						break	
				break
			
while True:
	strategy('ETHUSDT', 0.03)
	time.sleep(1)