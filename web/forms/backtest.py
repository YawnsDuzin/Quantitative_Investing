"""
Backtest forms
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, FloatField, IntegerField,
                     DateField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, NumberRange, Optional
from datetime import date


class BacktestForm(FlaskForm):
    """Backtest configuration form"""
    name = StringField('백테스트 이름', validators=[
        DataRequired(message='백테스트 이름을 입력해주세요.')
    ])

    strategy = SelectField('전략', choices=[
        ('momentum', '모멘텀 전략'),
        ('value', '가치 전략'),
        ('quality', '퀄리티 전략'),
        ('multifactor', '멀티팩터 전략'),
        ('size', '소형주 전략')
    ], validators=[DataRequired()])

    market = SelectField('시장', choices=[
        ('KR', '한국 (KOSPI/KOSDAQ)'),
        ('US', '미국 (NYSE/NASDAQ)')
    ], validators=[DataRequired()])

    start_date = DateField('시작일', validators=[
        DataRequired(message='시작일을 선택해주세요.')
    ], default=date(2020, 1, 1))

    end_date = DateField('종료일', validators=[
        DataRequired(message='종료일을 선택해주세요.')
    ], default=date.today())

    initial_capital = FloatField('초기 자본금', validators=[
        DataRequired(message='초기 자본금을 입력해주세요.'),
        NumberRange(min=1000000, message='최소 100만원 이상이어야 합니다.')
    ], default=100000000)

    rebalance_frequency = SelectField('리밸런싱 주기', choices=[
        ('daily', '매일'),
        ('weekly', '매주'),
        ('monthly', '매월'),
        ('quarterly', '분기별')
    ], default='monthly')

    max_positions = IntegerField('최대 종목 수', validators=[
        DataRequired(),
        NumberRange(min=5, max=100, message='5-100 사이의 값을 입력해주세요.')
    ], default=20)

    commission = FloatField('수수료 (%)', validators=[
        DataRequired(),
        NumberRange(min=0, max=1, message='0-1% 사이의 값을 입력해주세요.')
    ], default=0.15)

    slippage = FloatField('슬리피지 (%)', validators=[
        DataRequired(),
        NumberRange(min=0, max=1, message='0-1% 사이의 값을 입력해주세요.')
    ], default=0.1)

    stop_loss = FloatField('손절 (%)', validators=[
        Optional(),
        NumberRange(min=0, max=50, message='0-50% 사이의 값을 입력해주세요.')
    ], default=15)

    # Factor weights for multifactor strategy
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

    description = TextAreaField('설명', validators=[Optional()])

    submit = SubmitField('백테스트 실행')
