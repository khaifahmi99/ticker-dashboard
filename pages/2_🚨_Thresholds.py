import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import altair as alt
import pymongo

st.set_page_config(page_title="Watchlist Threshold", page_icon="🚨")
st.markdown("# Watchlist Threshold")

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo"])

client = init_connection()

@st.cache_data(ttl=14400)
def get_data(symbol):
    db = client.personal
    items = db.Stock.find({ 'symbol': symbol, 'percentageChange': {"$exists": True} }).sort('createdAt', pymongo.DESCENDING).limit(30)
    items = list(items)
    return items

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

# Percentage Changes
st.markdown("# Percentage Change")
percent_changes_data = get_data(selected_ticker)
change_dates = []
pos_percent_changes = []
neg_percent_changes = []
for d in percent_changes_data:
    change_dates.append(d['createdAt'].date())
    if (d['percentageChange'] >= 0):
        pos_percent_changes.append(round(d['percentageChange'] * 100, 2))
        neg_percent_changes.append(0)
    else:
        neg_percent_changes.append(abs(round(d['percentageChange'] * 100, 2)))
        pos_percent_changes.append(0)

perc_df = pd.DataFrame({ 
    'Date': change_dates, 
    'Percent Change (+%)': pos_percent_changes,
    'Percent Change (-%)': neg_percent_changes,
})
st.bar_chart(
    perc_df, 
    x='Date', 
    y=['Percent Change (+%)', 'Percent Change (-%)'],
    y_label='Percentage Change (%)',
    color=['#00ff00', '#ff0000',]
)

# Recommendation Trends
st.markdown("# Recommendation Trends")
rec_t = yf.Ticker(selected_ticker)
rec = rec_t.recommendations

strong_buy = []
buy = []
sell = []
strong_sell = []

for i, row in rec.iterrows():
    strong_buy.append(row['strongBuy'])
    buy.append(row['buy'])
    sell.append(0 - row['sell'])
    strong_sell.append(0 - row['strongSell'])

strong_buy.reverse()
buy.reverse()
sell.reverse()
strong_sell.reverse()

rec_df = pd.DataFrame({ '1. Strong Buy': strong_buy, '2. Buy': buy, '4. Sell': sell, '5. Strong Sell': strong_sell })
st.bar_chart(
   rec_df, y=["1. Strong Buy", "2. Buy", '4. Sell', '5. Strong Sell']
)