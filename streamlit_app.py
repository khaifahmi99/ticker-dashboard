import streamlit as st
import yfinance as yf
import altair as alt
import pandas as pd
from data import collections

# config
st.set_page_config(layout="wide")
st.title('Compare Shares')

query_params = st.query_params.to_dict()
company1_param = query_params.get('company1', 'GOOG')
company2_param = query_params.get('company2', 'AMZN')

with st.sidebar:
    with st.form("shares_form"):
        st.write("Insert two companies to compare")
        company_1 = st.text_input('Company 1', company1_param)
        company_2 = st.text_input('Company 2', company2_param)

        period = st.selectbox(
            'Please select a period',
            ('1Y', '1mo', '3mo', '6mo', 'YTD', '3Y', '5Y'),
        )

        submitted = st.form_submit_button("Compare")
    st.write("Or")
    with st.container(border=True):
        st.write("Select a collection")
        for col in collections:
            if st.button(col['title']):
                company_1 = ' '.join(col['companies'][:-1])
                company_2 = col['companies'][-1]

companies = ' '.join([company_1, company_2])
tickers = yf.Tickers(companies)

df = pd.DataFrame({ 'Company': [], 'Timestamp': [], 'Value': [] })
for ticker, data in tickers.tickers.items():
    hist = data.history(period=period, interval='1d')
    hist['Company'] = ticker
    hist['Timestamp'] = hist.index.copy()
    hist['Value'] = hist['Close'].round(2)
    
    df = pd.concat([df, hist[['Company', 'Timestamp', 'Value']]])

bound_percentage = 0.1
upper_bound = df['Value'].max() + (df['Value'].max() * bound_percentage)
lower_bound = df['Value'].min() - (df['Value'].min() * bound_percentage)


selected_companies = company_1.split(' ') + company_2.split(' ')
selected_companies = sorted(selected_companies)

groups = []
for company in selected_companies:
    filtered_df = df[df['Company'] == company]
    end_value = filtered_df.iloc[-1]['Value']
    start_value = filtered_df.iloc[0]['Value']

    diff_absolute = end_value - start_value
    diff_precentage = diff_absolute / end_value
    groups.append({
        'company': company,
        'diff_absolute': diff_absolute,
        'diff_percentage': diff_precentage,
    })

max_col = 3
n_cols = min(len(groups), 3)
row1 = st.columns(n_cols)

i = 0
for col in row1:
    if i <= len(groups) - 1:        
        tile = col.container(height=180)
        ticker = groups[i]['company']
        diff = groups[i]['diff_absolute']
        perc = groups[i]['diff_percentage']
        i+=1
        print(ticker, diff)
        if diff >= 0:
            title = ":rocket:"
            text_color = 'green'
        else:
            title = ":small_red_triangle_down:"
            text_color = 'red'

        tile.header(ticker)
        tile.subheader(f':{text_color}[{title} {abs(int(perc * 100))}% (${abs(diff).round(2)})]')


hover = alt.selection_single(
    fields=["Timestamp"],
    nearest=True,
    on="mouseover",
    empty="none",
)

title = ' vs '.join(selected_companies) if len(selected_companies) == 2 else ' | '.join(selected_companies)
lines = alt.Chart(df, title=f'{title} ({period})').mark_line().encode(
    x = alt.X('yearmonthdate(Timestamp)'),
    y = alt.Y('Value', scale=alt.Scale(domain=[lower_bound, upper_bound])),
    color = 'Company'
).properties(height=600)

points = lines.transform_filter(hover).mark_circle(size=65)
tooltips = (
        alt.Chart(df)
        .mark_rule()
        .encode(
            x="yearmonthdate(Timestamp)",
            y="Value",
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("Timestamp", title="Date"),
                alt.Tooltip("Value", title="Price (USD)"),
                alt.Tooltip("Company", title="Company")
            ],
        )
        .add_selection(hover)
    )
cht = (lines + points + tooltips).interactive()

chart = st.altair_chart(cht, use_container_width=True)

# recommendations
recs = []
for ticker, data in tickers.tickers.items():
    recommendations = data.recommendations.iloc[0]
    recs.append({ 
        'Company': ticker,
        'Strong Buy': recommendations['strongBuy'], 
        'Buy': recommendations['buy'], 
        'Hold': recommendations['hold'], 
        'Sell': recommendations['sell'], 
        'Strong Sell': recommendations['strongSell'] 
    })
    
rec_df = pd.DataFrame(recs)
st.title("Recommendations")
st.dataframe(rec_df, use_container_width=True)

# news
st.title('News')
news = []
for ticker, data in tickers.tickers.items():
    ticker_news = data.news
    for n in ticker_news:
        id = n['uuid']
        existing_ids = [en['uuid'] for en in news]

        if id not in existing_ids:
            news.append(n)

news.sort(key=lambda x: x['providerPublishTime'], reverse=True)

row1 = st.columns(2)
row2 = st.columns(2)
row3 = st.columns(2)
rows = [row1, row2, row3]

total_count = 0
for row in rows:
    for col in row:
        tile = col.container(height=180)
        title = news[total_count]['title']
        publisher = news[total_count]['publisher']
        url = news[total_count]['link']

        tile.markdown(f'<h3 style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{title}</h3>', unsafe_allow_html=True)
        tile.text(publisher)
        tile.link_button("Read more 🔗", url)
        total_count+=1