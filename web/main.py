from fastapi import FastAPI, Request, status, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from api.models import OrderRequest, OrderResponse
from api.order_service import OrderService
from api.exceptions import TradingBotException, ValidationException, OrderPlacementException, BinanceConnectionException
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

app = FastAPI(
    title="Prime Trade Assignment",
    description="Binance Futures Testnet Trading Interface",
    version="1.0.0"
)

# Mount static files and templates
templates = Jinja2Templates(directory='web/templates')
app.mount('/static', StaticFiles(directory='web/static'), name='static')

@app.get('/')
async def home(request: Request):
    """Renders the dashboard homepage."""
    return templates.TemplateResponse(request=request, name='index.html')


@app.get('/api/health')
async def health():
    """Checks system connectivity to Binance Futures Testnet."""
    service = OrderService()
    result = service.health_check()
    return result

@app.get('/api/price/{symbol}')
async def get_price(symbol: str):
    """Returns the live price of a specific trading pair."""
    service = OrderService()
    price = service.binance_client.get_symbol_price(symbol.upper())
    return {"symbol": symbol.upper(), "price": price}


@app.post('/api/order', response_model=OrderResponse)
async def place_order(request: OrderRequest):
    """API endpoint to place an order."""
    service = OrderService()
    try:
        response = service.place_order(request)
        return response
    except ValidationException as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": f"Validation Error: {e}", "symbol": request.symbol, "side": request.side, "order_type": request.order_type}
        )
    except (BinanceConnectionException, OrderPlacementException) as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": f"Execution Error: {e}", "symbol": request.symbol, "side": request.side, "order_type": request.order_type}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"Server Error: {e}", "symbol": request.symbol, "side": request.side, "order_type": request.order_type}
        )

@app.get('/api/wallet')
async def get_wallet(symbol: str = "BTCUSDT"):
    """Returns current virtual wallet status with estimated values."""
    from api.wallet import get_wallet_summary
    return get_wallet_summary(symbol)

@app.post('/api/wallet/load')
async def load_wallet_funds(amount: float = 10000.0):
    """Loads virtual funds into the wallet."""
    from api.wallet import load_funds
    new_balance = load_funds(amount)
    return {"message": f"Successfully loaded ${amount:,.2f} virtual funds", "balance": new_balance}

@app.post('/api/wallet/toggle-mock')
async def toggle_mock_mode(enabled: bool):
    """Toggles Mock Exchange Mode on/off."""
    from api.wallet import set_mock_mode
    res = set_mock_mode(enabled)
    return {"message": f"Mock Exchange Mode set to {res}", "mock_mode": res}


