"""
Main routes - home page and general pages
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('main/index.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')


@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('main/features.html')


@main_bp.route('/docs')
def docs():
    """Documentation page"""
    return render_template('main/docs.html')
