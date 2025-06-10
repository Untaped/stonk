from flask import Flask, request, render_template
import yfinance as yf

app = Flask(__name__)

def get_fundamentals(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info

    return {
        'symbol': symbol,
        'shortName': info.get('shortName', symbol),
        'marketCap': info.get('marketCap'),
        'averageVolume': info.get('averageVolume'),
        'ipoDate': info.get('ipoDate', '2000-01-01'),  # fallback for safety

        'revenueGrowth': info.get('revenueGrowth'),
        'earningsGrowth': info.get('earningsGrowth'),
        'netIncomeToCommon': info.get('netIncomeToCommon'),
        'returnOnEquity': info.get('returnOnEquity'),

        'debtToEquity': info.get('debtToEquity'),
        'currentRatio': info.get('currentRatio'),
        'freeCashflow': info.get('freeCashflow'),

        'forwardPE': info.get('forwardPE'),
        'pegRatio': info.get('pegRatio'),
        'priceToBook': info.get('priceToBook'),

        'beta': info.get('beta'),
        'dividendYield': info.get('dividendYield'),

        # Display Data
        'price': info.get('currentPrice'),
        'currency': info.get('currency'),
        'exchange': info.get('exchange'),
        'previousClose': info.get('previousClose'),
        'open': info.get('open'),
        'dayHigh': info.get('dayHigh'),
        'dayLow': info.get('dayLow'),
    }

def evaluate_stock_criteria(f):
    score = 0
    total_criteria = 12

    # Step 1: Pre-Filter
    if f.get('marketCap', 0) > 2_000_000_000:
        score += 1
    if f.get('averageVolume', 0) > 500_000:
        score += 1
    if f.get('ipoDate', '2000-01-01') < '2020-01-01':
        score += 1

    # Step 2: Growth & Profitability
    if f.get('revenueGrowth', 0) > 0.08:
        score += 1
    if f.get('earningsGrowth', 0) > 0.10:
        score += 1
    if f.get('netIncomeToCommon', 0) > 0:
        score += 1
    if f.get('returnOnEquity', 0) > 0.12:
        score += 1

    # Step 3: Financial Health
    if f.get('debtToEquity', 2.0) < 1.0:
        score += 1
    if f.get('currentRatio', 0) > 1.5:
        score += 1
    if f.get('freeCashflow', 0) > 0:
        score += 1

    # Step 4: Valuation
    if f.get('forwardPE', 30) < 25:
        score += 1
    if f.get('pegRatio', 2.0) < 1.5:
        score += 1

    percentage = (score / total_criteria) * 100

    if percentage >= 80:
        return f"✅ BUY: Strong candidate ({percentage:.0f}% of criteria met)"
    elif percentage >= 60:
        return f"👀 WATCHLIST: Meets {percentage:.0f}% of criteria"
    else:
        return f"❌ DO NOT BUY: Only {percentage:.0f}% of criteria met"

@app.route('/', methods=['GET', 'POST'])
def index():
    stock_data = None
    error = None
    recommendation = None
    symbol = ""

    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper().strip()

        if symbol:
            try:
                fundamentals = get_fundamentals(symbol)

                if 'shortName' in fundamentals:
                    stock_data = fundamentals
                    recommendation = evaluate_stock_criteria(fundamentals)
                else:
                    error = f"No data found for symbol '{symbol}'. Please check and try again."
            except Exception as e:
                error = f"Error fetching data: {str(e)}"
        else:
            error = "Please enter a stock symbol."

    return render_template('index.html',
                           symbol=symbol,
                           stock_data=stock_data,
                           recommendation=recommendation,
                           error=error)

if __name__ == '__main__':
    app.run(debug=True)
