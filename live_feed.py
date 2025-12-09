#!/usr/bin/env python3

import os
from pathlib import Path
import csv
import pandas as pd
import time
from datetime import datetime, timedelta, date, time
import requests as rq
from pyotp import TOTP
from time import sleep
import json
from collections import defaultdict
import asyncio
import statistics
import numpy as np
import math
from tabulate import tabulate

from api_helper import ShoonyaApiPy
import logging

OPT_STRIKE_SUBSCRIBE = False
TIME_FRAME = 1		# in minute
REQUEST_INTERVAL = 0.1 #should be greater than 0.1sec
#---------------------------------LOGIN--------------------------------#

user_id_input = 
vendor_code_input = 
password_input = 
token_input = 
api_key_input = 

#imei_key_input is the MAC address of the laptop
imei_key_input = 

#enter the otp received to the mobile
#otp_input = '17891'

#enable dbug to see request and responses
logging.basicConfig(level=logging.DEBUG)

 #start of our program
api = ShoonyaApiPy()

#credentials
user        = user_id_input
pwd         = password_input
factor2     = token_input
vc          = vendor_code_input
app_key     = api_key_input
imei        = imei_key_input

otp = TOTP(factor2).now().zfill(6)


ret = api.login(userid=user, password=pwd, twoFA=otp, vendor_code=vc, api_secret=app_key, imei=imei)
#print(ret)
print('\n\n')
#---------------------------------LOGIN--------------------------------#

#----------------------------VARIABLES-------------------------------#
NIFTY_50 = []
STRIKES_COUNT = 10
CALL_STRIKE_TOKEN = []
PUT_STRIKE_TOKEN = []
FINAL_EXCH_OPT_TOKEN = []
NIFTY_STRIKE_PRICE_STEP = 50

today = datetime.now().date()
starting_time = datetime.now().time()
current_time = datetime.now().time()
open_time = time(9,16,0)   #not 9:15:00. you can request time series data if starting_time is greater than 9:16:00 to get time_price_series

TF_1MIN = timedelta(hours=0, minutes=1, seconds=0)
TF_START_1MIN = datetime.combine(today, time(9, 15, 0))
TF_END_1MIN = datetime.combine(today, time(9, 16, 2))

if starting_time > open_time:
	while TF_END_1MIN <= datetime.combine(today, current_time):
		TF_START_1MIN += TF_1MIN
		TF_END_1MIN += TF_1MIN
#----------------------------VARIABLES-------------------------------#

#-------------------------------FETCH EXPIRY-------------------------------#
week = { 'MONDAY': 0, 'TUESDAY': 1, 'WEDNESDAY': 2, 'THURSDAY': 3, 'FRIDAY': 4, 'SATURDAY': 5, 'SUNDAY': 6 }
NIFTY_EXPIRY = week['TUESDAY']
EXPIRY_TODAY = False

def find_nifty_expiry_date():
	global EXPIRY_TODAY
	
	today = datetime.now().date()
	days_ahead = (NIFTY_EXPIRY - today.weekday()) % 7
	if days_ahead == 0:
		days_ahead = 7
	
	expiry_date = today + timedelta(days=days_ahead)
	expiry_str = expiry_date.strftime("%d%b%y").upper()
	
	EXPIRY_TODAY = (today.weekday() == NIFTY_EXPIRY)
	
	return expiry_str, EXPIRY_TODAY


# Example usage
NIFTY_EXPIRY_DATE, EXPIRY_TODAY = find_nifty_expiry_date()
print(NIFTY_EXPIRY_DATE, EXPIRY_TODAY)

#-------------------------------FETCH EXPIRY-------------------------------#

#-------------------------------NFO SYMBOLS---------------------------------#
# Load CSV once
symbolsDF = pd.read_csv('https://api.Shoonya.com/NFO_symbols.txt.zip', skipinitialspace=True)

def get_exchange_token_by_symbol(trading_symbol):
	"""
	Returns Exchange and Token for a given TradingSymbol.
	"""
	row = symbolsDF[symbolsDF['TradingSymbol'] == trading_symbol]
	if not row.empty:
		exchange = row.iloc[0]['Exchange']
		token = row.iloc[0]['Token']
		return exchange, token
	else:
		return None, None  # symbol not found
#-------------------------------NFO SYMBOLS---------------------------------#

#-------------------------------EXTRACT STRIKE PRICE TOKEN------------------------#
def extract_strike_price_token(value):
	global instruments
	global CALL_STRIKE_TOKEN
	global PUT_STRIKE_TOKEN
	global FINAL_EXCH_OPT_TOKEN

	call_strike_price = []
	call_strike_name = []
	put_strike_price = []
	put_strike_name = []

	i = 0
	reference = value - (value % NIFTY_STRIKE_PRICE_STEP)
	while len(put_strike_price) < STRIKES_COUNT:
		if (reference - i * NIFTY_STRIKE_PRICE_STEP) < value:
			strike = reference - i * NIFTY_STRIKE_PRICE_STEP
			put_strike_price.append(strike)
			put_strike_name.append(f'NIFTY{NIFTY_EXPIRY_DATE}P{int(strike)}')
			exchange, token = (get_exchange_token_by_symbol(put_strike_name[-1]))
			
			if str(token) not in PUT_STRIKE_TOKEN:
				FINAL_EXCH_OPT_TOKEN.append({'exch': str(exchange), 'strike_price': put_strike_price[-1], 'token': str(token)})
				PUT_STRIKE_TOKEN.append({'exch': str(exchange), 'strike_price': put_strike_price[-1], 'token': str(token)})
				globals()[f'NIFTY{NIFTY_EXPIRY_DATE}P{int(strike)}'] = []
		i += 1
	
	i = 0
	while len(call_strike_price) < STRIKES_COUNT:
		if (reference + i * NIFTY_STRIKE_PRICE_STEP) > value:
			strike = reference + i * NIFTY_STRIKE_PRICE_STEP
			call_strike_price.append(strike)
			call_strike_name.append(f'NIFTY{NIFTY_EXPIRY_DATE}C{int(strike)}')
			exchange, token = (get_exchange_token_by_symbol(call_strike_name[-1]))
			
			if str(token) not in CALL_STRIKE_TOKEN:
				FINAL_EXCH_OPT_TOKEN.append({'exch': str(exchange), 'strike_price': put_strike_price[-1], 'token': str(token)})
				CALL_STRIKE_TOKEN.append({'exch': str(exchange), 'strike_price': call_strike_price[-1], 'token': str(token)})
				globals()[f'NIFTY{NIFTY_EXPIRY_DATE}C{int(strike)}'] = []
		i += 1
#-------------------------------EXTRACT STRIKE PRICE TOKEN------------------------#

#---------------------------GET_TIME_PRICE_SERIES----------------------------#
def get_time_price_series_data(exch, tk):
	lastBusDay = datetime.today()
	lastBusDay = lastBusDay.replace(hour=9, minute=15, second=0, microsecond=0)
	ret = api.get_time_price_series(exchange=exch, token=tk, starttime=lastBusDay.timestamp(), interval=TIME_FRAME)
	return ret
#---------------------------GET_TIME_PRICE_SERIES----------------------------#

ret = api.get_quotes(exchange='NSE', token='26000')
print(ret['lp'])
sleep(REQUEST_INTERVAL)

extract_strike_price_token(float(ret['lp']))
print('FINAL_EXCH_OPT_TOKEN: ', FINAL_EXCH_OPT_TOKEN)
#print('FINAL_EXCH_OPT_TOKEN: ', FINAL_EXCH_OPT_TOKEN)
#print('CALL_STRIKE_TOKEN: ', CALL_STRIKE_TOKEN)
#print('PUT_STRIKE_TOKEN: ', PUT_STRIKE_TOKEN)

if starting_time > open_time:
	value = get_time_price_series_data('NSE', '26000')
	NIFTY_50 = value[::-1]
	sleep(REQUEST_INTERVAL)
	
	for item in CALL_STRIKE_TOKEN:
		value = get_time_price_series_data(item['exch'], item['token'])
		stk = int(item['strike_price'])
		globals()[f'NIFTY{NIFTY_EXPIRY_DATE}C{stk}'] = value[::-1]
		sleep(REQUEST_INTERVAL)

	for item in PUT_STRIKE_TOKEN:
		value = get_time_price_series_data(item['exch'], item['token'])
		stk = int(item['strike_price'])
		globals()[f'NIFTY{NIFTY_EXPIRY_DATE}P{stk}'] = value[::-1]
		sleep(REQUEST_INTERVAL)
		print('TF_START_1MIN: ', TF_START_1MIN)
		print('TF_END_1MIN: ', TF_END_1MIN)
		
while(True):
	current_time = datetime.now().time()
	
	if datetime.combine(today, current_time) > TF_END_1MIN:
		value = get_time_price_series_data('NSE', '26000')
		value = value[::-1]
		NIFTY_50.append(value[-1])
		sleep(REQUEST_INTERVAL)
		
		for item in CALL_STRIKE_TOKEN:
			value = get_time_price_series_data(item['exch'], item['token'])
			value = value[::-1]
			stk = int(item['strike_price'])
			globals()[f'NIFTY{NIFTY_EXPIRY_DATE}C{stk}'].append(value[-1])
			sleep(REQUEST_INTERVAL)

		for item in PUT_STRIKE_TOKEN:
			value = get_time_price_series_data(item['exch'], item['token'])
			value = value[::-1]
			stk = int(item['strike_price'])
			globals()[f'NIFTY{NIFTY_EXPIRY_DATE}P{stk}'].append(value[-1])
			sleep(REQUEST_INTERVAL)

		print('\n', 'NIFTY_50: ', NIFTY_50[-1])
		print('no. of candles: ', len(NIFTY_50))
		
#		for item in CALL_STRIKE_TOKEN:
#			stk = int(item['strike_price'])
#			print(f'NIFTY{NIFTY_EXPIRY_DATE}C{stk}: ', globals()[f'NIFTY{NIFTY_EXPIRY_DATE}C{stk}'])
		
		TF_START_1MIN += TF_1MIN
		TF_END_1MIN += TF_1MIN
		print('TF_START_1MIN: ', TF_START_1MIN)
		print('TF_END_1MIN: ', TF_END_1MIN)
