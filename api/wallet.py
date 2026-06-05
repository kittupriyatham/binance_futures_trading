import json
from pathlib import Path
from api.binance_client import BinanceClient

WALLET_FILE = Path('logs') / 'virtual_wallet.json'

def init_wallet():
    WALLET_FILE.parent.mkdir(exist_ok=True)
    if not WALLET_FILE.exists():
        save_wallet({"balance": 10000.0, "position": 0.0, "mock_mode": False, "total_deposited": 10000.0})

def load_wallet():
    init_wallet()
    try:
        with open(WALLET_FILE, 'r') as f:
            data = json.load(f)
            if "mock_mode" not in data:
                data["mock_mode"] = False
            if "total_deposited" not in data:
                data["total_deposited"] = data.get("balance", 10000.0)
            return data
    except Exception:
        return {"balance": 10000.0, "position": 0.0, "mock_mode": False, "total_deposited": 10000.0}

def save_wallet(data):
    WALLET_FILE.parent.mkdir(exist_ok=True)
    with open(WALLET_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_mock_mode() -> bool:
    return load_wallet().get("mock_mode", False)

def set_mock_mode(enabled: bool) -> bool:
    data = load_wallet()
    data["mock_mode"] = enabled
    save_wallet(data)
    return enabled

def get_balance() -> float:
    return load_wallet().get("balance", 10000.0)

def get_position() -> float:
    return load_wallet().get("position", 0.0)

def load_funds(amount: float) -> float:
    data = load_wallet()
    data["balance"] = data.get("balance", 10000.0) + amount
    data["total_deposited"] = data.get("total_deposited", 10000.0) + amount
    save_wallet(data)
    return data["balance"]

def transact_order(side: str, quantity: float, price: float) -> bool:
    """Deducts or adds funds based on order side and cost."""
    data = load_wallet()
    cost = quantity * price
    balance = data.get("balance", 10000.0)
    
    if side.upper() == 'BUY':
        if balance < cost:
            return False
        data["balance"] = balance - cost
        data["position"] = data.get("position", 0.0) + quantity
    else: # SELL
        data["balance"] = balance + cost
        data["position"] = data.get("position", 0.0) - quantity
        
    save_wallet(data)
    return True

def get_wallet_summary(symbol: str = "BTCUSDT") -> dict:
    """Calculates holding position value and total account net worth based on current market price."""
    data = load_wallet()
    balance = data.get("balance", 10000.0)
    position = data.get("position", 0.0)
    total_deposited = data.get("total_deposited", 10000.0)
    
    try:
        price = BinanceClient().get_symbol_price(symbol.upper())
        if price <= 0:
            price = 65000.0
    except Exception:
        price = 65000.0
        
    position_value = position * price
    total_value = balance + position_value
    profit_loss = total_value - total_deposited
    
    return {
        "balance": balance,
        "position": position,
        "position_value": position_value,
        "total_value": total_value,
        "price": price,
        "mock_mode": data.get("mock_mode", False),
        "total_deposited": total_deposited,
        "profit_loss": profit_loss
    }
