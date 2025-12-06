"""
Authentication forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from web.models.user import User


class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('이메일', validators=[
        DataRequired(message='이메일을 입력해주세요.'),
        Email(message='올바른 이메일 형식을 입력해주세요.')
    ])
    password = PasswordField('비밀번호', validators=[
        DataRequired(message='비밀번호를 입력해주세요.')
    ])
    remember_me = BooleanField('로그인 상태 유지')
    submit = SubmitField('로그인')


class RegistrationForm(FlaskForm):
    """Registration form"""
    username = StringField('사용자 이름', validators=[
        DataRequired(message='사용자 이름을 입력해주세요.'),
        Length(min=3, max=20, message='사용자 이름은 3-20자 사이여야 합니다.')
    ])
    email = StringField('이메일', validators=[
        DataRequired(message='이메일을 입력해주세요.'),
        Email(message='올바른 이메일 형식을 입력해주세요.')
    ])
    password = PasswordField('비밀번호', validators=[
        DataRequired(message='비밀번호를 입력해주세요.'),
        Length(min=8, message='비밀번호는 최소 8자 이상이어야 합니다.')
    ])
    password_confirm = PasswordField('비밀번호 확인', validators=[
        DataRequired(message='비밀번호 확인을 입력해주세요.'),
        EqualTo('password', message='비밀번호가 일치하지 않습니다.')
    ])
    submit = SubmitField('회원가입')

    def validate_username(self, field):
        """Check if username already exists"""
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('이미 사용 중인 사용자 이름입니다.')

    def validate_email(self, field):
        """Check if email already exists"""
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('이미 등록된 이메일입니다.')


class ProfileForm(FlaskForm):
    """User profile form"""
    username = StringField('사용자 이름', validators=[
        DataRequired(message='사용자 이름을 입력해주세요.'),
        Length(min=3, max=20, message='사용자 이름은 3-20자 사이여야 합니다.')
    ])
    email = StringField('이메일', validators=[
        DataRequired(message='이메일을 입력해주세요.'),
        Email(message='올바른 이메일 형식을 입력해주세요.')
    ])
    theme = SelectField('테마', choices=[
        ('light', '라이트 모드'),
        ('dark', '다크 모드')
    ])
    language = SelectField('언어', choices=[
        ('ko', '한국어'),
        ('en', 'English')
    ])
    default_market = SelectField('기본 시장', choices=[
        ('KR', '한국 (KOSPI/KOSDAQ)'),
        ('US', '미국 (NYSE/NASDAQ)')
    ])
    submit = SubmitField('저장')


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('현재 비밀번호', validators=[
        DataRequired(message='현재 비밀번호를 입력해주세요.')
    ])
    new_password = PasswordField('새 비밀번호', validators=[
        DataRequired(message='새 비밀번호를 입력해주세요.'),
        Length(min=8, message='비밀번호는 최소 8자 이상이어야 합니다.')
    ])
    confirm_password = PasswordField('새 비밀번호 확인', validators=[
        DataRequired(message='새 비밀번호 확인을 입력해주세요.'),
        EqualTo('new_password', message='비밀번호가 일치하지 않습니다.')
    ])
    submit = SubmitField('비밀번호 변경')
