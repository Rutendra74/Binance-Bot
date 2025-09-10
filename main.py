from flask import Flask, request, render_template, redirect, url_for, flash
from binance import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import logging
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('api')
API_SECRET =os.getenv('secret')

logging.basicConfig(filename='trading_bot.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.client = Client(api_key, api_secret)
        if testnet:
            self.client.FUTURE_URL = "https://testnet.binancefuture.com"
        logging.info("Binance Client Initialized")

    def get_balance(self):
        try:
            balance = self.client.futures_account_balance()
            logging.info("Fetched balance")
            return balance
        except (BinanceAPIException, BinanceRequestException) as e:
            logging.error(f"Balance error: {e}")
            return None

    def place_order(self, symbol, side, order_type, quantity, price=None, time_in_force="GTC"):
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            if price:
                params['price'] = price
                params['timeInForce'] = time_in_force

            logging.info(f"Placing order: {params}")

            if order_type == "MARKET":
                order = self.client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
            else:
                order = self.client.futures_create_order(symbol=symbol, side=side, type=order_type,
                                                         quantity=quantity, price=price, timeInForce=time_in_force)
            logging.info(f"Order response: {order}")
            return order
        except (BinanceAPIException, BinanceRequestException) as e:
            logging.error(f"Order error: {e}")
            return None

# Flask App
app = Flask(__name__)
app.secret_key = 'rutendra'
bot = BasicBot(API_KEY, API_SECRET, testnet=True)

@app.route('/')
def index():
    balance = bot.get_balance()
    if balance is None:
        balance = []
        flash("Could not fetch balance. Check API keys or permissions.")
    return render_template('index.html', balance=balance)

@app.route('/place_order', methods=['POST'])
def place_order():
    symbol = request.form.get('symbol')
    side = request.form.get('side')
    order_type = request.form.get('type')
    quantity = request.form.get('quantity')
    price = request.form.get('price') or None

    try:
        quantity = float(quantity)
        if price:
            price = float(price)
    except ValueError:
        flash("Quantity and Price must be numbers.")
        return redirect(url_for('index'))

    result = bot.place_order(symbol, side, order_type, quantity, price)

    if result:
        flash(f"Order placed: {result['orderId']}")
    else:
        flash("Order failed. Check logs for details.")

    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=6969)
