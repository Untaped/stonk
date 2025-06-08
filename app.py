from flask import Flask, request, render_template
import yfinance as yf

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    stock_data = {}
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.info
            stock_data = {
                'name': info.get('shortName', 'Unknown'),
                'symbol': symbol,
                'price': info.get('currentPrice', 'N/A'),
                'currency': info.get('currency', 'N/A'),
                'exchange': info.get('exchange', 'N/A')
            }
        except Exception as e:
            stock_data['error'] = f"Failed to fetch data for {symbol}."
    return render_template('index.html', stock_data=stock_data)
