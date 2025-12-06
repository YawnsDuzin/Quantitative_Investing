"""
Strategy configuration forms
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, FloatField, IntegerField,
                     SubmitField, TextAreaField, BooleanField)
from wtforms.validators import DataRequired, NumberRange, Optional, Length


class StrategyForm(FlaskForm):
    """Strategy configuration form"""
    name = StringField('전략 이름', validators=[
        DataRequired(message='전략 이름을 입력해주세요.'),
        Length(max=100)
    ])

    description = TextAreaField('설명', validators=[
        Optional(),
        Length(max=500)
    ])

    strategy_type = SelectField('전략 유형', choices=[
        ('momentum', '모멘텀'),
        ('value', '가치'),
        ('quality', '퀄리티'),
        ('multifactor', '멀티팩터'),
        ('size', '소형주'),
        ('custom', '커스텀')
    ], validators=[DataRequired()])

    market = SelectField('대상 시장', choices=[
        ('KR', '한국 (KOSPI/KOSDAQ)'),
        ('US', '미국 (NYSE/NASDAQ)'),
        ('BOTH', '전체')
    ], default='KR')

    # Position settings
    max_positions = IntegerField('최대 보유 종목 수', validators=[
        DataRequired(),
        NumberRange(min=5, max=100)
    ], default=20)

    min_positions = IntegerField('최소 보유 종목 수', validators=[
        DataRequired(),
        NumberRange(min=1, max=50)
    ], default=10)

    max_position_size = FloatField('최대 개별 비중 (%)', validators=[
        DataRequired(),
        NumberRange(min=1, max=50)
    ], default=10)

    # Risk management
    stop_loss = FloatField('손절 기준 (%)', validators=[
        Optional(),
        NumberRange(min=0, max=50)
    ], default=15)

    take_profit = FloatField('익절 기준 (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100)
    ])

    # Rebalancing
    rebalance_frequency = SelectField('리밸런싱 주기', choices=[
        ('daily', '매일'),
        ('weekly', '매주'),
        ('monthly', '매월'),
        ('quarterly', '분기별')
    ], default='monthly')

    equal_weight = BooleanField('동일 비중 사용', default=True)

    # Factor weights (for multifactor)
    momentum_weight = FloatField('모멘텀 비중', validators=[
        Optional(),
        NumberRange(min=0, max=1)
    ], default=0.4)

    value_weight = FloatField('가치 비중', validators=[
        Optional(),
        NumberRange(min=0, max=1)
    ], default=0.3)

    quality_weight = FloatField('퀄리티 비중', validators=[
        Optional(),
        NumberRange(min=0, max=1)
    ], default=0.2)

    size_weight = FloatField('사이즈 비중', validators=[
        Optional(),
        NumberRange(min=0, max=1)
    ], default=0.1)

    # Universe filters
    min_market_cap = FloatField('최소 시가총액 (억원)', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=500)

    min_volume = FloatField('최소 거래대금 (억원)', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=10)

    # Visibility
    is_public = BooleanField('공개 전략으로 설정', default=False)

    submit = SubmitField('저장')
