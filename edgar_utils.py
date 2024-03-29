import datetime
import pandas as pd
import re
import matplotlib as plt
import matplotlib.dates as mdates
import numpy as np
import requests
import yfinance as yf

bs_tag_alternates = {"AccountsPayableAndAccruedLiabilitiesCurrent":"AccountsPayable",
                     "AccountsPayableCurrent":"AccountsPayable",
                     "MarketableSecuritiesCurrent": "MarketableSecurities",
                     "IndefiniteLivedTradeNames":"IndefiniteLivedTrademarks",
                     "OtherIndefiniteLivedIntangibleAssets":"OtherIndefiniteLivedAndFiniteLivedIntangibleAssets",
                     "FiniteLivedIntangibleAssetsNet": "OtherIntangibleAssetsNet",
                     "IntangibleAssetsNetExcludingGoodwill": "OtherIntangibleAssetsNet",
                     "InventoryFinishedGoodsNetOfReserves": "InventoryNet"
                     }
is_tag_alternates = {'RevenueFromContractWithCustomerExcludingAssessedTax':"Revenues",
                     'GeneralAndAdministrativeExpense':'SellingGeneralAndAdministrativeExpense'
                     }
cf_tag_alternates = {'PaymentsToAcquireProductiveAssets':'PaymentsToAcquirePropertyPlantAndEquipment',
                     'Depreciation':'DepreciationDepletionAndAmortization'}


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
            # units=list(response.json()['facts']['us-gaap'][tag]['units'].keys())[0]
            units=list(response.json()['facts']['us-gaap'][tag]['units'].keys())

            for j in range(len(units)):
                
                data = pd.json_normalize(response.json()['facts']['us-gaap'][tag]['units'][units[j]])
                data['tag'] = tag
                data['units'] = units[j]
              
                company_data = pd.concat([company_data, data], ignore_index=True)
        except:
            print(tag + ' not found.')

    # Convert date strings to proper dates
    company_data['end']= pd.to_datetime(company_data['end'])
    company_data['filed']= pd.to_datetime(company_data['filed'])

    return company_data

def check_for_no_conflicts(k, v, df):

    x = df[df.tag.isin([k,v])]
    # x = x.groupby(['fy','tag'])
    y = x.loc[:,['fy','tag']].drop_duplicates()
    z = y.groupby(['fy'])['tag'].count() 
    # If there's an exception, uncomment the print and run again!
    # print(x)
    # print(y)
    # print(z)

    return (z < 2).all()

# Create financial statements

class FinStatement(object):

    def __init__(self, df, ticker, starting_year, ending_year=None):
        #self.attribs = attribs
        self.starting_year = starting_year
        # narrow down the dataframe to only the items of interest

        self.df = df

        self.ticker = ticker


        # NOTE: Capturing 10Ks & 8Ks because sometimes the 8Ks supplant the info in the 10Ks
        # Doesn't happen very much, but 2018 8-K for KO has a different value for NetInventory
        # so caused a problem; see below for a neat trick to filter out
        self.df = self.df[(self.df.form.isin(['10-K', '8-K']))]

        # Eliminate those items with 0s
        self.df = self.df[self.df.val > 0]

        

class BalanceSheet(FinStatement):

    def __init__(self, df, ticker, offset_fy, starting_year, ending_year=None):
        FinStatement.__init__(self, df, ticker, starting_year, ending_year)

        self.offset_fy = offset_fy

        #NOTE : offset_fy should be either 0 or 1
        # needed to account for company's fy being off by calendar year

        # if these alternate tags are used, print out warnings

        for k, v in bs_tag_alternates.items():
            if ~check_for_no_conflicts(k,v,self.df):
                raise ValueError('Both ' + k + ' and ' + v + ' found; Need to disambiguate')

            if (self.df.tag == k).any():
                print("WARN: Found " + k + "; Converting to: " + v)
                self.df.loc[self.df.tag==k,"tag"]=v


        self.attribs = ['LongTermDebtCurrent','MinorityInterest','PreferredStockIncludingAdditionalPaidInCapitalNetOfDiscount','OtherIntangibleAssetsNet','IndefiniteLivedTrademarks','OtherIndefiniteLivedAndFiniteLivedIntangibleAssets','RetainedEarningsAccumulatedDeficit','TreasuryStockValue','InventoryNet','MarketableSecurities','AccountsReceivableNetCurrent','CashAndCashEquivalentsAtCarryingValue','LongTermDebtNoncurrent', 'Assets','LiabilitiesCurrent','Liabilities','StockholdersEquity','LiabilitiesAndStockholdersEquity','AssetsCurrent', 'Goodwill', 'AccountsPayable', 'AccruedIncomeTaxesCurrent', 'OperatingLeaseLiabilityCurrent','ContractWithCustomerLiability','CustomerRefundLiabilityCurrent','AccruedAdvertisingCurrent','DerivativeLiabilitiesCurrent','LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent']
        # self.df = self.df[(self.df.tag.isin(self.attribs)) & (self.df.fy >= starting_year) & (self.df.end.dt.year == self.df.fy) & (self.df.frame.isnull())]

        self.df = self.df[(self.df.tag.isin(self.attribs)) & (self.df.fy >= starting_year) & (self.df.end.dt.year == self.df.fy+self.offset_fy) ]

        if ending_year:
            self.df = self.df[self.df.fy <= ending_year]
            self.ending_year = ending_year

        # below is useful trick to filter out dupes based on a certain criteria
        # https://stackoverflow.com/questions/68624884/pandas-how-to-use-groupby-and-max-to-select-the-rows-with-max-date

        # this occurs when there are multiple tags for a given year, possibly because of an amendment, or 8-K
        # or the 10-K just has multiple figures for the same tag for whatever reason
        temp_df = self.df[self.df.groupby('fy').filed.transform('max') == self.df.filed]
        temp_df = temp_df[temp_df.groupby('fy').end.transform('max') == temp_df.end]

        # return
        self.df = pd.pivot(temp_df, index=['fy'], columns='tag',values='val')

        # For any attribs that weren't available, fill them in and give them np.nan or 0 (tbd?)
        attrib_diffs = list(set(self.attribs) - set(self.df.columns))
        self.df.loc[:,attrib_diffs]=np.nan



        # Some values can be inferred; Plug them in
        # E.g. KO doesn't have liabilities!?! So just calc it!
        self.df['Liabilities'] = self.df['Assets'] - self.df['StockholdersEquity']

def filterPeriodStatement(df):
        
        """
        This is to be used on Statements for a period, not a point in time; hence Cashflow & Income Statement
        not Balance Sheets
        """
        new_df = df
    # Parse out lines in frame column that are CY#### ONLY
        new_df = new_df[~new_df.frame.isna()]

        new_df = new_df[new_df.frame.str.match('CY\d\d\d\d$')]
        new_df['fy'] = new_df.frame.str.extract('CY(\d\d\d\d)',expand=False)
        new_df['fy'] = new_df['fy'].astype(int)

        return new_df



class IncomeStatement(FinStatement):

    def __init__(self, df, starting_year, ending_year=None):
        FinStatement.__init__(self, df, starting_year, ending_year)

        # self.df.loc[self.df.tag=='RevenueFromContractWithCustomerExcludingAssessedTax',"tag"]='Revenues'
        # self.df.loc[self.df.tag=='GeneralAndAdministrativeExpense', "tag"] = 'SellingGeneralAndAdministrativeExpense' 
        #self.df.loc[self.df.tag=='CostsAndExpenses', "tag"] = 'OperatingExpenses'

        for k, v in is_tag_alternates.items():
            if ~check_for_no_conflicts(k,v,self.df):
                raise ValueError('Both ' + k + ' and ' + v + ' found; Need to disambiguate')

            if (self.df.tag == k).any():
                print("WARN: Found " + k + "; Converting to: " + v)
                self.df.loc[self.df.tag==k,"tag"]=v

        self.df = filterPeriodStatement(self.df)

        self.attribs = ['OperatingExpenses','IncomeTaxExpenseBenefit','IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest','InterestExpense','SellingGeneralAndAdministrativeExpense','GrossProfit','Revenues','OperatingIncomeLoss','NetIncomeLoss','EarningsPerShareDiluted', 'WeightedAverageNumberOfDilutedSharesOutstanding']

        self.df = self.df[(self.df.tag.isin(self.attribs) & (self.df.fy >= starting_year))]

        if ending_year:
            self.df = self.df[self.df.fy <= ending_year]
            self.ending_year = ending_year

        temp_df = self.df.filter(items=['val', 'fy', 'tag']).drop_duplicates() # get unique vals only; may need to revisit
        self.df = pd.pivot(temp_df, index=['fy'], columns='tag',values='val')

        # For any attribs that weren't available, fill them in and give them np.nan or 0 (tbd?)
        attrib_diffs = list(set(self.attribs) - set(self.df.columns))
        self.df.loc[:,attrib_diffs]=np.nan


class CashFlowStatement(FinStatement):

    def __init__(self, df, starting_year, ending_year=None):
        FinStatement.__init__(self, df, starting_year, ending_year)

        for k, v in cf_tag_alternates.items():
            if ~check_for_no_conflicts(k,v,self.df):
                raise ValueError('Both ' + k + ' and ' + v + ' found; Need to disambiguate')

            if (self.df.tag == k).any():
                print("WARN: Found " + k + "; Converting to: " + v)
                self.df.loc[self.df.tag==k,"tag"]=v

        self.df = filterPeriodStatement(self.df)

        self.attribs = ['ProceedsFromIssuanceOfCommonStock','PaymentsForRepurchaseOfCommonStock','DepreciationDepletionAndAmortization','ShareBasedCompensation','NetCashProvidedByUsedInOperatingActivities','PaymentsToAcquirePropertyPlantAndEquipment']
        self.df = self.df[(self.df.tag.isin(self.attribs) & (self.df.fy >= starting_year))]

        if ending_year:
            self.df = self.df[self.df.fy <= ending_year]
            self.ending_year = ending_year

        self.df = pd.pivot(self.df, index=['fy'], columns='tag',values='val')

        # For any attribs that weren't available, fill them in and give them np.nan or 0 (tbd?)
        attrib_diffs = list(set(self.attribs) - set(self.df.columns))
        self.df.loc[:,attrib_diffs]=np.nan


class MetricsMethodology(object):

    def __init__(self, bs, income, cfs=None):
        self.bs = bs
        self.income = income
        self.cfs = cfs
        self.metrics = None


    def pretty(self,attribs,nums, pct):

        # https://stackoverflow.com/questions/43102734/format-a-number-with-commas-to-separate-thousands
        
        return self.metrics.style.applymap(negative_red,subset=attribs).format(dict.fromkeys(nums,"{:,.0f}") | dict.fromkeys(pct,"{:,.2%}"))

    def write_spreadsheet(self, writer, sheetname):
        self.metrics.to_excel(writer, sheet_name=sheetname)
        self.report.to_excel(writer, sheet_name=sheetname,startrow=len(self.metrics)+4)
    
def negative_red(val):
    color = 'red' if val < 0 else 'green'
    return 'color: %s' % color

class Mizrahi(MetricsMethodology):

    def __init__(self, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)

        self.metrics = pd.DataFrame(index=bs.df.index)
        self.report = pd.DataFrame(index=bs.df.index)
        self.name = 'Mizrahi'

        
    def report_qualitative(self):

        cols = [
            'Sales',
            'NPM',
            'ROE',
            'OperatingMargin',
            'EPS',
            'FCF',
            'FCF Margin',
            'CurrentRatio',
            'Solvency (D/E)',
            # 'AdjDebtToEquity',
            # 'RetainedEarnings',
            # 'CapEx/NetIncome',
            # 'NetSharesBuyBack'
        ]


        self.metrics['Sales'] = self.income.df.Revenues
        self.metrics['Sales_YoY'] = self.metrics.Sales.pct_change(periods=1)

        self.metrics['NPM'] = self.income.df.NetIncomeLoss / self.income.df.Revenues
        self.metrics['NPM_YoY'] = self.metrics.NPM.pct_change(periods=1)
        self.metrics['ROE'] = self.income.df.NetIncomeLoss / self.bs.df.StockholdersEquity
        self.metrics['ROE_YoY'] = self.metrics.ROE.pct_change(periods=1)

        self.metrics['OperatingMargin'] = self.income.df['OperatingIncomeLoss'] / self.metrics.Sales
        self.metrics['OperatingMargin_YoY'] = self.metrics['OperatingMargin'].pct_change()

        self.metrics['EPS-DILUTED'] = self.income.df.EarningsPerShareDiluted
        self.metrics['EPS_YoY'] = self.metrics['EPS-DILUTED'].pct_change()

        self.metrics['FCF'] = self.cfs.df['NetCashProvidedByUsedInOperatingActivities'] - self.cfs.df['PaymentsToAcquirePropertyPlantAndEquipment']
        self.metrics['FCF_YoY'] = self.metrics['FCF'].pct_change()

        self.metrics['FCF_Margin'] = self.metrics['FCF'] / self.metrics['Sales']
        self.metrics['FCF_Margin_YoY'] = self.metrics['FCF_Margin'].pct_change()

        self.metrics['CurrentRatio'] = self.bs.df['AssetsCurrent'] / self.bs.df['LiabilitiesCurrent']
        self.metrics['Solvency (D/E Ratio)'] = self.bs.df['LongTermDebtNoncurrent']/self.bs.df['StockholdersEquity']
        self.metrics['Solvency_YoY'] = self.metrics['Solvency (D/E Ratio)'].pct_change()


        conditions = [
            [
                self.metrics['Sales_YoY'] >= .1,
                self.metrics['Sales_YoY'] < .1
            ],
            [
                self.metrics['NPM_YoY'] >= .1,
                self.metrics['NPM_YoY'] < .1
            ],
            [
                self.metrics['ROE_YoY'] >= .1,
                self.metrics['ROE_YoY'] < .1,
            ],
            [
                self.metrics['OperatingMargin_YoY'] >= .1,
                self.metrics['OperatingMargin_YoY'] < .1
            ],
            [
                self.metrics['EPS_YoY'] >= .1,
                self.metrics['EPS_YoY'] < 1
            ],
            [
                self.metrics['FCF_YoY'] >= .1,
                self.metrics['FCF_YoY'] < .1
            ],
            [
                self.metrics['FCF_Margin_YoY'] >= .1,
                self.metrics['FCF_Margin_YoY'] < .1
            ],
            [
                self.metrics['CurrentRatio'] >= 1,
                self.metrics['CurrentRatio'] < 1
            ],
            [
                self.metrics['Solvency_YoY'] >= .1,
                self.metrics['Solvency_YoY'] < .1
            ]
        ]

        values = [
            [
                'Sales YoY > 10%',
                'Sales YoY < 10%'
            ],
            [
                'NPM YoY up 10%',
                'NPM YoY under 10%'
            ],
            [
                'ROE YoY up 10%',
                'ROE YoY below 10%'
            ],
            [
                'Operating Margin YoY up 10%',
                'Operating Margin YoY below 10%'
            ],
            [
                'EPS YoY up 10%',
                'EPS YoY below 10%'
            ],
            [
                'FCF YoY up 10%',
                'FCF YoY below 10%'
            ],
            [
                'FCF Margin YoY up 10%',
                'FCF Margin YoY below 10%'
            ],
            [
                'Current Ratio : Good Level!',
                'Current Ratio : Not so hot'
            ],
            [
                'Solvency (D/E) YoY above 10% => Not good',
                'Solvency (D/E) YoY below 10% => Improving'
            ]
        ]

        for i in range(len(cols)):
            self.report[cols[i]] = np.select(conditions[i], values[i], default=np.nan)


        return self.report


    def report_quantitative(self):
        return self.pretty(['Solvency_YoY','ROE_YoY', 'Sales_YoY','NPM_YoY', 'OperatingMargin_YoY','EPS_YoY', 'FCF_YoY','FCF_Margin_YoY'],
                    ['Sales','FCF'],['FCF_Margin','OperatingMargin','ROE','NPM','ROE_YoY', 'Sales_YoY','NPM_YoY', 'OperatingMargin_YoY','EPS_YoY', 'FCF_YoY','FCF_Margin_YoY'])

    def write_spreadsheet(self, writer):
        MetricsMethodology.write_spreadsheet(self, writer, sheetname="Mizrahi")

class Safal(MetricsMethodology):

    def __init__(self, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)

        self.metrics = pd.DataFrame(index=bs.df.index)
        self.report = pd.DataFrame(index=bs.df.index)
        self.name = 'Safal'


    def get_market_metrics(self, ticker):


        # Need code to grab current marketcap & P/E; use GoogleFinance
        ticker_info = yf.Ticker(ticker).info
        
        # return [ticker_info['regularMarketPreviousClose'], 
                # ticker_info['marketCap']]
        # return [ticker_info.keys()]

        self.pe = ticker_info['trailingPE']
        self.marketcap = ticker_info['marketCap']


        
    def report_qualitative(self):

        cols = [
            'GrossMargin',
            'ROE'#,
          #  'MarketCap',
           # 'P/E',
        ]


        self.metrics['GrossProfit'] = self.income.df['GrossProfit']
        self.metrics['GrossProfit_YoY'] = self.income.df['GrossProfit'].pct_change()

        self.metrics['Gross Margin'] = self.income.df['GrossProfit'] / self.income.df.Revenues
        self.metrics['Gross Margin_YoY'] = self.metrics['Gross Margin'].pct_change()

        self.metrics['ROE'] = self.income.df.NetIncomeLoss / self.bs.df.StockholdersEquity
        self.metrics['ROE_YoY'] = self.metrics.ROE.pct_change(periods=1)

        #self.metrics['P/E'] = self.pe
        #self.metrics['MarketCap'] = self.marketcap

        conditions = [
            [
                self.metrics['Gross Margin'] >= .25,
                self.metrics['Gross Margin'] < .25
            ],
            [
                self.metrics['ROE'] >= .2,
                self.metrics['ROE'] < .2,
            ]#,
            # [
            #     self.metrics['MarketCap'] >= 80000000,
            #     self.metrics['MarketCap'] < 80000000
            # ],
            # [
            #     self.metrics['P/E'] <= 25,
            #     self.metrics['P/E'] > 25
            # ]

        ]

        values = [
            [
                'Gross Margins >= 25%',
                'Gross Margins < 25%'
            ],
            [
                'ROE >= 20%',
                'ROE < 20%'
            ]#,
            # [
            #     'MarketCap >= 80MM USD',
            #     'MarketCap < 80MM USD'
            # ],
            # [
            #     'P/E <= 25 :)',
            #     'P/E > 25 :('
            # ]
        ]

        for i in range(len(cols)):
            self.report[cols[i]] = np.select(conditions[i], values[i], default=np.nan)


        return self.report


    def report_quantitative(self):
        return self.pretty(['GrossProfit_YoY','Gross Margin_YoY','ROE_YoY'],
                    ['MarketCap', 'P/E', 'GrossProfit'],['Gross Margin', 'GrossProfit_YoY', 'ROE', 'Gross Margin_YoY','ROE_YoY'])

    def write_spreadsheet(self, writer):
        MetricsMethodology.write_spreadsheet(self, writer, sheetname="Safal")


class ThreeBrians(MetricsMethodology):

    def __init__(self, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)

        self.metrics = pd.DataFrame(index=bs.df.index)
        self.report = pd.DataFrame(index=bs.df.index)
        self.name = '3Brians'

        
    
    def report_qualitative(self):

        cols = [
            'QuickRatio',
            'CurrentRatio',
            'Solvency (D/E)',
            'Goodwill-to-Assets',
            'LessCashThanDebt?',
            'IntangiblesTooHigh?',
            'Goodwill Writedowns?',
            'GrossProfit Growth',
            'OperatingMargin Growth',
            'NPM Growth',
            'EPS Growth',
            'SharesBoughtBack?',
            'ExpenseGrowth',
            'SGASlowdown?',
            'SalesGrowth>ExpenseGrowth',
            'OperatingLeverage?',
            'OperatingCashFlow',
            'CapEx',
            'FCF',
            'SBC',
            'Deprec>CapEx?'
        ]

        self.metrics['QuickRatio'] = (self.bs.df['AccountsReceivableNetCurrent'] + self.bs.df['CashAndCashEquivalentsAtCarryingValue'] + self.bs.df['MarketableSecurities'])/ self.bs.df['LiabilitiesCurrent']

        self.metrics['CurrentRatio'] = self.bs.df['AssetsCurrent'] / self.bs.df['LiabilitiesCurrent']

        
        self.metrics['Solvency (D/E Ratio)'] = self.bs.df['LongTermDebtNoncurrent']/self.bs.df['StockholdersEquity']
        self.metrics['Solvency_YoY'] = self.metrics['Solvency (D/E Ratio)'].pct_change()

        self.metrics['Goodwill-to-Assets'] = self.bs.df['Goodwill'] / self.bs.df['Assets']
        self.metrics['GtoA_YoY'] = self.metrics['Goodwill-to-Assets'].pct_change()

        self.metrics['Cash'] = self.bs.df['CashAndCashEquivalentsAtCarryingValue']

        self.metrics['Intangibles'] = self.bs.df[['IndefiniteLivedTrademarks','OtherIndefiniteLivedAndFiniteLivedIntangibleAssets','Goodwill']].sum(axis=1)

        self.metrics['Goodwill_YoY'] = self.bs.df['Goodwill'].pct_change()

        self.metrics['Sales'] = self.income.df.Revenues
        self.metrics['Sales_YoY'] = self.metrics.Sales.pct_change(periods=1)

        self.metrics['GrossProfit'] = self.income.df['GrossProfit']
        self.metrics['GrossProfit_YoY'] = self.income.df['GrossProfit'].pct_change()

        self.metrics['Gross Margin'] = self.income.df['GrossProfit'] / self.metrics.Sales
        self.metrics['Gross Margin_YoY'] = self.metrics['Gross Margin'].pct_change()

        self.metrics['OperatingMargin'] = self.income.df['OperatingIncomeLoss'] / self.metrics.Sales
        self.metrics['OperatingMargin_YoY'] = self.metrics['OperatingMargin'].pct_change()

        self.metrics['NPM'] = self.income.df.NetIncomeLoss / self.metrics.Sales
        self.metrics['NPM_YoY'] = self.metrics.NPM.pct_change(periods=1)

        
        self.metrics['EPS-DILUTED'] = self.income.df.EarningsPerShareDiluted
        self.metrics['EPS_YoY'] = self.metrics['EPS-DILUTED'].pct_change()

        self.metrics['No. Shares Diluted'] = self.income.df.WeightedAverageNumberOfDilutedSharesOutstanding
        self.metrics['SharesOutstanding_YoY'] = self.metrics['No. Shares Diluted'].pct_change()

        self.metrics['OperatingExpenses_YoY'] = self.income.df['OperatingExpenses'].pct_change()

        self.metrics['SGA%'] = self.income.df['SellingGeneralAndAdministrativeExpense'] / self.income.df['GrossProfit']
        self.metrics['SGA%_YoY'] = self.metrics['SGA%'].pct_change()

        self.metrics['OperExpenses'] = self.income.df['OperatingExpenses'] / self.income.df['GrossProfit']
        self.metrics['OperExpenses_YoY'] = self.metrics['OperExpenses'].pct_change()

        self.metrics['OperatingCashFlow'] = self.cfs.df['NetCashProvidedByUsedInOperatingActivities']
        self.metrics['OperCashFlow_YoY'] = self.metrics['OperatingCashFlow'].pct_change()
        self.metrics['NetIncome'] = self.income.df.NetIncomeLoss
        self.metrics['NetIncome_YoY'] = self.metrics['NetIncome'].pct_change()
        self.metrics['CapEx'] = self.cfs.df['PaymentsToAcquirePropertyPlantAndEquipment']
        self.metrics['FCF'] = self.cfs.df['NetCashProvidedByUsedInOperatingActivities'] - self.metrics['CapEx']

        self.metrics['CapEx_YoY'] = self.metrics['CapEx'].pct_change()
        self.metrics['FCF_YoY'] = self.metrics['FCF'].pct_change()

        self.metrics['FCF Margin'] = self.metrics['FCF'] / self.metrics['Sales']
        self.metrics['FCF Margin_YoY'] = self.metrics['FCF Margin'].pct_change()


        # May include this back at some point but initially, it'll be too much noise
        # may drill into if further analysis is required, but otherwise leave for now


        self.metrics['SBC%'] = self.cfs.df['ShareBasedCompensation'] / self.metrics.Sales
        self.metrics['SBC_YoY'] = self.metrics['SBC%'].pct_change()

        self.metrics['Depreciation'] = self.cfs.df['DepreciationDepletionAndAmortization']

        self.metrics['Equity'] = self.bs.df.StockholdersEquity
        self.metrics['ROE'] = self.income.df.NetIncomeLoss / self.metrics.Equity
        self.metrics['ROE_YoY'] = self.metrics.ROE.pct_change(periods=1)
        
        conditions = [
            [
                self.metrics['QuickRatio'] < 1,
                (self.metrics['QuickRatio'] <= 1.5) &
                (self.metrics['QuickRatio'] >1),
                self.metrics['QuickRatio'] > 1.5
            ],
            [
                self.metrics['CurrentRatio'] < 1,
                (self.metrics['CurrentRatio'] <= 2.5) &
                (self.metrics['CurrentRatio'] >1),
                self.metrics['CurrentRatio'] > 2.5
            ],
            [
                self.metrics['Solvency (D/E Ratio)'] >= 2,
                (self.metrics['Solvency (D/E Ratio)'] < 2) &
                (self.metrics['Solvency (D/E Ratio)'] >= 1),
                self.metrics['Solvency (D/E Ratio)'] < 1
            ],
            [
                self.metrics['Goodwill-to-Assets'] > .5,
                (self.metrics['Goodwill-to-Assets'] > .1) &
                (self.metrics['Goodwill-to-Assets'] <= .5),
                self.metrics['Goodwill-to-Assets'] < .1
            ],
            [
                self.metrics['Cash'] > self.bs.df['LongTermDebtNoncurrent'],
                self.metrics['Cash'] <= self.bs.df['LongTermDebtNoncurrent']
            ],
            [
                self.metrics['Intangibles']/self.bs.df['Assets'] >= .5,
                self.metrics['Intangibles']/self.bs.df['Assets'] < .5
            ],
            [
                self.metrics['Goodwill_YoY'] < 0,
                self.metrics['Goodwill_YoY'] >= 0
            ],
            [
                self.metrics['GrossProfit_YoY'] > 0,
                self.metrics['GrossProfit_YoY'] <= 0
            ],
            [
                self.metrics['OperatingMargin_YoY'] > 0,
                self.metrics['OperatingMargin_YoY'] <= 0
            ],
            [
                self.metrics['NPM_YoY'] > 0,
                self.metrics['NPM_YoY'] <= 0
            ],
            [
                self.metrics['EPS_YoY'] > 0,
                self.metrics['EPS_YoY'] <= 0
            ],
            [
                self.metrics['SharesOutstanding_YoY'] < 0,
                self.metrics['SharesOutstanding_YoY'] >= 0
            ],
            [
                self.metrics['OperatingExpenses_YoY'] <= 0,
                self.metrics['OperatingExpenses_YoY'] > 0
            ],
            [
                self.metrics['SGA%_YoY'] <= 0,
                self.metrics['SGA%_YoY'] > 0,
                True # default fall-through condition
            ],
            [
                self.metrics['Sales_YoY'] > self.metrics['OperatingExpenses_YoY'],
                self.metrics['Sales_YoY'] <= self.metrics['OperatingExpenses_YoY']
            ],
            [
                (self.metrics['NPM_YoY'] > self.metrics['Sales_YoY']) & 
                (self.metrics['OperatingMargin_YoY'] > self.metrics['Sales_YoY']) & 
                (self.metrics['Gross Margin_YoY'] > self.metrics['Sales_YoY']) &
                (self.metrics['NPM_YoY'] > 0) & (self.metrics['OperatingMargin_YoY'] > 0) &
                (self.metrics['Gross Margin_YoY'] > 0) & (self.metrics['Sales_YoY'] > 0)
            ],
            [
                self.metrics['OperCashFlow_YoY'] > self.metrics['NetIncome_YoY'],
                self.metrics['OperCashFlow_YoY'] <= self.metrics['NetIncome_YoY']
            ],
            [
                self.metrics['CapEx_YoY'] <= 0,
                self.metrics['CapEx_YoY'] > 0
            ],
            [
                self.metrics['FCF_YoY'] > 0,
                self.metrics['FCF_YoY'] <= 0
            ],
            [
                self.metrics['SBC%'] > .4,
                self.metrics['SBC%'] <= .4
            ],
            [
                self.metrics['Depreciation'] > self.metrics['CapEx'],
                self.metrics['Depreciation'] <= self.metrics['CapEx']

            ]

        ]

        values = [
            [
                'QuickRatio: < 1.0 => Fragile',
                'QuickRatio: b/w 1 & 1.5 => Robust',
                'QuickRatio: > 1.5 => Antifragile'
             ],
             [
                'CurrentRatio: Fragile',
                'CurrentRatio: Robust',
                'CurrentRatio: Antifragile'
             ],
             [
                 'Solvency is Fragile',
                 'Solvency is Robust',
                 'Solvency is Anti-fragile'
             ],
             [
                 'Goodwill-to-Assets: >.5 => Fragile',
                 'Goodwill-to-Assets: b/w .1 & .5 => Robust',
                 'Goodwill-to-Assets: <.1 => Anti-fragile'
             ],
             [
                 'More Cash than Debt: GREEN LIGHT',
                 'Less Cash than Debt: YELLOW FLAG'
             ],
             [
                 'Intangibles > 50% of assets: YELLOW FLAG',
                 'Intangibles < 50% of assets: OK'
             ],
             [
                 'Goodwill writedowns: Yellow Flag',
                 'Goodwill steady or increasing: Cool'
             ],
             [
                 'Gross Profit YoY is growing',
                 'Gross Profit YoY flat/shrinking'
             ],
             [
                 'Oper Margin YoY is growing',
                 'Oper Margin YoY is flat/shrinking'
             ],
             [
                 'NPM YoY is growing',
                 'NPM YoY is flat/shrinking'
             ],
             [
                 'EPS YoY is growing',
                 'EPS YoY is flat/shrinking'
             ],
             [
                 'Shares Being Bought Back!',
                 'Net Shares buyback not happening'
             ],
             [
                 'Operating Expenses YoY flat/down',
                 'Operating Expenses YoY up!'
             ],
             [
                 'SGA as % of gross profit going down :)',
                 'SGA as % of gross profit going up :(',
                 'Not sure what to make of it'
             ],
             [
                 'SalesGrowth outpacing ExpenseGrowth :)',
                 'SalesGrowth lagging ExpenseGrowth :('
             ],
             [
                 'All margins growing faster than revenues: Operating Leverage!'
             ],
             [
                 'Operating Cash Flow YoY is greater than NetIncome YoY :)',
                 'Operating Cash Flow YoY is less than NetIncome YoY :('
             ],
             [
                 'Capex investment going down :(',
                 'Capex investment going up :)'
             ],
             [
                 'FCF YoY going up :)',
                 'FCF YoY going down :('
             ],
             [
                 'SBC is excessive! For high-growth companies, should cap at 30%',
                 'SBC seems OK'
             ],
             [
                 'Depreciation > CapEx; Yellow Flag :(',
                 'Depreciation < CapEx; OK'
             ]
        ]

        for i in range(len(cols)):
            self.report[cols[i]] = np.select(conditions[i], values[i], default=np.nan)


        return self.report
        
    
    def report_quantitative(self):

        return self.metrics
        # return self.pretty(['Solvency_YoY','ROE_YoY', 'Sales_YoY','NPM_YoY', 'Oper_Margin_YoY','EPS_YoY', 'FCF_YoY','FCF_Margin_YoY'],
        #             ['Sales','FCF'],['QuickRatio','CurrentRatio','ROE','NPM','ROE_YoY', 'Sales_YoY','NPM_YoY', 'Oper_Margin_YoY','EPS_YoY', 'FCF_YoY','FCF_Margin_YoY'])

    def write_spreadsheet(self, writer):
        MetricsMethodology.write_spreadsheet(self, writer, sheetname="3Brians")

class Buffett(MetricsMethodology):

    def __init__(self, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)
        
        self.metrics = pd.DataFrame(index=bs.df.index)
        self.report = pd.DataFrame(index=bs.df.index)
        self.name = 'Buffett'

    def report_qualitative(self):

        cols = [
            'GrossMargin',
            'R&D',
            'SGA',
            'InterestExpense',
            'DepreciationAmortizationExpense',
            'IncomeTaxScrutiny',
            'Asset Sale - Entry Other',
            'Inventory',
            'NetReceivables as Pct of Revenue',
            'AdjDebtToEquity',
            'RetainedEarnings',
            'CapEx/NetIncome',
            'NetSharesBuyBack'
            
        ]

        self.metrics['GrossMargin'] = self.income.df['GrossProfit'] / self.income.df['Revenues']
        self.metrics['R&D'] = 'tbd'
        self.metrics['NPM'] = self.income.df.NetIncomeLoss / self.income.df['Revenues']
        self.metrics['SGA'] = self.income.df['SellingGeneralAndAdministrativeExpense']/self.income.df['GrossProfit']
        self.metrics['InterestExpense'] = self.income.df['InterestExpense'] / self.income.df['OperatingIncomeLoss']
        self.metrics['DepreciationAmortizationExpense'] = self.cfs.df['DepreciationDepletionAndAmortization'] / self.income.df['OperatingIncomeLoss']
        self.metrics['IncomeTaxManualCalc'] = self.income.df['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'] * .21
        self.metrics['ReportedTax'] = self.income.df['IncomeTaxExpenseBenefit']
        self.metrics['EPS-DILUTED'] = self.income.df.EarningsPerShareDiluted
        self.metrics['EPS_YoY'] = self.metrics['EPS-DILUTED'].pct_change()
        self.metrics['EBT'] = self.income.df['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest']
        self.metrics['Inventory'] = self.bs.df['InventoryNet']
        self.metrics['NetIncome'] = self.income.df.NetIncomeLoss
        self.metrics['NetReceivables as % of Sales'] = self.bs.df['AccountsReceivableNetCurrent'] / self.income.df['Revenues']
        self.metrics['ROA'] = self.income.df.NetIncomeLoss / self.bs.df['Assets']
        self.metrics['YearsofNItoPayLTD'] = np.ceil(self.bs.df['LongTermDebtNoncurrent'] / self.income.df.NetIncomeLoss)
        self.metrics['AdjDebtToEquityRatio'] = self.bs.df['LongTermDebtNoncurrent']/(self.bs.df['TreasuryStockValue']+self.bs.df['StockholdersEquity'])
        self.metrics['RetainedEarnings'] = self.bs.df['RetainedEarningsAccumulatedDeficit']
        self.metrics['RetainedYoY'] = self.metrics['RetainedEarnings'].pct_change()
        self.metrics['CapEx/NetIncome'] = self.cfs.df['PaymentsToAcquirePropertyPlantAndEquipment']/self.income.df.NetIncomeLoss
        self.metrics['NetSharesBuyback'] = self.cfs.df['PaymentsForRepurchaseOfCommonStock'] - self.cfs.df['ProceedsFromIssuanceOfCommonStock']

        conditions = [
            [
            self.metrics['GrossMargin'] >= .4,
            (self.metrics['GrossMargin'] >= .2) &
                (self.metrics['GrossMargin'] < .4),
            self.metrics['GrossMargin'] <= .2
            ],
            [
                True
            ],
            [
                self.metrics['SGA'] <= .3,
                (self.metrics['SGA'] > .3) &
                (self.metrics['SGA'] <= .8),
                self.metrics['SGA'] > .8
             ],
             [
                 self.metrics['InterestExpense'] >= .1,
                 self.metrics['InterestExpense'] < .1
             ],
             [
                 self.metrics['DepreciationAmortizationExpense'] >= .1,
                 self.metrics['DepreciationAmortizationExpense'] < .1
             ],
             [
                 abs(self.metrics['ReportedTax']/self.metrics['IncomeTaxManualCalc'] -1) > .05,
                 abs(self.metrics['ReportedTax']/self.metrics['IncomeTaxManualCalc'] -1) <= .05
             ],
             [
                 True
             ],
             [
                 True
             ],
             [
                 True
             ],
             [
                 self.metrics['AdjDebtToEquityRatio'] >= .8,
                 self.metrics['AdjDebtToEquityRatio'] < .8
             ],
             [
                 True
             ],
             [
                 self.metrics['CapEx/NetIncome'] <= .25,
                 (self.metrics['CapEx/NetIncome'] > .25) &
                 (self.metrics['CapEx/NetIncome'] <= .5),
                 self.metrics['CapEx/NetIncome'] > .5
             ],
             [
                 self.metrics['NetSharesBuyback'] > 0,
                 self.metrics['NetSharesBuyback'] < 0
             ]

        ]

        values = [
            ['Gross Margin implies DCA',
             'Gross Margin implies tight competition',
             'Gross Margin implies fierce competition; no 1 company can create sustainable advantage'
             ],
             [
                 'Too Much R&D? tbd'
             ],
              [
                  "SGA < .3 of gross profits :)",
                  "SGA b/w .3 & .8; Sometimes necessary to keep DCA :/",
                  "SGA > .8; Too excessive :("
              ],
              [
                  "Interest expense as % of OI: >= .1 => Company may have tough competition :(",
                  "Interest expense as % of OI: < .1 :)"
              ],
              [
                  "Higher depreciation % of Gross Profits >= .1 => may have no DCA :(",
                  "Little to no deprec % of Gross Profits < .1; great! :)"
              ],
              [
                  "Tax gap may be too wide!",
                  "Taxes seem good"
              ],
              [
                  'Asset Sale: Look for Entry other? TBD'
              ],
              [
                  'Is Inventory going up alongside Net Income?'
              ],
              [
                  'Is Receivables/Sales trending down? This indicates DCA'
              ],
              [
                  'Tsy-Adjusted D/E >= .8 => Indicative of NO DCA :(',
                  'Tsy-Adjusted D/E < .8 => Indicative of DCA :)'
              ],
              [
                  'Is Retained Earnings going up?'
              ],
              [
                  'CapEx/NetIncome is < .25 => DCA likely :)',
                  'CapEx/NetIncome b/w .25 & .5 => May have DCA :/',
                  'CapEx/NetIncome > .5 => Expensive to maintain; Wary of DCA :('
              ],
              [
                  'Shares being bought back. Good!',
                  'Shares Issued, Not so great'
              ]
        ]

        for i in range(len(cols)):
            self.report[cols[i]] = np.select(conditions[i], values[i], default=np.nan)


        return self.report
    
    def report_quantitative(self):
        return self.pretty(['EPS_YoY', 'RetainedYoY'],
                    ['IncomeTaxManualCalc','ReportedTax','EBT','Inventory','RetainedEarnings','NetSharesBuyback'],
                    ['GrossMargin','NPM','SGA','InterestExpense','DepreciationAmortizationExpense', 'NetReceivables','ROA', 'AdjDebtToEquityRatio','RetainedYoY', 'CapEx/NetIncome'])
    
    def write_spreadsheet(self, writer):
        MetricsMethodology.write_spreadsheet(self, writer, sheetname="Buffett")
        # self.report.to_excel(writer, sheetname="Buffett")
    
class KJMarshall(MetricsMethodology):

    def __init__(self, ticker, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)
        
        self.metrics = pd.DataFrame(index=bs.df.index)
        self.report = pd.DataFrame(index=bs.df.index)
        self.name = 'KJMarshall'
        self.ticker = ticker

    def report_qualitative(self):

        cols = [
            'CapitalEmployed',
            'Levered FCF',
            'Unlevered FCF'
            
        ]

        # self.metrics['CapitalEmployed'] = self.bs.df['Assets'] - self.bs.df['AccountsPayable'] - self.bs.df['AccruedIncomeTaxesCurrent'] - self.bs.df['OperatingLeaseLiabilityCurrent'] - self.bs.df['ContractWithCustomerLiability'] - self.bs.df['AccruedAdvertisingCurrent'] - self.bs.df['DerivativeLiabilitiesCurrent'] - self.bs.df['LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent']

        # Below are used for Capital Employed
        self.metrics = self.bs.df.loc[:,['Assets','CashAndCashEquivalentsAtCarryingValue', 'MarketableSecurities', 'AccountsPayable','AccruedIncomeTaxesCurrent','OperatingLeaseLiabilityCurrent','ContractWithCustomerLiability','AccruedAdvertisingCurrent','DerivativeLiabilitiesCurrent','LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent']]
        
        # Oper Income used to calc ROCE
        self.metrics['OperatingIncome'] = self.income.df['OperatingIncomeLoss']
        self.metrics['Levered FCF'] = self.cfs.df['NetCashProvidedByUsedInOperatingActivities'] - self.cfs.df['PaymentsToAcquirePropertyPlantAndEquipment']

        self.metrics['InterestExpense'] = self.income.df['InterestExpense']
        
        self.metrics['ShareholderEquity'] = self.bs.df.StockholdersEquity

        self.metrics['No. Shares Diluted'] = self.income.df.WeightedAverageNumberOfDilutedSharesOutstanding

        self.metrics['Goodwill'] = self.bs.df['Goodwill']
        self.metrics['IndefiniteLivedTrademarks'] = self.bs.df['IndefiniteLivedTrademarks']
        self.metrics['OtherIndefiniteLivedAndFiniteLivedIntangibleAssets'] = self.bs.df['OtherIndefiniteLivedAndFiniteLivedIntangibleAssets']
        self.metrics['OtherIntangibleAssetsNet'] = self.bs.df['OtherIntangibleAssetsNet']

        self.metrics['Liabilities'] = self.bs.df['Liabilities']

        self.metrics['TotalDebt'] = self.bs.df['LongTermDebtCurrent'] + self.bs.df['LongTermDebtNoncurrent']
        self.metrics['MinorityInterest'] = self.bs.df['MinorityInterest']
        self.metrics['PreferredEquity'] = self.bs.df['PreferredStockIncludingAdditionalPaidInCapitalNetOfDiscount']

        conditions = [
            [
                True
            ],
            [
                True
            ],
            [
                True
            ]
        ]

        values = [
            [
                'Check value history of Goodwill to see if needs to be subtracted from Cap Emp'
             ],
             [
                 'Assuming CapEx is all maintenance CapEx unless can get better info from an Inv. Relations call'
             ],
             [
                 'Find out tax rate and apply to Interest; then subtract from Levered FCF'
             ]
        ]

        for i in range(len(cols)):
            self.report[cols[i]] = np.select(conditions[i], values[i], default=np.nan)


        return self.report

    def get_market_metrics(self, ticker):


        # Need code to grab current marketcap & P/E; use GoogleFinance
        ticker_info = yf.Ticker(ticker).info
        
        # return [ticker_info['regularMarketPreviousClose'], 
                # ticker_info['marketCap']]
        # return [ticker_info.keys()]

        self.pe = ticker_info['trailingPE']
        self.marketcap = ticker_info['marketCap']
    
    def report_quantitative(self):
        return self.metrics
        # return self.pretty(['EPS_YoY', 'RetainedYoY'],
        #         ['IncomeTaxManualCalc','ReportedTax','EBT','Inventory','RetainedEarnings','NetSharesBuyback'],
        #          ['GrossMargin','NPM','SGA','InterestExpense','DepreciationAmortizationExpense', 'NetReceivables','ROA', 'AdjDebtToEquityRatio','RetainedYoY', 'CapEx/NetIncome'])

    def write_spreadsheet(self, writer):
        MetricsMethodology.write_spreadsheet(self, writer, sheetname="KJMarshall")


def gather_columns(df, txt):
    return df.filter(regex=txt)

def create_common_metrics(*methods):

    df_common = pd.DataFrame()

    for s in ['Sales', 'Gross','CurrentRatio', 'Solvency', 'NPM', 'ROE', 'OperatingMargin', 'SGA','EPS', 'FCF']:

        # Gather metrics
        for m in methods:
            # df_common = pd.concat([df_common, gather_columns(m.metrics, s)], axis="columns").T.drop_duplicates().T
            df_common = pd.concat([df_common, gather_columns(m.metrics, s)], axis="columns")

        # Now gather commentary
        for m in methods:
            ret_df = gather_columns(m.report, s)
            # Nice trick to append to colnames
            # https://stackoverflow.com/questions/34049618/how-to-add-a-suffix-or-prefix-to-each-column-name
            ret_df.columns = [str(col) + '-' + m.name for col in ret_df.columns]

            df_common = pd.concat([df_common,ret_df],axis="columns")

    # Below trick to get rid of dupe columns from: https://sparkbyexamples.com/pandas/pandas-remove-duplicate-columns-from-dataframe/#:~:text=To%20drop%20duplicate%20columns%20from%20pandas%20DataFrame%20use%20df.,data%20regardless%20of%20column%20names.

    return df_common.T.drop_duplicates().T

    
def write_spreadsheet(fname, common_df, *methods): #, mizrahi, threebrians):
    with pd.ExcelWriter(fname) as writer:

        common_df.to_excel(writer, sheet_name='Common')
   
        for m in methods:
            m.write_spreadsheet(writer)

        # buffett.write_spreadsheet(writer)
        # data_frame2.to_excel(writer, sheet_name="Vegetables", index=False)
        # data_frame3.to_excel(writer, sheet_name="Baked Items", index=False)


   
