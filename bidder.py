import requests
import json
from random import random
import time
import websocket
import threading

# insert the auth key here
header = {"X-Starfighter-Authorization":
          "a7e60d9a71885feced35b223dfd65c65e977d236"}
baseurl = "https://api.stockfighter.io/ob/api"


def get_quote(venue, stock):
    """gets quote"""
    url = baseurl + "/venues/%s/stocks/%s/quote"%(venue, stock)
    get = requests.get(url, headers=header)
    return json.loads(get.content)


def get_order_status(order_id, venue, stock):
    url = baseurl + "/venues/%s/stocks/%s/orders/%s"%(venue, stock, order_id)
    get = requests.get(url, headers=header)
    return json.loads(get.content)


def order(account, venue, stock, price, qty, direction, orderType):
    """
    orders a stock. 
    account: string, you get this account number in level instructions for each
    attempt of a level
    venue, stock: whatever they mean
    price: integer, in cents
    qty: number of shares
    direction: "buy" or "sell"
    orderType: usually "limit", refer docs
    """
    data_all = {
            'account': account,
            'venue': venue,
            'stock': stock,
            'price': price,
            'qty': qty,
            'direction': direction,
            'orderType': orderType }
    #sanity
    data_filtered = { k: v for k, v in data_all.iteritems() if v is not None} 
    url = baseurl + "/venues/%s/stocks/%s/orders"%(venue, stock)
    print "ordering with data: ", data_filtered
    return json.loads(requests.post(url, headers=header, json=data_filtered).content)


def buy(account, venue, stock, price, qty, orderType):
    """wrapper to buy"""
    return order(account, venue, stock, price, qty, "buy", orderType)


def sell(account, venue, stock, price, qty, orderType):
    """wrapper to sell"""
    return order(account, venue, stock, price, qty, "sell", orderType)


def multiple_buy(account, venue, stock, price_qty_list, orderType,
                 randomness=0, sleep=0):
    """
    Buying multiple batches of stocks
    price_qty_list: pair of numbers for each batch
    eg: [ [3040, 20], [3120, 20], ...]
    experimental:
    randomness: introduce randomness in bid price, so as not to rouse
    suspiscion among others. might/or not work
    sleep: sleep between requests, seconds
    """
    for price, qty in price_qty_list:
        #a lil fuzzy in price
        time.sleep(sleep)
        yield buy(account, venue, stock, int(price + ((random()-0.5)*randomness)), qty, orderType)


def guess_price(venue, stock, attempts=10, sleep=0):
    """
    averages 'ask' for multiple quotes for a stock at a venue
    helps to get a good starting point for a bid
    
    attempts: number of attempts - some may have ask, others might not
    sleep: seconds
    """
    asks, bids = [], []
    for i in range(attempts):
        time.sleep(sleep)
        quote = get_quote(venue, stock)
        if 'ask' in quote:
            asks.append(quote.get('ask'))
        if 'bid' in quote:
            bids.append(quote.get('bid'))
    return sum(asks)/len(asks), sum(bids)/len(bids)


def quote_websocket(account, venue, stock, listener):
    """
    listener: a function that will receive (ws, message)
    """
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/tickertape/stocks/%s"
        % (account, venue, stock),
        on_message=listener)
    thread = threading.Thread(target=ws.run_forever)
    thread.daemon = True
    thread.start()
    return thread


def fills_websocket(account, venue, stock, listener):
    """
    listener: a function that will receive (ws, message)
    """
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/executions/stocks/%s"
        % (account, venue, stock),
        on_message=listener)
    thread = threading.Thread(target=ws.run_forever)
    thread.daemon = True
    thread.start()
    return thread
