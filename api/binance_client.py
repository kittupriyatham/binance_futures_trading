import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from api.exceptions import BinanceConnectionException, OrderPlacementException

class BinanceClient:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        
        # Determine testnet flag
        testnet_env = os.getenv('BINANCE_TESTNET', 'True').lower()
        self.testnet = testnet_env in ('true', '1')

        # Initialize the client. We pass testnet=self.testnet and ping=False
        # to avoid Spot Testnet check failures if the Spot testnet is down.
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet, ping=False)


    def ping(self):
        """Pings the Binance Futures server to check connectivity."""
        try:
            self.client.futures_ping()
            return True
        except Exception as e:
            raise BinanceConnectionException(f"Binance Futures Testnet unreachable: {e}")

    def get_symbol_price(self, symbol: str) -> float:
        """Gets the current market price of a symbol on Binance Futures Testnet."""
        try:
            res = self.client.futures_symbol_ticker(symbol=symbol)
            return float(res.get('price', 0.0))
        except Exception:
            return 0.0


    def place_market_order(self, symbol: str, side: str, quantity: float):
        """Places a MARKET order on Binance Futures."""
        try:
            response = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            return response
        except BinanceAPIException as e:
            raise OrderPlacementException(f"Binance API Error: {e.message} (code: {e.code})")
        except Exception as e:
            raise OrderPlacementException(f"Unexpected error placing MARKET order: {e}")

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float):
        """Places a LIMIT order on Binance Futures."""
        try:
            response = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            return response
        except BinanceAPIException as e:
            raise OrderPlacementException(f"Binance API Error: {e.message} (code: {e.code})")
        except Exception as e:
            raise OrderPlacementException(f"Unexpected error placing LIMIT order: {e}")

    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, price: float, stop_price: float):
        """Places a STOP_LIMIT order on Binance Futures."""
        try:
            response = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP',
                timeInForce='GTC',
                quantity=quantity,
                price=price,
                stopPrice=stop_price
            )

            return response
        except BinanceAPIException as e:
            raise OrderPlacementException(f"Binance API Error: {e.message} (code: {e.code})")
        except Exception as e:
            raise OrderPlacementException(f"Unexpected error placing STOP_LIMIT order: {e}")
