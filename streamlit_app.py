import streamlit as st
import yfinance as yf
import altair as alt
import pandas as pd

# config
st.set_page_config(layout="wide")
st.title('Compare Shares')

with st.sidebar:
    with st.form("shares_form"):
        st.write("Please insert two companies to compare")
        company_1 = st.text_input('Company 1', 'GOOG')
        company_2 = st.text_input('Company 2', 'AMZN')

        period = st.selectbox(
            'Please select a period',
            ('1Y', '1mo', '3mo', '6mo', 'YTD', '3Y', '5Y'),
        )

        submitted = st.form_submit_button("Compare")

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

lines = alt.Chart(df, title=f'{company_1} vs {company_2} - {period}').mark_line().encode(
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