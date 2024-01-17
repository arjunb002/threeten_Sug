import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts
import json
import numpy as np
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import pickle
from PIL import Image
import base64
import datetime
import calendar


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
st.title("ThreeTen Prototype")
import os

#to get the current working directory
directory = os.getcwd()

st.write(directory)
with open("stock_list.py", "rb") as file:
    stock_dict = pickle.load(file)
    
with open("ques_dict.py", "rb") as file:
    ques_dict = pickle.load(file)

question_1 = st.text_input("Enter your question:")
st.subheader("Example prompt")

if st.button(list(ques_dict.keys())[0]):
    st.write(ques_dict.get(list(ques_dict.keys())[0], "No answer found"))

if st.button(list(ques_dict.keys())[1]):
    st.write(ques_dict.get(list(ques_dict.keys())[1], "No answer found"))

if st.button(list(ques_dict.keys())[2]):
    st.write(ques_dict.get(list(ques_dict.keys())[2], "No answer found"))

st.sidebar.header('Stock List')
stock_name = st.sidebar.selectbox('Choose your stock :', list(stock_dict.keys()))
symbol = stock_dict[stock_name]


COLOR_BULL = 'rgba(38,166,154,0.9)' # #26a69a
COLOR_BEAR = 'rgba(239,83,80,0.9)'  # #ef5350

def get_stock_news_links(stock_symbol, num_links=5):
    api_url = "https://newsapi.org/v2/everything"
    api_key = "f557e62e757f449b9d60aa74f9c0b75d"  # Sign up at https://newsapi.org/ to get your API key

    params = {
        "q": stock_symbol,
        "apiKey": api_key,
        "sortBy": "publishedAt",
        "pageSize": num_links
    }

    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        if response.status_code == 200:
            articles = data.get("articles")
            if articles:
                for idx, article in enumerate(articles, 1):
                    title = article["title"]
                    link = article["url"]
                    st.markdown(f"{idx}. Title: {title}")
                    st.markdown(f"Link: {link}\n")
            else:
                st.markdown(f"No news found for {stock_symbol}")
        else:
            st.markdown(f"Failed to retrieve news for {stock_symbol}. Status Code: {response.status_code}")
    except Exception as e:
        st.markdown(f"An error occurred: {str(e)}")



# Request historic pricing data via finance.yahoo.com API
df = yf.Ticker('{}.NS'.format(symbol)).history(period='30D')[['Open', 'High', 'Low', 'Close', 'Volume']]
# if df.shape[0] == 0:
#     st.write("Data is not available for {}".format(stock_name))
#     break
# else:
#     continue
# Some data wrangling to match required format
df = df.reset_index()
df.columns = ['time','open','high','low','close','volume'] # rename columns
df['time'] = df['time'].dt.strftime('%Y-%m-%d')                             # Date to string
df['color'] = np.where(  df['open'] > df['close'], COLOR_BEAR, COLOR_BULL)  # bull or bear
df.ta.macd(close='close', fast=6, slow=12, signal=5, append=True)           # calculate macd
macd_fast = json.loads(df.rename(columns={"MACDh_6_12_5": "value"}).to_json(orient = "records"))
macd_slow = json.loads(df.rename(columns={"MACDs_6_12_5": "value"}).to_json(orient = "records"))
df['color'] = np.where(  df['MACD_6_12_5'] > 0, COLOR_BULL, COLOR_BEAR)  # MACD histogram color
macd_hist = json.loads(df.rename(columns={"MACD_6_12_5": "value"}).to_json(orient = "records"))

stock_symbol = "{}.NS".format(symbol)
current_date = datetime.date.today()
start_date = current_date - datetime.timedelta(days=365)
start_date = start_date.strftime('%Y-%m-01')
end_date = current_date.replace(day=1) - datetime.timedelta(days=1)

# Download historical stock data from Yahoo Finance
data = yf.download(stock_symbol, start=start_date, end=end_date)

# Extract the monthly differences
monthly_differences = []

for period in data.index.to_period('M').unique():
#     print(period)
    year = period.year
    month = period.month
    # Find the first available date in the month
    month_data = data.loc[data.index.to_period('M') == period]
    if len(month_data) > 0:
#         print(month_data.iloc[0], month_data.iloc[-1])
        start_of_month = month_data.iloc[0]['Close']
        end_of_month = month_data.iloc[-1]['Close']
        price_difference = ((end_of_month - start_of_month)/start_of_month)*100
#         monthly_differences.append({'Year': year, 'Month': month, 'Price Difference': price_difference})
        monthly_differences.append({'Date': period.strftime('%Y-%m'), 'Price Difference': price_difference})

# Create a DataFrame to display the results
result_df = pd.DataFrame(monthly_differences)
# result_df.set_index(['Year', 'Month'], inplace=True)


positive_lst = []
negative_lst = []
for month, percentage_increase in result_df.values.tolist():
    if percentage_increase > 0:
        positive_lst.append(percentage_increase)
    else:
        negative_lst.append(percentage_increase)
formatted_data1 = [{"time": date, "value": value} for date, value in result_df.values.tolist()]
positive_data = (formatted_data1[-1], {'time':current_date.strftime('%Y-%m'), 'value':np.mean(positive_lst)})
negative_data = ([formatted_data1[-1], {'time':current_date.strftime('%Y-%m'), 'value':np.mean(negative_lst)}])

candles = json.loads(
    df.filter(['time','close'], axis=1)
      .rename(columns={"close": "value"})
      .to_json(orient = "records"))

volume = json.loads(
    df.filter(['time','volume'], axis=1)
      .rename(columns={"volume": "value"})
      .to_json(orient = "records"))

current_date = datetime.datetime.now()
first_day_next_month = datetime.datetime(current_date.year, current_date.month + 1, 1).strftime('%Y-%m-01')

total_value1 = round((df.iloc[-1]['close']),2)

positive_price = (candles[-1], {'time': first_day_next_month, 'value': round(total_value1 * (1 + np.mean(positive_lst) / 100), 2)})
negative_price = (candles[-1], {'time': first_day_next_month, 'value': round(total_value1 * (1 + np.mean(negative_lst) / 100), 2)})


chartMultipaneOptions = [
    {
        "width": 800,
        "height": 400,
        "layout": {
            "background": {
                "type": "solid",
                "color": 'white'
            },
            "textColor": "black"
        },
        "grid": {
            "vertLines": {
                "color": "rgba(197, 203, 206, 0.5)"
                },
            "horzLines": {
                "color": "rgba(197, 203, 206, 0.5)"
            }
        },
        "crosshair": {
            "mode": 0
        },
        "priceScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)"
        },
        "timeScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)",
            "barSpacing": 15
        },
        "watermark": {
            "visible": True,
            "fontSize": 48,
            "horzAlign": 'center',
            "vertAlign": 'center',
            "color": 'rgba(171, 71, 188, 0.3)',
            "text": '{}'.format(symbol),
        }
    },
    {
        "width": 800,
        "height": 150,
        "layout": {
            "background": {
                "type": "solid",
                "color": 'white'
            },
            "textColor": "black"
        },
        "grid": {
            "vertLines": {
                "color": "rgba(197, 203, 206, 0.5)"
                },
            "horzLines": {
                "color": "rgba(197, 203, 206, 0.5)"
            }
        },
        "crosshair": {
            "mode": 0
        },
        "priceScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)"
        },
        "timeScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)",
            "barSpacing": 15
        },
        "watermark": {
            "visible": True,
            "fontSize": 18,
            "horzAlign": 'left',
            "vertAlign": 'center',
            "color": 'rgba(171, 71, 188, 0.3)',
            "text": 'Volume',
        }
    }
#     ,
#     {
#         "width": 800,
#         "height": 200,
#         "layout": {
#             "background": {
#                 "type": "solid",
#                 "color": 'white'
#             },
#             "textColor": "black"
#         },
#         "timeScale": {
#             "visible": False,
#         },
#         "watermark": {
#             "visible": True,
#             "fontSize": 18,
#             "horzAlign": 'left',
#             "vertAlign": 'center',
#             "color": 'rgba(171, 71, 188, 0.7)',
#             "text": 'MACD',
#         }
#     }
]

seriesCandlestickChart = [
    {
        "type": 'Line',
        "data": candles,
        "options": {
            "color": 'blue',
            "lineWidth": 2
        }

    },
    {
        "type": 'Line',
        "data": positive_price,
        "options" : {"color": 'green', "lineWidth": 2}
    },
    {
        "type": 'Line',
        "data": negative_price,
        "options" : {"color": 'red',"lineWidth": 2}
    }
]

seriesVolumeChart = [
    {
        "type": 'Line',
        "data": volume,
        "options": {
            "priceFormat": {
                "type": 'volume',"color": 'blue',
            "lineWidth": 2
            }
#             ,
#             "priceScaleId": "" # set as an overlay setting,
        }
#         ,"priceScale": {
#             "scaleMargins": {
#                 "top": 0,
#                 "bottom": 0,
#             },
#             "alignLabels": False
#         }
    }
]

seriesMACDchart = [
    {
        "type": 'Line',
        "data": macd_fast,
        "options": {
            "color": 'blue',
            "lineWidth": 2
        }
    },
    {
        "type": 'Line',
        "data": macd_slow,
        "options": {
            "color": 'green',
            "lineWidth": 2
        }
    },
    {
        "type": 'Histogram',
        "data": macd_hist,
        "options": {
            "color": 'red',
            "lineWidth": 1
        }
    }
]

overlaidAreaSeriesOptions ={
    "layout": {
        "textColor": 'black',
        "background": {
            "type": 'solid',
            "color": 'white'
        }
    },"watermark": {
            "visible": True,
            "fontSize": 48,
            "horzAlign": 'center',
            "vertAlign": 'center',
            "color": 'rgba(171, 71, 188, 0.3)',
            "text": '{}'.format(symbol),
        }
}


priceVolumeSeries = [
    {
        "type": 'Area',
        "data": formatted_data1,
        "options": {
#             "topColor": 'rgba(38,198,218, 0.56)',
#             "bottomColor": 'rgba(38,198,218, 0.04)',
            "lineColor": 'rgba(78,105,177, 1)',
            "lineWidth": 2,
        }
    },
    {
        "type": 'Line',
        "data": positive_data,
        "options" : {"color": 'green', "lineWidth": 2}
    },
    {
        "type": 'Line',
        "data": negative_data,
        "options" : {"color": 'red',"lineWidth": 2}
    }
]

st.subheader("Potential Upside and Downside for next one month (%)")
st.write("Analyzes monthly stock price changes on NSE over the past year, categorizes as positive/negative, and provides averages for each category.")

renderLightweightCharts([
    {
        "chart": overlaidAreaSeriesOptions,
        "series": priceVolumeSeries
    }
], 'priceAndVolume')

number = st.number_input("Enter the quantity you wish to purchase at ₹{} per stock".format(str(round(df.iloc[-1]['close'],2))), value=1)
total_value = round((df.iloc[-1]['close']) * number,2)

col1, col2, col3 = st.columns(3)
col1.metric("Total invested Amount", total_value)
col2.metric("Upside Value", round(total_value*(1+(np.mean(positive_lst))/100),2), str(round(np.mean(positive_lst),2))+'%')
col3.metric("Downside Value", round(total_value*(1+(np.mean(negative_lst))/100),2), str(round(np.mean(negative_lst),2))+'%')

st.subheader("Price And Volume Chart")

renderLightweightCharts([
    {
        "chart": chartMultipaneOptions[0],
        "series": seriesCandlestickChart
    }
    ,
    {
        "chart": chartMultipaneOptions[1],
        "series": seriesVolumeChart
    }
#     ,
#     {
#         "chart": chartMultipaneOptions[2],
#         "series": seriesMACDchart
#     }
], 'line')


# Embed the Trendlyne SWOT analysis widget using the HTML code
html_code = """
<blockquote class="trendlyne-widgets" data-get-url="https://trendlyne.com/web-widget/swot-widget/Poppins/{}/?posCol=00A25B&primaryCol=006AFF&negCol=EB3B00&neuCol=F7941E" data-theme="light"></blockquote>
<script async src="https://cdn-static.trendlyne.com/static/js/webwidgets/tl-widgets.js" charset="utf-8"></script>
""".format(symbol)

st.components.v1.html(html_code, width=800, height=300)

if __name__ == "__main__":
    stock_symbol = "{}".format(symbol)  # Replace with the stock symbol you're interested in
    get_stock_news_links(stock_symbol)
