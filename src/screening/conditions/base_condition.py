"""
Base Condition Class
기본 조건 클래스

모든 스크리닝 조건의 기반이 되는 추상 클래스와
조건 조합을 위한 AND, OR, NOT 클래스를 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np


class BaseCondition(ABC):
    """
    스크리닝 조건의 기본 클래스

    모든 조건 클래스는 이 클래스를 상속받아야 합니다.
    Python의 매직 메서드를 사용하여 조건 조합을 지원합니다.

    Example:
        >>> condition1 = PriceAbove(10000)
        >>> condition2 = RSIOversold()
        >>> combined = condition1 & condition2  # AND
        >>> combined = condition1 | condition2  # OR
        >>> inverted = ~condition1  # NOT
    """

    def __init__(self, name: str, description: str = ""):
        """
        Args:
            name: 조건 이름
            description: 조건 설명
        """
        self.name = name
        self.description = description
        self._required_columns: List[str] = []

    @abstractmethod
    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """
        조건을 평가하여 각 행에 대한 boolean Series를 반환합니다.

        Args:
            data: 평가할 데이터프레임

        Returns:
            pd.Series: 조건 충족 여부 (True/False)
        """
        pass

    @property
    def required_columns(self) -> List[str]:
        """조건 평가에 필요한 컬럼 목록"""
        return self._required_columns

    def validate_columns(self, data: pd.DataFrame) -> bool:
        """
        필요한 컬럼이 데이터에 존재하는지 확인합니다.

        Args:
            data: 검증할 데이터프레임

        Returns:
            bool: 모든 필요한 컬럼이 존재하면 True
        """
        missing = [col for col in self._required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"조건 '{self.name}'에 필요한 컬럼이 없습니다: {missing}")
        return True

    def __and__(self, other: 'BaseCondition') -> 'AndCondition':
        """AND 연산자 (&)"""
        return AndCondition(self, other)

    def __or__(self, other: 'BaseCondition') -> 'OrCondition':
        """OR 연산자 (|)"""
        return OrCondition(self, other)

    def __invert__(self) -> 'NotCondition':
        """NOT 연산자 (~)"""
        return NotCondition(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __str__(self) -> str:
        return f"{self.name}: {self.description}" if self.description else self.name

    def to_dict(self) -> Dict[str, Any]:
        """조건을 딕셔너리로 변환"""
        return {
            'type': self.__class__.__name__,
            'name': self.name,
            'description': self.description,
            'required_columns': self._required_columns
        }


class CompositeCondition(BaseCondition):
    """복합 조건의 기본 클래스"""

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self._conditions: List[BaseCondition] = []

    @property
    def conditions(self) -> List[BaseCondition]:
        """포함된 조건 목록"""
        return self._conditions

    @property
    def required_columns(self) -> List[str]:
        """모든 하위 조건에 필요한 컬럼 목록"""
        columns = set()
        for condition in self._conditions:
            columns.update(condition.required_columns)
        return list(columns)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['conditions'] = [c.to_dict() for c in self._conditions]
        return result


class AndCondition(CompositeCondition):
    """
    AND 조건 (모든 조건을 만족해야 함)

    Example:
        >>> cond = PriceAbove(10000) & RSIOversold()
        >>> # 가격이 10000 이상이고 RSI가 과매도 상태인 종목
    """

    def __init__(self, *conditions: BaseCondition):
        """
        Args:
            *conditions: 결합할 조건들
        """
        names = [c.name for c in conditions]
        super().__init__(
            name=f"AND({', '.join(names)})",
            description=f"모든 조건 충족: {', '.join(names)}"
        )
        self._conditions = list(conditions)

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """모든 조건이 True인 경우에만 True 반환"""
        if not self._conditions:
            return pd.Series([True] * len(data), index=data.index)

        result = pd.Series([True] * len(data), index=data.index)
        for condition in self._conditions:
            condition.validate_columns(data)
            result = result & condition.evaluate(data)
        return result

    def __and__(self, other: BaseCondition) -> 'AndCondition':
        """추가 AND 연산 시 조건 병합"""
        if isinstance(other, AndCondition):
            return AndCondition(*self._conditions, *other._conditions)
        return AndCondition(*self._conditions, other)


class OrCondition(CompositeCondition):
    """
    OR 조건 (하나 이상의 조건을 만족하면 됨)

    Example:
        >>> cond = RSIOversold() | StochasticOversold()
        >>> # RSI 또는 스토캐스틱이 과매도 상태인 종목
    """

    def __init__(self, *conditions: BaseCondition):
        """
        Args:
            *conditions: 결합할 조건들
        """
        names = [c.name for c in conditions]
        super().__init__(
            name=f"OR({', '.join(names)})",
            description=f"하나 이상 충족: {', '.join(names)}"
        )
        self._conditions = list(conditions)

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """하나 이상의 조건이 True이면 True 반환"""
        if not self._conditions:
            return pd.Series([False] * len(data), index=data.index)

        result = pd.Series([False] * len(data), index=data.index)
        for condition in self._conditions:
            condition.validate_columns(data)
            result = result | condition.evaluate(data)
        return result

    def __or__(self, other: BaseCondition) -> 'OrCondition':
        """추가 OR 연산 시 조건 병합"""
        if isinstance(other, OrCondition):
            return OrCondition(*self._conditions, *other._conditions)
        return OrCondition(*self._conditions, other)


class NotCondition(BaseCondition):
    """
    NOT 조건 (조건을 반전)

    Example:
        >>> cond = ~ExcludeAdministrative()
        >>> # 관리종목인 종목만 선택
    """

    def __init__(self, condition: BaseCondition):
        """
        Args:
            condition: 반전할 조건
        """
        super().__init__(
            name=f"NOT({condition.name})",
            description=f"조건 반전: {condition.name}"
        )
        self._condition = condition

    @property
    def condition(self) -> BaseCondition:
        """원본 조건"""
        return self._condition

    @property
    def required_columns(self) -> List[str]:
        """원본 조건에 필요한 컬럼 목록"""
        return self._condition.required_columns

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """원본 조건의 결과를 반전"""
        self._condition.validate_columns(data)
        return ~self._condition.evaluate(data)

    def __invert__(self) -> BaseCondition:
        """이중 NOT은 원본 조건 반환"""
        return self._condition

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['condition'] = self._condition.to_dict()
        return result


class CustomCondition(BaseCondition):
    """
    사용자 정의 조건

    람다 함수나 커스텀 함수를 사용하여 조건을 정의할 수 있습니다.

    Example:
        >>> # 종가가 시가보다 5% 이상 높은 종목
        >>> cond = CustomCondition(
        ...     name="강한상승",
        ...     func=lambda df: (df['close'] - df['open']) / df['open'] > 0.05,
        ...     required_columns=['open', 'close']
        ... )
    """

    def __init__(
        self,
        name: str,
        func: callable,
        required_columns: Optional[List[str]] = None,
        description: str = ""
    ):
        """
        Args:
            name: 조건 이름
            func: 조건 평가 함수 (DataFrame -> Series[bool])
            required_columns: 필요한 컬럼 목록
            description: 조건 설명
        """
        super().__init__(name, description)
        self._func = func
        self._required_columns = required_columns or []

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """사용자 정의 함수로 조건 평가"""
        self.validate_columns(data)
        result = self._func(data)

        # 결과가 Series가 아닌 경우 변환
        if not isinstance(result, pd.Series):
            result = pd.Series(result, index=data.index)

        return result.astype(bool)


class ThresholdCondition(BaseCondition):
    """
    임계값 기반 조건의 기본 클래스

    특정 컬럼의 값을 임계값과 비교하는 조건에 사용됩니다.
    """

    def __init__(
        self,
        column: str,
        threshold: float,
        operator: str,
        name: str = "",
        description: str = ""
    ):
        """
        Args:
            column: 비교할 컬럼명
            threshold: 임계값
            operator: 비교 연산자 ('>', '<', '>=', '<=', '==', '!=')
            name: 조건 이름
            description: 조건 설명
        """
        if not name:
            name = f"{column} {operator} {threshold}"
        super().__init__(name, description)

        self.column = column
        self.threshold = threshold
        self.operator = operator
        self._required_columns = [column]

        # 연산자 매핑
        self._operators = {
            '>': lambda x, t: x > t,
            '<': lambda x, t: x < t,
            '>=': lambda x, t: x >= t,
            '<=': lambda x, t: x <= t,
            '==': lambda x, t: x == t,
            '!=': lambda x, t: x != t,
        }

        if operator not in self._operators:
            raise ValueError(f"지원하지 않는 연산자: {operator}")

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """컬럼 값을 임계값과 비교"""
        self.validate_columns(data)
        op_func = self._operators[self.operator]
        return op_func(data[self.column], self.threshold)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'column': self.column,
            'threshold': self.threshold,
            'operator': self.operator
        })
        return result


class RangeCondition(BaseCondition):
    """
    범위 기반 조건의 기본 클래스

    특정 컬럼의 값이 주어진 범위 내에 있는지 확인합니다.
    """

    def __init__(
        self,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        inclusive: bool = True,
        name: str = "",
        description: str = ""
    ):
        """
        Args:
            column: 비교할 컬럼명
            min_value: 최소값 (None이면 하한 없음)
            max_value: 최대값 (None이면 상한 없음)
            inclusive: 경계값 포함 여부
            name: 조건 이름
            description: 조건 설명
        """
        if not name:
            if min_value is not None and max_value is not None:
                name = f"{min_value} <= {column} <= {max_value}"
            elif min_value is not None:
                name = f"{column} >= {min_value}"
            elif max_value is not None:
                name = f"{column} <= {max_value}"
            else:
                name = f"{column} (모든 값)"

        super().__init__(name, description)

        self.column = column
        self.min_value = min_value
        self.max_value = max_value
        self.inclusive = inclusive
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """컬럼 값이 범위 내에 있는지 확인"""
        self.validate_columns(data)
        values = data[self.column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_value is not None:
            if self.inclusive:
                result = result & (values >= self.min_value)
            else:
                result = result & (values > self.min_value)

        if self.max_value is not None:
            if self.inclusive:
                result = result & (values <= self.max_value)
            else:
                result = result & (values < self.max_value)

        return result

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'column': self.column,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'inclusive': self.inclusive
        })
        return result


class PercentileCondition(BaseCondition):
    """
    백분위 기반 조건

    특정 컬럼의 값이 전체 데이터에서 상위/하위 N% 내에 있는지 확인합니다.
    """

    def __init__(
        self,
        column: str,
        percentile: float,
        direction: str = 'top',
        name: str = "",
        description: str = ""
    ):
        """
        Args:
            column: 평가할 컬럼명
            percentile: 백분위 (0-100)
            direction: 'top' (상위) 또는 'bottom' (하위)
            name: 조건 이름
            description: 조건 설명
        """
        if not 0 <= percentile <= 100:
            raise ValueError("percentile은 0-100 사이여야 합니다")

        if direction not in ['top', 'bottom']:
            raise ValueError("direction은 'top' 또는 'bottom'이어야 합니다")

        if not name:
            name = f"{column} {'상위' if direction == 'top' else '하위'} {percentile}%"

        super().__init__(name, description)

        self.column = column
        self.percentile = percentile
        self.direction = direction
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        """백분위 기준으로 필터링"""
        self.validate_columns(data)
        values = data[self.column]

        if self.direction == 'top':
            threshold = np.percentile(values.dropna(), 100 - self.percentile)
            return values >= threshold
        else:  # bottom
            threshold = np.percentile(values.dropna(), self.percentile)
            return values <= threshold

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'column': self.column,
            'percentile': self.percentile,
            'direction': self.direction
        })
        return result
