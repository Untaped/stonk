# daily_data_collector.py
##
##python3 daily_data_collector.py
##cd ~/Desktop/Stonk
##python3 app.py
##
# daily_data_collector.py
import yfinance as yf
from app import get_sp500_symbols, evaluate_stock_criteria
from db import Stock, PriceHistory, SessionLocal
from datetime import datetime, timedelta

def fix_symbol(symbol):
    replacements = {
        "BRK.B": "BRK-B",
        "BF.B": "BF-B",
    }
    return replacements.get(symbol, symbol)

def get_fundamentals_yfinance(symbol):
    ticker = yf.Ticker(fix_symbol(symbol))
    info = ticker.info
    return {
        'shortName': info.get('shortName', symbol),
        'symbol': symbol,
        'price': info.get('currentPrice'),
        'marketCap': info.get('marketCap'),
        'averageVolume': info.get('averageVolume'),
        'revenueGrowth': info.get('revenueGrowth'),
        'earningsGrowth': info.get('earningsGrowth'),
        'netIncomeToCommon': info.get('netIncomeToCommon'),
        'returnOnEquity': info.get('returnOnEquity'),
        'debtToEquity': info.get('debtToEquity'),
        'currentRatio': info.get('currentRatio'),
        'freeCashflow': info.get('freeCashflow'),
        'forwardPE': info.get('forwardPE'),
        'pegRatio': info.get('pegRatio'),
    }

def collect_and_store():
    symbols = get_sp500_symbols()
    session = SessionLocal()
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)

    for symbol in symbols:
        try:
            fundamentals = get_fundamentals_yfinance(symbol)
            score, recommendation = evaluate_stock_criteria(fundamentals)

            # Save fundamentals and score
            stock = Stock(
                symbol=symbol,
                name=fundamentals.get('shortName'),
                date=today,
                price=fundamentals.get('price'),
                market_cap=fundamentals.get('marketCap'),
                average_volume=fundamentals.get('averageVolume'),
                revenue_growth=fundamentals.get('revenueGrowth'),
                earnings_growth=fundamentals.get('earningsGrowth'),
                net_income=fundamentals.get('netIncomeToCommon'),
                roe=fundamentals.get('returnOnEquity'),
                debt_to_equity=fundamentals.get('debtToEquity'),
                current_ratio=fundamentals.get('currentRatio'),
                free_cashflow=fundamentals.get('freeCashflow'),
                forward_pe=fundamentals.get('forwardPE'),
                peg_ratio=fundamentals.get('pegRatio'),
                score=score,
                recommendation=recommendation
            )
            session.add(stock)

            # Fetch 30 days of daily close prices
            fixed_symbol = fix_symbol(symbol)
            ticker = yf.Ticker(fixed_symbol)
            hist = ticker.history(start=thirty_days_ago.strftime("%Y-%m-%d"), end=today.strftime("%Y-%m-%d"), interval="1d")
            for date_idx, row in hist.iterrows():
                # Avoid duplicate entries for the same symbol and date
                existing = session.query(PriceHistory).filter(
                    PriceHistory.symbol == symbol,
                    PriceHistory.date == date_idx.date()
                ).first()
                if not existing:
                    price_entry = PriceHistory(
                        symbol=symbol,
                        date=date_idx.date(),
                        close_price=row['Close']
                    )
                    session.add(price_entry)

            session.commit()
        except Exception as e:
            print(f"Error saving {symbol}: {e}")

    session.close()
    print("Done saving today's stock data and price history.")

if __name__ == "__main__":
    collect_and_store()
