from flask import Flask, request, render_template
import yfinance as yf
from datetime import datetime
import pandas as pd
import concurrent.futures

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

app = Flask(__name__)

# Get stock fundamentals using yfinance
def get_fundamentals(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        'shortName': info.get('shortName', symbol),
        'symbol': symbol,
        'price': info.get('currentPrice'),
        'previousClose': info.get('previousClose'),
        'open': info.get('open'),
        'dayHigh': info.get('dayHigh'),
        'dayLow': info.get('dayLow'),
        'marketCap': info.get('marketCap'),
        'averageVolume': info.get('averageVolume'),
        'ipoDate': info.get('ipoExpectedDate'),
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

# Get 1-month price history
def get_price_history(symbol):
    hist = yf.Ticker(symbol).history(period="1mo", interval="1d")
    return {
        "dates": hist.index.strftime('%Y-%m-%d').tolist(),
        "prices": hist['Close'].fillna(0).tolist()
    }

def evaluate_stock_criteria(f):
    score = 0
    total_criteria = 12

    def safe_gt(val, threshold):
        return val is not None and val > threshold

    def safe_lt(val, threshold):
        return val is not None and val < threshold

    if safe_gt(f.get('marketCap'), 2_000_000_000): score += 1
    if safe_gt(f.get('averageVolume'), 500_000): score += 1

    # IPO Date check
    try:
        ipo_str = f.get('ipoDate')
        if ipo_str:
            ipo_date = datetime.strptime(ipo_str, '%Y-%m-%d')
            if ipo_date < datetime(2020, 1, 1): score += 1
    except Exception as e:
        print("IPO date error:", e)

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

    # Return both numeric score AND recommendation string
    return score, recommendation

@app.route('/sp500')
def sp500_list():
    symbols = get_sp500_symbols()
    stocks = []

    def evaluate(symbol):
        try:
            fundamentals = get_fundamentals(symbol)
            score, recommendation = evaluate_stock_criteria(fundamentals)
            if score >= 8:
                return {
                    'symbol': symbol,
                    'shortName': fundamentals.get('shortName', symbol),
                    'recommendation': recommendation,
                    'score': score
                }
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(evaluate, symbols)

    # Filter out None results
    stocks = [s for s in results if s]

    # Sort alphabetically
    stocks.sort(key=lambda s: s['symbol'])

    return render_template("sp500.html", stocks=stocks)


# Home route
@app.route('/', methods=['GET', 'POST'])
def index():
    stock_data = None
    recommendation = None
    price_history = None
    error = None
    symbol = ""

    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper().strip()
        try:
            fundamentals = get_fundamentals(symbol)
            stock_data = fundamentals
            recommendation = evaluate_stock_criteria(fundamentals)
            price_history = get_price_history(symbol)

            print("Fundamentals:", fundamentals)
            print("Recommendation:", recommendation)

        except Exception as e:
            error = f"Error retrieving data: {e}"

    return render_template("index.html",
        symbol=symbol,
        stock_data=stock_data,
        recommendation=recommendation,
        price_history=price_history,
        error=error
    )

if __name__ == '__main__':
    app.run(debug=True)
