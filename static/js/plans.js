/* ==========================================================================
   E-Cüzdan — Plans & Recurring Payments JavaScript (static/js/plans.js)
   Clean, User-Friendly Plan Drawer, Modals, Category Binding & Payments
   ========================================================================== */

function getPlanCopy() {
    return window.planCopy || {};
}

function getPlanCurrencySymbol() {
    return window.plan_currency_symbol || window.BASE_CURRENCY_SYMBOL || '₺';
}

function interpolatePlanCopy(template, values = {}) {
    return (template || '').replace(/\{(\w+)\}/g, (_, key) => values[key] ?? '');
}

const planDetailState = { planId: null, plan: null, returnFocus: null };

function escapePlanHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, character => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    })[character]);
}

function planLabel(map, value) {
    return (map && map[value]) || value || '—';
}

function planAmount(value) {
    if (value === null || value === undefined || value === '') return '—';
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return escapePlanHtml(value);
    return numeric.toLocaleString(document.documentElement.lang || undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

function occurrenceStatusTone(status) {
    return {
        scheduled: 'border-amber-100 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300',
        paid: 'border-emerald-100 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300',
        skipped: 'border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400',
        cancelled: 'border-rose-100 bg-rose-50 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300',
    }[status] || 'border-slate-200 bg-slate-50 text-slate-600';
}

function findPlanEditButton(detailButton) {
    return detailButton?.closest('[data-plan-row], [data-plan-card]')?.querySelector('[data-id]') || null;
}

function renderPlanDetail(data) {
    const copy = getPlanCopy();
    const curr = getPlanCurrencySymbol();
    const plan = data.plan || {};
    const summary = data.summary || {};
    const next = data.next_occurrence;
    const statusKeys = ['scheduled', 'paid', 'skipped', 'cancelled'];
    const detailTitle = document.getElementById('planDetailTitle');
    const content = document.getElementById('planDetailContent');
    if (!detailTitle || !content) return;
    detailTitle.textContent = plan.name || copy.detailTitle || 'Plan Detayı';
    const status = planLabel(copy.statusLabels, plan.status);
    const statusTone = plan.status === 'Aktif'
        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
        : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';
    const nextMarkup = next
        ? `<div class="rounded-2xl border border-indigo-100 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/30 p-4">
            <div class="flex items-center justify-between gap-3">
                <div>
                    <p class="text-[10px] font-black uppercase tracking-wider text-indigo-700 dark:text-indigo-300">${escapePlanHtml(copy.detailNext || 'Sıradaki Ödeme')}</p>
                    <p class="mt-2 text-sm font-black text-slate-800 dark:text-white">${escapePlanHtml(next.scheduled_date)}</p>
                    <p class="mt-1 text-[10px] font-semibold text-slate-500 dark:text-slate-400">${escapePlanHtml(interpolatePlanCopy(copy.occurrenceInfo, { number: next.occurrence_number, date: next.scheduled_date, status: planLabel(copy.occurrenceLabels, next.status) }))}</p>
                </div>
                <strong class="whitespace-nowrap text-sm font-black text-indigo-700 dark:text-indigo-300">${planAmount(next.amount)} ${escapePlanHtml(curr)}</strong>
            </div>
            ${next.status === 'scheduled' ? `
            <div class="mt-3 flex items-center gap-2 border-t border-indigo-100/60 dark:border-indigo-900/40 pt-2.5">
                <button data-macro="button_secondary" type="button" data-occurrence-action="cancel" data-occurrence-id="${next.id}" class="plan-btn plan-btn-secondary plan-btn-compact text-rose-600 hover:text-rose-700">Bu Ödemeyi İptal Et</button>
                <button data-macro="button_secondary" type="button" data-occurrence-action="skip" data-occurrence-id="${next.id}" class="plan-btn plan-btn-secondary plan-btn-compact text-amber-600 hover:text-amber-700">Bu Ayı Atla</button>
            </div>` : ''}
           </div>`
        : `<div class="rounded-2xl border border-dashed border-slate-200 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-800/40 p-4 text-xs font-semibold text-slate-500">${escapePlanHtml(copy.detailNoSchedule || 'Planlanmış ödeme bulunmuyor.')}</div>`;
    const occurrenceCards = statusKeys.map(key => `<div class="rounded-2xl border ${occurrenceStatusTone(key)} p-3"><p class="text-[10px] font-black uppercase tracking-wider">${escapePlanHtml(planLabel(copy.occurrenceLabels, key))}</p><p class="mt-2 text-xl font-black">${Number(summary[key] || 0)}</p></div>`).join('');
    content.innerHTML = `<div class="space-y-5">
        <section class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/60 p-4">
            <div class="flex items-start justify-between gap-3"><div class="min-w-0"><h3 class="truncate text-base font-black text-slate-900 dark:text-white">${escapePlanHtml(plan.name || '—')}</h3><p class="mt-1 text-xs font-semibold text-slate-500 dark:text-slate-400">${escapePlanHtml(plan.category || '—')}</p></div><span class="rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-wider ${statusTone}">${escapePlanHtml(status)}</span></div>
            ${plan.note ? `<p class="mt-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 p-3 text-xs font-semibold leading-relaxed text-slate-600 dark:text-slate-300">${escapePlanHtml(plan.note)}</p>` : ''}
        </section>
        <dl class="grid grid-cols-2 gap-3 text-xs">
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">${escapePlanHtml(copy.detailFieldFlow || 'Akış')}</dt><dd class="mt-1 font-black text-slate-700 dark:text-slate-200">${escapePlanHtml(planLabel(copy.flowLabels, plan.flow))}</dd></div>
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">${escapePlanHtml(copy.detailFieldAmount || 'Tutar')}</dt><dd class="mt-1 font-black text-slate-700 dark:text-slate-200">${planAmount(plan.amount)} ${escapePlanHtml(curr)}</dd></div>
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">${escapePlanHtml(copy.detailFieldFrequency || 'Sıklık')}</dt><dd class="mt-1 font-black text-slate-700 dark:text-slate-200">${escapePlanHtml(planLabel(copy.frequencyLabels, plan.frequency))}</dd></div>
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">${escapePlanHtml(copy.detailFieldLifecycle || 'Tip')}</dt><dd class="mt-1 font-black text-slate-700 dark:text-slate-200">${escapePlanHtml(planLabel(copy.lifecycleLabels, plan.lifecycle))}</dd></div>
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">${escapePlanHtml(copy.detailFieldStart || 'Başlangıç')}</dt><dd class="mt-1 font-black text-slate-700 dark:text-slate-200">${escapePlanHtml(plan.start_date || '—')}</dd></div>
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">${escapePlanHtml(copy.detailFieldEnd || 'Bitiş')}</dt><dd class="mt-1 font-black text-slate-700 dark:text-slate-200">${escapePlanHtml(plan.end_date || '—')}</dd></div>
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">Kalan Süre</dt><dd class="mt-1 font-black text-indigo-600 dark:text-indigo-400">${escapePlanHtml(plan.status === 'Tamamlandı' || plan.status === 'İptal' ? 'Tamamlandı' : (plan.months_remaining === null || plan.months_remaining === undefined ? 'Süresiz (∞)' : (plan.months_remaining === 0 ? 'Son ay' : plan.months_remaining + ' ay')))}</dd></div>
            <div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">Ödeme Günü</dt><dd class="mt-1 font-black text-slate-700 dark:text-slate-200">Her ayın ${escapePlanHtml(String(plan.payment_day || '1'))}. günü</dd></div>
            ${plan.remaining_total_amount ? `<div class="rounded-2xl border border-amber-100 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-amber-700 dark:text-amber-400">Kalan Toplam Tutar</dt><dd class="mt-1 font-black text-amber-900 dark:text-amber-200">${planAmount(plan.remaining_total_amount)} ${escapePlanHtml(curr)}</dd></div>` : ''}
            ${plan.payment_countdown ? `<div class="rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-3"><dt class="text-[10px] font-black uppercase tracking-wider text-slate-400">Ödeme Durumu</dt><dd class="mt-1 font-black"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${escapePlanHtml(plan.payment_countdown.badge_class)}">${escapePlanHtml(plan.payment_countdown.label)}</span></dd></div>` : ''}
        </dl>
        <section><div class="mb-3 flex items-center justify-between gap-3"><h3 class="text-sm font-black uppercase tracking-tight text-slate-800 dark:text-white">${escapePlanHtml(copy.detailOccurrences || 'Taksit / Dönem Dağılımı')}</h3><span class="text-[10px] font-black uppercase tracking-wider text-slate-400">${Number(summary.total || 0)}</span></div><div class="grid grid-cols-2 gap-3">${occurrenceCards}</div></section>
        <section><h3 class="mb-3 text-sm font-black uppercase tracking-tight text-slate-800 dark:text-white">${escapePlanHtml(copy.detailNext || 'Sıradaki Ödeme')}</h3>${nextMarkup}</section>
        <div class="space-y-2 border-t border-slate-100 dark:border-slate-800 pt-5">
            <div class="grid grid-cols-2 gap-3">
                <button data-macro="button_secondary" type="button" data-plan-detail-action="edit" class="plan-btn plan-btn-secondary">${escapePlanHtml(copy.detailEdit || 'Düzenle')}</button>
                <button data-macro="button_primary" type="button" data-plan-detail-action="pay" class="plan-btn plan-btn-success">${escapePlanHtml(copy.detailPay || 'Ödeme Yap')}</button>
            </div>
            <div class="grid grid-cols-2 gap-3">
                ${plan.status === 'Aktif' ? `
                    <button data-macro="button_secondary" type="button" data-plan-detail-action="pause-plan" class="plan-btn plan-btn-secondary text-amber-700 hover:bg-amber-50">Planı Duraklat</button>
                    <button data-macro="button_danger" type="button" data-plan-detail-action="cancel-plan" class="plan-btn plan-btn-danger">Planı İptal Et</button>
                ` : `
                    <button data-macro="button_secondary" type="button" data-plan-detail-action="activate-plan" class="plan-btn plan-btn-success col-span-2">Planı Yeniden Aktif Yap</button>
                `}
            </div>
        </div>
    </div>`;
}

async function openPlanDetail(planId, sourceButton = null) {
    const copy = getPlanCopy();
    const drawer = document.getElementById('planDetailDrawer');
    const panel = drawer?.querySelector('.plan-detail-panel');
    const content = document.getElementById('planDetailContent');
    if (!drawer || !panel || !content) return;
    planDetailState.planId = planId;
    planDetailState.plan = null;
    planDetailState.returnFocus = sourceButton || document.activeElement;
    drawer.classList.remove('hidden');
    drawer.classList.add('plan-detail-open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.classList.add('overflow-hidden');
    content.innerHTML = `<p class="rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-3 text-xs font-bold text-indigo-700">${escapePlanHtml(copy.detailLoading || 'Yükleniyor...')}</p>`;
    panel.focus();
    try {
        const payload = await ECuzdanApi.get(ECuzdanEndpoints.plans.detail(planId));
        const data = ECuzdanApi.dto.planDetail(payload);
        planDetailState.plan = data.plan;
        renderPlanDetail(data);
    } catch (error) {
        content.innerHTML = `<div class="rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-700">${escapePlanHtml(error?.status === 404 ? (copy.detailNotFound || 'Bulunamadı') : (copy.detailError || 'Hata oluştu'))}<button data-macro="button_secondary" type="button" data-plan-detail-action="retry" class="mt-3 block font-black underline">${escapePlanHtml(copy.detailTitle || 'Yeniden Dene')}</button></div>`;
    }
}

function closePlanDetail() {
    const drawer = document.getElementById('planDetailDrawer');
    if (!drawer) return;
    drawer.classList.remove('plan-detail-open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('overflow-hidden');
    window.setTimeout(() => drawer.classList.add('hidden'), 220);
    const returnFocus = planDetailState.returnFocus;
    planDetailState.planId = null;
    planDetailState.plan = null;
    if (returnFocus && typeof returnFocus.focus === 'function') returnFocus.focus();
}

async function updatePlanStatus(planId, newStatus) {
    const confirmMessages = {
        'İptal': 'Bu planı ve gelecekteki bekleyen ödemelerini iptal etmek istediğinize emin misiniz?',
        'Duraklatıldı': 'Bu planı duraklatmak istediğinize emin misiniz?',
        'Aktif': 'Bu planı yeniden aktife almak istediğinize emin misiniz?'
    };
    const msg = confirmMessages[newStatus] || 'Plan durumunu değiştirmek istediğinize emin misiniz?';
    if (!confirm(msg)) return;

    try {
        const formData = new FormData();
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        formData.append('csrf_token', csrfToken);
        formData.append('status', newStatus);

        const response = await fetch(ECuzdanEndpoints.plans.setStatus(planId), {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': csrfToken
            },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showToast(data.message || 'Plan durumu güncellendi.', 'success');
            setTimeout(() => {
                closePlanDetail();
                window.location.reload();
            }, 700);
        } else {
            showToast(data.message || 'Durum güncellenemedi.', 'error');
        }
    } catch (e) {
        console.error('Error updating plan status:', e);
        showToast('İşlem sırasında bir hata oluştu.', 'error');
    }
}

async function cancelOccurrence(occurrenceId) {
    if (!confirm('Bu döneme ait planlı ödemeyi iptal etmek istediğinize emin misiniz?')) return;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const response = await fetch(ECuzdanEndpoints.plans.occurrenceCancel(occurrenceId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({ reason: 'Kullanıcı tarafından iptal edildi' })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Planlı ödeme iptal edildi.', 'success');
            setTimeout(() => {
                closePlanDetail();
                window.location.reload();
            }, 700);
        } else {
            showToast(data.message || 'Ödeme iptal edilemedi.', 'error');
        }
    } catch (e) {
        console.error('Error cancelling occurrence:', e);
        showToast('İşlem sırasında bir hata oluştu.', 'error');
    }
}

async function skipOccurrence(occurrenceId) {
    if (!confirm('Bu döneme ait planlı ödemeyi atlamak istediğinize emin misiniz?')) return;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const response = await fetch(ECuzdanEndpoints.plans.occurrenceSkip(occurrenceId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({ reason: 'Kullanıcı bu ayı atladı' })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Planlı ödeme atlandı.', 'success');
            setTimeout(() => {
                closePlanDetail();
                window.location.reload();
            }, 700);
        } else {
            showToast(data.message || 'Ödeme atlanamadı.', 'error');
        }
    } catch (e) {
        console.error('Error skipping occurrence:', e);
        showToast('İşlem sırasında bir hata oluştu.', 'error');
    }
}

let planSortState = { col: null, asc: true };

function sortPlanTable(th, col) {
    const table = th.closest('table');
    if (!table) return;
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr[data-plan-row]'));
    if (!rows.length) return;

    if (planSortState.col === col) {
        planSortState.asc = !planSortState.asc;
    } else {
        planSortState.col = col;
        planSortState.asc = true;
    }

    rows.sort((a, b) => {
        if (col === 'name') {
            const valA = a.dataset.name || '';
            const valB = b.dataset.name || '';
            return planSortState.asc ? valA.localeCompare(valB, 'tr') : valB.localeCompare(valA, 'tr');
        } else if (col === 'amount') {
            const numA = parseFloat(a.dataset.amount || '0');
            const numB = parseFloat(b.dataset.amount || '0');
            return planSortState.asc ? numA - numB : numB - numA;
        } else if (col === 'day') {
            const numA = parseInt(a.dataset.day || '1', 10);
            const numB = parseInt(b.dataset.day || '1', 10);
            return planSortState.asc ? numA - numB : numB - numA;
        } else if (col === 'remaining') {
            const numA = parseFloat(a.dataset.remaining || '0');
            const numB = parseFloat(b.dataset.remaining || '0');
            return planSortState.asc ? numA - numB : numB - numA;
        } else if (col === 'status') {
            const valA = a.dataset.status || '';
            const valB = b.dataset.status || '';
            return planSortState.asc ? valA.localeCompare(valB, 'tr') : valB.localeCompare(valA, 'tr');
        }
        return 0;
    });

    rows.forEach(r => tbody.appendChild(r));

    // Update sort indicators on this table's thead
    table.querySelectorAll('th .sort-indicator').forEach(ind => {
        ind.textContent = '⇅';
        ind.classList.remove('text-indigo-600', 'font-black');
        ind.classList.add('text-slate-300');
    });
    const currentInd = th.querySelector('.sort-indicator');
    if (currentInd) {
        currentInd.textContent = planSortState.asc ? '▲' : '▼';
        currentInd.classList.remove('text-slate-300');
        currentInd.classList.add('text-indigo-600', 'font-black');
    }
}
window.sortPlanTable = sortPlanTable;

function switchTab(tabId, btn) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(tabId);
    if (target) target.classList.add('active');
    if (btn) btn.classList.add('active');
}

let currentDurationMode = 'indefinite';
const TR_MONTHS = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];

function onDurationModeChange(mode) {
    currentDurationMode = mode === 'installment' ? 'installment' : 'indefinite';
    const cardIndefinite = document.getElementById('duration_card_indefinite');
    const cardInstallment = document.getElementById('duration_card_installment');
    const radioIndefinite = document.getElementById('duration_mode_indefinite');
    const radioInstallment = document.getElementById('duration_mode_installment');
    const infoBox = document.getElementById('indefinite_info_box');
    const fieldsGroup = document.getElementById('installment_fields_group');
    const planTypeInput = document.getElementById('plan_type');
    const installmentsInput = document.getElementById('plan_installments');
    const flowEl = document.getElementById('flow_type_selector');
    const flow = flowEl ? flowEl.value : 'Gider';

    if (currentDurationMode === 'indefinite') {
        if (radioIndefinite) radioIndefinite.checked = true;
        if (radioInstallment) radioInstallment.checked = false;

        cardIndefinite?.classList.add('border-indigo-500', 'bg-indigo-50/50');
        cardIndefinite?.classList.remove('border-slate-200', 'bg-slate-50/50');

        cardInstallment?.classList.remove('border-indigo-500', 'bg-indigo-50/50');
        cardInstallment?.classList.add('border-slate-200', 'bg-slate-50/50');

        infoBox?.classList.remove('hidden');
        fieldsGroup?.classList.add('hidden');

        if (installmentsInput) {
            installmentsInput.value = 0;
            installmentsInput.required = false;
        }

        if (planTypeInput) {
            planTypeInput.value = flow === 'Yatırım' ? 'DCA' : 'Abonelik';
        }
    } else {
        if (radioIndefinite) radioIndefinite.checked = false;
        if (radioInstallment) radioInstallment.checked = true;

        cardInstallment?.classList.add('border-indigo-500', 'bg-indigo-50/50');
        cardInstallment?.classList.remove('border-slate-200', 'bg-slate-50/50');

        cardIndefinite?.classList.remove('border-indigo-500', 'bg-indigo-50/50');
        cardIndefinite?.classList.add('border-slate-200', 'bg-slate-50/50');

        infoBox?.classList.add('hidden');
        fieldsGroup?.classList.remove('hidden');

        if (installmentsInput) {
            if (!installmentsInput.value || installmentsInput.value === '0') {
                installmentsInput.value = 12;
            }
            installmentsInput.required = true;
        }

        if (planTypeInput) {
            planTypeInput.value = 'Taksit';
        }
    }

    updateDurationLiveSummary();
}
window.onDurationModeChange = onDurationModeChange;

function updateDurationLiveSummary() {
    const summaryText = document.getElementById('duration_summary_text');
    const totalText = document.getElementById('duration_total_text');
    if (!summaryText || !totalText) return;

    if (currentDurationMode === 'indefinite') {
        return;
    }

    const instInput = document.getElementById('plan_installments');
    const amtInput = document.getElementById('plan_amount');
    const startInput = document.getElementById('plan_start_date');
    const freqInput = document.getElementById('plan_frequency');
    const curr = getPlanCurrencySymbol();

    const installments = parseInt(instInput?.value || '0', 10);
    const amount = parseFloat(amtInput?.value || '0');
    const freq = freqInput?.value || 'Aylık';

    if (!installments || installments <= 0) {
        summaryText.textContent = 'Lütfen geçerli bir taksit sayısı girin.';
        totalText.textContent = 'Toplam: —';
        return;
    }

    // Calculate total amount
    const total = amount > 0 ? (amount * installments) : 0;
    const formattedTotal = total > 0 ? planAmount(total) + ' ' + curr : '—';
    totalText.textContent = `Toplam: ${formattedTotal}`;

    // Calculate completion date based on start date + frequency * installments
    let startDate = new Date();
    if (startInput?.value) {
        const parts = startInput.value.split('-');
        if (parts.length === 3) {
            startDate = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        }
    }

    const endDate = new Date(startDate.getTime());
    if (freq === 'Haftalık') {
        endDate.setDate(endDate.getDate() + (installments - 1) * 7);
    } else if (freq === '3-Aylık') {
        endDate.setMonth(endDate.getMonth() + (installments - 1) * 3);
    } else if (freq === 'Yıllık') {
        endDate.setFullYear(endDate.getFullYear() + (installments - 1));
    } else {
        // Aylık (default)
        endDate.setMonth(endDate.getMonth() + (installments - 1));
    }

    const endMonthName = TR_MONTHS[endDate.getMonth()] || '';
    const endYear = endDate.getFullYear();
    const periodLabel = freq === 'Haftalık' ? `${installments} hafta` : (freq === 'Yıllık' ? `${installments} yıl` : `${installments} ay`);

    summaryText.textContent = `${installments} Taksit • Son Ödeme: ${endMonthName} ${endYear} (${periodLabel} süresince)`;
}
window.updateDurationLiveSummary = updateDurationLiveSummary;

function toggleAdvancedEndDate() {
    const container = document.getElementById('advanced_end_date_container');
    const icon = document.getElementById('advanced_end_date_icon');
    if (!container) return;
    const isHidden = container.classList.contains('hidden');
    container.classList.toggle('hidden', !isHidden);
    if (icon) icon.textContent = isHidden ? '▾' : '▸';
}
window.toggleAdvancedEndDate = toggleAdvancedEndDate;

function updateCategoriesAndAction(selectedCat = null) {
    try {
        const flowSelector = document.getElementById('flow_type_selector');
        const catSelect = document.getElementById('plan_category');
        const actionInput = document.getElementById('planAction');
        if (!flowSelector || !catSelect || !actionInput) return;

        const flow = flowSelector.value;
        if (flow === 'Gelir') actionInput.value = 'add_income_plan';
        else if (flow === 'Gider') actionInput.value = 'add_expense_plan';
        else actionInput.value = 'add_investment_plan';

        // Target asset visibility & requirement
        const targetAssetWrapper = document.getElementById('target_asset_wrapper') || document.getElementById('target_asset_group');
        const targetAssetInput = document.getElementById('target_asset_id');
        const isInvestmentPlan = flow === 'Yatırım';
        if (targetAssetWrapper) {
            targetAssetWrapper.classList.toggle('hidden', !isInvestmentPlan);
        }
        if (targetAssetInput) {
            targetAssetInput.required = isInvestmentPlan;
        }

        // Plan type synchronization
        const planTypeInput = document.getElementById('plan_type');
        if (planTypeInput) {
            if (currentDurationMode === 'indefinite') {
                planTypeInput.value = isInvestmentPlan ? 'DCA' : 'Abonelik';
            } else {
                planTypeInput.value = 'Taksit';
            }
        }

        catSelect.innerHTML = '';
        const cats = (window.categoryData && window.categoryData[flow]) || [];

        if (cats.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = getPlanCopy().categoryMissing || 'Kategori Yok';
            catSelect.appendChild(opt);
        } else {
            cats.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                catSelect.appendChild(opt);
            });
        }

        if (selectedCat && cats.includes(selectedCat)) {
            catSelect.value = selectedCat;
        }
    } catch (e) {
        console.error('Error updating categories:', e);
    }
}

function updateInstallmentState() {
    onDurationModeChange(currentDurationMode);
}

function openPlanModal() {
    const form = document.getElementById('unifiedPlanForm');
    if (form) {
        form.reset();
        form.action = '/plans';
    }
    const planIdInput = document.getElementById('plan_id');
    if (planIdInput) planIdInput.value = '';
    const versionInput = document.getElementById('plan_version');
    if (versionInput) versionInput.value = '1';
    const statusInput = document.getElementById('plan_status');
    if (statusInput) statusInput.value = 'Aktif';
    const titleEl = document.getElementById('planModalTitle');
    if (titleEl) titleEl.textContent = getPlanCopy().createTitle || 'Yeni Plan Oluştur';

    // Set today as default start date if empty
    const startDateInput = document.getElementById('plan_start_date');
    if (startDateInput && !startDateInput.value) {
        startDateInput.value = new Date().toISOString().slice(0, 10);
    }

    // Set default payment day to today's day of month
    const paymentDayInput = document.getElementById('plan_payment_day');
    if (paymentDayInput && !paymentDayInput.value) {
        paymentDayInput.value = new Date().getDate();
    }

    // Collapse advanced end date
    const endDateContainer = document.getElementById('advanced_end_date_container');
    if (endDateContainer) endDateContainer.classList.add('hidden');
    const endDateIcon = document.getElementById('advanced_end_date_icon');
    if (endDateIcon) endDateIcon.textContent = '▸';

    updateCategoriesAndAction();
    onDurationModeChange('indefinite');
    window.openModal('unifiedPlanModal');
    setTimeout(() => document.getElementById('plan_name')?.focus(), 100);
}

function editPlan(btn) {
    if (!btn) return;
    const copy = getPlanCopy();
    const planForm = document.getElementById('unifiedPlanForm');
    if (planForm) {
        planForm.action = `/plans/${btn.dataset.id}/edit`;
    }
    document.getElementById('planAction').value = 'update_plan';
    document.getElementById('plan_id').value = btn.dataset.id;
    const versionInput = document.getElementById('plan_version');
    if (versionInput) versionInput.value = btn.dataset.version || '1';
    document.getElementById('plan_name').value = btn.dataset.name;

    const flow = btn.dataset.flowType;
    const flowSelector = document.getElementById('flow_type_selector');
    if (flowSelector) flowSelector.value = flow;
    updateCategoriesAndAction(btn.dataset.category);

    document.getElementById('plan_amount').value = btn.dataset.amount;
    document.getElementById('plan_payment_day').value = btn.dataset.paymentDay;
    document.getElementById('plan_note').value = btn.dataset.note || '';
    document.getElementById('plan_start_date').value = btn.dataset.startDate;
    document.getElementById('plan_end_date').value = btn.dataset.endDate || '';
    document.getElementById('plan_frequency').value = btn.dataset.frequency || 'Aylık';
    document.getElementById('target_asset_id').value = btn.dataset.targetAssetId || '';
    document.getElementById('plan_status').value = btn.dataset.status || 'Aktif';

    // Duration mode determination
    const instCount = parseInt(btn.dataset.installments || '0', 10);
    const planTypeVal = btn.dataset.planType || 'Taksit';
    const isIndefinite = (instCount === 0 || instCount === 9999 || planTypeVal === 'Abonelik' || planTypeVal === 'DCA');

    if (isIndefinite) {
        onDurationModeChange('indefinite');
    } else {
        onDurationModeChange('installment');
        document.getElementById('plan_installments').value = instCount;
    }

    if (btn.dataset.endDate) {
        const endDateContainer = document.getElementById('advanced_end_date_container');
        if (endDateContainer) endDateContainer.classList.remove('hidden');
        const endDateIcon = document.getElementById('advanced_end_date_icon');
        if (endDateIcon) endDateIcon.textContent = '▾';
    } else {
        const endDateContainer = document.getElementById('advanced_end_date_container');
        if (endDateContainer) endDateContainer.classList.add('hidden');
        const endDateIcon = document.getElementById('advanced_end_date_icon');
        if (endDateIcon) endDateIcon.textContent = '▸';
    }

    updateDurationLiveSummary();

    const titleEl = document.getElementById('planModalTitle');
    if (titleEl) titleEl.textContent = copy.editTitle || 'Planı Düzenle';
    window.openModal('unifiedPlanModal');
    setTimeout(() => document.getElementById('plan_amount')?.focus(), 100);
}

function closePlanModal() {
    window.closeModal('unifiedPlanModal');
}

function checkPlanBeforeDelete(planId, flowType) {
    const copy = getPlanCopy();
    if (confirm(copy.deleteConfirm || 'Bu planı silmek istediğinize emin misiniz?')) {
        if (typeof window.deletePlan === 'function') {
            window.deletePlan(planId, 'all');
        }
    }
}

function createPaymentIdempotencyKey(planId, occurrenceId = 'legacy') {
    const uuid = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    return `plans-payment-${planId}-${occurrenceId}-${uuid}`.slice(0, 64);
}

async function loadNextOccurrence(planId, fallbackAmount, fallbackDate) {
    const copy = getPlanCopy();
    const info = document.getElementById('paymentOccurrenceInfo');
    const occurrenceInput = document.getElementById('paymentOccurrenceId');
    if (!info || !occurrenceInput) return;
    occurrenceInput.value = '';
    try {
        const response = await ECuzdanApi.get(ECuzdanEndpoints.plans.occurrences(planId));
        const items = Array.isArray(response?.data?.items) ? response.data.items : [];
        const occurrence = items.find(item => item.status === 'scheduled');
        const submitBtn = document.querySelector('#paymentForm button[type="submit"]');
        if (!occurrence) {
            const isCompleted = items.length > 0 && items.every(item => item.status === 'paid' || item.status === 'skipped' || item.status === 'cancelled');
            if (isCompleted) {
                info.textContent = '🎉 Bu planın tüm taksitleri ödenmiş ve tamamlanmıştır.';
                info.className = 'mb-4 rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-[10px] font-semibold text-emerald-700';
            } else {
                info.textContent = copy.occurrenceNotFound || 'Sıradaki ödeme bulunamadı.';
                info.className = 'mb-4 rounded-xl border border-amber-100 bg-amber-50 px-3 py-2 text-[10px] font-semibold text-amber-700';
            }
            if (submitBtn) submitBtn.disabled = isCompleted;
            return;
        }
        if (submitBtn) submitBtn.disabled = false;
        occurrenceInput.value = occurrence.id;
        document.getElementById('paymentAmount').value = occurrence.amount ?? fallbackAmount;
        document.getElementById('paymentDate').value = occurrence.scheduled_date || fallbackDate;
        document.getElementById('paymentInstallmentNumber').value = occurrence.occurrence_number;
        info.textContent = interpolatePlanCopy(copy.occurrenceInfo, { number: occurrence.occurrence_number, date: occurrence.scheduled_date, status: occurrence.status });
        info.className = 'mb-4 rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-[10px] font-semibold text-emerald-700';
    } catch (error) {
        console.warn(copy.occurrenceFallback, error);
        info.textContent = copy.occurrenceFallback || 'Taksit bilgisi yüklenemedi.';
        info.className = 'mb-4 rounded-xl border border-amber-100 bg-amber-50 px-3 py-2 text-[10px] font-semibold text-amber-700';
    }
}

function openPaymentModal(planId, planName, amount, installments) {
    const copy = getPlanCopy();
    const today = new Date().toISOString().slice(0, 10);
    const submitBtn = document.querySelector('#paymentForm button[type="submit"]');
    if (submitBtn) submitBtn.disabled = false;
    document.getElementById('paymentPlanId').value = planId;
    document.getElementById('paymentOccurrenceId').value = '';
    document.getElementById('paymentPlanName').textContent = planName;
    document.getElementById('paymentAmount').value = amount;
    document.getElementById('paymentDate').value = today;
    document.getElementById('paymentInstallments').textContent = (installments == 0 || installments == 9999) ? (copy.paymentIndefinite || 'Süresiz') : installments;
    document.getElementById('paymentInstallmentNumber').value = 1;
    document.getElementById('paymentFeedback').classList.add('hidden');
    const info = document.getElementById('paymentOccurrenceInfo');
    if (info) {
        info.textContent = copy.occurrenceLoading || 'Yükleniyor...';
        info.className = 'mb-4 rounded-xl border border-indigo-100 bg-indigo-50 px-3 py-2 text-[10px] font-semibold text-indigo-700';
    }
    window.openModal('paymentModal');
    loadNextOccurrence(planId, amount, today);
    setTimeout(() => document.getElementById('paymentAmount')?.focus(), 100);
}

function closePaymentModal() {
    const form = document.getElementById('paymentForm');
    if (form) form.reset();
    document.getElementById('paymentOccurrenceId').value = '';
    window.closeModal('paymentModal');
}

function setPaymentFeedback(message, type = 'error') {
    const feedback = document.getElementById('paymentFeedback');
    if (!feedback) return;
    if (!message) { feedback.classList.add('hidden'); return; }
    feedback.textContent = message;
    feedback.classList.remove('hidden', 'bg-emerald-50', 'text-emerald-700', 'bg-rose-50', 'text-rose-700');
    feedback.classList.add(type === 'success' ? 'bg-emerald-50' : 'bg-rose-50');
    feedback.classList.add(type === 'success' ? 'text-emerald-700' : 'text-rose-700');
}

// Global Event Bindings
document.addEventListener('DOMContentLoaded', function() {
    // Plan detail drawer click delegation
    document.getElementById('planDetailContent')?.addEventListener('click', event => {
        const action = event.target.closest('[data-plan-detail-action]')?.dataset.planDetailAction;
        if (!action) return;
        if (action === 'retry' && planDetailState.planId) {
            openPlanDetail(planDetailState.planId, planDetailState.returnFocus);
            return;
        }
        if (!planDetailState.plan) return;
        const occBtn = event.target.closest('[data-occurrence-action]');
        if (occBtn) {
            const occAction = occBtn.dataset.occurrenceAction;
            const occId = occBtn.dataset.occurrenceId;
            if (occAction === 'cancel') {
                cancelOccurrence(occId);
            } else if (occAction === 'skip') {
                skipOccurrence(occId);
            }
            return;
        }

        const editButton = findPlanEditButton(planDetailState.returnFocus);
        if (action === 'edit' && editButton) {
            closePlanDetail();
            editPlan(editButton);
        } else if (action === 'pay') {
            const plan = planDetailState.plan;
            closePlanDetail();
            openPaymentModal(plan.id, plan.name, plan.amount, plan.occurrence_limit || 0);
        } else if (action === 'cancel-plan' && planDetailState.plan) {
            updatePlanStatus(planDetailState.plan.id, 'İptal');
        } else if (action === 'pause-plan' && planDetailState.plan) {
            updatePlanStatus(planDetailState.plan.id, 'Duraklatıldı');
        } else if (action === 'activate-plan' && planDetailState.plan) {
            updatePlanStatus(planDetailState.plan.id, 'Aktif');
        }
    });

    // Drawer accessibility keydown
    document.getElementById('planDetailDrawer')?.addEventListener('keydown', event => {
        const drawer = document.getElementById('planDetailDrawer');
        if (event.key === 'Escape') {
            closePlanDetail();
            return;
        }
        if (event.key !== 'Tab' || drawer?.classList.contains('hidden')) return;
        const focusable = [...drawer.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])')];
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });

    // Unified plan form submit
    document.getElementById('unifiedPlanForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const copy = getPlanCopy();
        const formData = new FormData(this);
        const flowVal = document.getElementById('flow_type_selector')?.value || 'Gider';

        if (currentDurationMode === 'indefinite') {
            formData.set('installments', '0');
            formData.set('plan_type', flowVal === 'Yatırım' ? 'DCA' : 'Abonelik');
            const advContainer = document.getElementById('advanced_end_date_container');
            if (advContainer?.classList.contains('hidden')) {
                formData.set('end_date', '');
            }
        } else {
            formData.set('plan_type', 'Taksit');
            const instVal = document.getElementById('plan_installments')?.value || '12';
            formData.set('installments', instVal);
        }

        const versionVal = document.getElementById('plan_version')?.value;
        const headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        };
        if (versionVal) {
            headers['If-Match'] = versionVal;
        }

        fetch(ECuzdanEndpoints.plans.list, {
            method: 'POST',
            headers: headers,
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message || copy.saveSuccess || 'Kaydedildi', 'success');
                setTimeout(() => {
                    closePlanModal();
                    window.location.reload();
                }, 1000);
            } else {
                showToast(data.message || copy.genericError || 'Hata oluştu', 'error');
            }
        })
        .catch(() => showToast(copy.genericError || 'Hata oluştu', 'error'));
    });

    // Payment form submit
    document.getElementById('paymentForm')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        setPaymentFeedback('');
        const formData = new FormData(this);
        const planId = document.getElementById('paymentPlanId').value;
        const occurrenceId = document.getElementById('paymentOccurrenceId').value;
        const idempotencyKey = createPaymentIdempotencyKey(planId, occurrenceId || 'legacy');
        try {
            let data;
            if (occurrenceId) {
                data = await ECuzdanApi.post(ECuzdanEndpoints.plans.occurrencePay(occurrenceId), {
                    headers: {
                        'Content-Type': 'application/json',
                        'Idempotency-Key': idempotencyKey,
                    },
                    body: JSON.stringify({
                        amount: formData.get('amount'),
                        payment_date: formData.get('payment_date'),
                        notes: formData.get('notes') || null,
                    }),
                });
            } else {
                data = await ECuzdanApi.post(ECuzdanEndpoints.plans.addPayment, {
                    headers: {'Idempotency-Key': idempotencyKey},
                    body: formData,
                });
            }
            if (data.success) {
                showToast(data.message || 'İşlem kaydedildi.', 'success');
                setTimeout(() => window.location.reload(), 700);
            } else {
                setPaymentFeedback(data.message || 'Ödeme kaydedilemedi.');
            }
        } catch (error) {
            console.error('Payment submit error:', error);
            setPaymentFeedback(error.message || 'Ödeme sırasında beklenmeyen bir hata oluştu.');
        }
    });

    // Auto-open modal if URL has ?modal=new
    try {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('modal') === 'new') {
            openPlanModal();
        }
    } catch (e) {
        console.warn('[Plans] URL parameter parse error:', e);
    }

    // Live search listener on visible plan table & cards
    document.getElementById('plan-search')?.addEventListener('input', function(e) {
        const term = (e.target.value || '').trim().toLowerCase();
        const activeTab = document.querySelector('.tab-content.active');
        if (!activeTab) return;
        const rows = activeTab.querySelectorAll('tbody tr[data-plan-row]');
        rows.forEach(r => {
            const name = (r.dataset.name || '').toLowerCase();
            const text = r.textContent.toLowerCase();
            r.style.display = (!term || name.includes(term) || text.includes(term)) ? '' : 'none';
        });
        const cards = activeTab.querySelectorAll('[data-plan-card]');
        cards.forEach(c => {
            const text = c.textContent.toLowerCase();
            c.style.display = (!term || text.includes(term)) ? '' : 'none';
        });
    });

    // Global ESC keydown handler for all plan modals & drawer
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const detailDrawer = document.getElementById('planDetailDrawer');
            if (detailDrawer && !detailDrawer.classList.contains('hidden') && detailDrawer.classList.contains('plan-detail-open')) {
                closePlanDetail();
                return;
            }
            const paymentModal = document.getElementById('paymentModal');
            if (paymentModal && !paymentModal.classList.contains('hidden')) {
                closePaymentModal();
                return;
            }
            const unifiedModal = document.getElementById('unifiedPlanModal');
            if (unifiedModal && !unifiedModal.classList.contains('hidden')) {
                closePlanModal();
                return;
            }
        }
    });
});

/**
 * Export visible plans table to Excel-compatible UTF-8 BOM CSV
 */
function exportPlansToCsv() {
    const activeTab = document.querySelector('.tab-content.active');
    const table = activeTab ? activeTab.querySelector('table') : document.querySelector('.plan-desktop-table table');
    if (!table) {
        showToast('Dışa aktarılacak plan tablosu bulunamadı.', 'error');
        return;
    }

    const rows = table.querySelectorAll('tbody tr[data-plan-row]');
    if (!rows.length) {
        showToast('Dışa aktarılacak plan bulunmuyor.', 'info');
        return;
    }

    const headers = ['Plan Adı', 'Kategori & Akış', 'Tutar', 'Planlama & Sıklık', 'Kalan Süre', 'Durum'];
    const csvRows = [headers];

    rows.forEach(tr => {
        const cells = tr.querySelectorAll('td');
        if (cells.length < 6) return;

        // Col 0: Plan Adı
        const nameEl = cells[0].querySelector('.font-bold');
        const name = (nameEl ? nameEl.innerText : cells[0].innerText).trim();

        // Col 1: Sınıflandırma (Gelir/Gider & Kategori)
        const flowCat = cells[1].innerText.trim().replace(/\s+/g, ' ');

        // Col 2: Tutar
        const amount = cells[2].innerText.trim().replace(/\s+/g, ' ');

        // Col 3: Planlama
        const schedule = cells[3].innerText.trim().replace(/\s+/g, ' ');

        // Col 4: Kalan
        const remaining = cells[4].innerText.trim().replace(/\s+/g, ' ');

        // Col 5: Durum
        const status = cells[5].innerText.trim().replace(/\s+/g, ' ');

        csvRows.push([name, flowCat, amount, schedule, remaining, status]);
    });

    const csvContent = '\uFEFF' + csvRows.map(row =>
        row.map(val => `"${(val || '').replace(/"/g, '""')}"`).join(';')
    ).join('\r\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const dateStr = new Date().toISOString().slice(0, 10);
    link.setAttribute('href', url);
    link.setAttribute('download', `e-cuzdan_planlar_${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast('Planlar başarıyla CSV formatında indirildi.', 'success');
}
window.exportPlansToCsv = exportPlansToCsv;

