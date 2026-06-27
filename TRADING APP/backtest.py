import logging
import yfinance as yf
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GlobalScanner")

# 1. Complete high-liquidity tracking registry for listed Indian stocks (NSE)
PUBLIC_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
    "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "TITAN.NS", "ULTRACEMCO.NS", "ADANIENT.NS",
    "NTPC.NS", "TATASTEEL.NS", "POWERGRID.NS", "ASIANPAINT.NS", "COALINDIA.NS",
    "M&M.NS", "BAJAJ-AUTO.NS", "ADANIPORTS.NS", "JIOFIN.NS", "TRENT.NS",
    "HINDALCO.NS", "JSWSTEEL.NS", "GRASIM.NS", "TECHM.NS", "INDUSINDBK.NS",
    "NESTLEIND.NS", "TATAMOTORS.NS", "CIPLA.NS", "EICHERMOT.NS", "BRITANNIA.NS",
    "BPCL.NS", "ONGC.NS", "ADANIGREEN.NS", "WIPRO.NS", "DIVISLAB.NS",
    "APOLLOHOSP.NS", "SHRIRAMFIN.NS", "HEROMOTOCO.NS", "BEL.NS", "HAL.NS"
]

# 2. Local Registry Mock for High-Value Pre-IPO Unlisted Companies
# Since yfinance cannot scrap these, we register them as static structural assets
UNLISTED_REGISTRY = {
    "NSE_UNLISTED": {"name": "National Stock Exchange (Pre-IPO)", "est_valuation": "₹4.86 Lakh Cr", "status": "Pre-IPO"},
    "SERUM_INSTITUTE": {"name": "Serum Institute of India", "est_valuation": "₹2.56 Lakh Cr", "status": "Private"},
    "ZERODHA": {"name": "Zerodha FinTech", "est_valuation": "₹86,660 Cr", "status": "Private Private"},
    "RELIANCE_RETAIL": {"name": "Reliance Retail (Unlisted)", "est_valuation": "₹8.20 Lakh Cr", "status": "Pre-IPO Subsidiary"},
    "CSK_SHARES": {"name": "Chennai Super Kings Cricket Franchise", "est_valuation": "₹7,200 Cr", "status": "OTC Traded"}
}

def analyze_stock_history(ticker_symbol):
    try:
        # Download complete data timeline up to today
        stock_data = yf.download(ticker_symbol, period="max", interval="1d", progress=False)
        if stock_data.empty:
            return None

        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_data.columns = stock_data.columns.get_level_values(0)

        stock_data = stock_data[['Close']].dropna()
        stock_data['SMA_14'] = stock_data['Close'].rolling(window=14).mean()
        stock_data = stock_data.dropna()
        
        cash = 100000.0
        initial_capital = 100000.0
        position = 0.0
        total_trades = 0
        
        close_array = stock_data['Close'].values.flatten().tolist()
        sma_array = stock_data['SMA_14'].values.flatten().tolist()
        
        if len(close_array) < 14:
            return None

        for i in range(1, len(close_array)):
            current_close = close_array[i]
            previous_close = close_array[i-1]
            current_sma = sma_array[i]
            previous_sma = sma_array[i-1]
            
            # Cross ABOVE SMA_14 -> Buy Crossover
            if position == 0 and previous_close <= previous_sma and current_close > current_sma:
                position = cash / current_close
                cash = 0.0
                total_trades += 1
            # Cross BELOW SMA_14 -> Sell Crossover
            elif position > 0 and previous_close >= previous_sma and current_close < current_sma:
                cash = position * current_close
                position = 0.0
                total_trades += 1

        if position > 0:
            cash = position * close_array[-1]
            
        final_return_pct = ((cash - initial_capital) / initial_capital) * 100
        return {"ticker": ticker_symbol, "net_return": final_return_pct, "trades": total_trades}
    except Exception:
        return None

def run_india_market_master_scan():
    print("\n" + "="*70)
    print(" 💼 SECTION 1: PROCESSING HIGH-VALUE UNLISTED / PRE-IPO CORPORATIONS ")
    print("="*70)
    for key, info in UNLISTED_REGISTRY.items():
        print(f"  ▪️ [UNLISTED] {info['name']:<40} | Val: {info['est_valuation']:<15} | Status: {info['status']}")
        
    print("\n" + "="*70)
    print(" ⏳ SECTION 2: RUNNING CROSSOVER BACKTEST ON ALL LISTED PUBLIC EQUITIES ")
    print("="*70)
    
    results = []
    for ticker in PUBLIC_TICKERS:
        report = analyze_stock_history(ticker)
        if report:
            results.append(report)
            print(f"   Processed {ticker:<14} | Lifetime Gain/Loss: {report['net_return']:+.2f}%")
            
    # Sort listed array entries by highest profit return
    results.sort(key=lambda x: x['net_return'], reverse=True)
    
    print("\n" + "="*70)
    print(" 🏆 FINAL ALL-COMPANY STRATEGY PROFIT RANKING REPORT ")
    print("="*70)
    print(f" Rank | Ticker Symbol  | Total Orders Executed | Lifetime Net Profit %")
    print("-"*70)
    for idx, res in enumerate(results[:30], start=1):
        print(f"  #{idx:02d} | {res['ticker']:<14} | {res['trades']:^20} | {res['net_return']:+.2f}%")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_india_market_master_scan()
