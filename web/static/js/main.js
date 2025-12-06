/**
 * Quantitative Investing Web Application
 * Main JavaScript File
 */

(function() {
    'use strict';

    // ===================================
    // Theme Management
    // ===================================

    const ThemeManager = {
        STORAGE_KEY: 'quant-theme',

        init: function() {
            // Load saved theme or use system preference
            const savedTheme = localStorage.getItem(this.STORAGE_KEY);
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

            this.setTheme(theme, false);
            this.bindEvents();
            this.updateIcon();
        },

        bindEvents: function() {
            const toggleBtn = document.getElementById('themeToggle');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => this.toggle());
            }

            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem(this.STORAGE_KEY)) {
                    this.setTheme(e.matches ? 'dark' : 'light', false);
                }
            });
        },

        toggle: function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme, true);
        },

        setTheme: function(theme, save = true) {
            document.documentElement.setAttribute('data-theme', theme);

            if (save) {
                localStorage.setItem(this.STORAGE_KEY, theme);

                // Save to server if logged in
                this.saveToServer(theme);
            }

            this.updateIcon();
            this.updateCharts(theme);
        },

        updateIcon: function() {
            const icon = document.getElementById('themeIcon');
            if (icon) {
                const theme = document.documentElement.getAttribute('data-theme');
                icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
            }
        },

        updateCharts: function(theme) {
            // Update Chart.js defaults for new charts
            if (typeof Chart !== 'undefined') {
                const textColor = theme === 'dark' ? '#adb5bd' : '#666666';
                const gridColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

                Chart.defaults.color = textColor;
                Chart.defaults.borderColor = gridColor;
            }
        },

        saveToServer: function(theme) {
            // Only save if CSRF token exists (user is logged in)
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ||
                              document.querySelector('input[name="csrf_token"]')?.value;

            if (csrfToken) {
                fetch('/api/theme', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ theme: theme })
                }).catch(() => {
                    // Silently fail if not logged in
                });
            }
        }
    };

    // ===================================
    // Chart Utilities
    // ===================================

    const ChartUtils = {
        // Default chart options for consistent styling
        getDefaultOptions: function(type = 'line') {
            const theme = document.documentElement.getAttribute('data-theme');
            const textColor = theme === 'dark' ? '#adb5bd' : '#666666';
            const gridColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: textColor
                        }
                    },
                    tooltip: {
                        backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
                        titleColor: theme === 'dark' ? '#fff' : '#212529',
                        bodyColor: theme === 'dark' ? '#e9ecef' : '#212529',
                        borderColor: gridColor,
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    y: {
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    }
                }
            };
        },

        // Format number for display
        formatNumber: function(value, decimals = 0) {
            return new Intl.NumberFormat('ko-KR', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(value);
        },

        // Format percentage
        formatPercent: function(value, decimals = 1) {
            return (value * 100).toFixed(decimals) + '%';
        },

        // Format currency
        formatCurrency: function(value, currency = 'KRW') {
            return new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        }
    };

    // ===================================
    // Form Utilities
    // ===================================

    const FormUtils = {
        // Serialize form to JSON
        toJSON: function(form) {
            const formData = new FormData(form);
            const json = {};
            formData.forEach((value, key) => {
                if (json[key]) {
                    if (!Array.isArray(json[key])) {
                        json[key] = [json[key]];
                    }
                    json[key].push(value);
                } else {
                    json[key] = value;
                }
            });
            return json;
        },

        // Validate form
        validate: function(form) {
            let isValid = true;
            const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            return isValid;
        },

        // Show loading state
        setLoading: function(button, loading = true) {
            if (loading) {
                button.disabled = true;
                button.dataset.originalText = button.innerHTML;
                button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>처리 중...';
            } else {
                button.disabled = false;
                button.innerHTML = button.dataset.originalText;
            }
        }
    };

    // ===================================
    // API Utilities
    // ===================================

    const API = {
        // Get CSRF token
        getCSRFToken: function() {
            return document.querySelector('meta[name="csrf-token"]')?.content ||
                   document.querySelector('input[name="csrf_token"]')?.value || '';
        },

        // Fetch with defaults
        fetch: async function(url, options = {}) {
            const defaults = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            };

            const config = { ...defaults, ...options };
            if (options.headers) {
                config.headers = { ...defaults.headers, ...options.headers };
            }

            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return response.json();
        },

        // GET request
        get: function(url) {
            return this.fetch(url);
        },

        // POST request
        post: function(url, data) {
            return this.fetch(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }
    };

    // ===================================
    // Notification Utilities
    // ===================================

    const Notify = {
        // Show toast notification
        show: function(message, type = 'info', duration = 5000) {
            const container = this.getContainer();
            const toast = document.createElement('div');
            toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
            toast.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            container.appendChild(toast);

            // Auto dismiss
            if (duration > 0) {
                setTimeout(() => {
                    toast.remove();
                }, duration);
            }
        },

        getContainer: function() {
            let container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1050; max-width: 400px;';
                document.body.appendChild(container);
            }
            return container;
        },

        success: function(message) { this.show(message, 'success'); },
        error: function(message) { this.show(message, 'error'); },
        warning: function(message) { this.show(message, 'warning'); },
        info: function(message) { this.show(message, 'info'); }
    };

    // ===================================
    // Stock Search
    // ===================================

    const StockSearch = {
        init: function(inputId, resultsId, options = {}) {
            const input = document.getElementById(inputId);
            const results = document.getElementById(resultsId);

            if (!input || !results) return;

            let timeout;

            input.addEventListener('input', (e) => {
                clearTimeout(timeout);
                const query = e.target.value.trim();

                if (query.length < 1) {
                    results.innerHTML = '';
                    return;
                }

                timeout = setTimeout(async () => {
                    try {
                        const market = options.marketFilter?.value || 'all';
                        const data = await API.get(`/api/stock-search?q=${encodeURIComponent(query)}&market=${market}`);
                        this.renderResults(results, data, options.onSelect);
                    } catch (error) {
                        console.error('Search error:', error);
                    }
                }, 300);
            });
        },

        renderResults: function(container, stocks, onSelect) {
            if (!stocks.length) {
                container.innerHTML = '<p class="text-muted p-3">검색 결과가 없습니다.</p>';
                return;
            }

            container.innerHTML = stocks.map(stock => `
                <div class="stock-result p-2 border-bottom" data-symbol="${stock.symbol}" style="cursor: pointer;">
                    <strong>${stock.symbol}</strong>
                    <span class="text-muted ms-2">${stock.name || ''}</span>
                    <span class="badge bg-secondary float-end">${stock.market || ''}</span>
                </div>
            `).join('');

            if (onSelect) {
                container.querySelectorAll('.stock-result').forEach(el => {
                    el.addEventListener('click', () => onSelect(el.dataset.symbol));
                });
            }
        }
    };

    // ===================================
    // Confirmation Dialog
    // ===================================

    const Confirm = {
        show: function(message, onConfirm) {
            if (confirm(message)) {
                onConfirm();
            }
        }
    };

    // ===================================
    // Initialize on DOM Ready
    // ===================================

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize theme manager
        ThemeManager.init();

        // Initialize Bootstrap tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));

        // Initialize Bootstrap popovers
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        popoverTriggerList.forEach(el => new bootstrap.Popover(el));

        // Auto-dismiss alerts after 5 seconds
        document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }, 5000);
        });

        // Add confirmation to delete forms
        document.querySelectorAll('form[data-confirm]').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!confirm(form.dataset.confirm)) {
                    e.preventDefault();
                }
            });
        });

        // Add loading state to submit buttons
        document.querySelectorAll('form[data-loading]').forEach(form => {
            form.addEventListener('submit', (e) => {
                const button = form.querySelector('button[type="submit"]');
                if (button) {
                    FormUtils.setLoading(button, true);
                }
            });
        });
    });

    // ===================================
    // Export to Global Scope
    // ===================================

    window.QuantApp = {
        ThemeManager,
        ChartUtils,
        FormUtils,
        API,
        Notify,
        StockSearch,
        Confirm
    };

})();
