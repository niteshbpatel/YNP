import logging
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yfinance as yf
from pmClient import PMClient
from credentials import API_KEY, API_SECRET, ACCESS_TOKEN, PUBLIC_ACCESS_TOKEN, READ_ACCESS_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingEngine")

app = FastAPI(title="Local Algorithmic Trading Server")
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

@app.get("/")
async def root():
    return FileResponse(Path("dist") / "index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TradingOrderSchema(BaseModel):
    symbol: str
    exchange: str
    quantity: int
    order_type: str
    price: float = 0.0

@app.get("/api/indicators")
def get_indicators(
    symbol: str = Query(default="RELIANCE"),
    exchange: str = Query(default="NSE")
):
    try:
        clean_symbol = symbol.strip().upper()
        clean_exchange = exchange.strip().upper()
        
        if clean_exchange == "BSE":
            ticker_string = f"{clean_symbol}.BO"
        else:
            ticker_string = f"{clean_symbol}.NS"
            
        logger.info(f"Downloading MAX historical data till date for: {ticker_string}")
        
        # CHANGED: period="max" downloads all historical data up to June 2026
        stock_data = yf.download(ticker_string, period="max", interval="1d", progress=False)
        
        if stock_data.empty:
            return {"success": False, "error": f"No data found for {clean_symbol}"}
            
        close_prices = stock_data['Close'].values.flatten().tolist()
        
        if len(close_prices) < 14:
            return {"success": False, "error": "Insufficient trading history."}
            
        current_price = round(float(close_prices[-1]), 2)
        recent_14_days = close_prices[-14:]
        calculated_sma = round(float(sum(recent_14_days) / 14), 2)
        
        if current_price > calculated_sma:
            trading_signal = "BUY"
            reasoning = f"Price ({current_price}) is above 14-day SMA line ({calculated_sma})."
        else:
            trading_signal = "SELL"
            reasoning = f"Price ({current_price}) is below 14-day SMA line ({calculated_sma})."
            
        return {
            "success": True,
            "ticker": ticker_string,
            "symbol": clean_symbol,
            "exchange": clean_exchange,
            "live_price": current_price,
            "sma_14": calculated_sma,
            "signal": trading_signal,
            "analysis": reasoning,
            "total_days_loaded": len(close_prices)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/historical")
def get_historical_data(symbol: str = Query(default="RELIANCE")):
    """Return full maximum available historical data from NSE and BSE symbols via yfinance."""
    try:
        clean_symbol = symbol.strip().upper()
        nse_ticker = f"{clean_symbol}.NS"
        bse_ticker = f"{clean_symbol}.BO"

        logger.info(f"Downloading MAX historical data for NSE:{nse_ticker} and BSE:{bse_ticker}")
        nse_data = yf.download(nse_ticker, period="max", interval="1d", progress=False)
        bse_data = yf.download(bse_ticker, period="max", interval="1d", progress=False)

        nse_history = nse_data.reset_index().to_dict(orient="records") if not nse_data.empty else []
        bse_history = bse_data.reset_index().to_dict(orient="records") if not bse_data.empty else []

        return {
            "success": True,
            "symbol": clean_symbol,
            "nse_ticker": nse_ticker,
            "bse_ticker": bse_ticker,
            "nse_history_count": len(nse_history),
            "bse_history_count": len(bse_history),
            "nse_history": nse_history,
            "bse_history": bse_history,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/place-order")
def execute_sandbox_order(order: TradingOrderSchema):
    return {
        "success": True,
        "message": "Simulated order executed successfully!",
        "order_details": {
            "symbol": order.symbol.upper(),
            "quantity": order.quantity,
            "type": order.order_type.upper(),
            "exchange": order.exchange.upper()
        }
    }

@app.get("/api/paytm-status")
def paytm_status():
    try:
        if not API_KEY or API_KEY == "your_paytm_money_api_key_here" or not API_SECRET or API_SECRET == "your_paytm_money_api_secret_here":
            return {
                "success": False,
                "message": "Paytm credentials are not configured yet.",
                "configured": False,
            }

        pm_client = PMClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            access_token=ACCESS_TOKEN or None,
            public_access_token=PUBLIC_ACCESS_TOKEN or None,
            read_access_token=READ_ACCESS_TOKEN or None,
        )

        return {
            "success": True,
            "message": "Paytm client initialized successfully.",
            "configured": True,
            "client_type": type(pm_client).__name__,
        }
    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "configured": False,
        }

@app.get("/api/paytm-login-callback")
def paytm_login_callback(request_token: str = None):
    """
    Submits the short-lived browser redirect request token
    and prints out your daily live session tokens.
    """
    if not request_token:
        return {"error": "Missing 'request_token' parameter in query string."}

    try:
        pm = PMClient(api_key=API_KEY, api_secret=API_SECRET)
        session_data = pm.generate_session(request_token)

        print("\n=== SUCCESS: DAILY TOKENS GENERATED ===")
        print(session_data)
        print("=======================================\n")

        return {
            "status": "Success",
            "message": "Tokens printed to your backend console terminal window. Update your credentials.py file with these keys.",
            "data": session_data,
        }
    except Exception as exc:
        return {"status": "Failed", "error": str(exc)}

@app.get("/{full_path:path}")
async def spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    candidate = Path("dist") / full_path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(Path("dist") / "index.html")
