from api.exceptions import ValidationException
from api.models import OrderType

def validate_order_request(req):
    if req.quantity <= 0:
        raise ValidationException('Quantity must be > 0')
    
    if req.order_type == OrderType.LIMIT:
        if req.price is None:
            raise ValidationException('Price required for LIMIT')
        if req.price <= 0:
            raise ValidationException('Price must be > 0')
            
    if req.order_type == OrderType.STOP_LIMIT:
        if req.price is None or req.stop_price is None:
            raise ValidationException('Price and stop_price required')
        if req.price <= 0 or req.stop_price <= 0:
            raise ValidationException('Price and stop_price must be > 0')

