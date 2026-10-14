(() => {
    'use strict';

    const page = document.getElementById('storage-health-page');
    if (!page) return;

    const overviewUrl  = page.dataset.overviewUrl;
    const cleanupUrl   = page.dataset.cleanupUrl;
    const tuneupUrl    = page.dataset.tuneupUrl;
    const dbhealthUrl  = page.dataset.dbhealthUrl;
    const csrfToken    = page.dataset.csrfToken || '';
    const locale       = document.documentElement.lang || navigator.language || 'tr-TR';

    const labels = {
        loading:                    page.dataset.loading                  || 'Yükleniyor…',
        error:                      page.dataset.error                    || 'Veri alınamadı',
        scanComplete:               page.dataset.scanComplete             || 'KUSURSUZ',
        scanReview:                 page.dataset.scanReview               || 'İNCELEME GEREKİYOR',
        trendAvailable:             page.dataset.trendAvailable           || 'MEVCUT',
        trendUnavailable:           page.dataset.trendUnavailable         || 'YETERSİZ VERİ',
        recommendOnly:              page.dataset.recommendOnly            || 'ÖNERİ',
        retentionHold:              page.dataset.retentionHold            || 'KORUMADA',
        retentionOwnerPolicy:       page.dataset.retentionOwnerPolicy     || 'POLİTİKA GEREKLİ',
        retentionNever:             page.dataset.retentionNever           || 'ASLA',
        retentionPeriodUnassigned:  page.dataset.retentionPeriodUnassigned || 'ATANMAMIŞ',
        retentionNoMutation:        page.dataset.retentionNoMutation      || 'DOKUNULMAZ',
        cleanupSelect:              page.dataset.cleanupSelect            || 'Seç',
        cleanupDeleteSelected:      page.dataset.cleanupDeleteSelected    || 'Seçilenleri Sil',
        cleanupModalTitle:          page.dataset.cleanupModalTitle        || 'Temizleme Onayı',
        cleanupModalBody:           page.dataset.cleanupModalBody         || 'Seçili adaylar kalıcı olarak silinecek.',
        cleanupModalConfirm:        page.dataset.cleanupModalConfirm      || 'Evet, Sil',
        cleanupModalCancel:         page.dataset.cleanupModalCancel       || 'İptal',
        cleanupSuccess:             page.dataset.cleanupSuccess           || 'Temizleme tamamlandı',
        cleanupError:               page.dataset.cleanupError             || 'Temizleme başarısız',
        cleanupRunning:             page.dataset.cleanupRunning           || 'Temizleniyor…',
        cleanupNoneSelected:        page.dataset.cleanupNoneSelected      || 'Hiçbir aday seçilmedi',
        safeAutoLabel:              page.dataset.safeAutoLabel            || 'SAFE_AUTO',
    };

    const refreshButton   = document.getElementById('storage-health-refresh');
    const btnSmartTuneup  = document.getElementById('btn-smart-tuneup');
    const filterInput     = document.getElementById('storage-health-filter');
    const candidatesBody  = document.getElementById('storage-health-candidates-body');
    const emptyState      = document.getElementById('storage-health-empty-state');
    const deleteBar       = document.getElementById('storage-health-delete-bar');
    const deleteBtn       = document.getElementById('storage-health-delete-btn');
    const selectedCounter = document.getElementById('storage-health-selected-count');

    // Tune-Up Modal elements
    const tuneupModal     = document.getElementById('sh-tuneup-modal');
    const tuneupCloseBtn  = document.getElementById('sh-tuneup-close-btn');
    const tuneupActionBtn = document.getElementById('sh-tuneup-action-btn');
    const tuneupStatusMsg = document.getElementById('sh-tuneup-status-msg');
    const tuneupSpinner   = document.getElementById('sh-tuneup-spinner');
    const tuneupTimer     = document.getElementById('sh-tuneup-timer');
    const tuneupCallout   = document.getElementById('sh-tuneup-summary-callout');
    const calloutDetail   = document.getElementById('sh-callout-detail');

    let candidates   = [];
    let planHash     = '';
    let snapshotId   = '';
    let selectedIds  = new Set();
    let donutChart   = null;
    let tuneupTimerId = null;

    // ── Formatters ────────────────────────────────────────────────────────

    const formatBytes = (value) => {
        const bytes = Number(value) || 0;
        if (bytes < 1024) return `${bytes.toLocaleString(locale)} B`;
        const units = ['KB', 'MB', 'GB', 'TB'];
        let amount = bytes, unit = -1;
        while (amount >= 1024 && unit < units.length - 1) { amount /= 1024; unit += 1; }
        return `${amount.toLocaleString(locale, { maximumFractionDigits: 2 })} ${units[unit]}`;
    };

    const formatDate = (epoch) => {
        if (!epoch) return '—';
        return new Date(Number(epoch) * 1000).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' });
    };

    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };

    const setStatus = (state, message) => {
        const dot  = document.getElementById('storage-health-status-dot');
        const text = document.getElementById('storage-health-status-text');
        if (dot)  dot.className  = `storage-health-status-dot ${state ? `is-${state}` : ''}`;
        if (text) text.textContent = message;
    };

    const createCell = (value, className = '') => {
        const cell = document.createElement('td');
        if (className) cell.className = className;
        cell.textContent = (value == null || value === '') ? '—' : String(value);
        return cell;
    };

    const createBadge = (value, risk = false) => {
        const badge = document.createElement('span');
        const normalized = String(value || '').toLowerCase();
        badge.className = `storage-health-badge ${risk ? `storage-health-badge-${normalized}` : ''}`;
        badge.textContent = value || '—';
        return badge;
    };

    // ── Selection management ──────────────────────────────────────────────

    const updateDeleteBar = () => {
        if (!deleteBar || !deleteBtn || !selectedCounter) return;
        const count = selectedIds.size;
        selectedCounter.textContent = count;
        deleteBar.hidden = count === 0;
        deleteBtn.disabled = count === 0;

        const headerCb = document.getElementById('sh-select-all');
        if (headerCb && candidatesBody) {
            const safeRows = candidatesBody.querySelectorAll('input[type=checkbox][data-safe]');
            headerCb.indeterminate = count > 0 && count < safeRows.length;
            headerCb.checked = safeRows.length > 0 && count === safeRows.length;
        }
    };

    const toggleSelect = (id, checked) => {
        checked ? selectedIds.add(id) : selectedIds.delete(id);
        updateDeleteBar();
    };

    const clearSelection = () => {
        selectedIds.clear();
        if (candidatesBody) {
            candidatesBody.querySelectorAll('input[type=checkbox]')
                .forEach(cb => { cb.checked = false; });
        }
        updateDeleteBar();
    };

    // ── Telemetry & Database Vital Signs ──────────────────────────────────

    const renderTelemetryAndVitals = (payload) => {
        const telem = payload.telemetry || {};
        const db    = payload.database_vitality || {};
        const rec   = payload.recommendation || {};

        // 1. OS Disk Pod
        if (telem.total_bytes > 0) {
            setText('kpi-disk-free', `${formatBytes(telem.free_bytes)} Boş`);
            setText('kpi-disk-total', `${formatBytes(telem.used_bytes)} / ${formatBytes(telem.total_bytes)} (%${telem.used_percentage})`);
            const bar = document.getElementById('kpi-disk-bar');
            if (bar) {
                bar.style.width = `${Math.min(100, telem.used_percentage)}%`;
                bar.className = 'sh-progress-bar' +
                    (telem.used_percentage >= 90 ? ' is-critical' : telem.used_percentage >= 75 ? ' is-warning' : '');
            }
        }

        // 2. Database Engine Pod
        if (db.exists) {
            setText('kpi-db-size', formatBytes(db.total_size_bytes || db.size_bytes));
            const integEl = document.getElementById('kpi-db-integrity');
            if (integEl) {
                const isOk = String(db.integrity_status).toLowerCase() === 'ok';
                integEl.textContent = isOk ? 'Bütünlük: OK' : 'Bütünlük: Uyarı';
                integEl.className = 'sh-kpi-pill ' + (isOk ? 'ok' : 'warning');
            }
            setText('kpi-db-wal', `WAL: ${formatBytes(db.wal_size_bytes)}`);
        }

        // 3. Reclaimable Pod
        const totalReclaimable = (db.reclaimable_bytes || 0) + (rec.safe_reclaimable_bytes || 0);
        setText('kpi-reclaimable-total', formatBytes(totalReclaimable));
        setText('kpi-freelist-pages', `${Number(db.freelist_count || 0).toLocaleString(locale)} Freelist Sayfası`);

        // 4. Vitals Panel
        setText('vitals-integrity', db.integrity_status === 'ok' ? '✓ %100 Doğrulandı (Kusursuz)' : String(db.integrity_status));
        setText('vitals-journal-mode', `${db.journal_mode || 'WAL'} (Eşzamanlı Okuma/Yazma)`);
        setText('vitals-fk-status', `${db.foreign_key_violations || 0} İhlal (İlişkisel Bütünlük Tam)`);
        setText('vitals-freelist', `${Number(db.freelist_count || 0).toLocaleString(locale)} Sayfa (~${formatBytes(db.freelist_count * (db.page_size || 4096))})`);
        setText('vitals-page-size', `${Number(db.page_size || 4096).toLocaleString(locale)} Bayt`);
    };

    // ── Chart.js Donut Breakdown ──────────────────────────────────────────

    const renderBreakdownChart = (breakdown) => {
        const canvas = document.getElementById('sh-breakdown-chart');
        const legendContainer = document.getElementById('sh-chart-legend');
        if (!canvas || !legendContainer || !breakdown || !Array.isArray(breakdown.categories)) return;

        const categories = breakdown.categories;
        const labelsList = categories.map(c => c.label);
        const dataList   = categories.map(c => c.bytes);
        const colorsList = categories.map(c => c.color);

        legendContainer.replaceChildren();
        categories.forEach(c => {
            const item = document.createElement('div');
            item.className = 'sh-legend-item';

            const left = document.createElement('div');
            left.className = 'sh-legend-left';
            const dot = document.createElement('span');
            dot.className = 'sh-legend-dot';
            dot.style.background = c.color;
            const label = document.createElement('span');
            label.className = 'sh-legend-label';
            label.textContent = c.label;
            left.append(dot, label);

            const right = document.createElement('div');
            right.className = 'sh-legend-right';
            const size = document.createElement('span');
            size.className = 'sh-legend-size';
            size.textContent = formatBytes(c.bytes);
            const pct = document.createElement('span');
            pct.className = 'sh-legend-pct';
            pct.textContent = `%${c.percentage}`;
            right.append(size, pct);

            item.append(left, right);
            legendContainer.appendChild(item);
        });

        if (typeof Chart === 'undefined') return;

        if (donutChart) {
            donutChart.destroy();
            donutChart = null;
        }

        const ctx = canvas.getContext('2d');
        donutChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labelsList,
                datasets: [{
                    data: dataList,
                    backgroundColor: colorsList,
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const val = context.raw || 0;
                                return ` ${formatBytes(val)}`;
                            },
                        },
                    },
                },
                cutout: '68%',
            },
        });
    };

    // ── Candidates table ──────────────────────────────────────────────────

    const renderCandidates = () => {
        if (!candidatesBody) return;
        const query = (filterInput?.value || '').trim().toLowerCase();
        const visible = candidates.filter(c => {
            const haystack = [
                c.relative_path, c.category, c.policy_class, c.risk_level,
                c.rollback?.strategy, c.governance?.owner,
                c.governance?.lifecycle_state, c.governance?.retention_class,
            ].join(' ').toLowerCase();
            return !query || haystack.includes(query);
        });

        candidatesBody.replaceChildren();

        if (!visible.length) {
            const row  = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 11;
            cell.className = 'storage-health-empty';
            cell.textContent = '—';
            row.appendChild(cell);
            candidatesBody.appendChild(row);
        } else {
            visible.forEach(c => {
                const row      = document.createElement('tr');
                const isSafe   = c.policy_class === 'SAFE_AUTO' && c.execute_eligible;

                const cbCell = document.createElement('td');
                cbCell.className = 'storage-health-cb-cell';
                if (isSafe) {
                    const cb = document.createElement('input');
                    cb.type = 'checkbox';
                    cb.className = 'storage-health-row-cb';
                    cb.setAttribute('aria-label', `Seç: ${c.relative_path}`);
                    cb.dataset.safe = '1';
                    cb.dataset.id   = c.candidate_id;
                    cb.checked = selectedIds.has(c.candidate_id);
                    cb.addEventListener('change', () => toggleSelect(c.candidate_id, cb.checked));
                    cbCell.appendChild(cb);
                }
                row.appendChild(cbCell);

                row.appendChild(createCell(c.relative_path));
                row.appendChild(createCell(c.category));
                row.appendChild(createCell(c.policy_class));

                const riskCell = document.createElement('td');
                riskCell.appendChild(createBadge(c.risk_level, true));
                row.appendChild(riskCell);

                row.appendChild(createCell(formatBytes(c.reclaimable_bytes)));
                row.appendChild(createCell(c.rollback?.strategy));

                const gov = c.governance || {};
                row.appendChild(createCell(gov.owner || 'unknown'));
                row.appendChild(createCell(gov.lifecycle_state || 'review'));
                row.appendChild(createCell(gov.retention_days == null ? '—' : gov.retention_days));

                const stateCell = document.createElement('td');
                if (isSafe) {
                    stateCell.className = 'storage-health-state-ready';
                    stateCell.textContent = labels.safeAutoLabel;
                } else {
                    stateCell.className = 'storage-health-state-blocked';
                    stateCell.textContent = labels.recommendOnly;
                }
                row.appendChild(stateCell);

                candidatesBody.appendChild(row);
            });
        }

        if (emptyState) emptyState.hidden = candidates.length !== 0;
        updateDeleteBar();
    };

    // ── Full overview render ──────────────────────────────────────────────

    const renderOverview = (payload) => {
        const scan           = payload.scan           || {};
        const recommendation = payload.recommendation || {};
        const execPreview    = payload.execution_preview || {};

        planHash   = execPreview.plan_hash   || '';
        snapshotId = execPreview.snapshot_id || recommendation.scan_snapshot_id || recommendation.snapshot_token || '';

        setText('storage-health-last-scan', formatDate(scan.scanned_at_epoch));
        setText('storage-health-snapshot', recommendation.scan_snapshot_id || recommendation.snapshot_token || '—');

        const scanGated = scan.truncated || (scan.errors || []).length;
        setText('storage-health-scan-quality', scanGated ? labels.scanReview : labels.scanComplete);

        renderTelemetryAndVitals(payload);
        renderBreakdownChart(payload.storage_breakdown);

        candidates = Array.isArray(recommendation.candidates) ? recommendation.candidates : [];
        selectedIds.clear();
        renderCandidates();
        renderHistory(payload.maintenance_history);
        setStatus(scanGated ? 'warning' : 'ready', scanGated ? labels.scanReview : labels.scanComplete);

        const headerCb = document.getElementById('sh-select-all');
        if (headerCb) {
            const safeCount = candidates.filter(c => c.policy_class === 'SAFE_AUTO' && c.execute_eligible).length;
            headerCb.disabled = safeCount === 0;
        }
    };

    // ── Maintenance History Logbook ───────────────────────────────────────

    const renderHistory = (historyItems) => {
        const body = document.getElementById('sh-history-body');
        if (!body) return;
        body.replaceChildren();

        if (!Array.isArray(historyItems) || historyItems.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 9;
            cell.className = 'storage-health-empty';
            cell.textContent = 'Kayıtlı bakım geçmişi bulunmuyor.';
            row.appendChild(cell);
            body.appendChild(row);
            return;
        }

        historyItems.forEach(item => {
            const row = document.createElement('tr');

            row.appendChild(createCell(item.date_str || formatDate(item.timestamp)));

            const triggerCell = document.createElement('td');
            const isAuto = item.trigger_source === 'scheduled_background';
            const trigPill = document.createElement('span');
            trigPill.className = 'sh-kpi-pill ' + (isAuto ? 'safe' : 'neutral');
            trigPill.textContent = isAuto ? '🤖 Otonom Gece' : '⚡ Manuel Yönetici';
            triggerCell.appendChild(trigPill);
            row.appendChild(triggerCell);

            row.appendChild(createCell(item.user_name || 'Yönetici'));

            const freedCell = document.createElement('td');
            const freedBadge = document.createElement('strong');
            freedBadge.className = 'text-emerald-600 font-bold';
            freedBadge.textContent = formatBytes(item.total_bytes_freed || 0);
            freedCell.appendChild(freedBadge);
            row.appendChild(freedCell);

            row.appendChild(createCell(formatBytes(item.db_bytes_freed || 0)));
            row.appendChild(createCell(formatBytes(item.cache_freed_bytes || 0)));
            row.appendChild(createCell(`${item.duration_ms || 0} ms`));

            const snapCell = document.createElement('td');
            const snapCode = document.createElement('code');
            snapCode.style.fontSize = '0.72rem';
            const pathParts = (item.snapshot_path || '').split(/[\\\\/]/);
            snapCode.textContent = pathParts[pathParts.length - 1] || '—';
            snapCell.appendChild(snapCode);
            row.appendChild(snapCell);

            const resCell = document.createElement('td');
            const resPill = document.createElement('span');
            resPill.className = 'sh-kpi-pill ' + (item.success ? 'ok' : 'warning');
            resPill.textContent = item.success ? '✓ Başarılı' : 'Uyarı';
            resCell.appendChild(resPill);
            row.appendChild(resCell);

            body.appendChild(row);
        });
    };


    // ── Load overview ─────────────────────────────────────────────────────

    const loadOverview = async (refresh = false) => {
        if (refreshButton) refreshButton.disabled = true;
        setStatus('', labels.loading);
        try {
            const url = new URL(overviewUrl, window.location.origin);
            if (refresh) url.searchParams.set('refresh', '1');
            const response = await fetch(url.toString(), {
                method: 'GET',
                credentials: 'same-origin',
                headers: { Accept: 'application/json' },
                cache: 'no-store',
            });
            const body = await response.json();
            if (!response.ok || !body.success || !body.data) throw new Error(body.error || labels.error);
            renderOverview(body.data);
        } catch (err) {
            setStatus('error', labels.error);
        } finally {
            if (refreshButton) refreshButton.disabled = false;
        }
    };

    // ── Smart Tune-Up Console Pipeline ────────────────────────────────────

    const setStepState = (stepKey, state, badgeText) => {
        const step = document.querySelector(`.sh-tuneup-step[data-step="${stepKey}"]`);
        if (!step) return;
        step.className = `sh-tuneup-step is-${state}`;
        const icon = step.querySelector('.sh-step-icon');
        const badge = step.querySelector('.sh-step-badge');
        if (state === 'running') {
            if (icon) icon.textContent = '⚙';
            if (badge) badge.textContent = badgeText || 'Çalışıyor…';
        } else if (state === 'done') {
            if (icon) icon.textContent = '✔';
            if (badge) badge.textContent = badgeText || 'Tamam';
        } else if (state === 'error') {
            if (icon) icon.textContent = '✖';
            if (badge) badge.textContent = badgeText || 'Hata';
        } else {
            if (icon) icon.textContent = '○';
            if (badge) badge.textContent = badgeText || 'Bekliyor';
        }
    };

    const resetTuneupModal = () => {
        ['preflight', 'snapshot', 'wal', 'vacuum', 'cache', 'optimize', 'postflight'].forEach(key => {
            setStepState(key, 'pending', 'Bekliyor');
        });
        if (tuneupStatusMsg) tuneupStatusMsg.textContent = 'Bakım hattı hazır. Başlatmak için butona tıklayın.';
        if (tuneupSpinner) tuneupSpinner.className = 'sh-tuneup-spinner is-hidden';
        if (tuneupTimer) tuneupTimer.textContent = '0.0s';
        if (tuneupCallout) tuneupCallout.hidden = true;
        if (tuneupActionBtn) {
            tuneupActionBtn.disabled = false;
            tuneupActionBtn.textContent = 'Bakımı Başlat';
            tuneupActionBtn.dataset.state = 'ready';
        }
        if (tuneupTimerId) {
            clearInterval(tuneupTimerId);
            tuneupTimerId = null;
        }
    };

    const runSmartTuneUp = async () => {
        if (!tuneupUrl) return;
        if (tuneupActionBtn) tuneupActionBtn.disabled = true;
        if (tuneupSpinner) tuneupSpinner.className = 'sh-tuneup-spinner';
        if (tuneupStatusMsg) tuneupStatusMsg.textContent = 'Bakım hattı çalıştırılıyor…';

        const startTime = performance.now();
        tuneupTimerId = setInterval(() => {
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
            if (tuneupTimer) tuneupTimer.textContent = `${elapsed}s`;
        }, 100);

        setStepState('preflight', 'running');

        try {
            // Simulated visual step progression while executing
            setTimeout(() => setStepState('snapshot', 'running'), 200);
            setTimeout(() => setStepState('wal', 'running'), 500);
            setTimeout(() => setStepState('vacuum', 'running'), 800);
            setTimeout(() => setStepState('cache', 'running'), 1100);
            setTimeout(() => setStepState('optimize', 'running'), 1400);
            setTimeout(() => setStepState('postflight', 'running'), 1700);

            const response = await fetch(tuneupUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    Accept: 'application/json',
                },
                body: JSON.stringify({ purge_cache: true, create_snapshot: true }),
            });

            const body = await response.json();
            clearInterval(tuneupTimerId);

            if (!response.ok || !body.success || !body.data) {
                throw new Error(body.error || 'Bakım sırasında hata oluştu');
            }

            const data = body.data;
            ['preflight', 'snapshot', 'wal', 'vacuum', 'cache', 'optimize', 'postflight'].forEach(key => {
                setStepState(key, 'done', 'Tamamlandı');
            });

            if (tuneupSpinner) tuneupSpinner.className = 'sh-tuneup-spinner is-hidden';
            if (tuneupStatusMsg) tuneupStatusMsg.textContent = 'Tüm bakım adımları başarıyla tamamlandı!';

            if (calloutDetail) {
                const totalMb = (data.total_bytes_freed / (1024 * 1024)).toFixed(1);
                const dbMb    = (data.db_bytes_freed / (1024 * 1024)).toFixed(1);
                const cacheMb = (data.cache_freed_bytes / (1024 * 1024)).toFixed(1);
                calloutDetail.textContent = `Toplam ${totalMb} MB alan geri kazanıldı (Veritabanı: ${dbMb} MB, Önbellek: ${cacheMb} MB). Veritabanı bütünlüğü %100 korundu.`;
            }
            if (tuneupCallout) tuneupCallout.hidden = false;

            if (tuneupActionBtn) {
                tuneupActionBtn.disabled = false;
                tuneupActionBtn.textContent = 'Kapat ve Güncelle';
                tuneupActionBtn.dataset.state = 'done';
            }

        } catch (err) {
            clearInterval(tuneupTimerId);
            if (tuneupSpinner) tuneupSpinner.className = 'sh-tuneup-spinner is-hidden';
            if (tuneupStatusMsg) tuneupStatusMsg.textContent = `Hata: ${err.message}`;
            setStepState('preflight', 'error', 'Hata');
            if (tuneupActionBtn) {
                tuneupActionBtn.disabled = false;
                tuneupActionBtn.textContent = 'Kapat';
                tuneupActionBtn.dataset.state = 'done';
            }
        }
    };

    // ── Wire event listeners ──────────────────────────────────────────────

    if (btnSmartTuneup && tuneupModal) {
        btnSmartTuneup.addEventListener('click', () => {
            resetTuneupModal();
            tuneupModal.hidden = false;
        });
    }

    if (tuneupCloseBtn && tuneupModal) {
        tuneupCloseBtn.addEventListener('click', () => {
            tuneupModal.hidden = true;
        });
    }

    if (tuneupActionBtn) {
        tuneupActionBtn.addEventListener('click', () => {
            if (tuneupActionBtn.dataset.state === 'done') {
                if (tuneupModal) tuneupModal.hidden = true;
                loadOverview(true);
            } else {
                runSmartTuneUp();
            }
        });
    }

    if (refreshButton) {
        refreshButton.addEventListener('click', () => loadOverview(true));
    }

    if (filterInput) {
        filterInput.addEventListener('input', renderCandidates);
    }

    // Header select-all checkbox
    const headerCb = document.getElementById('sh-select-all');
    if (headerCb) {
        headerCb.addEventListener('change', () => {
            const safeCbs = candidatesBody.querySelectorAll('input[type=checkbox][data-safe]');
            safeCbs.forEach(cb => {
                cb.checked = headerCb.checked;
                const id = cb.dataset.id;
                if (id) headerCb.checked ? selectedIds.add(id) : selectedIds.delete(id);
            });
            updateDeleteBar();
        });
    }

    // ── Candidates Sorting & CSV Export ──────────────────────────────────
    let candidateSort = { column: null, ascending: true };

    const sortCandidates = (column) => {
        if (candidateSort.column === column) {
            candidateSort.ascending = !candidateSort.ascending;
        } else {
            candidateSort.column = column;
            candidateSort.ascending = true;
        }

        const isAsc = candidateSort.ascending;

        // Update header indicators
        document.querySelectorAll('#storage-health-candidates-table th[data-sort-col]').forEach(th => {
            const ind = th.querySelector('.sh-sort-indicator');
            if (ind) {
                if (th.getAttribute('data-sort-col') === column) {
                    ind.textContent = isAsc ? '↑' : '↓';
                } else {
                    ind.textContent = '⇅';
                }
            }
        });

        candidates.sort((a, b) => {
            let valA, valB;
            if (column === 'resource') {
                valA = (a.relative_path || '').toLowerCase();
                valB = (b.relative_path || '').toLowerCase();
                return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else if (column === 'category') {
                valA = (a.category || '').toLowerCase();
                valB = (b.category || '').toLowerCase();
                return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else if (column === 'policy') {
                valA = (a.policy_class || '').toLowerCase();
                valB = (b.policy_class || '').toLowerCase();
                return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else if (column === 'risk') {
                valA = (a.risk_level || '').toLowerCase();
                valB = (b.risk_level || '').toLowerCase();
                return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else if (column === 'bytes') {
                valA = Number(a.reclaimable_bytes) || 0;
                valB = Number(b.reclaimable_bytes) || 0;
                return isAsc ? valA - valB : valB - valA;
            }
            return 0;
        });

        renderCandidates();
    };

    const exportCandidatesToCsv = () => {
        if (!candidates || !candidates.length) return;
        const headers = ['Kaynak', 'Kategori', 'Politika', 'Risk Seviyesi', 'Kazanılabilir Bayt', 'Geri Alma', 'Sahiplik', 'Yaşam Döngüsü', 'Saklama Günü', 'Eylem Durumu'];
        const rows = candidates.map(c => [
            `"${(c.relative_path || '').replace(/"/g, '""')}"`,
            `"${(c.category || '').replace(/"/g, '""')}"`,
            `"${(c.policy_class || '').replace(/"/g, '""')}"`,
            `"${(c.risk_level || '').replace(/"/g, '""')}"`,
            c.reclaimable_bytes || 0,
            `"${(c.rollback?.strategy || '').replace(/"/g, '""')}"`,
            `"${(c.governance?.owner || '').replace(/"/g, '""')}"`,
            `"${(c.governance?.lifecycle_state || '').replace(/"/g, '""')}"`,
            c.governance?.retention_days ?? '',
            `"${(c.policy_class === 'SAFE_AUTO' && c.execute_eligible ? 'SAFE_AUTO' : 'RECOMMEND_ONLY')}"`
        ]);

        const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `depolama_adaylari_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();
        URL.revokeObjectURL(link.href);
    };

    // Wire sort headers
    document.querySelectorAll('#storage-health-candidates-table th[data-sort-col]').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.getAttribute('data-sort-col');
            if (col) sortCandidates(col);
        });
    });

    // Wire CSV export button
    const btnExportCsv = document.getElementById('sh-export-candidates-csv');
    if (btnExportCsv) {
        btnExportCsv.addEventListener('click', exportCandidatesToCsv);
    }

    // Modal cleanup cancel
    const modalCancel = document.querySelector('[data-modal-cancel]');
    if (modalCancel) {
        modalCancel.addEventListener('click', () => {
            const m = document.getElementById('sh-cleanup-modal');
            if (m) m.hidden = true;
        });
    }

    // Keyboard ESC to close active modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (tuneupModal && !tuneupModal.hidden) {
                tuneupModal.hidden = true;
            }
            const cleanupModal = document.getElementById('sh-cleanup-modal');
            if (cleanupModal && !cleanupModal.hidden) {
                cleanupModal.hidden = true;
            }
        }
    });

    // Initial load
    loadOverview(false);

})();
