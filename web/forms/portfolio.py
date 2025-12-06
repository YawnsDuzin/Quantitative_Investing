"""
Portfolio forms
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, FloatField,
                     SubmitField, TextAreaField)
from wtforms.validators import DataRequired, NumberRange, Optional, Length


class PortfolioForm(FlaskForm):
    """Portfolio creation/edit form"""
    name = StringField('포트폴리오 이름', validators=[
        DataRequired(message='포트폴리오 이름을 입력해주세요.'),
        Length(max=100)
    ])

    description = TextAreaField('설명', validators=[
        Optional(),
        Length(max=500)
    ])

    initial_capital = FloatField('초기 자본금', validators=[
        DataRequired(message='초기 자본금을 입력해주세요.'),
        NumberRange(min=1000000, message='최소 100만원 이상이어야 합니다.')
    ], default=100000000)

    market = SelectField('대상 시장', choices=[
        ('KR', '한국 (KOSPI/KOSDAQ)'),
        ('US', '미국 (NYSE/NASDAQ)')
    ], validators=[DataRequired()])

    strategy_name = SelectField('적용 전략', choices=[
        ('', '전략 없음 (수동 관리)'),
        ('momentum', '모멘텀 전략'),
        ('value', '가치 전략'),
        ('quality', '퀄리티 전략'),
        ('multifactor', '멀티팩터 전략'),
        ('size', '소형주 전략')
    ], validators=[Optional()])

    rebalance_frequency = SelectField('리밸런싱 주기', choices=[
        ('manual', '수동'),
        ('daily', '매일'),
        ('weekly', '매주'),
        ('monthly', '매월'),
        ('quarterly', '분기별')
    ], default='monthly')

    submit = SubmitField('저장')


class AddHoldingForm(FlaskForm):
    """Add holding to portfolio form"""
    symbol = StringField('종목 코드', validators=[
        DataRequired(message='종목 코드를 입력해주세요.')
    ])

    quantity = FloatField('수량', validators=[
        DataRequired(message='수량을 입력해주세요.'),
        NumberRange(min=1, message='1주 이상 입력해주세요.')
    ])

    price = FloatField('매입가', validators=[
        DataRequired(message='매입가를 입력해주세요.'),
        NumberRange(min=0, message='0원 이상 입력해주세요.')
    ])

    submit = SubmitField('추가')
