from datetime import datetime, timedelta
import yfinance as yf

def get_price_history_db(symbol):
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)

    try:
        df = yf.Ticker(symbol).history(start=thirty_days_ago, end=today, interval="1d")
        if df.empty:
            return {"dates": [], "prices": []}

        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        return {
            "dates": df['Date'].tolist(),
            "prices": df['Close'].tolist()
        }

    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return {"dates": [], "prices": []}
