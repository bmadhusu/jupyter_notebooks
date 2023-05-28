import datetime
import pandas as pd
import re
import matplotlib as plt
import matplotlib.dates as mdates
import numpy as np
import requests

def get_json_financials_from_tikr(stock_ticker):


    # Below is from: https://medium.datadriveninvestor.com/access-companies-sec-filings-using-python-760e6075d3ad

    headers = {'User-Agent': "your@email.com"}
    tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)

    tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
    tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
    tickers_cik.set_index("ticker",inplace=True)

    cik = tickers_cik.loc[stock_ticker]['cik_str']

    url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + cik + '.json'
    response = requests.get(url, headers = headers)

    tags = list(response.json()['facts']['us-gaap'].keys())
    company_data = pd.DataFrame()

    for i in range(len(tags)):
        try:
            tag = tags[i]
            units=list(response.json()['facts']['us-gaap'][tag]['units'].keys())[0]
            data = pd.json_normalize(response.json()['facts']['us-gaap'][tag]['units'][units])
            data['tag'] = tag
            data['units'] = units
            company_data = pd.concat([company_data, data], ignore_index=True)
        except:
            print(tag + ' not found.')

    # Convert date strings to proper dates
    company_data['end']= pd.to_datetime(company_data['end'])
    company_data['filed']= pd.to_datetime(company_data['filed'])

    return company_data

# Create financial statements

class FinStatement(object):

    def __init__(self, df, attribs, starting_year, ending_year=None):
        self.attribs = attribs
        self.starting_year = starting_year
        # narrow down the dataframe to only the items of interest

        self.df = df[(df.tag.isin(attribs)) & (df.fy >= starting_year) & (df.form == '10-K') & (df.end.dt.year == df.fy) & (df.frame.isnull())]

        if ending_year:
            self.df = self.df[self.df.fy <= ending_year]
            self.ending_year = ending_year


class BalanceSheet(FinStatement):

    def __init__(self, df, starting_year, ending_year=None):
        FinStatement.__init__(self, df, ['Assets','LiabilitiesCurrent','Liabilities','LiabilitiesAndStockholdersEquity','AssetsCurrent', 'Goodwill'], starting_year, ending_year)

class IncomeStatement(FinStatement):

    def __init__(self, df, starting_year):
        FinStatement.__init__(['Assets'])

class CashFlowStatement(FinStatement):

    def __init__(self, df, starting_year):
        FinStatement.__init__(['Assets'])

