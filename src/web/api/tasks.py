"""
Tasks API
작업 관리 API

백그라운드 작업의 상태 조회 및 제어를 제공합니다.
"""

from flask import Blueprint, jsonify, request
from ..task_manager import task_manager

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/', methods=['GET'])
def list_tasks():
    """모든 작업 목록 조회"""
    tasks = task_manager.get_all_tasks()
    return jsonify({
        'success': True,
        'tasks': [t.to_dict() for t in tasks]
    })


@tasks_bp.route('/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """특정 작업 상태 조회"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({
            'success': False,
            'error': f'작업을 찾을 수 없습니다: {task_id}'
        }), 404

    return jsonify({
        'success': True,
        'task': task.to_dict()
    })


@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id: str):
    """작업 취소"""
    success = task_manager.cancel_task(task_id)
    if not success:
        return jsonify({
            'success': False,
            'error': '작업을 취소할 수 없습니다'
        }), 400

    return jsonify({
        'success': True,
        'message': '작업이 취소되었습니다'
    })


@tasks_bp.route('/<task_id>/result', methods=['GET'])
def get_task_result(task_id: str):
    """작업 결과 조회"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({
            'success': False,
            'error': f'작업을 찾을 수 없습니다: {task_id}'
        }), 404

    if task.status.value not in ['completed']:
        return jsonify({
            'success': False,
            'error': f'작업이 완료되지 않았습니다. 상태: {task.status.value}'
        }), 400

    return jsonify({
        'success': True,
        'result': task.result
    })
