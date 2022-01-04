from binance import Client
import pandas as pd
import ta
import numpy as np
import time

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
	
def applytechnicals(df, dx):
	df['ema3'] = ta.trend.ema_indicator(df.Close, window=3)
	df['ema6'] = ta.trend.ema_indicator(df.Close, window=6)
	df['ema9'] = ta.trend.ema_indicator(df.Close, window=9)
	df['rsi'] = ta.momentum.rsi(df.Close, window=9)
	df['ATR'] = ta.volatility.average_true_range(df.High, df.Low, df.Close, window=14)
	df['macd'] = ta.trend.macd_diff(df.Close, window_slow=18, window_fast=7, window_sign=9)
	df.dropna(inplace=True)
	dx['ema3'] = ta.trend.ema_indicator(dx.Close, window=3)
	dx['ema6'] = ta.trend.ema_indicator(dx.Close, window=6)
	dx['ema9'] = ta.trend.ema_indicator(dx.Close, window=9)
	dx['rsi'] = ta.momentum.rsi(dx.Close, window=9)
	dx['ATR'] = ta.volatility.average_true_range(dx.High, dx.Low, dx.Close, window=14)
	dx.dropna(inplace=True)

class Signals:
	def __init__(self, df, dx):
		self.df = df
		self.dx = dx	
	def decide(self):
		self.df['Buy'] = np.where((self.df.ema3[-1] > self.df.ema9[-1])
		                       & (self.df.ema6[-1] > self.df.ema9[-1])
		                       & (self.df.ema3[-1] > self.df.ema6[-1])
		                       & (self.df.rsi > 50)
		                       & (self.df.Open.iloc[-2] < self.df.Close.iloc[-2])
		                       & (self.df.High[-2] < self.df.Close), 1, 0)
		self.df['Sell'] = np.where((self.df.ema3[-1] < self.df.ema9[-1])
		                          & (self.df.ema6[-1] < self.df.ema9[-1])
		                          & (self.df.ema3[-1] < self.df.ema6[-1])
	                          	& (self.df.rsi < 50)
	                          	& (self.df.Open.iloc[-2] > self.df.Close.iloc[-2])
	                          	& (self.df.Low[-2] > self.df.Close), 1, 0)
		self.dx['HBuy'] = np.where((self.dx.ema3 > self.dx.ema9)
		                       & (self.dx.ema6 > self.dx.ema9)
		                       & (self.dx.ema3 > self.dx.ema6)
		                       & (self.dx.rsi > 50)
		                       , 1, 0)
		self.dx['HSell'] = np.where((self.dx.ema3 < self.dx.ema6)
	                          	& (self.dx.ema3 < self.dx.ema9)
	                          	& (self.dx.ema6 < self.dx.ema9)
	                          	& (self.dx.rsi < 50), 1, 0)
'''df = GetMinuteData('ETHUSDT', '5m', '10')
applytechnicals(df)
inst = Signals(df)
inst.decide()
print(df.to_string())
dfx = df.loc[(df.index > pd.to_datetime('1639953910', unit='s')) > (df.index > pd.to_datetime('1639951210', unit='s'))]
print(dfx.to_string())'''

	                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          		                          	
def strategy(pair, qty):
	df = GetMinuteData('ETHUSDT', '5m', '600')
	dx = GetMinuteData('ETHUSDT', '15m', '1200')
	applytechnicals(df, dx)
	inst = Signals(df, dx)
	inst.decide()
	print(f'Current Close is '+str(df.Close.iloc[-1]))

	if df.Buy.iloc[-1] and dx.HBuy.iloc[-1]:
		buyprice = df.Close.iloc[-1]
		order = client.futures_create_order(symbol=pair, 
		                            side='BUY',
		                            type='MARKET',
		                            quantity=qty)
		print(order)
		while True:
			time.sleep(2)
			df = GetMinuteData(pair, '1m', '600')
			dx = GetMinuteData(pair, '15m', '1200')
			applytechnicals(df, dx)
			inst = Signals(df, dx)
			inst.decide()
			dfx = df.loc[df.index > pd.to_datetime(order['updateTime'], unit='ms')]
			dfx = dfx.copy()
			if len(dfx) > 0:
				dfx['B1'] = dfx.High.cummax()
				dfx['TSL1'] = dfx.B1 - (dfx.ATR * 2)
				print(f'Current Stop is '+str(dfx.TSL1.iloc[-1]))
				if dfx.Close.iloc[-1] < dfx.TSL1.iloc[-1]:
					order = client.futures_create_order(symbol=pair, 
		                            side='SELL',
		                            type='MARKET',
		                            quantity=qty)
					print(order)	
					while True:
						time.sleep(5)
						df = GetMinuteData(pair, '5m', '600')
						dx = GetMinuteData(pair, '15m', '1200')
						applytechnicals(df, dx)
						inst = Signals(df, dx)
						inst.decide()
						dfx = df.loc[df.index > pd.to_datetime(order['updateTime'], unit='ms')]
						dfx = dfx.copy()
						if len(dfx) > 0:
							break
					break
	if df.Sell.iloc[-1] and dx.HSell.iloc[-1]:
		sellprice = df.Close.iloc[-1]
		order = client.futures_create_order(symbol=pair, 
		                           side='SELL',
		                            type='MARKET',
		                            quantity=qty)
		print(order)
		while True:
			time.sleep(2)
			df = GetMinuteData(pair, '1m', '600')
			dx = GetMinuteData(pair, '15m', '1200')
			applytechnicals(df, dx)
			inst = Signals(df, dx)
			inst.decide()		
			dfx = df.loc[df.index > pd.to_datetime(order['updateTime'], unit='ms')]
			dfx = dfx.copy()
			if len(dfx) > 0:
				dfx['B2'] = dfx.Low.cummin()
				dfx['TSL2'] = dfx.B2 + (dfx.ATR * 2)
				print(f'Current Stop is '+str(dfx.TSL2.iloc[-1]))
				if dfx.Close.iloc[-1] > dfx.TSL2.iloc[-1]:	
					order = client.futures_create_order(symbol=pair, 
		                            			side='BUY',
		                           			 type='MARKET',
		                           			 quantity=qty)
					print(order)
					while True:
						time.sleep(5)
						df = GetMinuteData(pair, '5m', '600')
						dx = GetMinuteData(pair, '15m', '1200')
						applytechnicals(df, dx)
						inst = Signals(df, dx)
						inst.decide()
						dfx = df.loc[df.index > pd.to_datetime(order['updateTime'], unit='ms')]
						dfx = dfx.copy()
						if len(dfx) > 0:
							break
					break
			
while True:
	strategy('ETHUSDT', 0.01)
	time.sleep(2)