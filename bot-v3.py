#!/usr/bin/python
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import random
import sys
import socket
import json
import time

order_no = 1

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name = "RFLESERIU"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False
stonks = {'valbz':[], 'vale': [], 'xlf': [], 'bond': [],  'gs': [], 'ms': [], 'wfc': []}
orderid = 0

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index = 0
prod_exchange_hostname = "production"

port = 25000 + (tesat_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile("rw", 1)


def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    return json.loads(exchange.readline())

# ~~~~~============== NETWORKING CODE ==============~~~~~

def analyze(exchange):
    count = 0
    print ("Updating Server info...")
    while(count<1000):
        info = read_from_exchange(exchange)
        if not info:
            break
        type = info["type"]
        if(type == "close"):
            print ("Server closed.")
            return
        if(type == "trade"):
            
            if(info["symbol"] == "VALBZ"):
                stonks['valbz'].append(info["price"])
                
            if(info["symbol"] == "VALE"):
                stonks['vale'].append(info["price"])

            if (info["symbol"] == "XLF"):
                stonks['xlf'].append(info["price"])

            if (info["symbol"] == "BOND"):
                stonks['bond'].append(info["price"])

            if (info["symbol"] == "GS"):
                stonks['gs'].append(info["price"])

            if (info["symbol"] == "MS"):
                stonks['ms'].append(info["price"])

            if (info["symbol"] == "WFC"):
                stonks['wfc'].append(info["price"])

        time.sleep(0.01)
        count += 1

def mean(val):
    return sum(val)//len(val)


def ADRSignal(val1, val2):
    meanVal1 = mean(val1)
    meanVal2 = mean(val2)
    if meanVal2 - meanVal1 >= 2:
        return [True, meanVal1, meanVal2]
    else:
        return [False, meanVal1, meanVal2]

def strategy(XLF_trade_price, bond_trade_price, GS_trade_price, MS_trade_price, WFC_trade_price):

    XLF_mean = mean(XLF_trade_price)
    bond_mean = mean(bond_trade_price)
    GS_mean = mean(GS_trade_price)
    MS_mean = mean(MS_trade_price)
    WFC_mean = mean(WFC_trade_price)

    #find long etf arbitrage opportunities
    if 10 * XLF_mean + 150 < (3 * bond_mean + 2 * GS_mean + 3 * MS_mean + 2 * WFC_mean):
        return ["long", XLF_mean, bond_mean, GS_mean, MS_mean, WFC_mean]
    #find short etf arbitrage opportunites
    if 10 * XLF_mean - 150 > (3 * bond_mean + 2 * GS_mean + 3 * MS_mean + 2 * WFC_mean):
        return ["short", XLF_mean, bond_mean, GS_mean, MS_mean, WFC_mean]


def action(exchange,vale, valbz, xlf, bond, gs, ms, wfc):
    global orderid

    if(len(vale) >= 10 and len(valbz) >= 10):
        vale = vale[-10:]
        valbz = valbz[-10:]
        result = ADRSignal(valbz, vale)
        if(result != None and result[0] == True):
            print ("\n------------------------- ADR Make Action!-------------------------\n")
            orderid +=1
            write_to_exchange(exchange, {"type" : "add", "order_id": orderid, "symbol": "VALE", "dir" : "BUY",
                                         "price": result[1]+1, "size": 10})
            
            orderid +=1
            write_to_exchange(exchange, {"type" : "convert", "order_id": orderid, "symbol": "VALE", "dir" : "SELL",
                                         "size": 10})

            orderid +=1
            write_to_exchange(exchange, {"type" : "add", "order_id": orderid, "symbol": "VALBZ", "dir" : "SELL",
                                         "price": result[2]-1, "size": 10})

    #ETF arbitrage trading
    if (len(xlf) >25 and len(bond) >= 25 and len(gs) >= 25 and len(ms) >= 25 and len(wfc) >= 25):
        xlf = xlf[-25:]
        bond = bond[-25:]
        gs = gs[-25:]
        ms = ms[-25:]
        wfc = wfc[-25:]
        etf = strategy(xlf, bond, gs, ms, wfc)
        if (etf != None and etf[0] == 'long'):
            print("\n------------------------- ETF Long Make Action!-------------------------\n")
            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "XLF", "dir": "BUY",
                                         "price": etf[1] + 1, "size": 100})

            orderid += 1
            write_to_exchange(exchange,
                              {"type": "convert", "order_id": orderid, "symbol": "XLF", "dir": "SELL", "size": 100})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "BOND", "dir": "SELL",
                                         "price": etf[2] - 1, "size": 30})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "GS", "dir": "SELL",
                                         "price": etf[3] - 1, "size": 20})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "MS", "dir": "SELL",
                                         "price": etf[4] - 1, "size": 30})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "WFC", "dir": "SELL",
                                         "price": etf[5] - 1, "size": 20})

        if (etf != None and etf[0] == 'short'):
            print("\n------------------------- ETF SHORT Make Action!-------------------------\n")
            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "BOND", "dir": "BUY",
                "price": etf[2] - 1, "size": 30})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "GS", "dir": "BUY",
                                         "price": etf[3] - 1, "size": 20})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "MS", "dir": "BUY",
                                          "price": etf[4] - 1, "size": 30})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "WFC", "dir": "BUY",
                                         "price": etf[5] - 1, "size": 20})

            orderid += 1
            write_to_exchange(exchange,
                               {"type": "convert", "order_id": orderid, "symbol": "XLF", "dir": "BUY", "size": 100})

            orderid += 1
            write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "XLF", "dir": "SELL",
                                          "price": etf[1] + 1, "size": 100})


# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    global order_no
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    while(True):
        analyze(exchange)
        action(exchange,stonks['vale'], stonks['valbz'], stonks['xlf'], stonks['bond'], stonks['gs'], stonks['ms'], stonks['wfc'])


if __name__ == "__main__":
    main()