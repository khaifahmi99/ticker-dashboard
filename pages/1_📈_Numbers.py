import streamlit as st
import yfinance as yf
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

companies = [
    "AAPL",
    "ADBE",
    "AMD",
    "AMZN",
    "ARM",
    "DIS",
    "DUOL",
    "GOOG",
    "INTC",
    "LULU",
    "META",
    "MSFT",
    "NFLX",
    "NKE",
    "NVDA",
    "SNOW",
    "TSLA",
    "TSM",
    "QCOM",
]

def round_decimal(x):
  x = Decimal(x.item())
  return x.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

st.set_page_config(page_title="The Numbers", page_icon="📈")

st.markdown("# Share Numbers")

companies = ' '.join(companies)
tickers = yf.Tickers(companies)

# key: [period, interval]
settings = {
    '1D Change': ['1d', '1h'],
    '5D Change': ['5d', '1d'],
    '1M Change': ['1mo', '1wk'],
    '3M Change': ['3mo', '1mo'],
    '6M Change': ['6mo', '1mo'],
    '1Y Change': ['1y', '3mo'],
    '3Y Change': ['3y', '3mo'],
    '5Y Change': ['5y', '3mo'],
}

rows = []
for ticker, data in tickers.tickers.items():
    value_now = data.history(period='1d', interval='1h')['Close'].iloc[-1]
    row = [ticker, value_now]
    for period_title in list(settings.keys()):
        period, interval = settings[period_title]

        hist = data.history(period=period, interval=interval)

        first_value = hist['Close'].iloc[0]
        row.append(first_value)
    rows.append(row)

rows_with_field = []
for r in rows:
    curr = r[1]
    diff_1d = ((curr - r[2]) / curr) * 100
    diff_5d = ((curr - r[3]) / curr) * 100
    diff_1m = ((curr - r[4]) / curr) * 100
    diff_3m = ((curr - r[5]) / curr) * 100
    diff_6m = ((curr - r[6]) / curr) * 100
    diff_1y = ((curr - r[7]) / curr) * 100
    diff_3y = ((curr - r[8]) / curr) * 100
    diff_5y = ((curr - r[9]) / curr) * 100

    rows_with_field.append({
        'Company': r[0], 
        'Value': f"%.2f" % curr,
        '1D %': round_decimal(diff_1d),
        '5D %': round_decimal(diff_5d),
        '1M %': round_decimal(diff_1m),
        '3M %': round_decimal(diff_3m),
        '6M %': round_decimal(diff_6m),
        '1Y %': round_decimal(diff_1y),
        '3Y %': round_decimal(diff_3y),
        '5Y %': round_decimal(diff_5y),
    })

def highlight_pos_neg(val):
    if isinstance(val, str):
        return
    color = 'green' if val >= 0 else 'red'
    return f'color: {color}'
df = pd.DataFrame(rows_with_field)
st.dataframe(df.style.map(highlight_pos_neg), use_container_width=True)

    
