"""
Main Routes
메인 라우트

페이지 렌더링을 담당합니다.
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@main_bp.route('/screening')
def screening():
    """스크리닝 페이지"""
    return render_template('screening.html')


@main_bp.route('/screening/preset')
def screening_preset():
    """프리셋 스크리닝 페이지"""
    return render_template('screening_preset.html')


@main_bp.route('/screening/custom')
def screening_custom():
    """커스텀 스크리닝 페이지"""
    return render_template('screening_custom.html')


@main_bp.route('/tasks')
def tasks():
    """작업 관리 페이지"""
    return render_template('tasks.html')
