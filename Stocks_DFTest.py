import unittest
import pandas as pd
from pandas.testing import assert_frame_equal 
import edgar_utils as eu
import numpy as np

# References
# https://docs.python.org/3/library/unittest.html
# https://stackoverflow.com/questions/27950891/how-to-use-a-pandas-data-frame-in-a-unit-test

df_bs_prototype = pd.DataFrame(columns=['AccountsReceivableNetCurrent',
                                        'Assets',
                                        'AssetsCurrent',
                                        'CashAndCashEquivalentsAtCarryingValue',
                                        'Goodwill',
                                        'InventoryNet',
                                        'Liabilities',
                                        'LiabilitiesAndStockholdersEquity',
                                        'LiabilitiesCurrent',
                                        'LongTermDebtNoncurrent',
                                        'MarketableSecurities',
                                        'RetainedEarningsAccumulatedDeficit',
                                        'StockholdersEquity',
                                        'TreasuryStockValue'],
                                        index=[2014,2015,2016,2017,2018,2019,2020,2021,2022]
                                 )
df_bs_prototype.index.name='fy'
df_bs_prototype.columns.name='tag'
df_bs_prototype = df_bs_prototype.apply(pd.to_numeric)


df_income_prototype = pd.DataFrame(columns=['EarningsPerShareDiluted',
                                            'GrossProfit',
                                            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
                                            'IncomeTaxExpenseBenefit',
                                            'InterestExpense',
                                            'NetIncomeLoss',
                                            'OperatingIncomeLoss',
                                            'Revenues',
                                            'SellingGeneralAndAdministrativeExpense',
                                            'WeightedAverageNumberOfDilutedSharesOutstanding'],
                                   index=[2014,2015,2016,2017,2018,2019,2020,2021,2022])
df_income_prototype.index.name='fy'
df_income_prototype.columns.name='tag'
df_income_prototype = df_income_prototype.apply(pd.to_numeric)


df_cfs_prototype = pd.DataFrame(columns=['DepreciationDepletionAndAmortization',
                                         'NetCashProvidedByUsedInOperatingActivities',
                                         'PaymentsForRepurchaseOfCommonStock',
                                         'PaymentsToAcquirePropertyPlantAndEquipment',
                                         'ProceedsFromIssuanceOfCommonStock',
                                         'ShareBasedCompensation'],
                                index=[2014,2015,2016,2017,2018,2019,2020,2021,2022])
df_cfs_prototype.index.name='fy'
df_cfs_prototype.columns.name='tag'
df_cfs_prototype = df_cfs_prototype.apply(pd.to_numeric)

ko_edgar = eu.get_json_financials_from_tikr('KO')
aapl_edgar = eu.get_json_financials_from_tikr('AAPL')


class DFTests(unittest.TestCase):

    """ class for running unittests """

    def setUp(self):
        """ Your setUp """

        # Neat trick to get the dataframe into a dictionary
        # use: dataframename.to_dict() which will produce the below
        self.df_KO_bs = pd.DataFrame({'AccountsReceivableNetCurrent': {
                                    2014: 4466000000.0,
                                    2015: 3941000000.0,
                                    2016: 3856000000.0,
                                    2017: 3667000000.0,
                                    2018: 3685000000.0,
                                    2019: 3971000000.0,
                                    2020: 3144000000.0,
                                    2021: 3512000000.0,
                                    2022: 3487000000.0},
                                    'Assets': {2014: 92023000000.0,
                                    2015: 89996000000.0,
                                    2016: 87270000000.0,
                                    2017: 87896000000.0,
                                    2018: 83216000000.0,
                                    2019: 86381000000.0,
                                    2020: 87296000000.0,
                                    2021: 94354000000.0,
                                    2022: 92763000000.0},
                                    'AssetsCurrent': {2014: 32986000000.0,
                                    2015: 33395000000.0,
                                    2016: 34010000000.0,
                                    2017: 36545000000.0,
                                    2018: 24930000000.0,
                                    2019: 20411000000.0,
                                    2020: 19240000000.0,
                                    2021: 22545000000.0,
                                    2022: 22591000000.0},
                                    'CashAndCashEquivalentsAtCarryingValue': {2014: 8958000000.0,
                                    2015: 7309000000.0,
                                    2016: 8555000000.0,
                                    2017: 6006000000.0,
                                    2018: 9077000000.0,
                                    2019: 6480000000.0,
                                    2020: 6795000000.0,
                                    2021: 9684000000.0,
                                    2022: 9519000000.0},
                                    'Goodwill': {2014: 12100000000.0,
                                    2015: 11289000000.0,
                                    2016: 10629000000.0,
                                    2017: 9401000000.0,
                                    2018: 14109000000.0,
                                    2019: 16764000000.0,
                                    2020: 17506000000.0,
                                    2021: 19363000000.0,
                                    2022: 18782000000.0},
                                    'IndefiniteLivedTrademarks': {2014: 6533000000.0,
                                    2015: 5989000000.0,
                                    2016: 6097000000.0,
                                    2017: 6729000000.0,
                                    2018: 6682000000.0,
                                    2019: 9266000000.0,
                                    2020: 10395000000.0,
                                    2021: 14465000000.0,
                                    2022: 14214000000.0},
                                    'InventoryNet': {2014: 3100000000.0,
                                    2015: 2902000000.0,
                                    2016: 2675000000.0,
                                    2017: 2655000000.0,
                                    2018: 3071000000.0,
                                    2019: 3379000000.0,
                                    2020: 3266000000.0,
                                    2021: 3414000000.0,
                                    2022: 4233000000.0},
                                    'LiabilitiesAndStockholdersEquity': {2014: 92023000000.0,
                                    2015: 89996000000.0,
                                    2016: 87270000000.0,
                                    2017: 87896000000.0,
                                    2018: 83216000000.0,
                                    2019: 86381000000.0,
                                    2020: 87296000000.0,
                                    2021: 94354000000.0,
                                    2022: 92763000000.0},
                                    'LiabilitiesCurrent': {2014: 32374000000.0,
                                    2015: 26929000000.0,
                                    2016: 26532000000.0,
                                    2017: 27194000000.0,
                                    2018: 28782000000.0,
                                    2019: 26973000000.0,
                                    2020: 14601000000.0,
                                    2021: 19950000000.0,
                                    2022: 19724000000.0},
                                    'LongTermDebtNoncurrent': {2014: 19063000000.0,
                                    2015: 28311000000.0,
                                    2016: 29684000000.0,
                                    2017: 31182000000.0,
                                    2018: 25376000000.0,
                                    2019: 27516000000.0,
                                    2020: 40125000000.0,
                                    2021: 38116000000.0,
                                    2022: 36377000000.0},
                                    'MarketableSecurities': {2014: 3665000000.0,
                                    2015: 4269000000.0,
                                    2016: 4051000000.0,
                                    2017: 5317000000.0,
                                    2018: 5013000000.0,
                                    2019: 3228000000.0,
                                    2020: 2348000000.0,
                                    2021: 1699000000.0,
                                    2022: 1069000000.0},
                                    'RetainedEarningsAccumulatedDeficit': {2014: 63408000000.0,
                                    2015: 65018000000.0,
                                    2016: 65502000000.0,
                                    2017: 60430000000.0,
                                    2018: 63234000000.0,
                                    2019: 65855000000.0,
                                    2020: 66555000000.0,
                                    2021: 69094000000.0,
                                    2022: 71019000000.0},
                                    'StockholdersEquity': {2014: 30320000000.0,
                                    2015: 25554000000.0,
                                    2016: 23062000000.0,
                                    2017: 17072000000.0,
                                    2018: 16981000000.0,
                                    2019: 18981000000.0,
                                    2020: 19299000000.0,
                                    2021: 22999000000.0,
                                    2022: 24105000000.0},
                                    'TreasuryStockValue': {2014: 42225000000.0,
                                    2015: 45066000000.0,
                                    2016: 47988000000.0,
                                    2017: 50677000000.0,
                                    2018: 51719000000.0,
                                    2019: 52244000000.0,
                                    2020: 52016000000.0,
                                    2021: 51641000000.0,
                                    2022: 52601000000.0},
                                    'Liabilities': {2014: np.nan,
                                    2015: np.nan,
                                    2016: np.nan,
                                    2017: np.nan,
                                    2018: np.nan,
                                    2019: np.nan,
                                    2020: np.nan,
                                    2021: np.nan,
                                    2022: np.nan},
                                    'OtherIndefiniteLivedAndFiniteLivedIntangibleAssets': {2014: np.nan,
                                    2015: np.nan,
                                    2016: np.nan,
                                    2017: np.nan,
                                    2018: np.nan,
                                    2019: np.nan,
                                    2020: np.nan,
                                    2021: np.nan,
                                    2022: np.nan}})
        
        self.df_KO_bs.index.name='fy'
        self.df_KO_bs.columns.name='tag'

        self.df_KO_income = pd.DataFrame(
                            {'EarningsPerShareDiluted': {2014: 1.6,
                            2015: 1.67,
                            2016: 1.49,
                            2017: 0.29,
                            2018: 1.5,
                            2019: 2.07,
                            2020: 1.79,
                            2021: 2.25,
                            2022: 2.19},
                            'GrossProfit': {2014: 28109000000.0,
                            2015: 26812000000.0,
                            2016: 25398000000.0,
                            2017: 22491000000.0,
                            2018: 21233000000.0,
                            2019: 22647000000.0,
                            2020: 19581000000.0,
                            2021: 23298000000.0,
                            2022: 25004000000.0},
                            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest': {2014: 9325000000.0,
                            2015: 9605000000.0,
                            2016: 8136000000.0,
                            2017: 6890000000.0,
                            2018: 8225000000.0,
                            2019: 10786000000.0,
                            2020: 9749000000.0,
                            2021: 12425000000.0,
                            2022: 11686000000.0},
                            'IncomeTaxExpenseBenefit': {2014: 2201000000.0,
                            2015: 2239000000.0,
                            2016: 1586000000.0,
                            2017: 5607000000.0,
                            2018: 1749000000.0,
                            2019: 1801000000.0,
                            2020: 1981000000.0,
                            2021: 2621000000.0,
                            2022: 2115000000.0},
                            'InterestExpense': {2014: 483000000.0,
                            2015: 856000000.0,
                            2016: 733000000.0,
                            2017: 853000000.0,
                            2018: 950000000.0,
                            2019: 946000000.0,
                            2020: 1437000000.0,
                            2021: 1597000000.0,
                            2022: 882000000.0},
                            'NetIncomeLoss': {2014: 7098000000.0,
                            2015: 7351000000.0,
                            2016: 6527000000.0,
                            2017: 1248000000.0,
                            2018: 6434000000.0,
                            2019: 8920000000.0,
                            2020: 7747000000.0,
                            2021: 9771000000.0,
                            2022: 9542000000.0},
                            'OperatingIncomeLoss': {2014: 9708000000.0,
                            2015: 8728000000.0,
                            2016: 8657000000.0,
                            2017: 7755000000.0,
                            2018: 9152000000.0,
                            2019: 10086000000.0,
                            2020: 8997000000.0,
                            2021: 10308000000.0,
                            2022: 10909000000.0},
                            'Revenues': {2014: np.nan,
                            2015: np.nan,
                            2016: 41863000000.0,
                            2017: 36212000000.0,
                            2018: 34300000000.0,
                            2019: 37266000000.0,
                            2020: 33014000000.0,
                            2021: 38655000000.0,
                            2022: 43004000000.0},
                            'SellingGeneralAndAdministrativeExpense': {2014: 17218000000.0,
                            2015: 16427000000.0,
                            2016: 15370000000.0,
                            2017: 12834000000.0,
                            2018: 11002000000.0,
                            2019: 12103000000.0,
                            2020: 9731000000.0,
                            2021: 12144000000.0,
                            2022: 12880000000.0},
                            'WeightedAverageNumberOfDilutedSharesOutstanding': {2014: 4450000000.0,
                            2015: 4405000000.0,
                            2016: 4367000000.0,
                            2017: 4324000000.0,
                            2018: 4299000000.0,
                            2019: 4314000000.0,
                            2020: 4323000000.0,
                            2021: 4340000000.0,
                            2022: 4350000000.0},
                            'OperatingExpenses': {2014: np.nan,
                            2015: np.nan,
                            2016: np.nan,
                            2017: np.nan,
                            2018: np.nan,
                            2019: np.nan,
                            2020: np.nan,
                            2021: np.nan,
                            2022: np.nan}})
        
        self.df_KO_income.index.name='fy'
        self.df_KO_income.columns.name='tag'
        
       
        self.df_KO_cfs = df_cfs_prototype
        self.df_KO_cfs.loc[2014]=[1.9760e+09, 1.0615e+10, 4.1620e+09, 2.4060e+09, 1.5320e+09,
        2.0900e+08]
        self.df_KO_cfs.loc[2015]=[1.9700e+09, 1.0528e+10, 3.5640e+09, 2.5530e+09, 1.2450e+09,
        2.3600e+08]
        self.df_KO_cfs.loc[2016]=[1.7870e+09, 8.7920e+09, 3.6810e+09, 2.2620e+09, 1.4340e+09,
        2.5800e+08]
        self.df_KO_cfs.loc[2017]=[1.2600e+09, 7.0410e+09, 3.6820e+09, 1.7500e+09, 1.5950e+09,
        2.1900e+08]
        self.df_KO_cfs.loc[2018]=[1.0860e+09, 7.6270e+09, 1.9120e+09, 1.5480e+09, 1.4760e+09,
        2.2500e+08]
        self.df_KO_cfs.loc[2019]=[1.3650e+09, 1.0471e+10, 1.1030e+09, 2.0540e+09, 1.0120e+09,
        2.0100e+08]
        self.df_KO_cfs.loc[2020]=[1.5360e+09, 9.8440e+09, 1.1800e+08, 1.1770e+09, 6.4700e+08,
        1.2600e+08]
        self.df_KO_cfs.loc[2021]=[1.4520e+09, 1.2625e+10, 1.1100e+08, 1.3670e+09, 7.0200e+08,
        3.3700e+08]
        self.df_KO_cfs.loc[2022]=[1.2600e+09, 1.1018e+10, 1.4180e+09, 1.4840e+09, 8.3700e+08,
        3.5600e+08]

        # self.df_AAPL_bs = df_bs_prototype
        # self.df_AAPL_income = df_income_prototype
        # self.df_AAPL_cfs = df_cfs_prototype
        # self.df_CMG_bs = df_bs_prototype
        # self.df_CMG_income = df_income_prototype
        # self.df_CMG_cfs = df_cfs_prototype

    def test_dataFrame_KO_BS_Expected(self):
        """ Test that the KO BS dataframe is as expected """

        ko_bs = eu.BalanceSheet(ko_edgar,2014)
        #assert_frame_equal(self.df_KO_bs, ko_bs.df)
        assert_frame_equal(self.df_KO_bs.sort_index(axis=1), ko_bs.df.sort_index(axis=1), check_names=True)

    def test_dataFrame_KO_Income_Expected(self):
        """ Test that the KO Income dataframe is as expected """

        ko_income = eu.IncomeStatement(ko_edgar,2014)
        # assert_frame_equal(self.df_KO_income, ko_income.df)
        assert_frame_equal(self.df_KO_income.sort_index(axis=1), ko_income.df.sort_index(axis=1), check_names=True)


    def test_dataFrame_KO_Cashflow_Expected(self):
        """ Test that the KO Cashflow dataframe is as expected """

        ko_cfs = eu.CashFlowStatement(ko_edgar,2014)
        assert_frame_equal(self.df_KO_cfs, ko_cfs.df)

    def test_dataFrame_AAPL_Income_Expected(self):
        """ Test that the AAPL Income dataframe is as expected """

        aapl_income = eu.IncomeStatement(aapl_edgar,2014)

        self.df_AAPL_income = pd.DataFrame(
            {'EarningsPerShareDiluted': {2014: 6.45,
  2015: 9.22,
  2016: 8.31,
  2017: 9.21,
  2018: 2.98,
  2019: 2.97,
  2020: 3.28,
  2021: 5.61,
  2022: 6.11},
 'GrossProfit': {2014: 70537000000.0,
  2015: 93626000000.0,
  2016: 84263000000.0,
  2017: 88186000000.0,
  2018: 101839000000.0,
  2019: 98392000000.0,
  2020: 104956000000.0,
  2021: 152836000000.0,
  2022: 170782000000.0},
 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest': {2014: 53483000000.0,
  2015: 72515000000.0,
  2016: 61372000000.0,
  2017: 64089000000.0,
  2018: 72903000000.0,
  2019: 65737000000.0,
  2020: 67091000000.0,
  2021: 109207000000.0,
  2022: 119103000000.0},
 'IncomeTaxExpenseBenefit': {2014: 13973000000.0,
  2015: 19121000000.0,
  2016: 15685000000.0,
  2017: 15738000000.0,
  2018: 13372000000.0,
  2019: 10481000000.0,
  2020: 9680000000.0,
  2021: 14527000000.0,
  2022: 19300000000.0},
 'InterestExpense': {2014: 384000000.0,
  2015: 733000000.0,
  2016: 1456000000.0,
  2017: 2323000000.0,
  2018: 3240000000.0,
  2019: 3576000000.0,
  2020: 2873000000.0,
  2021: 2645000000.0,
  2022: 2931000000.0},
 'NetIncomeLoss': {2014: 39510000000.0,
  2015: 53394000000.0,
  2016: 45687000000.0,
  2017: 48351000000.0,
  2018: 59531000000.0,
  2019: 55256000000.0,
  2020: 57411000000.0,
  2021: 94680000000.0,
  2022: 99803000000.0},
 'OperatingExpenses': {2014: 18034000000.0,
  2015: 22396000000.0,
  2016: 24239000000.0,
  2017: 26842000000.0,
  2018: 30941000000.0,
  2019: 34462000000.0,
  2020: 38668000000.0,
  2021: 43887000000.0,
  2022: 51345000000.0},
 'OperatingIncomeLoss': {2014: 52503000000.0,
  2015: 71230000000.0,
  2016: 60024000000.0,
  2017: 61344000000.0,
  2018: 70898000000.0,
  2019: 63930000000.0,
  2020: 66288000000.0,
  2021: 108949000000.0,
  2022: 119437000000.0},
 'Revenues': {2014: np.nan,
  2015: np.nan,
  2016: 215639000000.0,
  2017: 229234000000.0,
  2018: 265595000000.0,
  2019: 260174000000.0,
  2020: 274515000000.0,
  2021: 365817000000.0,
  2022: 394328000000.0},
 'SellingGeneralAndAdministrativeExpense': {2014: 11993000000.0,
  2015: 14329000000.0,
  2016: 14194000000.0,
  2017: 15261000000.0,
  2018: 16705000000.0,
  2019: 18245000000.0,
  2020: 19916000000.0,
  2021: 21973000000.0,
  2022: 25094000000.0},
 'WeightedAverageNumberOfDilutedSharesOutstanding': {2014: 6122663000.0,
  2015: 5793069000.0,
  2016: 5500281000.0,
  2017: 5251692000.0,
  2018: 20000435000.0,
  2019: 18595651000.0,
  2020: 17528214000.0,
  2021: 16864919000.0,
  2022: 16325819000.0}}
        )

        self.df_AAPL_income.index.name='fy'
        self.df_AAPL_income.columns.name='tag'
        assert_frame_equal(self.df_AAPL_income, aapl_income.df)

    def test_dataFrame_AAPL_BS_Expected(self):
        """ Test that the AAPL BS dataframe is as expected """

        aapl_bs = eu.BalanceSheet(aapl_edgar,2014)

        self.df_AAPL_bs = pd.DataFrame(
                    {'AccountsReceivableNetCurrent': {2014: 17460000000.0,
  2015: 16849000000.0,
  2016: 15754000000.0,
  2017: 17874000000.0,
  2018: 23186000000.0,
  2019: 22926000000.0,
  2020: 16120000000.0,
  2021: 26278000000.0,
  2022: 28184000000.0},
 'Assets': {2014: 231839000000.0,
  2015: 290479000000.0,
  2016: 321686000000.0,
  2017: 375319000000.0,
  2018: 365725000000.0,
  2019: 338516000000.0,
  2020: 323888000000.0,
  2021: 351002000000.0,
  2022: 352755000000.0},
 'AssetsCurrent': {2014: 68531000000.0,
  2015: 89378000000.0,
  2016: 106869000000.0,
  2017: 128645000000.0,
  2018: 131339000000.0,
  2019: 162819000000.0,
  2020: 143713000000.0,
  2021: 134836000000.0,
  2022: 135405000000.0},
 'CashAndCashEquivalentsAtCarryingValue': {2014: 13844000000.0,
  2015: 21120000000.0,
  2016: 20484000000.0,
  2017: 20289000000.0,
  2018: 25913000000.0,
  2019: 48844000000.0,
  2020: 38016000000.0,
  2021: 34940000000.0,
  2022: 23646000000.0},
 'Goodwill': {2014: 4616000000.0,
  2015: 5116000000.0,
  2016: 5414000000.0,
  2017: 5717000000.0,
  2018: np.nan,
  2019: np.nan,
  2020: np.nan,
  2021: np.nan,
  2022: np.nan},
 'InventoryNet': {2014: 2111000000.0,
  2015: 2349000000.0,
  2016: 2132000000.0,
  2017: 4855000000.0,
  2018: 3956000000.0,
  2019: 4106000000.0,
  2020: 4061000000.0,
  2021: 6580000000.0,
  2022: 4946000000.0},
 'Liabilities': {2014: 120292000000.0,
  2015: 171124000000.0,
  2016: 193437000000.0,
  2017: 241272000000.0,
  2018: 258578000000.0,
  2019: 248028000000.0,
  2020: 258549000000.0,
  2021: 287912000000.0,
  2022: 302083000000.0},
 'LiabilitiesAndStockholdersEquity': {2014: 231839000000.0,
  2015: 290479000000.0,
  2016: 321686000000.0,
  2017: 375319000000.0,
  2018: 365725000000.0,
  2019: 338516000000.0,
  2020: 323888000000.0,
  2021: 351002000000.0,
  2022: 352755000000.0},
 'LiabilitiesCurrent': {2014: 63448000000.0,
  2015: 80610000000.0,
  2016: 79006000000.0,
  2017: 100814000000.0,
  2018: 116866000000.0,
  2019: 105718000000.0,
  2020: 105392000000.0,
  2021: 125481000000.0,
  2022: 153982000000.0},
 'LongTermDebtNoncurrent': {2014: np.nan,
  2015: 53463000000.0,
  2016: 75427000000.0,
  2017: 97207000000.0,
  2018: 93735000000.0,
  2019: 91807000000.0,
  2020: 98667000000.0,
  2021: 109106000000.0,
  2022: 98959000000.0},
 'MarketableSecurities': {2014: np.nan,
  2015: np.nan,
  2016: np.nan,
  2017: np.nan,
  2018: np.nan,
  2019: 51713000000.0,
  2020: 52927000000.0,
  2021: 27699000000.0,
  2022: 24658000000.0},
 'RetainedEarningsAccumulatedDeficit': {2014: 87152000000.0,
  2015: 92284000000.0,
  2016: 96364000000.0,
  2017: 98330000000.0,
  2018: 70400000000.0,
  2019: 45898000000.0,
  2020: 14966000000.0,
  2021: 5562000000.0,
  2022: -3068000000.0},
 'StockholdersEquity': {2014: 111547000000.0,
  2015: 119355000000.0,
  2016: 128249000000.0,
  2017: 134047000000.0,
  2018: 107147000000.0,
  2019: 90488000000.0,
  2020: 65339000000.0,
  2021: 63090000000.0,
  2022: 50672000000.0},
 'IndefiniteLivedTrademarks': {2014: np.nan,
  2015: np.nan,
  2016: np.nan,
  2017: np.nan,
  2018: np.nan,
  2019: np.nan,
  2020: np.nan,
  2021: np.nan,
  2022: np.nan},
 'TreasuryStockValue': {2014: np.nan,
  2015: np.nan,
  2016: np.nan,
  2017: np.nan,
  2018: np.nan,
  2019: np.nan,
  2020: np.nan,
  2021: np.nan,
  2022: np.nan},
 'OtherIndefiniteLivedAndFiniteLivedIntangibleAssets': {2014: np.nan,
  2015: np.nan,
  2016: np.nan,
  2017: np.nan,
  2018: np.nan,
  2019: np.nan,
  2020: np.nan,
  2021: np.nan,
  2022: np.nan}}
        )

        self.df_AAPL_bs.index.name='fy'
        self.df_AAPL_bs.columns.name='tag'
        assert_frame_equal(self.df_AAPL_bs.sort_index(axis=1), aapl_bs.df.sort_index(axis=1), check_names=True)


    def test_dataFrame_AAPL_Cashflow_Expected(self):
        """ Test that the AAPL Cashflow dataframe is as expected """

        aapl_cfs = eu.CashFlowStatement(aapl_edgar,2014)

        self.df_AAPL_cfs = df_cfs_prototype

        self.df_AAPL_cfs.loc[2014]=[np.nan, np.nan, 4.50000e+10, 9.57100e+09, 7.30000e+08,
        2.86300e+09]
        self.df_AAPL_cfs.loc[2015]=[9.20000e+09, 8.12660e+10, 3.52530e+10, 1.12470e+10, 5.43000e+08,
        3.58600e+09]
        self.df_AAPL_cfs.loc[2016]=[1.05050e+10, 6.62310e+10, 2.97220e+10, 1.27340e+10, 4.95000e+08,
        4.21000e+09]
        self.df_AAPL_cfs.loc[2017]=[1.01570e+10, 6.42250e+10, 3.29000e+10, 1.24510e+10, 5.55000e+08,
        4.84000e+09]
        self.df_AAPL_cfs.loc[2018]=[1.09030e+10, 7.74340e+10, 7.27380e+10, 1.33130e+10, 6.69000e+08,
        5.34000e+09]
        self.df_AAPL_cfs.loc[2019]=[1.25470e+10, 6.93910e+10, 6.68970e+10, 1.04950e+10, 7.81000e+08,
        6.06800e+09]
        self.df_AAPL_cfs.loc[2020]=[1.10560e+10, 8.06740e+10, 7.23580e+10, 7.30900e+09, 8.80000e+08,
        6.82900e+09]
        self.df_AAPL_cfs.loc[2021]=[1.12840e+10, 1.04038e+11, 8.59710e+10, 1.10850e+10, 1.10500e+09,
        7.90600e+09]
        self.df_AAPL_cfs.loc[2022]=[1.11040e+10, 1.22151e+11, 8.94020e+10, 1.07080e+10, np.nan,
        9.03800e+09]


        assert_frame_equal(self.df_AAPL_cfs, aapl_cfs.df)

if __name__ == '__main__':
    unittest.main()