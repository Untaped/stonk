from flask import Flask, request, render_template
from datetime import datetime
from db import Stock, SessionLocal
from db import PriceHistory
from collections import defaultdict
from datetime import timedelta
import yfinance as yf

def get_price_history_db(symbol):
    today = datetime.now().date()
    two_years_ago = today - timedelta(days=730)

    try:
        df = yf.Ticker(symbol).history(start=two_years_ago, end=today, interval="1d")
        if df.empty:
            return {"dates": [], "prices": [], "year_growths": {}, "projected_growth": None}
        
        df = df.reset_index()
        df['Date'] = df['Date'].dt.date
        df['Year'] = df['Date'].apply(lambda d: d.year)

        # Group by year
        year_data = df.groupby('Year')['Close'].apply(list).to_dict()

        # Calculate yearly growth
        year_growths = {}
        sorted_years = sorted(year_data.keys())
        for i in range(1, len(sorted_years)):
            y_prev, y_curr = sorted_years[i - 1], sorted_years[i]
            if year_data[y_prev] and year_data[y_curr]:
                start = year_data[y_prev][0]
                end = year_data[y_curr][-1]
                if start and end:
                    growth = ((end - start) / start) * 100
                    year_growths[y_curr] = round(growth, 2)

        # Projected growth
        recent_growths = list(year_growths.values())[-2:]
        projected_growth = round(sum(recent_growths) / len(recent_growths), 2) if recent_growths else None

        return {
            "dates": df['Date'].astype(str).tolist(),
            "prices": df['Close'].tolist(),
            "year_growths": year_growths,
            "projected_growth": projected_growth
        }

    except Exception as e:
        print(f"Error getting price history for {symbol}: {e}")
        return {"dates": [], "prices": [], "year_growths": {}, "projected_growth": None}


app = Flask(__name__)

# Load S&P 500 symbols (still useful for filtering)
import pandas as pd
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        symbols = df['Symbol'].tolist()
        return symbols
    except Exception as e:
        print("Error fetching S&P 500 symbols:", e)
        return []

# Get fundamentals from the database
def get_fundamentals(symbol, date=None):
    session = SessionLocal()
    if not date:
        date = datetime.now().date()

    stock = session.query(Stock).filter(Stock.symbol == symbol, Stock.date == date).first()
    session.close()

    if not stock:
        raise ValueError(f"No data found for {symbol} on {date}")

    return {
        'shortName': stock.name,
        'symbol': stock.symbol,
        'price': stock.price,
        'marketCap': stock.market_cap,
        'averageVolume': stock.average_volume,
        'revenueGrowth': stock.revenue_growth,
        'earningsGrowth': stock.earnings_growth,
        'netIncomeToCommon': stock.net_income,
        'returnOnEquity': stock.roe,
        'debtToEquity': stock.debt_to_equity,
        'currentRatio': stock.current_ratio,
        'freeCashflow': stock.free_cashflow,
        'forwardPE': stock.forward_pe,
        'pegRatio': stock.peg_ratio,
        'ipoDate': None  # IPO date not stored yet in db
    }

# Placeholder for price history (optional future use)
def get_price_history(symbol):
    return {
        "dates": [],
        "prices": []
    }

# Scoring algorithm remains unchanged
def evaluate_stock_criteria(f):
    score = 0
    total_criteria = 12

    def safe_gt(val, threshold):
        return val is not None and val > threshold

    def safe_lt(val, threshold):
        return val is not None and val < threshold

    if safe_gt(f.get('marketCap'), 2_000_000_000): score += 1
    if safe_gt(f.get('averageVolume'), 500_000): score += 1

    # IPO check removed (not in db)
    if safe_gt(f.get('revenueGrowth'), 0.1): score += 1.5
    if safe_gt(f.get('earningsGrowth'), 0.12): score += 1.5
    if safe_gt(f.get('netIncomeToCommon'), 0): score += 1
    if safe_gt(f.get('returnOnEquity'), 0.15): score += 1.5
    if safe_lt(f.get('debtToEquity'), 0.8): score += 1
    if safe_gt(f.get('currentRatio'), 2.0): score += 0.5
    if safe_gt(f.get('freeCashflow'), 0): score += 1.5
    if safe_lt(f.get('forwardPE'), 2.0): score += 1
    if safe_lt(f.get('pegRatio'), 1.5): score += 1.5

    pct = (score / total_criteria) * 100

    if pct >= 60:
        recommendation = f"BUY: Strong candidate ({pct:.0f}% of criteria met)"
    elif pct >= 40:
        recommendation = f"WATCHLIST: Meets {pct:.0f}% of criteria"
    else:
        recommendation = f"DO NOT BUY: Only {pct:.0f}% of criteria met"

    return score, recommendation

# Routes

@app.route('/sp500')
def sp500_list():
    session = SessionLocal()
    today = datetime.now().date()
    symbols = get_sp500_symbols()

    stocks = session.query(Stock).filter(
        Stock.date == today,
        Stock.symbol.in_(symbols),
        Stock.score >= 10
    ).order_by(Stock.symbol).all()

    session.close()

    return render_template("sp500.html", stocks=[{
        'symbol': s.symbol,
        'shortName': s.name,
        'recommendation': s.recommendation,
        'score': s.score
    } for s in stocks])

@app.route('/database')
def view_from_database():
    session = SessionLocal()
    today = datetime.now().date()

    stocks = session.query(Stock).filter(Stock.date == today, Stock.score >= 8).order_by(Stock.symbol).all()
    session.close()

    return render_template("sp500.html", stocks=[{
        'symbol': s.symbol,
        'shortName': s.name,
        'recommendation': s.recommendation,
        'score': s.score
    } for s in stocks])

@app.route('/history')
def show_history():
    session = SessionLocal()
    data = session.query(Stock).order_by(Stock.date.desc(), Stock.symbol).limit(100).all()
    session.close()
    return render_template("history.html", stocks=data)

@app.route('/', methods=['GET', 'POST'])
def index():
    stock_data = None
    recommendation = None
    price_history = None
    error = None
    symbol = ""
    growth_summary = None

    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper().strip()
        try:
            fundamentals = get_fundamentals(symbol)
            stock_data = fundamentals
            score, recommendation_text = evaluate_stock_criteria(fundamentals)
            recommendation = (score, recommendation_text)
            price_history = get_price_history_db(symbol)

            if price_history.get("projected_growth") is not None:
                growth_summary = {
                    "projected": price_history["projected_growth"],
                    "history": price_history["year_growths"]
                }


        except Exception as e:
            error = f"Error retrieving data: {e}"

    return render_template("index.html",
        symbol=symbol,
        stock_data=stock_data,
        recommendation=recommendation,
        price_history=price_history,
        growth_summary=growth_summary,
        error=error
    )




if __name__ == '__main__':
    app.run(debug=True)