#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_helper import ShoonyaApiPy
import datetime
import logging
import time
#import yaml
import pandas as pd
from time import sleep
#sample
logging.basicConfig(level=logging.DEBUG)
from pyotp import TOTP

#flag to tell us if the websocket is open
socket_opened = False

#application callbacks
def event_handler_order_update(message):
    print("order event: " + str(message))


SYMBOLDICT = {}
def event_handler_quote_update(message):
    global SYMBOLDICT
    #e   Exchange
    #tk  Token
    #lp  LTP
    #pc  Percentage change
    #v   volume
    #o   Open price
    #h   High price
    #l   Low price
    #c   Close price
    #ap  Average trade price

    #if 'lp' not in message:
       # print("\n key 'ltq' NOT found") 
    #if 'lp' in message:
       # print("\n key 'ltq' IS found") 
    #print("The message is \n", message)

    print("quote event: {0}".format(time.strftime('%d-%m-%Y %H:%M:%S')) + str(message))
    
    key = message['e'] + '|' + message['tk']

    if key in SYMBOLDICT:
        symbol_info =  SYMBOLDICT[key]
        symbol_info.update(message)
        SYMBOLDICT[key] = symbol_info
    else:
        SYMBOLDICT[key] = message

    print(SYMBOLDICT[key])

def open_callback():
    global socket_opened
    socket_opened = True
    print('app is connected')
    
    #api.subscribe("NSE|26000", feed_type='d')
    #api.subscribe(["NSE|22","NSE|13","BSE|522032"], feed_type='d')
    #api.subscribe(["NSE|22","NSE|13"], feed_type='d')
    api.subscribe(["NSE|20734"], feed_type='d')
    #api.subscribe(["C:\\Users\\pkansal\\Desktop\\ShoonyaApi-py-master\\BSE_symbols.txt"], feed_type='d')

#end of callbacks

def get_time(time_string):
    data = time.strptime(time_string,'%d-%m-%Y %H:%M:%S')

    return time.mktime(data)

user_id_input = 'FA181965'
vendor_code_input = 'FA181965_U'
password_input = 'SpkKpk@8883'
token_input = 'HE474553XO7D2O2Y4GJ5VBNQSRO7545B'
api_key_input = '0bb6bef472587f083bc2b83c0401a0aa'

#imei_key_input is the MAC address of the laptop
imei_key_input = '04:7C:16:A8:7F:60'

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

if ret != None:   
    ret = api.start_websocket(order_update_callback=event_handler_order_update, subscribe_callback=event_handler_quote_update, socket_open_callback=open_callback)
    while True:
        if socket_opened == True:
            print('q => quit')
            
            print('r => ')
            prompt1=input('what shall we do? ').lower()    
            if prompt1 == 's':
                print('closing websocket')
                api.close_websocket()
                continue
            if prompt1 == 'r':
                print('closing websocket')
                api.close_websocket()
                sleep(1)
                api.start_websocket(order_update_callback=event_handler_order_update, subscribe_callback=event_handler_quote_update, socket_open_callback=open_callback)            
                continue
            else:
                print('Fin') #an answer that wouldn't be yes or no
                break   

        else:
            continue

