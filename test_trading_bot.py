import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from api.models import OrderRequest, OrderSide, OrderType, OrderResponse
from api.validators import validate_order_request
from api.exceptions import ValidationException, OrderPlacementException, BinanceConnectionException
from api.order_service import OrderService


class TestTradingBotValidators(unittest.TestCase):
    def test_quantity_must_be_positive(self):
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("-0.001")
        )
        with self.assertRaises(ValidationException) as ctx:
            validate_order_request(req)
        self.assertIn("Quantity must be > 0", str(ctx.exception))

    def test_limit_requires_price(self):
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.001"),
            price=None
        )
        with self.assertRaises(ValidationException) as ctx:
            validate_order_request(req)
        self.assertIn("Price required for LIMIT", str(ctx.exception))

    def test_limit_price_must_be_positive(self):
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.001"),
            price=Decimal("-10.0")
        )
        with self.assertRaises(ValidationException) as ctx:
            validate_order_request(req)
        self.assertIn("Price must be > 0", str(ctx.exception))

    def test_stop_limit_requires_price_and_stop_price(self):
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.STOP_LIMIT,
            quantity=Decimal("0.001"),
            price=None,
            stop_price=Decimal("50000")
        )
        with self.assertRaises(ValidationException) as ctx:
            validate_order_request(req)
        self.assertIn("Price and stop_price required", str(ctx.exception))

    def test_stop_limit_prices_must_be_positive(self):
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.STOP_LIMIT,
            quantity=Decimal("0.001"),
            price=Decimal("50000"),
            stop_price=Decimal("-1")
        )
        with self.assertRaises(ValidationException) as ctx:
            validate_order_request(req)
        self.assertIn("Price and stop_price must be > 0", str(ctx.exception))


class TestOrderService(unittest.TestCase):
    @patch('api.wallet.get_balance', return_value=100000.0)
    @patch('api.wallet.transact_order')
    @patch('api.wallet.is_mock_mode', return_value=False)
    @patch('api.order_service.BinanceClient')
    def test_place_market_order_success(self, mock_client_class, mock_is_mock, mock_transact, mock_get_balance):
        mock_client = MagicMock()
        mock_client.get_symbol_price.return_value = 68500.25
        mock_client.place_market_order.return_value = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "orderId": 987654321,
            "status": "FILLED",
            "executedQty": "0.005",
            "avgPrice": "68500.25"
        }
        mock_client_class.return_value = mock_client

        service = OrderService()
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.005")
        )

        response = service.place_order(req)
        self.assertTrue(response.success)
        self.assertEqual(response.order_id, 987654321)
        self.assertEqual(response.status, "FILLED")
        self.assertEqual(response.executed_qty, "0.005")
        self.assertEqual(response.avg_price, "68500.25")
        mock_transact.assert_called_once_with("BUY", 0.005, 68500.25)

    @patch('api.wallet.get_balance', return_value=100000.0)
    @patch('api.wallet.transact_order')
    @patch('api.wallet.is_mock_mode', return_value=False)
    @patch('api.order_service.BinanceClient')
    def test_place_limit_order_success(self, mock_client_class, mock_is_mock, mock_transact, mock_get_balance):
        mock_client = MagicMock()
        mock_client.place_limit_order.return_value = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "orderId": 987654322,
            "status": "NEW",
            "executedQty": "0.000",
            "price": "69000.00"
        }
        mock_client_class.return_value = mock_client

        service = OrderService()
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.01"),
            price=Decimal("69000.00")
        )

        response = service.place_order(req)
        self.assertTrue(response.success)
        self.assertEqual(response.order_id, 987654322)
        self.assertEqual(response.status, "NEW")
        self.assertEqual(response.avg_price, "69000.00")
        mock_transact.assert_called_once_with("SELL", 0.01, 69000.00)

    @patch('api.wallet.get_balance', return_value=100000.0)
    @patch('api.wallet.transact_order')
    @patch('api.wallet.is_mock_mode')
    @patch('api.order_service.BinanceClient')
    def test_place_order_sandbox_mode(self, mock_client_class, mock_is_mock, mock_transact, mock_get_balance):
        mock_is_mock.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        service = OrderService()
        req = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("10.0")
        )
        
        response = service.place_order(req)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.order_id)
        mock_client.place_market_order.assert_not_called()
        mock_transact.assert_called_once()



class TestVirtualWallet(unittest.TestCase):
    @patch('api.wallet.save_wallet')
    @patch('api.wallet.load_wallet')
    def test_get_balance_and_position(self, mock_load, mock_save):
        mock_load.return_value = {"balance": 5000.0, "position": 0.05}
        from api.wallet import get_balance, get_position
        self.assertEqual(get_balance(), 5000.0)
        self.assertEqual(get_position(), 0.05)

    @patch('api.wallet.save_wallet')
    @patch('api.wallet.load_wallet')
    def test_load_funds(self, mock_load, mock_save):
        mock_load.return_value = {"balance": 5000.0, "position": 0.0, "total_deposited": 5000.0}
        from api.wallet import load_funds
        new_bal = load_funds(2000.0)
        self.assertEqual(new_bal, 7000.0)
        mock_save.assert_called_once_with({"balance": 7000.0, "position": 0.0, "total_deposited": 7000.0})

    @patch('api.wallet.save_wallet')
    @patch('api.wallet.load_wallet')
    def test_transact_order_buy_success(self, mock_load, mock_save):
        mock_load.return_value = {"balance": 10000.0, "position": 0.0}
        from api.wallet import transact_order
        res = transact_order("BUY", 0.1, 50000.0)
        self.assertTrue(res)
        mock_save.assert_called_once_with({"balance": 5000.0, "position": 0.1})

    @patch('api.wallet.save_wallet')
    @patch('api.wallet.load_wallet')
    def test_transact_order_buy_insufficient_funds(self, mock_load, mock_save):
        mock_load.return_value = {"balance": 1000.0, "position": 0.0}
        from api.wallet import transact_order
        res = transact_order("BUY", 0.1, 50000.0)
        self.assertFalse(res)
        mock_save.assert_not_called()


    @patch('api.wallet.BinanceClient')
    @patch('api.wallet.load_wallet')
    def test_get_wallet_summary(self, mock_load, mock_client_class):
        mock_load.return_value = {"balance": 15000.0, "position": 0.5}
        mock_client = MagicMock()
        mock_client.get_symbol_price.return_value = 60000.0
        mock_client_class.return_value = mock_client
        
        from api.wallet import get_wallet_summary
        summary = get_wallet_summary("BTCUSDT")
        
        self.assertEqual(summary["balance"], 15000.0)
        self.assertEqual(summary["position"], 0.5)
        self.assertEqual(summary["position_value"], 30000.0)
        self.assertEqual(summary["total_value"], 45000.0)


if __name__ == "__main__":
    unittest.main()

