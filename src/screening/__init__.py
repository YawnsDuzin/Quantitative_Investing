"""
Stock Screening Module
주식 스크리닝 모듈

다양한 조건을 조합하여 종목을 필터링하는 기능을 제공합니다.
"""

from .screener import StockScreener, ScreenerBuilder
from .conditions.base_condition import (
    BaseCondition,
    AndCondition,
    OrCondition,
    NotCondition
)
from .conditions.price_conditions import (
    PriceAbove,
    PriceBelow,
    PriceBetween,
    PriceChangePercent,
    Above52WeekHigh,
    Below52WeekLow,
    NearHighPercent,
    NearLowPercent,
    GapUp,
    GapDown,
    VolumeAbove,
    VolumeBelow,
    VolumeRatio,
    AverageVolumeAbove
)
from .conditions.technical_conditions import (
    SMACondition,
    EMACondition,
    PriceAboveSMA,
    PriceBelowSMA,
    GoldenCross,
    DeathCross,
    RSICondition,
    RSIOverbought,
    RSIOversold,
    MACDCondition,
    MACDCrossover,
    BollingerBandCondition,
    ATRCondition,
    StochasticCondition,
    ADXCondition
)
from .conditions.fundamental_conditions import (
    MarketCapAbove,
    MarketCapBelow,
    MarketCapBetween,
    PERAbove,
    PERBelow,
    PERBetween,
    PBRAbove,
    PBRBelow,
    PBRBetween,
    DividendYieldAbove,
    ROEAbove,
    ROAAbove,
    DebtRatioBelow,
    EPSGrowthAbove,
    RevenueGrowthAbove
)
from .conditions.market_conditions import (
    MarketIs,
    SectorIs,
    IndustryIs,
    ExcludeAdministrative,
    ExcludeTradingHalt,
    OnlyETF,
    ExcludeETF
)
from .presets.preset_strategies import (
    get_preset_strategy,
    list_preset_strategies,
    ValueInvestingPreset,
    GrowthInvestingPreset,
    MomentumPreset,
    DividendPreset,
    SmallCapValuePreset
)

__all__ = [
    # Main classes
    'StockScreener',
    'ScreenerBuilder',

    # Base conditions
    'BaseCondition',
    'AndCondition',
    'OrCondition',
    'NotCondition',

    # Price conditions
    'PriceAbove',
    'PriceBelow',
    'PriceBetween',
    'PriceChangePercent',
    'Above52WeekHigh',
    'Below52WeekLow',
    'NearHighPercent',
    'NearLowPercent',
    'GapUp',
    'GapDown',
    'VolumeAbove',
    'VolumeBelow',
    'VolumeRatio',
    'AverageVolumeAbove',

    # Technical conditions
    'SMACondition',
    'EMACondition',
    'PriceAboveSMA',
    'PriceBelowSMA',
    'GoldenCross',
    'DeathCross',
    'RSICondition',
    'RSIOverbought',
    'RSIOversold',
    'MACDCondition',
    'MACDCrossover',
    'BollingerBandCondition',
    'ATRCondition',
    'StochasticCondition',
    'ADXCondition',

    # Fundamental conditions
    'MarketCapAbove',
    'MarketCapBelow',
    'MarketCapBetween',
    'PERAbove',
    'PERBelow',
    'PERBetween',
    'PBRAbove',
    'PBRBelow',
    'PBRBetween',
    'DividendYieldAbove',
    'ROEAbove',
    'ROAAbove',
    'DebtRatioBelow',
    'EPSGrowthAbove',
    'RevenueGrowthAbove',

    # Market conditions
    'MarketIs',
    'SectorIs',
    'IndustryIs',
    'ExcludeAdministrative',
    'ExcludeTradingHalt',
    'OnlyETF',
    'ExcludeETF',

    # Presets
    'get_preset_strategy',
    'list_preset_strategies',
    'ValueInvestingPreset',
    'GrowthInvestingPreset',
    'MomentumPreset',
    'DividendPreset',
    'SmallCapValuePreset',
]
