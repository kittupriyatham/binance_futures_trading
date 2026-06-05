from api.validators import validate_order_request
from api.logging_config import get_logger
from api.binance_client import BinanceClient
from api.models import OrderType, OrderResponse
from api.exceptions import TradingBotException, OrderPlacementException, BinanceConnectionException, ValidationException
from binance.exceptions import BinanceAPIException
import logging

# We get loggers for API order logging
logger = get_logger('trading_api', 'trading_api.log')

class OrderService:
    def __init__(self):
        # Initialize the BinanceClient
        self.binance_client = BinanceClient()

    def health_check(self):
        """Pings the Binance Futures exchange to check connectivity."""
        try:
            self.binance_client.ping()
            return {'status': 'ok', 'exchange': 'Binance Futures Testnet'}
        except BinanceConnectionException as e:
            return {'status': 'error', 'message': str(e), 'exchange': 'Binance Futures Testnet'}
        except Exception as e:
            return {'status': 'error', 'message': f"Unexpected connection error: {e}", 'exchange': 'Binance Futures Testnet'}

    def place_order(self, request) -> OrderResponse:
        """Validates, logs, and places an order on Binance Futures Testnet."""
        # 1. Validation
        validate_order_request(request)
        
        # Calculate expected execution price for virtual wallet simulation
        from api.wallet import transact_order, get_balance, is_mock_mode
        try:
            exec_price = float(request.price) if request.price else float(self.binance_client.get_symbol_price(request.symbol))
        except (TypeError, ValueError):
            exec_price = 0.0
            
        if exec_price <= 0:
            exec_price = 68000.0 # fallback default price
            
        cost = float(request.quantity) * exec_price
        if request.side.value == 'BUY' and get_balance() < cost:
            raise ValidationException(f"Insufficient virtual balance. Required: ${cost:,.2f}, Available: ${get_balance():,.2f}")
        
        # 2. Log request
        logger.info(f"ORDER REQUEST: type={request.order_type}, symbol={request.symbol}, side={request.side}, quantity={request.quantity}, price={request.price}, stop_price={request.stop_price}")
        
        mock_execution = is_mock_mode()
        
        try:
            if mock_execution:
                # Bypass actual Binance execution and simulate response
                import random
                mock_order_id = random.randint(10000000, 99999999)
                res = {
                    "symbol": request.symbol,
                    "side": request.side.value,
                    "type": request.order_type.value,
                    "orderId": mock_order_id,
                    "status": "FILLED" if request.order_type == OrderType.MARKET else "NEW",
                    "executedQty": str(request.quantity) if request.order_type == OrderType.MARKET else "0.0",
                    "price": str(exec_price),
                    "avgPrice": str(exec_price)
                }
            else:
                # 3. Call Binance integration based on order type
                if request.order_type == OrderType.MARKET:
                    res = self.binance_client.place_market_order(
                        symbol=request.symbol,
                        side=request.side.value,
                        quantity=float(request.quantity)
                    )
                elif request.order_type == OrderType.LIMIT:
                    res = self.binance_client.place_limit_order(
                        symbol=request.symbol,
                        side=request.side.value,
                        quantity=float(request.quantity),
                        price=float(request.price)
                    )
                elif request.order_type == OrderType.STOP_LIMIT:
                    res = self.binance_client.place_stop_limit_order(
                        symbol=request.symbol,
                        side=request.side.value,
                        quantity=float(request.quantity),
                        price=float(request.price),
                        stop_price=float(request.stop_price)
                    )
                else:
                    raise OrderPlacementException(f"Unsupported order type: {request.order_type}")
            
            # Execute local virtual wallet transaction
            transact_order(request.side.value, float(request.quantity), exec_price)

            # 4. Log response
            logger.info(f"ORDER RESPONSE SUCCESS: symbol={request.symbol}, orderId={res.get('orderId')}, status={res.get('status')}, executedQty={res.get('executedQty')}, avgPrice={res.get('avgPrice')}")
            
            # 5. Normalize Response
            return OrderResponse(
                success=True,
                message="Order placed successfully",
                symbol=res.get("symbol", request.symbol),
                side=res.get("side", request.side.value),
                order_type=res.get("type", request.order_type.value),
                order_id=res.get("orderId"),
                status=res.get("status"),
                executed_qty=res.get("executedQty", "0.0"),
                avg_price=res.get("avgPrice") or res.get("price") or "0.0"
            )
            
        except TradingBotException as e:
            logger.error(f"ORDER RESPONSE FAILED: {request.symbol} {request.order_type} -> Error: {e}")
            raise
        except Exception as e:
            logger.error(f"ORDER RESPONSE FAILED: {request.symbol} {request.order_type} -> Unexpected error: {e}")
            raise OrderPlacementException(f"Failed to place order: {e}")
