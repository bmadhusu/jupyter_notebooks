import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
import pandas as pd
import datetime as datetime
import matplotlib.dates as mdates
import requests
import yfinance as yf


def get_data_from_multpl_site():
    # From: https://stackoverflow.com/questions/6325216/parse-html-table-to-python-list
    
    url = r'https://www.multpl.com/s-p-500-dividend-yield/table/by-month'
    tables = pd.read_html(url) # Returns list of all tables on page
    sp500_div_table = tables[0] # Select table of interest

    sp500_div_table.Date = sp500_div_table['Date'].astype('datetime64[ns]')
    sp500_div_table.rename(columns={'Yield Value': 'DivYield'}, inplace=True)
    sp500_div_table.DivYield = sp500_div_table.DivYield.str.extract('(\d+.\d+)',expand=False).astype(float)/100.0
    sp500_div_table.set_index(sp500_div_table['Date'].dt.month.astype(str)+'-'+sp500_div_table['Date'].dt.year.astype(str), inplace=True)

    sp500_div_table = sp500_div_table.tail(-1) # drop 1st row

    url = r'https://www.multpl.com/s-p-500-pe-ratio/table/by-month'
    tables = pd.read_html(url) # Returns list of all tables on page
    sp500_pe_table = tables[0] # Select table of interest


    sp500_pe_table.Date = sp500_pe_table['Date'].astype('datetime64[ns]')
    sp500_pe_table.rename(columns={'Value Value': 'PE'}, inplace=True)
    sp500_pe_table.PE = sp500_pe_table.PE.str.extract('(\d+.\d+)', expand=False).astype(float)
    sp500_pe_table.set_index(sp500_pe_table['Date'].dt.month.astype(str)+'-'+sp500_pe_table['Date'].dt.year.astype(str), inplace=True)

    sp500_pe_table = sp500_pe_table.tail(-1) # drop 1st row

    url = r'https://www.multpl.com/10-year-treasury-rate/table/by-month'
    tables = pd.read_html(url) # Returns list of all tables on page
    tsy_yield_table = tables[0] # Select table of interest

    tsy_yield_table.Date = tsy_yield_table['Date'].astype('datetime64[ns]')
    tsy_yield_table.rename(columns={'Value Value': 'TsyYield'}, inplace=True)
    tsy_yield_table.TsyYield = tsy_yield_table.TsyYield.str.extract('(\d+.\d+)',expand=False).astype(float)/100.0

    tsy_yield_table.set_index(tsy_yield_table['Date'].dt.month.astype(str)+'-'+tsy_yield_table['Date'].dt.year.astype(str), inplace=True)

    tsy_yield_table = tsy_yield_table.tail(-1)

    # MERGE RESULTS
    temp_df = pd.merge(sp500_pe_table.iloc[:,1], sp500_div_table.iloc[:,1], left_index=True, right_index=True)

    temp_df = pd.merge(temp_df, tsy_yield_table.iloc[:,1],left_index=True, right_index=True)
    # return sp500_div_table, sp500_pe_table,tsy_yield_table
    return temp_df

def get_data_from_shiller():

    temp_df = pd.read_excel("http://www.econ.yale.edu/~shiller/data/ie_data.xls",sheet_name='Data',skiprows=8,usecols="A:M",names=['date','s&p comp price','s&p comp div','s&p comp earnings','CPI',
                        'date fraction','int rate GS10','real price','real div','real total ret price', 'real earnings','real tr scaled earnings','CAPE'],header=None,skipfooter=1)

    temp_df['date']=temp_df['date'].astype(str)
    temp_df.set_index('date', inplace=True)
    return temp_df

def get_datasets():
    return get_data_from_multpl_site(), get_data_from_shiller()

def calcJBWSP500(tbl, month, year):
    
    indx = str(month)+'-'+str(year)
    growth = tbl.loc[indx, "DivYield"]+.05
    tsy_yield = tbl.loc[indx, "TsyYield"]

    df = pd.DataFrame({"DivYield": [tbl.loc[indx, "DivYield"]],
                       "Total Return": [growth],
                       "10-yr Tsy Rate": [tsy_yield],
                       "Tot Return - 10yr Tsy": [growth - tsy_yield]})
    
    # if growth > tsy_yield:
    #     s = f'Growth {growth:.4f} is larger than TsyYield of {tsy_yield:.4f}; Diff is {growth-tsy_yield:.4f}; May be OK to enter market!'
    # else:
    #     s = f'Growth {growth:.4f} is smaller than TsyYield of {tsy_yield:.4f}; Diff is {growth-tsy_yield:.4f}; Market may be bubbly!'

    return df

def calcBogle(tbl, month, year,future_pes=[10,15,20,25,30]):

    print(f"Assuming long-run growth of earnings of 5%")
    indx = str(month) + '-' + str(year)
    div_yield = tbl.loc[indx, "DivYield"]
    tsy_yield = tbl.loc[indx, "TsyYield"]
    pe = tbl.loc[indx, "PE"]

    scenarios_df = pd.DataFrame({'Earnings Growth %':[.05]*len(future_pes)})
    scenarios_df['PE in 10 years'] = future_pes

    print(f'PE on {indx} is: {pe}')
    scenarios_df['PE Growth'] = pow((scenarios_df['PE in 10 years']/pe),(1/10))-1
    scenarios_df['TotalReturn'] = div_yield + .05 + scenarios_df['PE Growth']
    scenarios_df['TsyYield'] = tsy_yield
    scenarios_df['TotReturn - TsyYield'] = scenarios_df['TotalReturn'] - scenarios_df['TsyYield']

    return scenarios_df

def calcShillerCAEP(tbl, month, year):

    print("Using 2.5% as long run inflation rate; may not apply now!")

    indx = str(year)+'.'

    "Sticking a leading 0 in front of month if needed"
    mth = str(month)
    if len(mth) < 2:
        indx += '0'
    indx += mth

    cape = tbl.loc[indx, 'CAPE']
    caep = (1/cape) * 100
    tsy_rate = tbl.loc[indx, 'int rate GS10']
    real_tsy_rate = tsy_rate - 2.5
    total_ret = caep - real_tsy_rate

    temp_df = pd.DataFrame({'CAPE': [cape],
                            'CAEP': [caep],
                            'TSY RATE': [tsy_rate],
                            'REAL TSY RATE': [real_tsy_rate],
                            'TOT RET': [total_ret]})


    return temp_df

def get_ticker(tkr):
    tkr_data = yf.Ticker(tkr)

    return tkr_data
# .history(start="2020-06-02", end="2020-06-07", interval="1m")

def calcJBWforTikr(tikr, tsy_yield, div_growth = .05):

    try:
        divYield = tikr.info['dividendYield']
    except:
        print(f"No dividend for {tikr}")
        return

    growth = divYield + div_growth

    df = pd.DataFrame({"DivYield": [divYield],
                       "Total Return": [growth],
                       "10-yr Tsy Rate": [tsy_yield],
                       "Tot Return - 10yr Tsy": [growth - tsy_yield]})
    
    return df

def calcIRRforTikr(tikr, rate1, num_years1, rate2):

    # Take dividend and extrapolate by rate1 for num_years1 length of time
    # Then apply rate2 after num_years1 until year 100
    # Then calc IRR using negative of today's stock price to see what return is

    dividend = tikr.info['dividendRate']

    s1 = pd.Series([rate1]*num_years1)
    s2 = pd.Series([rate2] * (100-num_years1))

    s = pd.concat([s1, s2])
    s.index=range(1,101)

    df = pd.DataFrame(data={"Year": range(1,101),
                       "GrowthRate": (1+s)})

# https://stackoverflow.com/questions/34224990/how-to-calculate-compound-interest-by-day-in-pandas
    df['Dividend'] = df['GrowthRate'].cumprod()*dividend

    fv_s = [-tikr.info['currentPrice']]+df['Dividend'].tolist()

    print(f"Current Price is: {tikr.info['currentPrice']}")
    Solution = npf.irr(fv_s)
    print(f"Returning result as %")
    return Solution * 100

def calcJBWFromShareholderYield(d_per_share, tips_yield, risk_premium=.04, g=.02):
    """ JBW Variation using Shareholder Yield:
    Add Dividends + Repurchases and calc V = D /(R-g)
    where R = Current 30-year TIPS Yield + Risk_Premium_I_Desire & g = long-term-growth rate (~.02)
    d_per_share represents (dividends + shareholder buybacks) / # of shares outstanding
    """

    return (d_per_share)/(tips_yield+risk_premium-g)

def calcBogleForStock(tikr, tsy_yield, earnings_growth=[.05,.10,.05,.10], future_pes=[30,30,15,20]):
    """
    calcBogleForStock takes earnings growth projections and future pe's and calcs
    Bogle Numbers for 10 years out
    """

    pe = tikr.info['trailingPE']
    try:
        div_yield = tikr.info['dividendYield']
    except:
        div_yield = 0

    print(f'Current P/E is {pe}')
    # indx = str(month) + '-' + str(year)
    # div_yield = tbl.loc[indx, "DivYield"]
    # tsy_yield = tbl.loc[indx, "TsyYield"]
    # pe = tbl.loc[indx, "PE"]

    scenarios_df = pd.DataFrame({'Earnings Growth %':earnings_growth})
    # scenarios_df['Earnings Growth %'] = earnings_growth

    # print(f'PE on {indx} is: {pe}')
    scenarios_df['PE in 10 years'] = future_pes
    scenarios_df['PE Growth %'] = pow((scenarios_df['PE in 10 years']/pe),(1/10))-1
    scenarios_df['TotalReturn'] = div_yield + scenarios_df['Earnings Growth %'] + scenarios_df['PE Growth %']
    scenarios_df['TsyYield'] = tsy_yield
    scenarios_df['TotReturn - TsyYield'] = scenarios_df['TotalReturn'] - scenarios_df['TsyYield']

    return scenarios_df
    



