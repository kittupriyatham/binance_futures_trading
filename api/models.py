from enum import Enum
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

class OrderType(str, Enum):
    MARKET='MARKET'
    LIMIT='LIMIT'
    STOP_LIMIT='STOP_LIMIT'

class OrderSide(str, Enum):
    BUY='BUY'
    SELL='SELL'

class OrderRequest(BaseModel):
    symbol:str
    side:OrderSide
    order_type:OrderType
    quantity:Decimal
    price:Optional[Decimal]=None
    stop_price:Optional[Decimal]=None

class OrderResponse(BaseModel):
    success:bool
    message:str
    symbol:str
    side:str
    order_type:str
    order_id:int|None=None
    status:str|None=None
    executed_qty:str|None=None
    avg_price:str|None=None
