#!/usr/bin/env python
# coding: utf-8

# In[1]:


import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pickle
import streamlit as st
from PIL import Image
import base64
from io import BytesIO

# st.set_page_config(layout="wide")
img = Image.open('logo.png')
img_logo = Image.open('310_wo_white_bg_1.png')

st.set_page_config(page_title='ThreeTen', page_icon = img, layout = 'wide', initial_sidebar_state = 'auto')

# Define the custom CSS
hide_streamlit_style = """
<style>
footer {visibility: hidden;}
footer:after {
    content: 'Made by Arjun & Team';
    visibility: visible;
    display: block;
    position: relative;
    color: purple;
}
</style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.sidebar.image(img_logo)



# Title and image layout
st.title("ThreeTen Suggestion")


with open("stock_list_500.py", "rb") as file:
    stock_dict_500 = pickle.load(file)

# In[3]:


@st.cache_data(show_spinner=False)

def signal_ind(sticker, stock_name):

    lookback = 100
    demand_threshold = 2

    symbol = '{}.NS'.format(sticker)

    df = yf.download(symbol) 
    
    df['demand'] = df['High'].rolling(window=lookback).max() - df['Low']
    df['supply'] = df['Low'] - df['Low'].rolling(window=lookback).min()

    df['long_signal'] = False
    df['short_signal'] = False

    df.loc[(df['demand'] > demand_threshold) & (df['supply'] < df['demand']), 'long_signal'] = True
    df.loc[(df['supply'] > df['demand']) & (df['demand'] < demand_threshold), 'short_signal'] = True
    
    #all_time_high_365 = df.tail(365)['Close'].max()
    #min_drawdown = all_time_high_365 * 0.9
    #max_drawdown = all_time_high_365 * 0.7
    
    df_new = df.iloc[[-1]]
    
    if (df.iloc[-1]['long_signal'] == True): #and (df.iloc[-1]['Close'] >= min_drawdown) and (df.iloc[-1]['Close'] <= max_drawdown):
        df_new['Filter_1'] = 'Yes'
    else:
        df_new['Filter_1'] = 'No'


    all_time_high = df['High'].max()
    current_price = df['Close'].iloc[-1]

    if current_price >= (0.95 * all_time_high) and current_price <= (1.05 * all_time_high):
        df_new['Filter_2'] = 'Yes'
    else:
        df_new['Filter_2'] = 'No'

        
    last_30_days_data = df.iloc[-30:]
    min_price = current_price * 0.90  # 5% below the all-time high
    max_price = current_price * 1.05  # 1% above the all-time high
    within_range = all(
        min_price <= price <= max_price
        for price in last_30_days_data['Close']
    )

    if within_range:
        df_new['Filter_3'] = 'Yes'
    else:
        df_new['Filter_3'] = 'No'
        
    return df_new


if st.button("Run for Suggestion"):
    with st.spinner('Loading Suggested Stocks...'):
        buy_df1 = pd.DataFrame()
        buy_df2 = pd.DataFrame()
        buy_df3 = pd.DataFrame()
        for i in stock_dict_500.keys():
            symbol = stock_dict_500[i]
            try:
                df_new = signal_ind(symbol, i)
                if df_new.iloc[-1]['Filter_1'] == 'Yes':
                    buy_df1 = pd.concat([buy_df1, pd.DataFrame([{'Stock Name':i, 'Current Price' : df_new.iloc[-1]['Close']}])])
                if df_new.iloc[-1]['Filter_2'] == 'Yes':
                    buy_df2 = pd.concat([buy_df2, pd.DataFrame([{'Stock Name':i, 'Current Price' : df_new.iloc[-1]['Close']}])])
                if df_new.iloc[-1]['Filter_3'] == 'Yes':
                    buy_df3 = pd.concat([buy_df3, pd.DataFrame([{'Stock Name':i, 'Current Price' : df_new.iloc[-1]['Close']}])])
            except:
                pass


try:
    buy_df1.reset_index(inplace=True, drop=True)
    common_stocks = pd.merge(buy_df2[['Stock Name','Current Price']], buy_df3[['Stock Name']], on='Stock Name', how='inner')
    print(buy_df1.head(2))
    print(common_stocks.head(2))
    st.write("### Suggestion for Stocks to buy today")
    col1, col2 = st.columns(2)
    col1.dataframe(buy_df1.sort_index())
    col2.dataframe(common_stocks.sort_index())
except:
    pass


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.000'}) 
    worksheet.set_column('B:B', None, format1)  
    writer.close()
    processed_data = output.getvalue()
    return processed_data

current_date = (datetime.today()).strftime('%Y_%b_%d') 

try:
    df_xlsx1 = to_excel(buy_df1)
    df_xlsx2 = to_excel(common_stocks)
    col1.download_button(label='📥 Download Current Suggestion 1',
                                    data=df_xlsx1 ,
                                    file_name= 'Stock_Suggestion_1_'+current_date+'.xlsx')
    col2.download_button(label='📥 Download Current Suggestion 2',
                                    data=df_xlsx2 ,
                                    file_name= 'Stock_Suggestion_2_'+current_date+'.xlsx')
except:
    pass

    

st.sidebar.write("Button to rerun the suggestion list")

if st.sidebar.button("Refresh Program"):
    st.cache_data.clear()


# In[ ]:




