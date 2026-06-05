class TradingBotException(Exception): pass
class ValidationException(TradingBotException): pass
class BinanceConnectionException(TradingBotException): pass
class OrderPlacementException(TradingBotException): pass
