(function installReconciliationWorkspace(global) {
    'use strict';

    const endpoints = global.ECuzdanEndpoints.reconciliation;
    const i18n = global.ReconciliationI18n;
    const state = {
        accountId: new URLSearchParams(global.location.search).get('account_id') || 'all',
        currency: new URLSearchParams(global.location.search).get('currency') || '',
        accounts: [],
        lastPayload: null,
    };

    const byId = id => document.getElementById(id);
    const escapeHtml = value => String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');

    function formatMoney(value, currency) {
        if (value === null || value === undefined || value === '') return '—';
        const number = Number(value);
        if (!Number.isFinite(number)) return '—';
        const locale = document.documentElement.lang || 'tr-TR';
        const formatted = number.toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 4 });
        return `${formatted}${currency ? ` ${escapeHtml(currency)}` : ''}`;
    }

    function setMetric(name, value, currency, money = true) {
        const node = document.querySelector(`[data-reconciliation="${name}"]`);
        if (node) node.textContent = money ? formatMoney(value, currency) : String(value ?? '—');
    }

    function accountLabel(account) {
        return account.institution ? `${account.name} · ${account.institution}` : account.name;
    }

    function accountTypeLabel(type) {
        return ({
            checking: i18n.typeChecking,
            savings: i18n.typeSavings,
            credit_card: i18n.typeCreditCard,
            cash: i18n.typeCash,
        }[type] || type || '—');
    }

    function syncUrl() {
        const params = new URLSearchParams();
        if (state.accountId !== 'all') params.set('account_id', state.accountId);
        if (state.accountId === 'all' && state.currency) params.set('currency', state.currency);
        const query = params.toString();
        global.history.replaceState(null, '', `${global.location.pathname}${query ? `?${query}` : ''}`);
    }

    function renderAccountControls(accounts) {
        state.accounts = Array.isArray(accounts) ? accounts : [];
        const select = byId('reconciliationAccountSelect');
        const cards = byId('reconciliationAccountCards');
        const empty = byId('reconciliationEmptyState');
        if (!select || !cards || !empty) return;

        if (!state.accounts.length) {
            select.innerHTML = `<option value="all">${escapeHtml(i18n.selectAccount)}</option>`;
            select.disabled = true;
            cards.innerHTML = '';
            empty.classList.remove('hidden');
            return;
        }
        empty.classList.add('hidden');
        select.disabled = false;
        if (state.accountId !== 'all' && !state.accounts.some(account => String(account.id) === String(state.accountId))) {
            state.accountId = 'all';
        }
        const currencySet = [...new Set(state.accounts.map(account => account.currency))].sort();
        if (state.accountId === 'all' && currencySet.length > 1 && !currencySet.includes(state.currency)) {
            state.currency = '';
        }
        const allOption = `<option value="all" ${state.accountId === 'all' ? 'selected' : ''}>${escapeHtml(i18n.allScope)}</option>`;
        const accountOptions = state.accounts.map(account => `<option value="${escapeHtml(account.id)}" ${String(account.id) === String(state.accountId) ? 'selected' : ''}>${escapeHtml(accountLabel(account))} · ${escapeHtml(account.currency)}</option>`).join('');
        select.innerHTML = allOption + accountOptions;

        const currencyWrap = byId('reconciliationCurrencyWrap');
        const currencySelect = byId('reconciliationCurrency');
        if (currencyWrap && currencySelect) {
            currencyWrap.classList.toggle('hidden', !(state.accountId === 'all' && currencySet.length > 1));
            currencySelect.innerHTML = `<option value="">${escapeHtml(i18n.selectCurrency)}</option>` + currencySet.map(currency => `<option value="${escapeHtml(currency)}" ${currency === state.currency ? 'selected' : ''}>${escapeHtml(currency)}</option>`).join('');
        }

        const allCard = `<button type="button" data-account-card="all" class="reconciliation-account-card ${state.accountId === 'all' ? 'is-selected' : ''} rounded-2xl border bg-white p-4 text-left shadow-sm"><span class="text-[10px] font-black uppercase tracking-wider text-indigo-500">${escapeHtml(i18n.allScope)}</span><strong class="mt-3 block text-sm font-black text-slate-900">${escapeHtml(i18n.accountsTitle || i18n.allScope)}</strong><span class="mt-1 block text-xs text-slate-500">${state.accounts.length} · ${escapeHtml(currencySet.join(' / '))}</span></button>`;
        const accountCards = state.accounts.map(account => `<button type="button" data-account-card="${escapeHtml(account.id)}" class="reconciliation-account-card ${String(account.id) === String(state.accountId) ? 'is-selected' : ''} rounded-2xl border bg-white p-4 text-left shadow-sm"><span class="text-[10px] font-black uppercase tracking-wider text-slate-400">${escapeHtml(account.currency)} · ${escapeHtml(accountTypeLabel(account.account_type))}</span><strong class="mt-3 block truncate text-sm font-black text-slate-900">${escapeHtml(account.name)}</strong><span class="mt-1 block truncate text-xs text-slate-500">${escapeHtml(account.institution || '—')}</span></button>`).join('');
        cards.innerHTML = allCard + accountCards;
        syncUrl();
    }

    function statusText(status) {
        return ({
            statement_required: i18n.statusRequired,
            reconciled: i18n.statusReconciled,
            explained_by_pending: i18n.statusExplained,
            unexplained_variance: i18n.statusUnreconciled,
            currency_selection_required: i18n.statusCurrency,
            no_accounts: i18n.statusNoAccounts,
            account_not_found: i18n.statusError,
        }[status] || status || i18n.statusError);
    }

    function renderIssues(data) {
        const node = byId('reconciliationIssueList');
        if (!node) return;
        const issues = Array.isArray(data.issues) ? data.issues : [];
        if (!issues.length) {
            node.innerHTML = `<div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-bold text-emerald-800">${escapeHtml(i18n.statusReconciled)}</div>`;
            return;
        }
        node.innerHTML = issues.map(issue => {
            const title = ({
                STATEMENT_BALANCE_REQUIRED: i18n.issueStatement,
                PENDING_TIMING_DIFFERENCE: i18n.issuePending,
                UNEXPLAINED_VARIANCE: i18n.issueUnexplained,
                CURRENCY_SELECTION_REQUIRED: i18n.issueCurrency,
                NO_BANK_ACCOUNTS: i18n.issueNoAccounts,
                UNASSIGNED_TRANSACTIONS: i18n.issueUnassigned,
            }[issue.code] || issue.code || i18n.issueTitle);
            const tone = issue.severity === 'warning' ? 'border-amber-200 bg-amber-50 text-amber-900' : 'border-sky-200 bg-sky-50 text-sky-900';
            const detail = issue.amount ? ` · ${formatMoney(issue.amount, data.currency)}` : issue.count ? ` · ${escapeHtml(issue.count)}` : '';
            return `<div class="rounded-2xl border ${tone} p-3 text-xs leading-5"><strong>${escapeHtml(title)}</strong><span>${detail}</span></div>`;
        }).join('');
    }

    function focusPending() {
        byId('reconciliationPendingSection')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function openAccountModal() {
        const modal = byId('bankAccountModal');
        if (modal) { modal.classList.remove('hidden'); modal.classList.add('flex'); byId('bankAccountForm')?.querySelector('input[name="name"]')?.focus(); }
    }

    function closeAccountModal() {
        const modal = byId('bankAccountModal');
        if (modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); }
        const error = byId('bankAccountFormError');
        if (error) { error.textContent = ''; error.classList.add('hidden'); }
    }

    function renderRecommendations(data) {
        const node = byId('reconciliationRecommendations');
        if (!node) return;
        const actions = Array.isArray(data.recommendations) ? data.recommendations : [];
        node.innerHTML = actions.map(action => {
            if (action === 'ENTER_STATEMENT_BALANCE') return `<button type="button" data-focus-statement class="rounded-xl bg-slate-900 px-3 py-2.5 text-left text-xs font-black text-white hover:bg-slate-700">${escapeHtml(i18n.enterStatement)}</button>`;
            if (action === 'REVIEW_PENDING_TRANSACTIONS') return `<button type="button" data-focus-pending class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left text-xs font-black text-slate-700 hover:border-indigo-300">${escapeHtml(i18n.reviewPending)}</button>`;
            if (action === 'INSPECT_TRANSACTION_EXCEPTIONS') return `<a href="/transactions/explorer" class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left text-xs font-black text-slate-700 hover:border-indigo-300">${escapeHtml(i18n.reviewExceptions)}</a>`;
            if (action === 'ASSIGN_TRANSACTIONS_TO_ACCOUNT') return `<a href="/transactions" class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left text-xs font-black text-slate-700 hover:border-indigo-300">${escapeHtml(i18n.assignTransactions)}</a>`;
            if (action === 'ADD_BANK_ACCOUNT') return `<button type="button" data-open-account-modal class="rounded-xl bg-indigo-600 px-3 py-2.5 text-left text-xs font-black text-white hover:bg-indigo-700">${escapeHtml(i18n.addAccountAction)}</button>`;
            if (action === 'SELECT_CURRENCY') return `<button type="button" data-focus-currency class="rounded-xl bg-amber-500 px-3 py-2.5 text-left text-xs font-black text-slate-950 hover:bg-amber-400">${escapeHtml(i18n.selectCurrency)}</button>`;
            if (action === 'SELECT_ACCOUNT') return `<button type="button" data-focus-account class="rounded-xl bg-indigo-600 px-3 py-2.5 text-left text-xs font-black text-white hover:bg-indigo-700">${escapeHtml(i18n.selectAccount)}</button>`;
            return '';
        }).filter(Boolean).join('');
    }

    function renderPending(data) {
        const body = byId('reconciliationPendingBody');
        const meta = byId('reconciliationPendingMeta');
        if (!body || !meta) return;
        const items = Array.isArray(data.pending_items) ? data.pending_items : [];
        body.innerHTML = items.length ? items.map(item => `<tr class="border-t border-slate-100 hover:bg-slate-50"><td class="px-3 py-2.5 text-xs font-semibold text-slate-500">${escapeHtml(item.date)}</td><td class="px-3 py-2.5 text-xs font-bold text-slate-700">${escapeHtml(item.description || item.category || '—')}</td><td class="px-3 py-2.5 text-xs text-slate-500">${escapeHtml(item.category || '—')}</td><td class="px-3 py-2.5 text-xs text-slate-500">${escapeHtml(item.type || '—')}</td><td class="px-3 py-2.5 text-right text-xs font-black ${Number(item.signed_amount) >= 0 ? 'text-emerald-600' : 'text-rose-600'}">${formatMoney(item.signed_amount, data.currency)}</td><td class="px-3 py-2.5 text-right"><a class="text-[10px] font-black uppercase text-indigo-600 hover:underline" href="/transactions?edit=${encodeURIComponent(item.id)}">${escapeHtml(i18n.transaction)}</a></td></tr>`).join('') : `<tr><td colspan="6" class="px-3 py-8 text-center text-sm text-slate-400">${escapeHtml(i18n.pendingEmpty)}</td></tr>`;
        meta.textContent = data.pending_has_more ? `${items.length}+` : `${items.length} / ${data.pending_count || 0}`;
    }

    function renderCoverage(data) {
        const node = byId('reconciliationCoverage');
        if (!node) return;
        const coverage = data.statement_coverage || {};
        if (!data.accounts?.length) { node.textContent = i18n.noAccounts; return; }
        const label = coverage.complete ? i18n.coverageComplete : i18n.coverageMissing;
        node.innerHTML = `<strong class="text-slate-800">${escapeHtml(label)}</strong><br>${escapeHtml(i18n.accountsWithStatement)}: ${escapeHtml(coverage.accounts_with_statement ?? 0)} · ${escapeHtml(i18n.accountsMissingStatement)}: ${escapeHtml(coverage.accounts_missing_statement?.length ?? 0)}`;
    }

    function renderSummary(data) {
        state.lastPayload = data;
        renderAccountControls(data.accounts || []);
        const currency = data.currency || (data.account && data.account.currency) || '';
        ['book_balance', 'statement_balance', 'cleared_balance', 'pending_net', 'difference'].forEach(metric => setMetric(metric, data[metric], currency));
        setMetric('pending_count', data.pending_count, currency, false);
        const status = byId('reconciliationStatus');
        if (status) {
            status.textContent = `${i18n.issueTitle}: ${statusText(data.status_code)}`;
            status.className = `font-black ${data.reconciled ? 'text-emerald-600' : data.explainable ? 'text-sky-600' : data.status_code === 'unexplained_variance' ? 'text-amber-600' : 'text-slate-500'}`;
        }
        const scope = byId('reconciliationScopeMeta');
        if (scope) {
            const label = data.account ? accountLabel(data.account) : data.scope === 'all_accounts' ? i18n.allScope : i18n.selectAccount;
            scope.textContent = `${label}${currency ? ` · ${currency}` : ''} · ${data.as_of}`;
        }
        const statementInput = byId('reconciliationStatementBalance');
        if (statementInput && data.statement_source === 'saved_snapshot' && document.activeElement !== statementInput) statementInput.value = data.statement_balance || '';
        const currencyHint = byId('reconciliationCurrencyHint');
        if (currencyHint) {
            currencyHint.textContent = data.status_code === 'currency_selection_required' ? i18n.currencyHint : data.unassigned_count ? `${i18n.unassignedNote} (${data.unassigned_count})` : '';
            currencyHint.classList.toggle('hidden', !currencyHint.textContent);
        }
        renderIssues(data);
        renderRecommendations(data);
        renderPending(data);
        renderCoverage(data);
    }

    async function loadSummary() {
        const status = byId('reconciliationStatus');
        const button = byId('runReconciliation');
        const params = new URLSearchParams();
        const asOf = byId('reconciliationAsOf')?.value;
        const statement = byId('reconciliationStatementBalance')?.value.trim();
        if (asOf) params.set('as_of', asOf);
        if (statement) params.set('statement_balance', statement.replace(',', '.'));
        if (state.accountId !== 'all') params.set('account_id', state.accountId);
        if (state.accountId === 'all' && state.currency) params.set('currency', state.currency);
        if (button) button.disabled = true;
        if (status) { status.textContent = i18n.statusLoading; status.className = 'font-black text-slate-500'; }
        try {
            const payload = await global.ECuzdanApi.get(`${endpoints.summary}?${params.toString()}`);
            renderSummary(global.ECuzdanApi.dto.reconciliation(payload));
            await loadHistory();
        } catch (error) {
            if (status) { status.textContent = error.message || i18n.statusError; status.className = 'font-black text-rose-600'; }
        } finally {
            if (button) button.disabled = false;
        }
    }

    async function loadHistory() {
        const body = byId('reconciliationHistoryBody');
        const meta = byId('reconciliationHistoryMeta');
        if (!body || !meta) return;
        if (state.accountId === 'all') {
            body.innerHTML = `<tr><td colspan="4" class="px-5 py-8 text-center text-sm text-slate-400">${escapeHtml(i18n.selectAccount)}</td></tr>`;
            meta.textContent = '';
            return;
        }
        try {
            const payload = await global.ECuzdanApi.get(`${endpoints.statements}?account_id=${encodeURIComponent(state.accountId)}`);
            const statements = Array.isArray(payload.statements) ? payload.statements : [];
            body.innerHTML = statements.length ? statements.map(item => `<tr class="border-t border-slate-100"><td class="px-3 py-2.5 text-xs font-semibold text-slate-600">${escapeHtml(item.as_of)}</td><td class="px-3 py-2.5 text-xs font-black text-slate-800">${formatMoney(item.balance, item.currency)}</td><td class="px-3 py-2.5 text-xs text-slate-500">${escapeHtml(item.source === 'manual' ? i18n.manualSource : i18n.savedSource)}</td><td class="px-3 py-2.5 text-right"><button type="button" data-history-date="${escapeHtml(item.as_of)}" class="text-[10px] font-black uppercase text-indigo-600 hover:underline">${escapeHtml(i18n.historyOpen)}</button></td></tr>`).join('') : `<tr><td colspan="4" class="px-3 py-6 text-center text-sm text-slate-400">${escapeHtml(i18n.historyEmpty)}</td></tr>`;
            meta.textContent = statements.length ? String(statements.length) : '';
        } catch (error) {
            body.innerHTML = `<tr><td colspan="4" class="px-5 py-8 text-center text-sm text-rose-500">${escapeHtml(error.message || i18n.statusError)}</td></tr>`;
            meta.textContent = '';
        }
    }

    async function saveStatement() {
        const status = byId('reconciliationStatus');
        const accountId = state.accountId;
        const asOf = byId('reconciliationAsOf')?.value;
        const balance = byId('reconciliationStatementBalance')?.value.trim();
        if (accountId === 'all' || !asOf || !balance) {
            if (status) { status.textContent = i18n.enterStatement; status.className = 'font-black text-amber-600'; }
            if (accountId === 'all') byId('reconciliationAccountSelect')?.focus(); else byId('reconciliationStatementBalance')?.focus();
            return;
        }
        try {
            const payload = await global.ECuzdanApi.post(endpoints.statements, { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ account_id: Number(accountId), as_of: asOf, balance: balance.replace(',', '.'), note: byId('reconciliationStatementNote')?.value || '' }) });
            if (status) { status.textContent = i18n.saved; status.className = 'font-black text-emerald-600'; }
            renderSummary(global.ECuzdanApi.dto.reconciliation(payload.reconciliation));
            await loadHistory();
        } catch (error) {
            if (status) { status.textContent = error.message || i18n.saveError; status.className = 'font-black text-rose-600'; }
        }
    }

    function openAccountModal() {
        const modal = byId('bankAccountModal');
        if (!modal) return;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        const firstInput = modal.querySelector('input[name="name"]');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 50);
        }
    }

    function closeAccountModal() {
        const modal = byId('bankAccountModal');
        if (!modal) return;
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        const form = byId('bankAccountForm');
        if (form) form.reset();
        const errorNode = byId('bankAccountFormError');
        if (errorNode) {
            errorNode.textContent = '';
            errorNode.classList.add('hidden');
        }
    }

    async function createAccount(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const errorNode = byId('bankAccountFormError');
        try {
            const values = Object.fromEntries(new FormData(form).entries());
            const payload = await global.ECuzdanApi.post(endpoints.accounts, { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) });
            state.accountId = String(payload.account.id);
            state.currency = '';
            closeAccountModal();
            form.reset();
            await loadSummary();
        } catch (error) {
            if (errorNode) { errorNode.textContent = error.message || i18n.accountCreateError; errorNode.classList.remove('hidden'); }
        }
    }

    function bindEvents() {
        byId('reconciliationAccountSelect')?.addEventListener('change', event => { state.accountId = event.target.value; state.currency = ''; byId('reconciliationStatementBalance').value = ''; syncUrl(); loadSummary(); });
        byId('reconciliationCurrency')?.addEventListener('change', event => { state.currency = event.target.value; syncUrl(); loadSummary(); });
        byId('reconciliationAsOf')?.addEventListener('change', loadSummary);
        byId('runReconciliation')?.addEventListener('click', loadSummary);
        byId('saveReconciliationStatement')?.addEventListener('click', saveStatement);
        byId('reconciliationStatementBalance')?.addEventListener('keydown', event => { if (event.key === 'Enter') loadSummary(); });
        document.querySelectorAll('[data-open-account-modal]').forEach(node => node.addEventListener('click', openAccountModal));
        document.querySelectorAll('[data-close-account-modal]').forEach(node => node.addEventListener('click', closeAccountModal));
        byId('addBankAccount')?.addEventListener('click', openAccountModal);
        byId('bankAccountModal')?.addEventListener('click', event => {
            if (event.target === byId('bankAccountModal')) closeAccountModal();
        });
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                const modal = byId('bankAccountModal');
                if (modal && !modal.classList.contains('hidden')) closeAccountModal();
            }
        });
        byId('bankAccountForm')?.addEventListener('submit', createAccount);
        document.addEventListener('click', event => {
            const card = event.target.closest('[data-account-card]');
            if (card) { state.accountId = card.dataset.accountCard; state.currency = ''; byId('reconciliationStatementBalance').value = ''; syncUrl(); renderAccountControls(state.accounts); loadSummary(); return; }
            if (event.target.closest('[data-focus-pending]')) focusPending();
            if (event.target.closest('[data-focus-statement]')) byId('reconciliationStatementBalance')?.focus();
            if (event.target.closest('[data-focus-currency]')) byId('reconciliationCurrency')?.focus();
            if (event.target.closest('[data-focus-account]')) byId('reconciliationAccountSelect')?.focus();
            const historyButton = event.target.closest('[data-history-date]');
            if (historyButton) { byId('reconciliationAsOf').value = historyButton.dataset.historyDate; byId('reconciliationStatementBalance').value = ''; loadSummary(); }
        });
    }

    async function bootstrap() {
        const asOf = byId('reconciliationAsOf');
        if (asOf && !asOf.value) asOf.value = new Date().toISOString().slice(0, 10);
        bindEvents();
        await loadSummary();
    }

    document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
}(window));
