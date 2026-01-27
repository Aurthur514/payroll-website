import requests
import time
import json
import urllib.parse
from cryptography.hazmat.primitives.asymmetric import ed25519
from config import API_KEY, API_SECRET, BASE_URL

class CoinSwitchAPI:
    def __init__(self):
        self.api_key = API_KEY
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(API_SECRET))
        self.base_url = BASE_URL
        self.session = requests.Session()

    def _get_signature(self, method, endpoint, epoch_time, body=''):
        if method == 'GET':
            unquote_endpoint = urllib.parse.unquote_plus(endpoint)
            message = method + unquote_endpoint + epoch_time
        else:
            message = method + endpoint + body
        signature_bytes = self.private_key.sign(message.encode())
        signature = signature_bytes.hex()
        return signature

    def _get_headers(self, method, endpoint, data=None):
        epoch_time = str(int(time.time() * 1000))
        body = ''
        if data and method in ['POST', 'DELETE']:
            body = json.dumps(data, separators=(',', ':'), sort_keys=True)
        signature = self._get_signature(method, endpoint, epoch_time, body)
        headers = {
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
        if method == 'GET':
            headers['X-AUTH-EPOCH'] = epoch_time
        return headers

    def get(self, endpoint, params=None):
        if params:
            query_string = '?' + urllib.parse.urlencode(params)
            endpoint += query_string
        url = self.base_url + endpoint
        headers = self._get_headers('GET', endpoint)
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data=None):
        url = self.base_url + endpoint
        headers = self._get_headers('POST', endpoint, data)
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint, data=None):
        url = self.base_url + endpoint
        headers = self._get_headers('DELETE', endpoint, data)
        response = self.session.delete(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    # Specific API methods
    def get_server_time(self):
        return self.get('/trade/api/v2/time')

    def validate_keys(self):
        return self.get('/trade/api/v2/validate/keys')

    def get_ticker(self, exchange, symbol):
        return self.get('/trade/api/v2/24hr/ticker', {'exchange': exchange, 'symbol': symbol})

    def get_order_book(self, exchange, symbol):
        return self.get('/trade/api/v2/depth', {'exchange': exchange, 'symbol': symbol})

    def get_recent_trades(self, exchange, symbol):
        return self.get('/trade/api/v2/trades', {'exchange': exchange, 'symbol': symbol})

    def place_order(self, side, symbol, order_type, price, quantity, exchange):
        data = {
            'side': side,
            'symbol': symbol,
            'order_type': order_type,
            'price': price,
            'quantity': quantity,
            'exchange': exchange,
            'reduce_only': False
        }
        return self.post('/trade/api/v2/futures/order', data)

    def cancel_order(self, order_id):
        data = {'order_id': order_id}
        return self.delete('/trade/api/v2/order', data)

    def get_order_status(self, order_id):
        return self.get('/trade/api/v2/order', {'order_id': order_id})

    def get_open_orders(self, exchange=None, symbol=None):
        params = {'open': True}
        if exchange:
            params['exchanges'] = exchange
        if symbol:
            params['symbols'] = symbol
        return self.get('/trade/api/v2/orders', params)

    def get_exchange_info(self, exchange):
        return self.get('/trade/api/v2/exchangeInfo', {'exchange': exchange})

    def get_all_tickers(self, exchange):
        return self.get('/trade/api/v2/tickers', {'exchange': exchange})

    def get_coins(self, exchange):
        return self.get('/trade/api/v2/coins', {'exchange': exchange})

    def get_all_pairs_ticker(self, exchange):
        return self.get('/trade/api/v2/24hr/all-pairs/ticker', {'exchange': exchange})

    def get_portfolio(self):
        return self.get('/trade/api/v2/portfolio')