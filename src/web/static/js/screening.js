/**
 * 스크리닝 기능 JavaScript
 */

class ScreeningManager {
    constructor(options) {
        this.options = options;
        this.type = options.type; // 'preset' or 'custom'
        this.socket = null;
        this.currentTaskId = null;
        this.conditions = []; // 선택된 조건들 (커스텀용)
        this.presets = [];
        this.availableConditions = {};
    }

    init() {
        this.connectSocket();
        this.bindEvents();

        if (this.type === 'preset') {
            this.loadPresets();
        } else {
            this.loadConditions();
        }
    }

    connectSocket() {
        this.socket = new SocketManager('/screening');
        this.socket
            .on('progress', (data) => this.handleProgress(data))
            .on('completed', (data) => this.handleCompleted(data))
            .on('error', (data) => this.handleError(data))
            .connect();
    }

    bindEvents() {
        // 공통 이벤트
        if (this.options.btnRun) {
            this.options.btnRun.addEventListener('click', () => this.runScreening());
        }
        if (this.options.btnCancel) {
            this.options.btnCancel.addEventListener('click', () => this.cancelScreening());
        }

        // 프리셋 모드 이벤트
        if (this.type === 'preset') {
            if (this.options.presetSelect) {
                this.options.presetSelect.addEventListener('change', (e) => this.onPresetChange(e.target.value));
            }
        }

        // 커스텀 모드 이벤트
        if (this.type === 'custom') {
            if (this.options.categorySelect) {
                this.options.categorySelect.addEventListener('change', (e) => this.onCategoryChange(e.target.value));
            }
            if (this.options.conditionSelect) {
                this.options.conditionSelect.addEventListener('change', (e) => this.onConditionChange(e.target.value));
            }
            if (this.options.btnAddCondition) {
                this.options.btnAddCondition.addEventListener('click', () => this.addCondition());
            }
            if (this.options.btnClearConditions) {
                this.options.btnClearConditions.addEventListener('click', () => this.clearConditions());
            }
        }

        // 시장 변경 이벤트
        document.querySelectorAll('input[name="market"]').forEach(radio => {
            radio.addEventListener('change', () => {
                if (this.type === 'preset' && this.options.presetSelect.value) {
                    this.onPresetChange(this.options.presetSelect.value);
                }
            });
        });
    }

    // ========== 프리셋 모드 ==========

    async loadPresets() {
        try {
            const data = await Utils.api('/api/screening/presets');
            this.presets = data.presets || [];
            this.renderPresetOptions();
        } catch (error) {
            Utils.showToast('프리셋 로드 실패: ' + error.message, 'error');
        }
    }

    renderPresetOptions() {
        const select = this.options.presetSelect;
        select.innerHTML = '<option value="">-- 프리셋 선택 --</option>';

        this.presets.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.name;
            option.textContent = preset.display_name;
            select.appendChild(option);
        });
    }

    async onPresetChange(presetName) {
        if (!presetName) {
            this.options.presetDescription.classList.add('d-none');
            this.options.paramsContainer.classList.add('d-none');
            this.options.btnRun.disabled = true;
            return;
        }

        try {
            const market = document.querySelector('input[name="market"]:checked').value;
            const data = await Utils.api(`/api/screening/presets/${presetName}/info?market=${market}`);

            // 설명 표시
            this.options.presetName.textContent = data.display_name;
            this.options.presetDesc.textContent = data.description;
            this.options.presetDescription.classList.remove('d-none');

            // 파라미터 폼 생성
            this.renderParamsForm(data.parameters);
            this.options.paramsContainer.classList.remove('d-none');

            // 실행 버튼 활성화
            this.options.btnRun.disabled = false;
        } catch (error) {
            Utils.showToast('프리셋 정보 로드 실패: ' + error.message, 'error');
        }
    }

    renderParamsForm(parameters) {
        const form = this.options.paramsForm;
        form.innerHTML = '';

        parameters.forEach(param => {
            const div = document.createElement('div');
            div.className = 'mb-3';

            let input;
            if (param.type === 'int' || param.type === 'float') {
                input = `<input type="number" class="form-control" id="param-${param.name}"
                    value="${param.default}" step="${param.type === 'float' ? '0.01' : '1'}"
                    ${param.min !== undefined ? `min="${param.min}"` : ''}
                    ${param.max !== undefined ? `max="${param.max}"` : ''}>`;
            } else if (param.type === 'bool') {
                input = `<select class="form-select" id="param-${param.name}">
                    <option value="true" ${param.default ? 'selected' : ''}>예</option>
                    <option value="false" ${!param.default ? 'selected' : ''}>아니오</option>
                </select>`;
            } else {
                input = `<input type="text" class="form-control" id="param-${param.name}" value="${param.default || ''}">`;
            }

            div.innerHTML = `
                <label class="form-label" for="param-${param.name}">${param.display_name}</label>
                ${input}
                ${param.description ? `<small class="text-muted">${param.description}</small>` : ''}
            `;
            form.appendChild(div);
        });
    }

    getParamsValues() {
        const params = {};
        this.options.paramsForm.querySelectorAll('input, select').forEach(el => {
            const name = el.id.replace('param-', '');
            let value = el.value;

            // 타입 변환
            if (el.type === 'number') {
                value = el.step === '1' ? parseInt(value) : parseFloat(value);
            } else if (el.tagName === 'SELECT' && (value === 'true' || value === 'false')) {
                value = value === 'true';
            }

            params[name] = value;
        });
        return params;
    }

    // ========== 커스텀 모드 ==========

    async loadConditions() {
        try {
            const data = await Utils.api('/api/screening/conditions');
            this.availableConditions = data.conditions || {};
        } catch (error) {
            Utils.showToast('조건 목록 로드 실패: ' + error.message, 'error');
        }
    }

    onCategoryChange(category) {
        const select = this.options.conditionSelect;
        select.innerHTML = '<option value="">-- 조건 선택 --</option>';

        if (!category || !this.availableConditions[category]) {
            select.disabled = true;
            return;
        }

        const conditions = this.availableConditions[category];
        conditions.forEach(cond => {
            const option = document.createElement('option');
            option.value = cond.class_name;
            option.textContent = cond.display_name;
            select.appendChild(option);
        });

        select.disabled = false;
        this.options.conditionDescription.classList.add('d-none');
        this.options.conditionParams.classList.add('d-none');
    }

    onConditionChange(conditionName) {
        if (!conditionName) {
            this.options.conditionDescription.classList.add('d-none');
            this.options.conditionParams.classList.add('d-none');
            return;
        }

        const category = this.options.categorySelect.value;
        const conditions = this.availableConditions[category] || [];
        const condition = conditions.find(c => c.class_name === conditionName);

        if (!condition) return;

        // 설명 표시
        this.options.conditionName.textContent = condition.display_name;
        this.options.conditionDesc.textContent = condition.description || '';
        this.options.conditionDescription.classList.remove('d-none');

        // 파라미터 폼 생성
        this.renderConditionParamsForm(condition.parameters || []);
        this.options.conditionParams.classList.remove('d-none');
    }

    renderConditionParamsForm(parameters) {
        const form = this.options.conditionParamsForm;
        form.innerHTML = '';

        if (parameters.length === 0) {
            form.innerHTML = '<p class="text-muted small">파라미터가 필요없습니다.</p>';
            return;
        }

        parameters.forEach(param => {
            const div = document.createElement('div');
            div.className = 'mb-2';

            div.innerHTML = `
                <label class="form-label small" for="cond-param-${param.name}">${param.name}</label>
                <input type="number" class="form-control form-control-sm"
                    id="cond-param-${param.name}"
                    value="${param.default || ''}"
                    step="${param.type === 'float' ? '0.01' : '1'}">
            `;
            form.appendChild(div);
        });
    }

    addCondition() {
        const category = this.options.categorySelect.value;
        const conditionName = this.options.conditionSelect.value;

        if (!category || !conditionName) return;

        const conditions = this.availableConditions[category] || [];
        const condition = conditions.find(c => c.class_name === conditionName);
        if (!condition) return;

        // 파라미터 수집
        const params = {};
        this.options.conditionParamsForm.querySelectorAll('input').forEach(el => {
            const name = el.id.replace('cond-param-', '');
            params[name] = el.type === 'number' ? parseFloat(el.value) : el.value;
        });

        // 조건 추가
        this.conditions.push({
            category,
            class_name: conditionName,
            display_name: condition.display_name,
            params
        });

        this.renderSelectedConditions();
        this.updateRunButton();

        // 폼 초기화
        this.options.categorySelect.value = '';
        this.options.conditionSelect.innerHTML = '<option value="">-- 조건 선택 --</option>';
        this.options.conditionSelect.disabled = true;
        this.options.conditionDescription.classList.add('d-none');
        this.options.conditionParams.classList.add('d-none');

        Utils.showToast('조건이 추가되었습니다.', 'success');
    }

    renderSelectedConditions() {
        const container = this.options.selectedConditions;

        if (this.conditions.length === 0) {
            container.innerHTML = `
                <p class="text-muted text-center mb-0">
                    <i class="bi bi-info-circle"></i> 왼쪽 패널에서 조건을 추가하세요.
                </p>
            `;
            return;
        }

        container.innerHTML = '';
        this.conditions.forEach((cond, index) => {
            const paramsStr = Object.entries(cond.params)
                .map(([k, v]) => `${k}: ${v}`)
                .join(', ');

            const card = document.createElement('div');
            card.className = `condition-card ${cond.category} fade-in`;
            card.innerHTML = `
                <button class="btn-remove" data-index="${index}">
                    <i class="bi bi-x"></i>
                </button>
                <div class="condition-name">${cond.display_name}</div>
                <div class="condition-params">${paramsStr || '파라미터 없음'}</div>
            `;
            container.appendChild(card);
        });

        // 삭제 버튼 이벤트
        container.querySelectorAll('.btn-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                this.removeCondition(index);
            });
        });
    }

    removeCondition(index) {
        this.conditions.splice(index, 1);
        this.renderSelectedConditions();
        this.updateRunButton();
    }

    clearConditions() {
        this.conditions = [];
        this.renderSelectedConditions();
        this.updateRunButton();
    }

    updateRunButton() {
        if (this.options.btnRun) {
            this.options.btnRun.disabled = this.conditions.length === 0;
        }
    }

    // ========== 스크리닝 실행 ==========

    async runScreening() {
        const market = document.querySelector('input[name="market"]:checked').value;

        let endpoint, body;

        if (this.type === 'preset') {
            const presetName = this.options.presetSelect.value;
            if (!presetName) {
                Utils.showToast('프리셋을 선택하세요.', 'warning');
                return;
            }

            endpoint = '/api/screening/run/preset';
            body = {
                preset_name: presetName,
                market: market,
                params: this.getParamsValues()
            };
        } else {
            if (this.conditions.length === 0) {
                Utils.showToast('조건을 추가하세요.', 'warning');
                return;
            }

            const combineMode = document.querySelector('input[name="combine"]:checked').value;

            endpoint = '/api/screening/run/custom';
            body = {
                conditions: this.conditions.map(c => ({
                    class_name: c.class_name,
                    params: c.params
                })),
                combine_mode: combineMode,
                market: market
            };
        }

        try {
            // UI 업데이트
            this.options.btnRun.disabled = true;
            this.showProgressPanel();

            const data = await Utils.api(endpoint, {
                method: 'POST',
                body: JSON.stringify(body)
            });

            this.currentTaskId = data.task_id;
            this.updateProgress(0, '스크리닝 작업을 시작합니다...');

        } catch (error) {
            Utils.showToast('스크리닝 시작 실패: ' + error.message, 'error');
            this.hideProgressPanel();
            this.options.btnRun.disabled = false;
        }
    }

    async cancelScreening() {
        if (!this.currentTaskId) return;

        try {
            await Utils.api(`/api/tasks/${this.currentTaskId}/cancel`, {
                method: 'POST'
            });
            Utils.showToast('작업이 취소되었습니다.', 'info');
            this.hideProgressPanel();
            this.options.btnRun.disabled = false;
        } catch (error) {
            Utils.showToast('작업 취소 실패: ' + error.message, 'error');
        }
    }

    // ========== 소켓 이벤트 핸들러 ==========

    handleProgress(data) {
        if (data.task_id !== this.currentTaskId) return;

        this.updateProgress(data.percentage, data.message);
        if (data.log) {
            this.appendLog(data.log);
        }
    }

    handleCompleted(data) {
        if (data.task_id !== this.currentTaskId) return;

        this.updateProgress(100, '스크리닝 완료!');
        this.hideProgressPanel();
        this.showResults(data.result);
        this.options.btnRun.disabled = false;

        Utils.showToast('스크리닝이 완료되었습니다.', 'success');
    }

    handleError(data) {
        if (data.task_id !== this.currentTaskId) return;

        this.hideProgressPanel();
        this.options.btnRun.disabled = false;

        Utils.showToast('스크리닝 오류: ' + data.error, 'error');
    }

    // ========== UI 업데이트 ==========

    showProgressPanel() {
        if (this.options.progressPanel) {
            this.options.progressPanel.classList.remove('d-none');
        }
        if (this.options.resultsPanel) {
            this.options.resultsPanel.classList.add('d-none');
        }
        if (this.options.initialState) {
            this.options.initialState.classList.add('d-none');
        }
        if (this.options.taskLogs) {
            this.options.taskLogs.textContent = '';
        }
    }

    hideProgressPanel() {
        if (this.options.progressPanel) {
            this.options.progressPanel.classList.add('d-none');
        }
    }

    updateProgress(percentage, message) {
        if (this.options.progressBar) {
            this.options.progressBar.style.width = percentage + '%';
            this.options.progressBar.textContent = percentage + '%';
        }
        if (this.options.progressMessage) {
            this.options.progressMessage.textContent = message;
        }
    }

    appendLog(log) {
        if (this.options.taskLogs) {
            this.options.taskLogs.textContent += log + '\n';
            // 스크롤을 맨 아래로
            const container = this.options.taskLogs.parentElement;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }
    }

    showResults(result) {
        if (!result) return;

        // 결과 패널 표시
        if (this.options.resultsPanel) {
            this.options.resultsPanel.classList.remove('d-none');
        }

        // 요약 정보
        const stocks = result.stocks || [];
        const totalCount = result.total_count || 0;
        const filteredCount = stocks.length;
        const filterRate = totalCount > 0 ? ((filteredCount / totalCount) * 100).toFixed(1) : 0;

        if (this.options.resultsCount) {
            this.options.resultsCount.textContent = filteredCount + '개';
        }
        if (this.options.totalStocks) {
            this.options.totalStocks.textContent = Utils.formatNumber(totalCount);
        }
        if (this.options.filteredStocks) {
            this.options.filteredStocks.textContent = Utils.formatNumber(filteredCount);
        }
        if (this.options.filterRate) {
            this.options.filterRate.textContent = filterRate + '%';
        }

        // 결과 테이블
        this.renderResultsTable(stocks);
    }

    renderResultsTable(stocks) {
        const tbody = this.options.resultsBody;
        if (!tbody) return;

        tbody.innerHTML = '';

        if (stocks.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-muted py-4">
                        조건에 맞는 종목이 없습니다.
                    </td>
                </tr>
            `;
            return;
        }

        stocks.forEach((stock, index) => {
            const changeClass = Utils.getColorClass(stock.change_rate);
            const changeIcon = stock.change_rate > 0 ? '▲' : (stock.change_rate < 0 ? '▼' : '-');

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${index + 1}</td>
                <td><code>${stock.code}</code></td>
                <td><strong>${stock.name}</strong></td>
                <td class="text-end">${Utils.formatNumber(stock.price)}</td>
                <td class="text-end ${changeClass}">
                    ${changeIcon} ${Utils.formatPercent(Math.abs(stock.change_rate))}
                </td>
                <td class="text-end">${Utils.formatMarketCap(stock.market_cap)}</td>
                <td class="text-end">${stock.per ? stock.per.toFixed(2) : '-'}</td>
                <td class="text-end">${stock.pbr ? stock.pbr.toFixed(2) : '-'}</td>
                <td class="text-end">${stock.roe ? Utils.formatPercent(stock.roe) : '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    }
}

// 전역으로 내보내기
window.ScreeningManager = ScreeningManager;
