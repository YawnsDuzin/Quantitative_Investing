/**
 * 퀀트 투자 시스템 - 메인 JavaScript
 */

// 전역 유틸리티 함수
const Utils = {
    // 숫자 포맷팅 (천 단위 콤마)
    formatNumber(num) {
        if (num === null || num === undefined) return '-';
        return new Intl.NumberFormat('ko-KR').format(num);
    },

    // 통화 포맷팅
    formatCurrency(num, currency = 'KRW') {
        if (num === null || num === undefined) return '-';
        const formatter = new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: 0
        });
        return formatter.format(num);
    },

    // 퍼센트 포맷팅
    formatPercent(num, decimals = 2) {
        if (num === null || num === undefined) return '-';
        return num.toFixed(decimals) + '%';
    },

    // 시가총액 포맷팅 (억 단위)
    formatMarketCap(num) {
        if (num === null || num === undefined) return '-';
        if (num >= 1000000000000) {
            return (num / 1000000000000).toFixed(1) + '조';
        } else if (num >= 100000000) {
            return (num / 100000000).toFixed(0) + '억';
        } else if (num >= 10000) {
            return (num / 10000).toFixed(0) + '만';
        }
        return this.formatNumber(num);
    },

    // 날짜 포맷팅
    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },

    // 시간 포맷팅
    formatTime(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('ko-KR');
    },

    // 상대 시간 (몇 분 전)
    formatRelativeTime(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return '방금 전';
        if (diff < 3600) return Math.floor(diff / 60) + '분 전';
        if (diff < 86400) return Math.floor(diff / 3600) + '시간 전';
        return Math.floor(diff / 86400) + '일 전';
    },

    // 숫자에 색상 클래스 추가
    getColorClass(num) {
        if (num > 0) return 'text-danger';  // 상승 (빨간색)
        if (num < 0) return 'text-primary'; // 하락 (파란색)
        return '';
    },

    // 로딩 오버레이 표시
    showLoading() {
        const overlay = document.createElement('div');
        overlay.className = 'spinner-overlay';
        overlay.id = 'loading-overlay';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">처리 중...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    },

    // 로딩 오버레이 숨기기
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    },

    // 토스트 메시지 표시
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container') || this.createToastContainer();

        const toastId = 'toast-' + Date.now();
        const bgClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning text-dark',
            'info': 'bg-primary'
        }[type] || 'bg-primary';

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white ${bgClass} border-0`;
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        container.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // 자동 제거
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    },

    // 토스트 컨테이너 생성
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    },

    // API 호출 래퍼
    async api(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'API 요청 실패');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // 디바운스
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 스로틀
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// 소켓 연결 관리
class SocketManager {
    constructor(namespace = '') {
        this.namespace = namespace;
        this.socket = null;
        this.handlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        if (typeof io === 'undefined') {
            console.error('Socket.IO not loaded');
            return;
        }

        this.socket = io(this.namespace, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: 1000
        });

        this.socket.on('connect', () => {
            console.log('Socket connected:', this.namespace);
            this.reconnectAttempts = 0;
        });

        this.socket.on('disconnect', (reason) => {
            console.log('Socket disconnected:', reason);
        });

        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.reconnectAttempts++;
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                Utils.showToast('서버 연결에 실패했습니다.', 'error');
            }
        });

        // 등록된 핸들러 바인딩
        Object.entries(this.handlers).forEach(([event, handler]) => {
            this.socket.on(event, handler);
        });

        return this;
    }

    on(event, handler) {
        this.handlers[event] = handler;
        if (this.socket) {
            this.socket.on(event, handler);
        }
        return this;
    }

    emit(event, data) {
        if (this.socket && this.socket.connected) {
            this.socket.emit(event, data);
        }
        return this;
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// 페이지 초기화
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap 툴팁 초기화
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Bootstrap 팝오버 초기화
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    console.log('Quant Investing System initialized');
});

// 전역 에러 핸들러
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    Utils.showToast('오류가 발생했습니다: ' + event.reason.message, 'error');
});

// 전역으로 내보내기
window.Utils = Utils;
window.SocketManager = SocketManager;
