import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import altair as alt

st.set_page_config(page_title="Watchlist Threshold", page_icon="🚨")
st.markdown("# Watchlist Threshold")

data_us = requests.get("https://raw.githubusercontent.com/khaifahmi99/stock-alarm/master/watchlist-us.json").json()
data_au = requests.get("https://raw.githubusercontent.com/khaifahmi99/stock-alarm/master/watchlist-au.json").json()
watchlist = data_us["watchlist"] + data_au["watchlist"]
company_list = sorted([w["symbol"] for w in watchlist])
companies = ' '.join(company_list)
tickers = yf.Tickers(companies)

watchlist_thresholds = {}

df = pd.DataFrame({ 'Company': [], 'Timestamp': [], 'Value': [] })

with st.sidebar:
    period = st.selectbox(
        'Please select a period',
        ('1Y', '1mo', '3mo', '6mo', 'YTD', '3Y', '5Y'),
    )
    selected_ticker = st.selectbox(
        "Choose a company?",
        company_list,
    )


for ticker, data in tickers.tickers.items():
    watchlist_item = [x for x in watchlist if x["symbol"] == ticker][0]

    hist = data.history(period=period, interval='1d')
    hist['Company'] = ticker
    hist['Timestamp'] = hist.index.copy()
    hist['Value'] = hist['Close'].round(2)
    watchlist_thresholds[ticker] = {
        "lower": watchlist_item["thresholds"]["lower"],
        "upper": watchlist_item["thresholds"]["upper"]
    }
    
    df = pd.concat([df, hist[['Company', 'Timestamp', 'Value']]])

filtered_df = df[df['Company'] == selected_ticker]
bound_percentage = 0.1

upper_bound = filtered_df['Value'].max() + (filtered_df['Value'].max() * bound_percentage)
lower_bound = filtered_df['Value'].min() - (filtered_df['Value'].min() * bound_percentage)

upper_bound = max([upper_bound, *watchlist_thresholds[selected_ticker]["upper"]])
lower_bound = min([lower_bound, *watchlist_thresholds[selected_ticker]["lower"]])

hover = alt.selection_single(
    fields=["Timestamp"],
    nearest=True,
    on="mouseover",
    empty="none",
)

base = alt.Chart(filtered_df, title=f'{selected_ticker} ({period})')
line = base.mark_line().encode(
    x = alt.X('Timestamp'),
    y = alt.Y('Value', scale=alt.Scale(domain=[lower_bound, upper_bound])),
    color = 'Company'
).properties(height=600)

lowers = [
    base.mark_rule(color='orange').encode(y=alt.datum(value), strokeDash=alt.value([8,8]))
    for value in watchlist_thresholds[selected_ticker]["lower"]
]

uppers = [
    base.mark_rule(color='red').encode(y=alt.datum(value), strokeDash=alt.value([8,8]))
    for value in watchlist_thresholds[selected_ticker]["upper"]
]

cht = alt.layer(line, *uppers, *lowers)
chart = st.altair_chart(cht, use_container_width=True)