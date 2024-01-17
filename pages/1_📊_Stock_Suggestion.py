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

import os

#to get the current working directory
directory = os.getcwd()

st.write(directory)
# In[ ]:

# st.set_page_config(layout="wide")
#img = Image.open('/mount/src/threeten_sug/main/logo.png')
#img_logo = Image.open('/mount/src/threeten_sug/main/10_wo_white_bg_1.png')

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


with open("/mount/src/threeten_sug/main/stock_list_500.py", "rb") as file:
    stock_dict_500 = pickle.load(file)

# In[3]:


@st.cache_data(show_spinner=False)

def signal_ind(sticker):
    lookback = 100

    # Define the threshold for minimum demand
    demand_threshold = 2

    symbol = '{}.NS'.format(sticker)
    end_date = (datetime.today()+ timedelta(days=1)).strftime('%Y-%m-%d') 
    start_date = (datetime.today() - timedelta(days=200)).strftime('%Y-%m-%d')

    # Fetch data from Yahoo Finance
    df = yf.download(symbol, start=start_date, end=end_date) 
    
#     df = yf.download(symbol, end='2024-01-17')

    # Calculate the demand and supply levels
    df['demand'] = df['High'].rolling(window=lookback).max() - df['Low']
    df['supply'] = df['Low'] - df['Low'].rolling(window=lookback).min()

    # Initialize signal columns
    df['long_signal'] = False
    df['short_signal'] = False

    # Generate buy signals
    df.loc[(df['demand'] > demand_threshold) & (df['supply'] < df['demand']), 'long_signal'] = True

    # Generate sell signals
    df.loc[(df['supply'] > df['demand']) & (df['demand'] < demand_threshold), 'short_signal'] = True
    
    return df.iloc[[-1]]


if st.button("Run for Suggestion"):
    with st.spinner('Loading Suggested Stocks...'):
        buy_df = pd.DataFrame()
        buy_list = []
        for i in stock_dict_500.keys():
            symbol = stock_dict_500[i]
            try:
                df = signal_ind(symbol)
                if df.iloc[-1]['long_signal'] == True:
                    buy_df = pd.concat([buy_df, pd.DataFrame([{'Stock Name':i, 'Current Price' : df.iloc[-1]['Close']}])])
                    buy_list.append(i)
            except:
                pass


# In[ ]:

try:
    st.write("### Suggestion for Stocks to buy today", buy_df.sort_index())
except:
    pass

current_date = (datetime.today()).strftime('%Y_%b_%d') 

# st.dataframe(buy_df)
# st.write(buy_list)

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

try:
    df_xlsx = to_excel(buy_df)
    st.download_button(label='📥 Download Current Result',
                                data=df_xlsx ,
                                file_name= 'Stock_Suggestion_'+current_date+'.xlsx')
except:
    pass


st.sidebar.write("Button to rerun the suggestion list")

if st.sidebar.button("Refresh Program"):
    st.cache_data.clear()


# In[ ]:




