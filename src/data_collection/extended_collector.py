"""
Extended Stock Data Collector
Collects additional data for enhanced backtesting and screening
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from tqdm import tqdm
import time

try:
    import yfinance as yf
except ImportError:
    print("Warning: yfinance not installed")
    print("Install with: pip install yfinance")

from ..utils.logger import get_logger
from ..utils.database import get_db
from ..utils.helpers import get_date_range

logger = get_logger(__name__)


class ExtendedDataCollector:
    """
    Extended data collector for comprehensive fundamental and alternative data
    Collects additional metrics not covered by basic collectors
    """

    def __init__(self):
        """Initialize extended data collector"""
        self.db = get_db()
        logger.info("Extended Data Collector initialized")

    def get_extended_fundamentals(self, symbol: str) -> Dict:
        """
        Get extended fundamental data for a stock

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with extended fundamental metrics
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get financial statements for calculations
            income_stmt = ticker.income_stmt
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow

            fundamentals = {
                'symbol': symbol,
                'date': datetime.now().date(),

                # === Valuation Metrics ===
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'per': info.get('trailingPE'),
                'forward_per': info.get('forwardPE'),
                'pbr': info.get('priceToBook'),
                'psr': info.get('priceToSalesTrailing12Months'),  # Price-to-Sales
                'peg_ratio': info.get('pegRatio'),  # PEG Ratio
                'ev_to_ebitda': info.get('enterpriseToEbitda'),
                'ev_to_revenue': info.get('enterpriseToRevenue'),

                # === Per Share Metrics ===
                'eps': info.get('trailingEps'),
                'forward_eps': info.get('forwardEps'),
                'bps': info.get('bookValue'),  # Book Value Per Share
                'revenue_per_share': info.get('revenuePerShare'),

                # === Profitability Metrics ===
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),
                'gross_margin': info.get('grossMargins'),
                'operating_margin': info.get('operatingMargins'),
                'profit_margin': info.get('profitMargins'),  # Net Margin
                'ebitda_margin': info.get('ebitdaMargins'),

                # === Growth Metrics ===
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),

                # === Financial Health ===
                'debt_ratio': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'total_debt': info.get('totalDebt'),
                'total_cash': info.get('totalCash'),
                'total_cash_per_share': info.get('totalCashPerShare'),

                # === Income Statement ===
                'revenue': info.get('totalRevenue'),
                'gross_profit': info.get('grossProfits'),
                'operating_income': info.get('operatingIncome'),
                'ebitda': info.get('ebitda'),
                'net_income': info.get('netIncomeToCommon'),

                # === Cash Flow Metrics ===
                'operating_cash_flow': info.get('operatingCashflow'),
                'free_cash_flow': info.get('freeCashflow'),

                # === Dividend Metrics ===
                'dividend_yield': info.get('dividendYield'),
                'dividend_rate': info.get('dividendRate'),  # Annual Dividend
                'payout_ratio': info.get('payoutRatio'),
                'ex_dividend_date': info.get('exDividendDate'),
                'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield'),

                # === Risk Metrics ===
                'beta': info.get('beta'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'fifty_day_average': info.get('fiftyDayAverage'),
                'two_hundred_day_average': info.get('twoHundredDayAverage'),

                # === Volume & Liquidity ===
                'avg_volume': info.get('averageVolume'),
                'avg_volume_10d': info.get('averageVolume10days'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'shares_short': info.get('sharesShort'),
                'short_ratio': info.get('shortRatio'),
                'short_percent_of_float': info.get('shortPercentOfFloat'),

                # === Ownership ===
                'held_percent_insiders': info.get('heldPercentInsiders'),
                'held_percent_institutions': info.get('heldPercentInstitutions'),

                # === Analyst Data ===
                'target_high_price': info.get('targetHighPrice'),
                'target_low_price': info.get('targetLowPrice'),
                'target_mean_price': info.get('targetMeanPrice'),
                'target_median_price': info.get('targetMedianPrice'),
                'recommendation_mean': info.get('recommendationMean'),
                'recommendation_key': info.get('recommendationKey'),
                'number_of_analyst_opinions': info.get('numberOfAnalystOpinions'),

                # === Company Info ===
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'full_time_employees': info.get('fullTimeEmployees'),
            }

            # Calculate additional derived metrics
            fundamentals = self._calculate_derived_metrics(fundamentals, info)

            return fundamentals

        except Exception as e:
            logger.error(f"Error fetching extended fundamentals for {symbol}: {str(e)}")
            return {'symbol': symbol, 'date': datetime.now().date()}

    def _calculate_derived_metrics(self, fundamentals: Dict, info: Dict) -> Dict:
        """
        Calculate additional derived metrics

        Args:
            fundamentals: Basic fundamentals dictionary
            info: Raw yfinance info dictionary

        Returns:
            Updated fundamentals with derived metrics
        """
        try:
            # Free Cash Flow Yield = FCF / Market Cap
            if fundamentals.get('free_cash_flow') and fundamentals.get('market_cap'):
                fcf = fundamentals['free_cash_flow']
                market_cap = fundamentals['market_cap']
                if market_cap > 0:
                    fundamentals['fcf_yield'] = fcf / market_cap

            # Cash Flow to Debt Ratio
            if fundamentals.get('operating_cash_flow') and fundamentals.get('total_debt'):
                ocf = fundamentals['operating_cash_flow']
                debt = fundamentals['total_debt']
                if debt and debt > 0:
                    fundamentals['cf_to_debt'] = ocf / debt

            # Interest Coverage Ratio (approximation)
            if fundamentals.get('operating_income') and fundamentals.get('total_debt'):
                op_income = fundamentals['operating_income']
                debt = fundamentals['total_debt']
                if debt and debt > 0:
                    # Assume 5% average interest rate
                    interest_expense = debt * 0.05
                    if interest_expense > 0:
                        fundamentals['interest_coverage'] = op_income / interest_expense

            # Price relative to 52-week range
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            high_52w = fundamentals.get('fifty_two_week_high')
            low_52w = fundamentals.get('fifty_two_week_low')

            if current_price and high_52w and low_52w and (high_52w - low_52w) > 0:
                fundamentals['price_to_52w_high'] = current_price / high_52w
                fundamentals['price_to_52w_low'] = current_price / low_52w
                fundamentals['price_52w_range_pct'] = (current_price - low_52w) / (high_52w - low_52w)

            # Upside to target price
            if current_price and fundamentals.get('target_mean_price'):
                target = fundamentals['target_mean_price']
                fundamentals['upside_to_target'] = (target - current_price) / current_price

        except Exception as e:
            logger.warning(f"Error calculating derived metrics: {str(e)}")

        return fundamentals

    def get_financial_statements(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Get detailed financial statements

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with income_stmt, balance_sheet, cash_flow DataFrames
        """
        try:
            ticker = yf.Ticker(symbol)

            return {
                'income_stmt': ticker.income_stmt,
                'balance_sheet': ticker.balance_sheet,
                'cash_flow': ticker.cashflow,
                'quarterly_income_stmt': ticker.quarterly_income_stmt,
                'quarterly_balance_sheet': ticker.quarterly_balance_sheet,
                'quarterly_cash_flow': ticker.quarterly_cashflow
            }

        except Exception as e:
            logger.error(f"Error fetching financial statements for {symbol}: {str(e)}")
            return {}

    def calculate_piotroski_f_score(self, symbol: str) -> Dict:
        """
        Calculate Piotroski F-Score (Financial Health Score)
        F-Score ranges from 0-9, higher is better

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with F-Score and component scores
        """
        try:
            ticker = yf.Ticker(symbol)

            # Get financial data
            income_stmt = ticker.income_stmt
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow

            if income_stmt.empty or balance_sheet.empty or cash_flow.empty:
                logger.warning(f"Insufficient data for F-Score calculation: {symbol}")
                return {'symbol': symbol, 'f_score': None}

            # Get most recent and previous year data
            current_col = income_stmt.columns[0]
            previous_col = income_stmt.columns[1] if len(income_stmt.columns) > 1 else current_col

            f_score = 0
            score_details = {}

            # === Profitability Criteria (4 points) ===

            # 1. Positive Net Income
            net_income = self._safe_get(income_stmt, 'Net Income', current_col)
            if net_income and net_income > 0:
                f_score += 1
                score_details['positive_net_income'] = 1
            else:
                score_details['positive_net_income'] = 0

            # 2. Positive Operating Cash Flow
            ocf = self._safe_get(cash_flow, 'Operating Cash Flow', current_col)
            if ocf and ocf > 0:
                f_score += 1
                score_details['positive_ocf'] = 1
            else:
                score_details['positive_ocf'] = 0

            # 3. ROA Improvement (Net Income / Total Assets)
            total_assets_current = self._safe_get(balance_sheet, 'Total Assets', current_col)
            total_assets_prev = self._safe_get(balance_sheet, 'Total Assets', previous_col)
            net_income_prev = self._safe_get(income_stmt, 'Net Income', previous_col)

            if total_assets_current and total_assets_prev and net_income and net_income_prev:
                roa_current = net_income / total_assets_current
                roa_prev = net_income_prev / total_assets_prev
                if roa_current > roa_prev:
                    f_score += 1
                    score_details['roa_improvement'] = 1
                else:
                    score_details['roa_improvement'] = 0
            else:
                score_details['roa_improvement'] = 0

            # 4. Quality of Earnings (OCF > Net Income)
            if ocf and net_income and ocf > net_income:
                f_score += 1
                score_details['earnings_quality'] = 1
            else:
                score_details['earnings_quality'] = 0

            # === Leverage & Liquidity Criteria (3 points) ===

            # 5. Decrease in Long-term Debt Ratio
            long_term_debt_current = self._safe_get(balance_sheet, 'Long Term Debt', current_col)
            long_term_debt_prev = self._safe_get(balance_sheet, 'Long Term Debt', previous_col)

            if long_term_debt_current is not None and long_term_debt_prev is not None:
                if total_assets_current and total_assets_prev:
                    debt_ratio_current = long_term_debt_current / total_assets_current if total_assets_current else 0
                    debt_ratio_prev = long_term_debt_prev / total_assets_prev if total_assets_prev else 0
                    if debt_ratio_current <= debt_ratio_prev:
                        f_score += 1
                        score_details['debt_decrease'] = 1
                    else:
                        score_details['debt_decrease'] = 0
            else:
                score_details['debt_decrease'] = 0

            # 6. Increase in Current Ratio
            current_assets_current = self._safe_get(balance_sheet, 'Current Assets', current_col)
            current_liab_current = self._safe_get(balance_sheet, 'Current Liabilities', current_col)
            current_assets_prev = self._safe_get(balance_sheet, 'Current Assets', previous_col)
            current_liab_prev = self._safe_get(balance_sheet, 'Current Liabilities', previous_col)

            if current_assets_current and current_liab_current and current_assets_prev and current_liab_prev:
                cr_current = current_assets_current / current_liab_current if current_liab_current else 0
                cr_prev = current_assets_prev / current_liab_prev if current_liab_prev else 0
                if cr_current > cr_prev:
                    f_score += 1
                    score_details['current_ratio_increase'] = 1
                else:
                    score_details['current_ratio_increase'] = 0
            else:
                score_details['current_ratio_increase'] = 0

            # 7. No New Shares Issued
            shares_current = self._safe_get(balance_sheet, 'Ordinary Shares Number', current_col)
            shares_prev = self._safe_get(balance_sheet, 'Ordinary Shares Number', previous_col)

            if shares_current and shares_prev:
                if shares_current <= shares_prev:
                    f_score += 1
                    score_details['no_dilution'] = 1
                else:
                    score_details['no_dilution'] = 0
            else:
                score_details['no_dilution'] = 0

            # === Operating Efficiency Criteria (2 points) ===

            # 8. Gross Margin Improvement
            revenue_current = self._safe_get(income_stmt, 'Total Revenue', current_col)
            revenue_prev = self._safe_get(income_stmt, 'Total Revenue', previous_col)
            gross_profit_current = self._safe_get(income_stmt, 'Gross Profit', current_col)
            gross_profit_prev = self._safe_get(income_stmt, 'Gross Profit', previous_col)

            if revenue_current and revenue_prev and gross_profit_current and gross_profit_prev:
                gm_current = gross_profit_current / revenue_current if revenue_current else 0
                gm_prev = gross_profit_prev / revenue_prev if revenue_prev else 0
                if gm_current > gm_prev:
                    f_score += 1
                    score_details['gross_margin_increase'] = 1
                else:
                    score_details['gross_margin_increase'] = 0
            else:
                score_details['gross_margin_increase'] = 0

            # 9. Asset Turnover Improvement
            if revenue_current and revenue_prev and total_assets_current and total_assets_prev:
                at_current = revenue_current / total_assets_current if total_assets_current else 0
                at_prev = revenue_prev / total_assets_prev if total_assets_prev else 0
                if at_current > at_prev:
                    f_score += 1
                    score_details['asset_turnover_increase'] = 1
                else:
                    score_details['asset_turnover_increase'] = 0
            else:
                score_details['asset_turnover_increase'] = 0

            return {
                'symbol': symbol,
                'f_score': f_score,
                'date': datetime.now().date(),
                **score_details
            }

        except Exception as e:
            logger.error(f"Error calculating F-Score for {symbol}: {str(e)}")
            return {'symbol': symbol, 'f_score': None}

    def calculate_altman_z_score(self, symbol: str) -> Dict:
        """
        Calculate Altman Z-Score (Bankruptcy Risk Score)
        Z > 2.99: Safe Zone
        1.81 < Z < 2.99: Grey Zone
        Z < 1.81: Distress Zone

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with Z-Score and component values
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            balance_sheet = ticker.balance_sheet
            income_stmt = ticker.income_stmt

            if balance_sheet.empty or income_stmt.empty:
                logger.warning(f"Insufficient data for Z-Score calculation: {symbol}")
                return {'symbol': symbol, 'z_score': None}

            current_col = balance_sheet.columns[0]

            # Get required values
            current_assets = self._safe_get(balance_sheet, 'Current Assets', current_col)
            current_liabilities = self._safe_get(balance_sheet, 'Current Liabilities', current_col)
            total_assets = self._safe_get(balance_sheet, 'Total Assets', current_col)
            total_liabilities = self._safe_get(balance_sheet, 'Total Liabilities Net Minority Interest', current_col)
            retained_earnings = self._safe_get(balance_sheet, 'Retained Earnings', current_col)
            ebit = self._safe_get(income_stmt, 'EBIT', current_col)
            revenue = self._safe_get(income_stmt, 'Total Revenue', current_col)
            market_cap = info.get('marketCap')

            if not all([total_assets, total_liabilities]):
                return {'symbol': symbol, 'z_score': None}

            # Calculate components
            working_capital = (current_assets or 0) - (current_liabilities or 0)

            # A = Working Capital / Total Assets
            A = working_capital / total_assets if total_assets else 0

            # B = Retained Earnings / Total Assets
            B = (retained_earnings or 0) / total_assets if total_assets else 0

            # C = EBIT / Total Assets
            C = (ebit or 0) / total_assets if total_assets else 0

            # D = Market Cap / Total Liabilities
            D = (market_cap or 0) / total_liabilities if total_liabilities else 0

            # E = Revenue / Total Assets
            E = (revenue or 0) / total_assets if total_assets else 0

            # Altman Z-Score Formula (for public manufacturing companies)
            # Z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
            z_score = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E

            # Determine zone
            if z_score > 2.99:
                zone = 'Safe'
            elif z_score > 1.81:
                zone = 'Grey'
            else:
                zone = 'Distress'

            return {
                'symbol': symbol,
                'z_score': z_score,
                'z_score_zone': zone,
                'date': datetime.now().date(),
                'working_capital_to_assets': A,
                'retained_earnings_to_assets': B,
                'ebit_to_assets': C,
                'market_cap_to_liabilities': D,
                'revenue_to_assets': E
            }

        except Exception as e:
            logger.error(f"Error calculating Z-Score for {symbol}: {str(e)}")
            return {'symbol': symbol, 'z_score': None}

    def _safe_get(self, df: pd.DataFrame, row_name: str, col_name) -> Optional[float]:
        """Safely get a value from DataFrame"""
        try:
            if row_name in df.index:
                value = df.loc[row_name, col_name]
                if pd.notna(value):
                    return float(value)
        except:
            pass
        return None

    def get_analyst_recommendations(self, symbol: str) -> pd.DataFrame:
        """
        Get analyst recommendations history

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame with analyst recommendations
        """
        try:
            ticker = yf.Ticker(symbol)
            recommendations = ticker.recommendations

            if recommendations is not None and not recommendations.empty:
                recommendations['symbol'] = symbol
                return recommendations

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching analyst recommendations for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_institutional_holders(self, symbol: str) -> pd.DataFrame:
        """
        Get institutional holders information

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame with institutional holders
        """
        try:
            ticker = yf.Ticker(symbol)
            holders = ticker.institutional_holders

            if holders is not None and not holders.empty:
                holders['symbol'] = symbol
                return holders

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching institutional holders for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_insider_transactions(self, symbol: str) -> pd.DataFrame:
        """
        Get insider transactions

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame with insider transactions
        """
        try:
            ticker = yf.Ticker(symbol)
            insider_txns = ticker.insider_transactions

            if insider_txns is not None and not insider_txns.empty:
                insider_txns['symbol'] = symbol
                return insider_txns

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching insider transactions for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_dividend_history(self, symbol: str) -> pd.DataFrame:
        """
        Get dividend history

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame with dividend history
        """
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends

            if dividends is not None and len(dividends) > 0:
                df = dividends.reset_index()
                df.columns = ['date', 'dividend']
                df['symbol'] = symbol
                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching dividend history for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_earnings_history(self, symbol: str) -> pd.DataFrame:
        """
        Get earnings history (actual vs estimate)

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame with earnings history
        """
        try:
            ticker = yf.Ticker(symbol)
            earnings = ticker.earnings_history

            if earnings is not None and not earnings.empty:
                earnings['symbol'] = symbol
                # Calculate surprise
                if 'epsActual' in earnings.columns and 'epsEstimate' in earnings.columns:
                    earnings['earnings_surprise'] = earnings['epsActual'] - earnings['epsEstimate']
                    earnings['earnings_surprise_pct'] = (
                        earnings['earnings_surprise'] / earnings['epsEstimate'].abs()
                    ).replace([np.inf, -np.inf], np.nan)
                return earnings

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching earnings history for {symbol}: {str(e)}")
            return pd.DataFrame()

    def collect_extended_data(self,
                             symbols: List[str],
                             include_scores: bool = True,
                             delay: float = 0.5) -> pd.DataFrame:
        """
        Collect extended fundamental data for multiple stocks

        Args:
            symbols: List of stock ticker symbols
            include_scores: Include Piotroski F-Score and Altman Z-Score
            delay: Delay between requests (seconds)

        Returns:
            DataFrame with extended fundamental data
        """
        logger.info(f"Collecting extended data for {len(symbols)} stocks")

        all_data = []

        for symbol in tqdm(symbols, desc="Collecting extended data"):
            try:
                # Get extended fundamentals
                fundamentals = self.get_extended_fundamentals(symbol)

                # Add financial health scores if requested
                if include_scores:
                    f_score_data = self.calculate_piotroski_f_score(symbol)
                    z_score_data = self.calculate_altman_z_score(symbol)

                    fundamentals['f_score'] = f_score_data.get('f_score')
                    fundamentals['z_score'] = z_score_data.get('z_score')
                    fundamentals['z_score_zone'] = z_score_data.get('z_score_zone')

                all_data.append(fundamentals)

            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {str(e)}")
                continue

            time.sleep(delay)

        if all_data:
            df = pd.DataFrame(all_data)
            logger.info(f"Collected extended data for {len(df)} stocks")
            return df
        else:
            logger.warning("No extended data collected")
            return pd.DataFrame()


def main():
    """Example usage"""
    collector = ExtendedDataCollector()

    # Test with a few stocks
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']

    print("Collecting extended fundamentals...")
    df = collector.collect_extended_data(test_symbols, include_scores=True)

    if not df.empty:
        print("\nExtended Fundamentals Sample:")
        print(df[['symbol', 'market_cap', 'peg_ratio', 'ev_to_ebitda',
                  'gross_margin', 'roe', 'f_score', 'z_score']].to_string())

        print("\nAnalyst Data:")
        print(df[['symbol', 'target_mean_price', 'recommendation_key',
                  'number_of_analyst_opinions', 'upside_to_target']].to_string())

        print("\nOwnership Data:")
        print(df[['symbol', 'held_percent_insiders', 'held_percent_institutions',
                  'short_percent_of_float']].to_string())


if __name__ == "__main__":
    main()
