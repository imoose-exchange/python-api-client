# coding=utf-8

import hashlib
import hmac
import requests
from decimal import Decimal
import time
from operator import itemgetter
from exceptions import ImooseAPIException

class Client(object):
    
    API_URL = 'https://api.imoose.com'

    MARKET_TYPE_SPOT = 'spot'
    MARKET_TYPE_VIRTUAL = 'virtual'

    SIDE_BUY = 'buy'
    SIDE_SELL = 'sell'
    ORDER_TYPE_LIMIT = 'limit'
    ORDER_TYPE_MARKET = 'market'

    def __init__(self, api_key, api_secret):
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
   
    def _init_session(self):
        session = requests.session()
        session.headers.update({'Accept': 'application/json',
        'User-Agent': 'imoose/python-api-client',
        'Api-Key': self.API_KEY})
        return session
    
    def _create_api_uri(self, path, signed=True):
        return self.API_URL + '/' + path

    def _handle_response(self, response):
        if not str(response.status_code).startswith('2'):
            raise ImooseAPIException(response)
        try:
            return response.json()
        except ValueError:
            raise ValueError('Invalid Response: %s' % response.text)

    def _request(self, method, uri, force_params=False, **kwargs):

        # set default requests timeout
        kwargs['timeout'] = 10

        data = kwargs.get('data', None)
        kwargs.setdefault('headers',{"Api-Key": self.API_KEY})

        if "/private" in uri:
            # generate signature
            kwargs['data']['timestamp'] = int(time.time() * 1000)
            kwargs['headers']['Api-Sign'] = self._generate_signature(kwargs['data'])
 
        # sort get and post params to match signature order
        if data:
            # find any requests params passed and apply them
            if 'requests_params' in kwargs['data']:
                # merge requests params into kwargs
                kwargs.update(kwargs['data']['requests_params'])
                del(kwargs['data']['requests_params'])

            # sort post params
            kwargs['data'] = self._order_params(kwargs['data'])

        # if get request assign data array to params value for requests lib
        if data and (method == 'get' or method == 'delete'):
            kwargs['params'] = kwargs['data']
            del(kwargs['data'])


        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)
    
    def _generate_signature(self, data):
        ordered_data = self._order_params(data)
        query_string = '&'.join(["{}={}".format(d[0], d[1]) for d in ordered_data])
     
        m = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        return m.hexdigest()

    def _order_params(self, data):
        params = []
        for key, value in data.items():
            params.append((key, value))

        params.sort(key=itemgetter(0))
        return params

    def _request_api(self, method, path, **kwargs):
        uri = self._create_api_uri(path)

        return self._request(method, uri, **kwargs)

    def _get(self, path, **kwargs):
        return self._request_api('get', path, data=kwargs)

    def _post(self, path, **kwargs):
        return self._request_api('post', path, data=kwargs)

    def _put(self, path, **kwargs):
        return self._request_api('put', path, data=kwargs)

    def _delete(self, path, **kwargs):
        return self._request_api('delete', path, data=kwargs)

    def get_server_status(self):
        return self._get('v1/public/status')

    def get_server_time(self):
        return self._get('v1/public/time')

    def get_asset(self, asset_id):
        return self._get('v1/public/asset',id=asset_id)

    def get_assets(self):
        return self._get('v1/public/asset')

    def get_market(self, market_id):
        return self._get('v1/public/market',id=market_id)

    def get_markets(self):
        return self._get('v1/public/market')

    def get_markets(self, type):
      return self._get('v1/public/market',type=type)

    def get_market_ticker(self,id):
        return self._get('v1/public/ticker',id=id)

    def get_market_tickers(self):
        return self._get('v1/public/ticker')
    
    def get_market_tickers(self,type):
        return self._get('v1/public/ticker',type=type)

    def _get_market_trades(self,market_id):
        return self._get('v1/public/trade',id=market_id)

    def get_market_trades(self,market_id):
        trades = self._get_market_trades(market_id)
        processedTrades = []
        for rawTrade in trades:
            processedTrades.append({"price": rawTrade[0], "volume": rawTrade[1],"time": rawTrade[2]})
        return processedTrades
    
    def _get_market_depth(self, market_id):
        return self._get('v1/public/depth',id=market_id)
    
    def get_market_depth(self, market_id):
        orderBook = self._get_market_depth(market_id)
        processedBook = {"bids": [], "asks": []}

        for priceLevel in orderBook["bids"]:
          processedBook["bids"].append({"price": priceLevel[0], "volume": priceLevel[1]})
        
        for priceLevel in orderBook["asks"]:
          processedBook["asks"].append({"price": priceLevel[0], "volume": priceLevel[1]})

        return processedBook

    def get_portfolios(self):
        return self._get('v1/private/portfolio')
    
    def get_portfolio_balances(self,id):
        return self._get('v1/private/balance',id=id)

    def get_order(self,id):
        return self._get('v1/private/order',id=id)

    def get_open_orders(self,portfolio_id):
        return self._get('v1/private/order/open',id=portfolio_id)

    def get_closed_orders(self,portfolio_id):
        return self._get('v1/private/order/closed',id=portfolio_id)

    def cancel_order(self,order_id):
        return self._delete('v1/private/order',id=order_id)

    def place_order(self,portfolio_id,side,type,market_id,volume,price=0.0):
        return self._post('v1/private/order',portfolio_id=portfolio_id,type=type,side=side,market=market_id,volume=volume,price=price)