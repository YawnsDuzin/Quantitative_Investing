"""
Market Conditions
시장/분류 조건 클래스

시장 구분, 업종, 관리종목 제외 등 시장 관련 조건을 정의합니다.
"""

from typing import List, Union
import pandas as pd
import numpy as np

from .base_condition import BaseCondition


class MarketIs(BaseCondition):
    """
    특정 시장에 속하는 조건

    Example:
        >>> cond = MarketIs('KOSPI')
        >>> # KOSPI 시장 종목만

        >>> cond = MarketIs(['KOSPI', 'KOSDAQ'])
        >>> # KOSPI 또는 KOSDAQ 종목
    """

    def __init__(
        self,
        market: Union[str, List[str]],
        column: str = 'market'
    ):
        """
        Args:
            market: 시장 이름 또는 시장 이름 리스트
                - 한국: 'KOSPI', 'KOSDAQ', 'KONEX'
                - 미국: 'NYSE', 'NASDAQ', 'AMEX'
            column: 시장 컬럼명
        """
        if isinstance(market, str):
            self.markets = [market]
        else:
            self.markets = list(market)

        markets_str = ', '.join(self.markets)
        super().__init__(
            name=f"시장: {markets_str}",
            description=f"{markets_str} 시장에 상장된 종목"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column].isin(self.markets)


class SectorIs(BaseCondition):
    """
    특정 섹터에 속하는 조건

    Example:
        >>> cond = SectorIs('IT')
        >>> # IT 섹터 종목만

        >>> cond = SectorIs(['IT', '반도체'])
        >>> # IT 또는 반도체 섹터 종목
    """

    def __init__(
        self,
        sector: Union[str, List[str]],
        column: str = 'sector'
    ):
        """
        Args:
            sector: 섹터 이름 또는 섹터 이름 리스트
            column: 섹터 컬럼명
        """
        if isinstance(sector, str):
            self.sectors = [sector]
        else:
            self.sectors = list(sector)

        sectors_str = ', '.join(self.sectors)
        super().__init__(
            name=f"섹터: {sectors_str}",
            description=f"{sectors_str} 섹터에 속하는 종목"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column].isin(self.sectors)


class SectorExclude(BaseCondition):
    """
    특정 섹터를 제외하는 조건

    Example:
        >>> cond = SectorExclude(['금융', '보험'])
        >>> # 금융, 보험 섹터 제외
    """

    def __init__(
        self,
        sector: Union[str, List[str]],
        column: str = 'sector'
    ):
        """
        Args:
            sector: 제외할 섹터 이름 또는 리스트
            column: 섹터 컬럼명
        """
        if isinstance(sector, str):
            self.sectors = [sector]
        else:
            self.sectors = list(sector)

        sectors_str = ', '.join(self.sectors)
        super().__init__(
            name=f"섹터 제외: {sectors_str}",
            description=f"{sectors_str} 섹터 제외"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return ~data[self.column].isin(self.sectors)


class IndustryIs(BaseCondition):
    """
    특정 업종에 속하는 조건

    Example:
        >>> cond = IndustryIs('반도체')
        >>> # 반도체 업종 종목만
    """

    def __init__(
        self,
        industry: Union[str, List[str]],
        column: str = 'industry'
    ):
        """
        Args:
            industry: 업종 이름 또는 업종 이름 리스트
            column: 업종 컬럼명
        """
        if isinstance(industry, str):
            self.industries = [industry]
        else:
            self.industries = list(industry)

        industries_str = ', '.join(self.industries)
        super().__init__(
            name=f"업종: {industries_str}",
            description=f"{industries_str} 업종에 속하는 종목"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column].isin(self.industries)


class IndustryExclude(BaseCondition):
    """
    특정 업종을 제외하는 조건

    Example:
        >>> cond = IndustryExclude(['은행', '증권'])
        >>> # 은행, 증권 업종 제외
    """

    def __init__(
        self,
        industry: Union[str, List[str]],
        column: str = 'industry'
    ):
        """
        Args:
            industry: 제외할 업종 이름 또는 리스트
            column: 업종 컬럼명
        """
        if isinstance(industry, str):
            self.industries = [industry]
        else:
            self.industries = list(industry)

        industries_str = ', '.join(self.industries)
        super().__init__(
            name=f"업종 제외: {industries_str}",
            description=f"{industries_str} 업종 제외"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return ~data[self.column].isin(self.industries)


class ExcludeAdministrative(BaseCondition):
    """
    관리종목 제외 조건

    Example:
        >>> cond = ExcludeAdministrative()
        >>> # 관리종목 제외
    """

    def __init__(self, column: str = 'is_administrative'):
        """
        Args:
            column: 관리종목 여부 컬럼명 (True/False 또는 1/0)
        """
        super().__init__(
            name="관리종목 제외",
            description="관리종목으로 지정된 종목 제외"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        # 관리종목이 아닌 것만 True
        return ~data[self.column].astype(bool)


class ExcludeTradingHalt(BaseCondition):
    """
    거래정지 종목 제외 조건

    Example:
        >>> cond = ExcludeTradingHalt()
        >>> # 거래정지 종목 제외
    """

    def __init__(self, column: str = 'is_trading_halt'):
        """
        Args:
            column: 거래정지 여부 컬럼명
        """
        super().__init__(
            name="거래정지 제외",
            description="거래정지 상태인 종목 제외"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return ~data[self.column].astype(bool)


class OnlyETF(BaseCondition):
    """
    ETF만 선택 조건

    Example:
        >>> cond = OnlyETF()
        >>> # ETF만 선택
    """

    def __init__(self, column: str = 'is_etf'):
        """
        Args:
            column: ETF 여부 컬럼명
        """
        super().__init__(
            name="ETF만",
            description="ETF 종목만 선택"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column].astype(bool)


class ExcludeETF(BaseCondition):
    """
    ETF 제외 조건

    Example:
        >>> cond = ExcludeETF()
        >>> # ETF 제외 (일반 주식만)
    """

    def __init__(self, column: str = 'is_etf'):
        """
        Args:
            column: ETF 여부 컬럼명
        """
        super().__init__(
            name="ETF 제외",
            description="ETF 제외 (일반 주식만)"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return ~data[self.column].astype(bool)


class OnlyPreferred(BaseCondition):
    """
    우선주만 선택 조건

    Example:
        >>> cond = OnlyPreferred()
        >>> # 우선주만 선택
    """

    def __init__(self, column: str = 'is_preferred'):
        """
        Args:
            column: 우선주 여부 컬럼명
        """
        super().__init__(
            name="우선주만",
            description="우선주만 선택"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column].astype(bool)


class ExcludePreferred(BaseCondition):
    """
    우선주 제외 조건

    Example:
        >>> cond = ExcludePreferred()
        >>> # 우선주 제외 (보통주만)
    """

    def __init__(self, column: str = 'is_preferred'):
        """
        Args:
            column: 우선주 여부 컬럼명
        """
        super().__init__(
            name="우선주 제외",
            description="우선주 제외 (보통주만)"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return ~data[self.column].astype(bool)


class ExcludeSPAC(BaseCondition):
    """
    SPAC 제외 조건

    Example:
        >>> cond = ExcludeSPAC()
        >>> # SPAC 제외
    """

    def __init__(self, column: str = 'is_spac'):
        """
        Args:
            column: SPAC 여부 컬럼명
        """
        super().__init__(
            name="SPAC 제외",
            description="SPAC(기업인수목적회사) 제외"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return ~data[self.column].astype(bool)


class ExcludeREIT(BaseCondition):
    """
    리츠 제외 조건

    Example:
        >>> cond = ExcludeREIT()
        >>> # 리츠 제외
    """

    def __init__(self, column: str = 'is_reit'):
        """
        Args:
            column: 리츠 여부 컬럼명
        """
        super().__init__(
            name="리츠 제외",
            description="리츠(REITs) 종목 제외"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return ~data[self.column].astype(bool)


class ListedDaysAbove(BaseCondition):
    """
    상장일수가 특정 값 이상인 조건

    Example:
        >>> cond = ListedDaysAbove(365)
        >>> # 상장 1년 이상된 종목
    """

    def __init__(self, days: int, column: str = 'listed_days'):
        """
        Args:
            days: 최소 상장일수
            column: 상장일수 컬럼명
        """
        if days >= 365:
            days_str = f"{days // 365}년"
        else:
            days_str = f"{days}일"

        super().__init__(
            name=f"상장일수 >= {days_str}",
            description=f"상장 후 {days_str} 이상 경과"
        )
        self.days = days
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column] >= self.days


class IndexMember(BaseCondition):
    """
    특정 지수 구성종목 조건

    Example:
        >>> cond = IndexMember('KOSPI200')
        >>> # KOSPI200 구성종목만

        >>> cond = IndexMember('S&P500')
        >>> # S&P500 구성종목만
    """

    def __init__(
        self,
        index_name: Union[str, List[str]],
        column: str = 'index_member'
    ):
        """
        Args:
            index_name: 지수 이름 또는 지수 이름 리스트
                - 한국: 'KOSPI200', 'KOSPI100', 'KOSDAQ150'
                - 미국: 'S&P500', 'NASDAQ100', 'DOW30'
            column: 지수 구성종목 컬럼명
        """
        if isinstance(index_name, str):
            self.indices = [index_name]
        else:
            self.indices = list(index_name)

        indices_str = ', '.join(self.indices)
        super().__init__(
            name=f"지수 구성: {indices_str}",
            description=f"{indices_str} 지수 구성종목"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)

        # 컬럼이 리스트 형태인 경우
        if data[self.column].dtype == object:
            return data[self.column].apply(
                lambda x: any(idx in (x if isinstance(x, list) else [x]) for idx in self.indices)
            )
        # 컬럼이 단일 값인 경우
        return data[self.column].isin(self.indices)


class CountryIs(BaseCondition):
    """
    특정 국가 종목 조건

    Example:
        >>> cond = CountryIs('KR')
        >>> # 한국 종목만

        >>> cond = CountryIs(['US', 'KR'])
        >>> # 미국 또는 한국 종목
    """

    def __init__(
        self,
        country: Union[str, List[str]],
        column: str = 'country'
    ):
        """
        Args:
            country: 국가 코드 또는 국가 코드 리스트
                - 'KR': 한국
                - 'US': 미국
                - 'JP': 일본
                - 'CN': 중국
            column: 국가 컬럼명
        """
        if isinstance(country, str):
            self.countries = [country]
        else:
            self.countries = list(country)

        countries_str = ', '.join(self.countries)
        super().__init__(
            name=f"국가: {countries_str}",
            description=f"{countries_str} 상장 종목"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column].isin(self.countries)


class ThemeIs(BaseCondition):
    """
    특정 테마에 속하는 조건

    Example:
        >>> cond = ThemeIs('2차전지')
        >>> # 2차전지 테마 종목

        >>> cond = ThemeIs(['AI', '로봇', '반도체'])
        >>> # AI, 로봇, 반도체 테마 종목
    """

    def __init__(
        self,
        theme: Union[str, List[str]],
        column: str = 'theme'
    ):
        """
        Args:
            theme: 테마 이름 또는 테마 이름 리스트
            column: 테마 컬럼명
        """
        if isinstance(theme, str):
            self.themes = [theme]
        else:
            self.themes = list(theme)

        themes_str = ', '.join(self.themes)
        super().__init__(
            name=f"테마: {themes_str}",
            description=f"{themes_str} 테마에 속하는 종목"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)

        # 컬럼이 리스트 형태인 경우 (한 종목이 여러 테마에 속할 수 있음)
        if data[self.column].dtype == object:
            return data[self.column].apply(
                lambda x: any(
                    theme in (x if isinstance(x, list) else [x])
                    for theme in self.themes
                ) if pd.notna(x) else False
            )
        return data[self.column].isin(self.themes)
