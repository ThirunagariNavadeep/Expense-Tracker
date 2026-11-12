const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

async function fetchJson(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const csrfToken = getCookie('csrf_token');
    if (csrfToken && !headers.has('X-CSRF-Token')) {
        headers.set('X-CSRF-Token', csrfToken);
    }
    if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }
    const response = await fetch(url, { ...options, headers });
    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
        throw new Error(typeof payload === 'string' ? payload : (payload.detail || 'Request failed'));
    }
    return payload;
}

async function getCsrfToken() {
    try {
        const payload = await fetchJson('/api/auth/csrf');
        if (payload.csrf_token) {
            document.cookie = `csrf_token=${payload.csrf_token}; path=/; samesite=lax`;
        }
    } catch (error) {
        console.warn('CSRF token unavailable', error);
    }
}

function showMessage(text, type = 'success') {
    let alert = document.querySelector('.alert');
    if (!alert) {
        alert = document.createElement('div');
        alert.className = 'alert';
        const target = document.querySelector('form') || document.querySelector('.content');
        if (target) {
            target.prepend(alert);
        }
    }
    alert.className = `alert ${type}`;
    alert.textContent = text;
}

async function checkAuthAndRedirect() {
    try {
        await fetchJson('/api/auth/me');
    } catch (error) {
        window.location.href = '/login';
    }
}

function formatCurrency(value) {
    const amount = Number(value || 0);
    return currencyFormatter.format(amount);
}

async function initLoginPage() {
    const form = document.getElementById('login-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());
        try {
            await fetchJson('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
            await getCsrfToken();
            window.location.href = '/dashboard';
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });
}

async function initRegisterPage() {
    const form = document.getElementById('register-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());
        try {
            await fetchJson('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
            await getCsrfToken();
            window.location.href = '/dashboard';
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });
}

async function loadCategories(selectId, includeEmpty = false) {
    const select = document.getElementById(selectId);
    if (!select) return [];
    const categories = await fetchJson('/api/categories');
    select.innerHTML = includeEmpty ? '<option value="">Overall budget</option>' : '';
    const filtered = categories.filter((category) => category.type === 'expense');
    filtered.forEach((category) => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        select.appendChild(option);
    });
    return filtered;
}

async function initDashboardPage() {
    await checkAuthAndRedirect();
    await getCsrfToken();

    const monthInput = document.getElementById('summary-month');
    const yearInput = document.getElementById('summary-year');
    const now = new Date();
    monthInput.value = now.getMonth() + 1;
    yearInput.value = now.getFullYear();

    const loadSummary = async () => {
        const month = Number(monthInput.value || now.getMonth() + 1);
        const year = Number(yearInput.value || now.getFullYear());
        const summary = await fetchJson(`/api/dashboard/summary?month=${month}&year=${year}`);

        document.getElementById('income-total').textContent = formatCurrency(summary.income_total);
        document.getElementById('expense-total').textContent = formatCurrency(summary.expense_total);
        document.getElementById('remaining-balance').textContent = formatCurrency(summary.remaining_balance);
        document.getElementById('monthly-budget').textContent = formatCurrency(summary.monthly_budget);
        document.getElementById('remaining-budget').textContent = formatCurrency(summary.remaining_budget);
        document.getElementById('budget-utilization').textContent = `${Number(summary.budget_utilization || 0).toFixed(1)}%`;
        document.getElementById('recent-count').textContent = summary.recent_transactions.length;

        const warningBox = document.getElementById('budget-warning');
        const warningState = summary.budget_warning || 'healthy';
        if (warningState === 'warning') {
            warningBox.style.display = 'block';
            warningBox.className = 'alert warning';
            warningBox.textContent = 'Warning: spending has reached 80% of your monthly budget.';
        } else if (warningState === 'exceeded') {
            warningBox.style.display = 'block';
            warningBox.className = 'alert error';
            warningBox.textContent = 'Budget exceeded: you have spent beyond your monthly limit.';
        } else {
            warningBox.style.display = 'none';
        }

        const breakdown = await fetchJson(`/api/dashboard/category-breakdown?month=${month}&year=${year}`);
        const container = document.getElementById('category-breakdown');
        container.innerHTML = '';
        if (!breakdown.length) {
            container.innerHTML = '<p>No data yet.</p>';
        } else {
            const max = Math.max(...breakdown.map((item) => Number(item.total || 0)));
            breakdown.forEach((item) => {
                const row = document.createElement('div');
                row.className = 'list-item';
                const width = max ? Math.min((Number(item.total) / max) * 100, 100) : 0;
                row.innerHTML = `
                    <div style="flex:1">
                        <div class="flex-between"><strong>${item.category_name}</strong><span>${formatCurrency(item.total)}</span></div>
                        <div class="bar"><span class="bar-fill" style="width:${width}%"></span></div>
                    </div>
                `;
                container.appendChild(row);
            });
        }

        const trends = await fetchJson('/api/dashboard/monthly-trends');
        const trendContainer = document.getElementById('monthly-trend');
        trendContainer.innerHTML = '';
        trends.forEach((item) => {
            const row = document.createElement('div');
            row.className = 'list-item';
            row.innerHTML = `
                <div style="flex:1">
                    <div class="flex-between"><strong>${item.month}</strong><span>${formatCurrency(item.expenses)}</span></div>
                    <small>Income: ${formatCurrency(item.income)}</small>
                </div>
            `;
            trendContainer.appendChild(row);
        });

        const tableBody = document.getElementById('recent-transactions-table');
        tableBody.innerHTML = summary.recent_transactions.map((item) => `
            <tr>
                <td>${new Date(item.transaction_date).toLocaleDateString()}</td>
                <td>${item.type}</td>
                <td>${item.category_id || 'N/A'}</td>
                <td>${item.description || '—'}</td>
                <td>${formatCurrency(item.amount)}</td>
            </tr>
        `).join('') || '<tr><td colspan="5">No transactions found.</td></tr>';
    };

    document.getElementById('refresh-summary').addEventListener('click', loadSummary);
    document.getElementById('logout-button').addEventListener('click', async () => {
        await fetchJson('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    });
    loadSummary();
}

async function initTransactionsPage() {
    await checkAuthAndRedirect();
    await getCsrfToken();

    const categorySelect = document.getElementById('transaction-category-select');
    const transactionTypeSelect = document.querySelector('select[name="transaction_type"]');

    async function refreshCategories() {
        const categories = await fetchJson('/api/categories');
        const expenseCategories = categories.filter((category) => category.type === transactionTypeSelect.value || category.is_default || category.user_id !== null);
        categorySelect.innerHTML = '';
        expenseCategories.forEach((category) => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            categorySelect.appendChild(option);
        });
    }

    transactionTypeSelect.addEventListener('change', refreshCategories);
    await refreshCategories();

    const form = document.getElementById('transaction-form');
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.amount = Number(payload.amount);
        payload.category_id = Number(payload.category_id);
        try {
            await fetchJson('/api/transactions', { method: 'POST', body: JSON.stringify(payload) });
            form.reset();
            await loadTransactionTable();
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });

    const loadTransactionTable = async () => {
        const type = document.getElementById('filter-type').value;
        const search = document.getElementById('transaction-search').value.trim();
        const url = `/api/transactions?transaction_type=${encodeURIComponent(type || '')}&search=${encodeURIComponent(search)}`;
        const data = await fetchJson(url);
        const tbody = document.getElementById('transaction-table-body');
        tbody.innerHTML = data.items.map((item) => `
            <tr>
                <td>${new Date(item.transaction_date).toLocaleDateString()}</td>
                <td><span class="status-pill ${item.transaction_type === 'income' ? 'status-good' : 'status-warning'}">${item.transaction_type}</span></td>
                <td>${item.category_id}</td>
                <td>${item.description || '—'}</td>
                <td>${formatCurrency(item.amount)}</td>
                <td><div class="table-actions"><button class="mini-button danger-button" data-delete-id="${item.id}">Delete</button></div></td>
            </tr>
        `).join('') || '<tr><td colspan="6">No transactions found.</td></tr>';

        tbody.querySelectorAll('[data-delete-id]').forEach((button) => {
            button.addEventListener('click', async () => {
                await fetchJson(`/api/transactions/${button.dataset.deleteId}`, { method: 'DELETE' });
                await loadTransactionTable();
            });
        });
    };

    document.getElementById('refresh-transactions').addEventListener('click', loadTransactionTable);
    document.getElementById('filter-type').addEventListener('change', loadTransactionTable);
    document.getElementById('transaction-search').addEventListener('input', loadTransactionTable);
    document.getElementById('logout-button').addEventListener('click', async () => {
        await fetchJson('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    });

    await loadTransactionTable();
}

async function initBudgetsPage() {
    await checkAuthAndRedirect();
    await getCsrfToken();

    const categorySelect = document.getElementById('budget-category-select');
    const categories = await fetchJson('/api/categories');
    categories.filter((category) => category.type === 'expense').forEach((category) => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        categorySelect.appendChild(option);
    });

    const form = document.getElementById('budget-form');
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.amount = Number(payload.amount);
        payload.category_id = payload.category_id ? Number(payload.category_id) : null;
        try {
            await fetchJson('/api/budgets', { method: 'POST', body: JSON.stringify(payload) });
            form.reset();
            await loadBudgets();
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });

    const loadBudgets = async () => {
        const budgets = await fetchJson('/api/budgets');
        const tbody = document.getElementById('budget-table-body');
        tbody.innerHTML = budgets.map((budget) => `
            <tr>
                <td>${budget.month}/${budget.year}</td>
                <td>${budget.category_id ? `Category #${budget.category_id}` : 'Overall'}</td>
                <td>${formatCurrency(budget.amount)}</td>
                <td><span class="status-pill ${Number(budget.amount) > 0 ? 'status-good' : 'status-warning'}">${Number(budget.amount) > 0 ? 'Active' : 'Ready'}</span></td>
                <td><div class="table-actions"><button class="mini-button danger-button" data-delete-budget="${budget.id}">Delete</button></div></td>
            </tr>
        `).join('') || '<tr><td colspan="5">No budgets found.</td></tr>';

        tbody.querySelectorAll('[data-delete-budget]').forEach((button) => {
            button.addEventListener('click', async () => {
                await fetchJson(`/api/budgets/${button.dataset.deleteBudget}`, { method: 'DELETE' });
                await loadBudgets();
            });
        });
    };

    document.getElementById('logout-button').addEventListener('click', async () => {
        await fetchJson('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    });

    await loadBudgets();
}

async function initReportsPage() {
    await checkAuthAndRedirect();
    await getCsrfToken();

    const now = new Date();
    const summary = await fetchJson(`/api/reports/monthly?month=${now.getMonth() + 1}&year=${now.getFullYear()}`);
    document.getElementById('report-income').textContent = formatCurrency(summary.income_total);
    document.getElementById('report-expense').textContent = formatCurrency(summary.expense_total);
    document.getElementById('report-balance').textContent = formatCurrency(summary.remaining_balance);

    const breakdown = await fetchJson(`/api/reports/category-wise?month=${now.getMonth() + 1}&year=${now.getFullYear()}`);
    const container = document.getElementById('report-category-breakdown');
    const max = Math.max(...breakdown.map((item) => Number(item.total || 0)), 1);
    container.innerHTML = breakdown.map((item) => `
        <div class="list-item">
            <div style="flex:1;">
                <div class="flex-between"><strong>${item.category_name}</strong><span>${formatCurrency(item.total)}</span></div>
                <div class="bar"><span class="bar-fill" style="width:${((Number(item.total) / max) * 100).toFixed(2)}%"></span></div>
            </div>
        </div>
    `).join('') || '<p>No expense categories yet.</p>';

    document.getElementById('logout-button').addEventListener('click', async () => {
        await fetchJson('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    });
}

async function initProfilePage() {
    await checkAuthAndRedirect();
    await getCsrfToken();
    const profile = await fetchJson('/api/auth/me');
    const profileInfo = document.getElementById('profile-info');
    profileInfo.innerHTML = `
        <div><strong>Username:</strong> ${profile.username}</div>
        <div><strong>Email:</strong> ${profile.email}</div>
        <div><strong>Member since:</strong> ${new Date(profile.created_at).toLocaleDateString()}</div>
    `;

    document.getElementById('logout-button').addEventListener('click', async () => {
        await fetchJson('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    const page = document.body.dataset.page;
    if (page === 'login') return initLoginPage();
    if (page === 'register') return initRegisterPage();
    if (page === 'dashboard') return initDashboardPage();
    if (page === 'transactions') return initTransactionsPage();
    if (page === 'budgets') return initBudgetsPage();
    if (page === 'reports') return initReportsPage();
    if (page === 'profile') return initProfilePage();
});
