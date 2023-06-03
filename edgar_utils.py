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

# Create financial statements

class FinStatement(object):

    def __init__(self, df, starting_year, ending_year=None):
        #self.attribs = attribs
        self.starting_year = starting_year
        # narrow down the dataframe to only the items of interest

        self.df = df

        # NOTE: Capturing 10Ks & 8Ks because sometimes the 8Ks supplant the info in the 10Ks
        # Doesn't happen very much, but 2018 8-K for KO has a different value for NetInventory
        # so caused a problem; see below for a neat trick to filter out
        self.df = self.df[(self.df.form.isin(['10-K', '8-K']))]

        

class BalanceSheet(FinStatement):

    def filterMarketableSecurities(df):
        return_df = df[df.tag.isin(['MarketableSecuritiesCurrent', 'MarketableSecurities'])]

        return return_df


    def __init__(self, df, starting_year, ending_year=None):
        FinStatement.__init__(self, df, starting_year, ending_year)

        #self.df = self.filterMarketableSecurities(self.df)

        self.df.loc[self.df.tag=='MarketableSecuritiesCurrent',"tag"]='MarketableSecurities'


        self.attribs = ['InventoryNet','MarketableSecurities','AccountsReceivableNetCurrent','CashAndCashEquivalentsAtCarryingValue','LongTermDebtNoncurrent', 'Assets','LiabilitiesCurrent','Liabilities','StockholdersEquity','LiabilitiesAndStockholdersEquity','AssetsCurrent', 'Goodwill']
        # self.df = self.df[(self.df.tag.isin(self.attribs)) & (self.df.fy >= starting_year) & (self.df.end.dt.year == self.df.fy) & (self.df.frame.isnull())]

        self.df = self.df[(self.df.tag.isin(self.attribs)) & (self.df.fy >= starting_year) & (self.df.end.dt.year == self.df.fy) ]

        if ending_year:
            self.df = self.df[self.df.fy <= ending_year]
            self.ending_year = ending_year

        # below is useful trick to filter out dupes based on a certain criteria
        # https://stackoverflow.com/questions/68624884/pandas-how-to-use-groupby-and-max-to-select-the-rows-with-max-date

        temp_df = self.df[self.df.groupby('fy').filed.transform('max') == self.df.filed]
        self.df = pd.pivot(temp_df, index=['fy'], columns='tag',values='val')

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

        self.df.loc[self.df.tag=='RevenueFromContractWithCustomerExcludingAssessedTax',"tag"]='Revenues'
        self.df.loc[self.df.tag=='GeneralAndAdministrativeExpense', "tag"] = 'SellingGeneralAndAdministrativeExpense' 
        self.df.loc[self.df.tag=='CostsAndExpenses', "tag"] = 'OperatingExpenses'

        self.df = filterPeriodStatement(self.df)

        self.attribs = ['IncomeTaxExpenseBenefit','IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest','InterestExpense','SellingGeneralAndAdministrativeExpense','OperatingExpenses','GrossProfit','Revenues','OperatingIncomeLoss','NetIncomeLoss','EarningsPerShareDiluted', 'WeightedAverageNumberOfDilutedSharesOutstanding']

        self.df = self.df[(self.df.tag.isin(self.attribs) & (self.df.fy >= starting_year))]

        if ending_year:
            self.df = self.df[self.df.fy <= ending_year]
            self.ending_year = ending_year

        temp_df = self.df.filter(items=['val', 'fy', 'tag']).drop_duplicates() # get unique vals only; may need to revisit
        self.df = pd.pivot(temp_df, index=['fy'], columns='tag',values='val')


class CashFlowStatement(FinStatement):

    def __init__(self, df, starting_year, ending_year=None):
        FinStatement.__init__(self, df, starting_year, ending_year)

        self.df = filterPeriodStatement(self.df)

        self.attribs = ['DepreciationDepletionAndAmortization','ShareBasedCompensation','NetCashProvidedByUsedInOperatingActivities','PaymentsToAcquirePropertyPlantAndEquipment']
        self.df = self.df[(self.df.tag.isin(self.attribs) & (self.df.fy >= starting_year))]

        if ending_year:
            self.df = self.df[self.df.fy <= ending_year]
            self.ending_year = ending_year

        self.df = pd.pivot(self.df, index=['fy'], columns='tag',values='val')


class MetricsMethodology(object):

    def __init__(self, bs, income, cfs=None):
        self.bs = bs
        self.income = income
        self.cfs = cfs

def negative_red(val):
    color = 'red' if val < 0 else 'green'
    return 'color: %s' % color

class Mizrahi(MetricsMethodology):

    def __init__(self, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)
        
        self.metrics = pd.DataFrame(index=bs.df.index)
        self.metrics['Sales'] = self.income.df.Revenues
        self.metrics['Sales_YoY'] = self.metrics.Sales.pct_change(periods=1)

        self.metrics['NI'] = self.income.df.NetIncomeLoss
        self.metrics['Equity'] = self.bs.df.StockholdersEquity
        self.metrics['ROE'] = self.metrics.NI / self.metrics.Equity
        self.metrics['ROE_YoY'] = self.metrics.ROE.pct_change(periods=1)

        
        self.metrics['Oper Margin'] = self.income.df['OperatingIncomeLoss'] / self.metrics.Sales
        self.metrics['Oper Margin_YoY'] = self.metrics['Oper Margin'].pct_change()

        self.metrics['NPM'] = self.metrics.NI / self.metrics.Sales
        self.metrics['NPM_YoY'] = self.metrics.NPM.pct_change(periods=1)


        self.metrics['EPS-DILUTED'] = self.income.df.EarningsPerShareDiluted
        self.metrics['EPS_YoY'] = self.metrics['EPS-DILUTED'].pct_change()
        self.metrics['No. Shares Diluted'] = self.income.df.WeightedAverageNumberOfDilutedSharesOutstanding

        self.metrics['CurrentRatio'] = self.bs.df['AssetsCurrent'] / self.bs.df['LiabilitiesCurrent']

        if 'LongTermDebtNoncurrent' in self.bs.df.columns:
            self.metrics['Solvency (D/E Ratio)'] = self.bs.df['LongTermDebtNoncurrent']/self.bs.df['StockholdersEquity']
            self.metrics['Solvency_YoY'] = self.metrics['Solvency (D/E Ratio)'].pct_change()

        self.metrics['FCF'] = self.cfs.df['NetCashProvidedByUsedInOperatingActivities'] - self.cfs.df['PaymentsToAcquirePropertyPlantAndEquipment']
        self.metrics['FCF_YoY'] = self.metrics['FCF'].pct_change()

        self.metrics['FCF Margin'] = self.metrics['FCF'] / self.metrics['Sales']
        self.metrics['FCF Margin_YoY'] = self.metrics['FCF Margin'].pct_change()


    def pretty(self):

# https://stackoverflow.com/questions/43102734/format-a-number-with-commas-to-separate-thousands
        
        return self.metrics.style.applymap(negative_red,subset=['ROE_YoY', 'Sales_YoY','NPM_YoY', 'Oper Margin_YoY','EPS_YoY', 'FCF_YoY','FCF Margin_YoY']).format({"NI": "{:,.0f}", "Equity": "{:,.0f}",
                                                           "Sales": "{:,.0f}", "No. Shares Diluted": "{:,.0f}",
                                                           "ROE": "{:,.2%}", "ROE_YoY": "{:,.2%}","Sales_YoY": "{:,.2%}",
                                                            "Oper Margin": "{:,.2%}","Oper Margin_YoY": "{:,.2%}",
                                                           "NPM": "{:,.2%}","NPM_YoY": "{:,.2%}", "EPS_YoY": "{:,.2%}",
                                                            "Solvency (D/E Ratio)": "{:,.2%}", "Solvency_YoY": "{:,.2%}",
                                                            "FCF": "{:,.0f}", "FCF_YoY": "{:,.2%}",
                                                            "FCF Margin": "{:,.2%}","FCF Margin_YoY": "{:,.2%}"})


class ThreeBrians(MetricsMethodology):

    def __init__(self, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)
        
        self.metrics = pd.DataFrame(index=bs.df.index)

        self.metrics['Sales'] = self.income.df.Revenues
        self.metrics['Sales_YoY'] = self.metrics.Sales.pct_change(periods=1)
        self.metrics['NI'] = self.income.df.NetIncomeLoss
        self.metrics['OperatingCashFlow'] = self.cfs.df['NetCashProvidedByUsedInOperatingActivities']
        self.metrics['FCF'] = self.cfs.df['NetCashProvidedByUsedInOperatingActivities'] - self.cfs.df['PaymentsToAcquirePropertyPlantAndEquipment']

        self.metrics['Equity'] = self.bs.df.StockholdersEquity
        self.metrics['ROE'] = self.metrics.NI / self.metrics.Equity
        self.metrics['ROE_YoY'] = self.metrics.ROE.pct_change(periods=1)



        if 'GrossProfit' in self.income.df.columns:
            self.metrics['Gross Margin'] = self.income.df['GrossProfit'] / self.metrics.Sales
            self.metrics['Gross Margin_YoY'] = self.metrics['Gross Margin'].pct_change()
        
        self.metrics['Oper Margin'] = self.income.df['OperatingIncomeLoss'] / self.metrics.Sales
        self.metrics['Oper Margin_YoY'] = self.metrics['Oper Margin'].pct_change()

        self.metrics['NPM'] = self.metrics.NI / self.metrics.Sales
        self.metrics['NPM_YoY'] = self.metrics.NPM.pct_change(periods=1)

        self.metrics['OperCashFlow_YoY'] = self.metrics['OperatingCashFlow'].pct_change()

        self.metrics['FCF_YoY'] = self.metrics['FCF'].pct_change()

        self.metrics['FCF Margin'] = self.metrics['FCF'] / self.metrics['Sales']
        self.metrics['FCF Margin_YoY'] = self.metrics['FCF Margin'].pct_change()

        self.metrics['EPS-DILUTED'] = self.income.df.EarningsPerShareDiluted
        self.metrics['EPS_YoY'] = self.metrics['EPS-DILUTED'].pct_change()
        self.metrics['No. Shares Diluted'] = self.income.df.WeightedAverageNumberOfDilutedSharesOutstanding
        self.metrics['SharesOutstanding_YoY'] = self.metrics['No. Shares Diluted'].pct_change()

        # May include this back at some point but initially, it'll be too much noise
        # may drill into if further analysis is required, but otherwise leave for now

        # if 'SellingGeneralAndAdministrativeExpense' in self.income.df.columns:
        #     self.metrics['SGA%'] = self.income.df['SellingGeneralAndAdministrativeExpense'] / self.income.df['GrossProfit']
        #     self.metrics['SGA%_YoY'] = self.metrics['SGA%'].pct_change()
        # elif 'OperatingExpenses' in self.income.df.columns:
        #     self.metrics['OperExpenses'] = self.income.df['OperatingExpenses'] / self.income.df['GrossProfit']
        #     self.metrics['OperExpenses_YoY'] = self.metrics['OperExpenses'].pct_change()
        

        self.metrics['CurrentRatio'] = self.bs.df['AssetsCurrent'] / self.bs.df['LiabilitiesCurrent']
        self.metrics['QuickRatio'] = (self.bs.df['AccountsReceivableNetCurrent'] + self.bs.df['CashAndCashEquivalentsAtCarryingValue'] + self.bs.df['MarketableSecurities'])/ self.bs.df['LiabilitiesCurrent']

        if 'LongTermDebtNoncurrent' in self.bs.df.columns:
            self.metrics['Solvency (D/E Ratio)'] = self.bs.df['LongTermDebtNoncurrent']/self.bs.df['StockholdersEquity']
            self.metrics['Solvency_YoY'] = self.metrics['Solvency (D/E Ratio)'].pct_change()

        self.metrics['Goodwill-to-Assets Ratio'] = self.bs.df['Goodwill'] / self.bs.df['Assets']
        self.metrics['GtoA_YoY'] = self.metrics['Goodwill-to-Assets Ratio'].pct_change()

        self.metrics['SBC%'] = self.cfs.df['ShareBasedCompensation'] / self.metrics.Sales
        self.metrics['SBC_YoY'] = self.metrics['SBC%'].pct_change()



        # self.metrics['MoreCashThanDebt?'] = 'N'
        # self.metrics.loc[self.bs.df['CashAndCashEquivalentsAtCarryingValue']>
        #                  self.bs.df['LongTermDebtNoncurrent'],'MoreCashThanDebt?'] = 'Y'

    def pretty(self):

# https://stackoverflow.com/questions/43102734/format-a-number-with-commas-to-separate-thousands
        
        # return self.metrics.style.applymap(negative_red,subset=['ROE_YoY','SBC_YoY','Solvency_YoY','SharesOutstanding_YoY','Sales_YoY','NPM_YoY','EPS_YoY','FCF_YoY','FCF Margin_YoY','Oper Margin_YoY','GtoA_YoY','Gross Margin_YoY']).format({"NI": "{:,.0f}", "Equity": "{:,.0f}",
        #                                                     "Gross Margin": "{:,.2%}", "SharesOutstanding_YoY":"{:,.2%}",
        #                                                    "Sales": "{:,.0f}", "No. Shares Diluted": "{:,.0f}",
        #                                                    "ROE": "{:,.2%}", "ROE_YoY": "{:,.2%}","Sales_YoY": "{:,.2%}",
        #                                                     "Oper Margin": "{:,.2%}","Oper Margin_YoY": "{:,.2%}",
        #                                                    "NPM": "{:,.2%}","NPM_YoY": "{:,.2%}", "EPS_YoY": "{:,.2%}",
        #                                                     "Solvency (D/E Ratio)": "{:,.2%}", "Solvency_YoY": "{:,.2%}",
        #                                                     "FCF": "{:,.0f}", "FCF_YoY": "{:,.2%}",
        #                                                     "FCF Margin": "{:,.2%}","FCF Margin_YoY": "{:,.2%}",
        #                                                     "GtoA_YoY": "{:,.2%}", "Gross Margin_YoY": "{:,.2%}",
        #                                                     "OperatingCashFlow": "{:,.0f}",
        #                                                     "SBC%": "{:,.2%}", "SBC_YoY": "{:,.2%}"
        #                                                     })

        return self.metrics.style.applymap(negative_red,subset=['ROE_YoY','SBC_YoY','SharesOutstanding_YoY','Sales_YoY','NPM_YoY','EPS_YoY','FCF_YoY','FCF Margin_YoY','Oper Margin_YoY','GtoA_YoY']).format({"NI": "{:,.0f}", "Equity": "{:,.0f}",
                                                            "SharesOutstanding_YoY":"{:,.2%}",
                                                           "Sales": "{:,.0f}", "No. Shares Diluted": "{:,.0f}",
                                                           "ROE": "{:,.2%}", "ROE_YoY": "{:,.2%}","Sales_YoY": "{:,.2%}",
                                                            "Oper Margin": "{:,.2%}","Oper Margin_YoY": "{:,.2%}",
                                                           "NPM": "{:,.2%}","NPM_YoY": "{:,.2%}", "EPS_YoY": "{:,.2%}",
                                                            "Solvency (D/E Ratio)": "{:,.2%}", "Solvency_YoY": "{:,.2%}",
                                                            "FCF": "{:,.0f}", "FCF_YoY": "{:,.2%}",
                                                            "FCF Margin": "{:,.2%}","FCF Margin_YoY": "{:,.2%}",
                                                            "GtoA_YoY": "{:,.2%}",
                                                            "OperatingCashFlow": "{:,.0f}",
                                                            "SBC%": "{:,.2%}", "SBC_YoY": "{:,.2%}"
                                                            })


class Buffett(MetricsMethodology):

    def __init__(self, bs, income, cfs):
        MetricsMethodology.__init__(self, bs, income, cfs)
        
        self.metrics = pd.DataFrame(index=bs.df.index)
        self.report = pd.DataFrame(index=bs.df.index)


    def pretty(self):
        return self.metrics.style.applymap(negative_red,subset=['ROE_YoY','SBC_YoY','SharesOutstanding_YoY','Sales_YoY','NPM_YoY','EPS_YoY','FCF_YoY','FCF Margin_YoY','Oper Margin_YoY','GtoA_YoY']).format({"NI": "{:,.0f}", "Equity": "{:,.0f}",
                                                            "SharesOutstanding_YoY":"{:,.2%}",
                                                           "Sales": "{:,.0f}", "No. Shares Diluted": "{:,.0f}",
                                                           "ROE": "{:,.2%}", "ROE_YoY": "{:,.2%}","Sales_YoY": "{:,.2%}",
                                                            "Oper Margin": "{:,.2%}","Oper Margin_YoY": "{:,.2%}",
                                                           "NPM": "{:,.2%}","NPM_YoY": "{:,.2%}", "EPS_YoY": "{:,.2%}",
                                                            "Solvency (D/E Ratio)": "{:,.2%}", "Solvency_YoY": "{:,.2%}",
                                                            "FCF": "{:,.0f}", "FCF_YoY": "{:,.2%}",
                                                            "FCF Margin": "{:,.2%}","FCF Margin_YoY": "{:,.2%}",
                                                            "GtoA_YoY": "{:,.2%}",
                                                            "OperatingCashFlow": "{:,.0f}",
                                                            "SBC%": "{:,.2%}", "SBC_YoY": "{:,.2%}"
                                                            })

    def report_qualitative(self):

        cols = [
            'GrossMargin',
            'R&D',
            'NPM',
            'SGA',
            'InterestExpense',
            'DepreciationAmortizationExpense',
            'IncomeTaxScrutiny',
            'Asset Sale - Entry Other',
            'Inventory',
            'NetReceivables'
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
        self.metrics['NetReceivables'] = self.bs.df['AccountsReceivableNetCurrent'] / self.income.df['Revenues']

        
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
                self.metrics['NPM'] >= .2,
                (self.metrics['NPM'] < .2) &
                (self.metrics['NPM'] >= .1),
                self.metrics['NPM'] < .1
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
             ['NPM implies DCA',
              'NPM implies grey area; may or may have some DCA',
              'NPM implies highly competitive industry; hard to see DCA'
              ],
              [
                  "Fantastic! Keeping SGA down",
                  "May be OK; Sometimes necessary to keep DCA",
                  "Too excessive"
              ],
              [
                  "Company may have tough competition",
                  "Little to no interest expense; great!"
              ],
              [
                  "Higher depreciation % => may have no DCA",
                  "Little to no deprec expense; great!"
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
              ]


        ]



        for i in range(len(cols)):
            self.report[cols[i]] = np.select(conditions[i], values[i], default=np.nan)


        return self.report
    
    def report_quantitative(self):
        return self.metrics
