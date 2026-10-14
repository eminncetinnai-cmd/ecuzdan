/* ==========================================================================
   E-Cüzdan — Settings Hub JavaScript (static/js/settings.js)
   Clean, User-Friendly Settings Interactions, Tabs, Security & Export/Import
   ========================================================================== */

function getSettingsCopy() {
    return window.settingsCopy || {};
}

/* ---------- Risksiz faiz: manuel alan görünürlüğü ---------- */
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('input[name="risk_free_rate_mode"]').forEach(function (radio) {
        radio.addEventListener('change', function () {
            const manual = document.getElementById('rf_mode_manual');
            document.getElementById('rf_manual_container')?.classList.toggle('hidden', !manual?.checked);
        });
    });

    // Backup encryption toggle
    document.getElementById('encrypt_backup')?.addEventListener('change', function() {
        document.getElementById('backup_password_container')?.classList.toggle('hidden', !this.checked);
        const input = document.getElementById('backup_password');
        if (input) input.required = this.checked;
    });

    document.getElementById('import_encrypted')?.addEventListener('change', function() {
        document.getElementById('import_password_container')?.classList.toggle('hidden', !this.checked);
        const input = document.getElementById('import_backup_password');
        if (input) input.required = this.checked;
    });

    // Reset Data Form protection & loading state
    const resetForm = document.getElementById('resetDataForm');
    if (resetForm) {
        resetForm.addEventListener('submit', function(e) {
            const confirmed = confirm('DİKKAT: Çalışma alanındaki tüm finansal veriler (işlemler, varlıklar, planlar ve banka hesapları) kalıcı olarak silinecektir.\n\nBu işlem geri alınamaz. Devam etmek istiyor musunuz?');
            if (!confirmed) {
                e.preventDefault();
                return false;
            }
            const submitBtn = resetForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
                submitBtn.innerHTML = '<svg class="w-3 h-3 mr-1.5 inline animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Sıfırlanıyor...';
            }
        });
    }

    initSettingsTabs();
});

/* ---------- Sekme yönetimi ---------- */
function initSettingsTabs() {
    const tabs = Array.from(document.querySelectorAll('.settings-tab'));
    const panels = Array.from(document.querySelectorAll('.settings-panel'));
    if (!tabs.length) return;

    function activate(name, persist) {
        const target = tabs.find(t => t.dataset.tab === name) || tabs[0];
        const activeName = target.dataset.tab;
        tabs.forEach(t => t.setAttribute('aria-selected', String(t.dataset.tab === activeName)));
        panels.forEach(p => p.classList.toggle('hidden', p.dataset.panel !== activeName));
        if (persist) {
            try { localStorage.setItem('settingsActiveTab', activeName); } catch (e) { /* storage kapalı */ }
            history.replaceState(null, '', '#' + activeName);
        }
    }

    tabs.forEach((t, index) => {
        t.addEventListener('click', () => activate(t.dataset.tab, true));
        t.addEventListener('keydown', (e) => {
            let targetIdx = null;
            if (e.key === 'ArrowRight') {
                targetIdx = (index + 1) % tabs.length;
            } else if (e.key === 'ArrowLeft') {
                targetIdx = (index - 1 + tabs.length) % tabs.length;
            } else if (e.key === 'Home') {
                targetIdx = 0;
            } else if (e.key === 'End') {
                targetIdx = tabs.length - 1;
            }
            if (targetIdx !== null) {
                e.preventDefault();
                tabs[targetIdx].focus();
                activate(tabs[targetIdx].dataset.tab, true);
            }
        });
    });

    let initial = (location.hash || '').replace('#', '');
    if (!initial) {
        try { initial = localStorage.getItem('settingsActiveTab') || ''; } catch (e) { initial = ''; }
    }
    activate(initial, false);
}

async function changeLang(lang) {
    const copy = getSettingsCopy();
    const buttons = Array.from(document.querySelectorAll('[onclick^="changeLang("]'));
    buttons.forEach(button => { button.disabled = true; button.setAttribute('aria-busy', 'true'); });
    try {
        const endpoint = (window.ECuzdanEndpoints?.settings?.language) ? window.ECuzdanEndpoints.settings.language(lang) : `/set_language/${encodeURIComponent(lang)}`;
        const payload = window.ECuzdanApi?.post
            ? await window.ECuzdanApi.post(endpoint)
            : await (async () => {
                const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
                const response = await fetch(endpoint, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        Accept: 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        ...(token ? { 'X-CSRF-Token': token } : {}),
                    },
                });
                const result = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(result.message || result.error || `HTTP ${response.status}`);
                return result;
            })();
        if (payload?.success === true || payload?.status === 'success') {
            window.location.reload();
            return;
        }
        throw new Error(payload?.message || copy.languageSaveError || 'Dil kaydedilemedi.');
    } catch (error) {
        buttons.forEach(button => { button.disabled = false; button.removeAttribute('aria-busy'); });
        if (window.showToast) window.showToast(error.message || copy.languageSaveError || 'Dil kaydedilemedi.', 'error');
        else window.alert(error.message || copy.languageSaveError || 'Dil kaydedilemedi.');
    }
}

function checkPasswordStrength(password) {
    const copy = getSettingsCopy();
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
    if (password.match(/\d/)) strength++;
    if (password.match(/[^a-zA-Z\d]/)) strength++;
    const bars = [1,2,3,4].map(i => document.getElementById('strength-' + i));
    const text = document.getElementById('strength-text');
    const colors = ['#ef4444', '#f59e0b', '#84cc16', '#10b981'];
    const labels = [
        copy.passwordWeak || 'Zayıf',
        copy.passwordMedium || 'Orta',
        copy.passwordStrong || 'Güçlü',
        copy.passwordVeryStrong || 'Çok Güçlü'
    ];
    bars.forEach((bar, index) => {
        if (!bar) return;
        bar.style.backgroundColor = index < strength ? colors[strength - 1] : '#e2e8f0';
    });
    if (text) {
        text.textContent = (copy.passwordStrength || 'Şifre Gücü') + ': ' + (labels[strength - 1] || copy.passwordVeryWeak || 'Çok Zayıf');
        text.style.color = colors[strength - 1] || '#94a3b8';
    }
}

function handleImportSubmit(form, title, msg) {
    const copy = getSettingsCopy();
    const fileInput = form.querySelector('input[name="db_file"]');
    const encryptCheckbox = form.querySelector('#import_encrypted');
    const passwordInput = form.querySelector('input[name="backup_password"]');
    const button = document.getElementById('import_backup_btn');
    const buttonText = document.getElementById('import_button_text');
    
    // File validation
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        if (window.showToast) {
            window.showToast(copy.backupFileRequired || 'Lütfen bir yedek dosyası seçin.', 'error');
        } else {
            alert(copy.backupFileRequired || 'Lütfen bir yedek dosyası seçin.');
        }
        return false;
    }
    
    // Password validation for encrypted backups
    if (encryptCheckbox && encryptCheckbox.checked && (!passwordInput.value || passwordInput.value.length < 8)) {
        if (window.showToast) {
            window.showToast(copy.backupPasswordWeak || 'Şifre en az 8 karakter olmalıdır.', 'error');
        } else {
            alert(copy.backupPasswordWeak || 'Şifre en az 8 karakter olmalıdır.');
        }
        return false;
    }
    
    const replaceRestore = form.querySelector('[name="restore_mode"][value="replace"]')?.checked;
    const confirmationMessage = replaceRestore
        ? (copy.restoreReplaceConfirm || 'Bu işlem mevcut tüm verilerin üzerine yazacaktır. Emin misiniz?')
        : msg;
    
    if (confirm(confirmationMessage)) {
        if (button) button.disabled = true;
        if (buttonText) {
            buttonText.innerHTML = '<svg class="w-3 h-3 mr-2 inline animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>' + (copy.backupImporting || 'İçe Aktarılıyor...');
        }
        form.submit();
        return false;
    }
    return false;
}

function confirmSettingSubmit(form, title, msg, isDanger = false, actionVal = null) {
    if (!form) return false;
    const copy = getSettingsCopy();

    // 1. Action parametresini güncelle
    if (actionVal) {
        const el = form.querySelector('input[name="action"]') || document.getElementById('adminAutoDataAction');
        if (el) el.value = actionVal;
    }

    // 2. HTML5 form geçerliliği (örn. boş şifre alanını submit öncesi yakala)
    if (typeof form.checkValidity === 'function' && !form.checkValidity()) {
        if (typeof form.reportValidity === 'function') {
            form.reportValidity();
        }
        return false;
    }

    // 3. Kullanıcı onay diyaloğu
    const replaceRestore = form.querySelector('[name="restore_mode"][value="replace"]')?.checked;
    const confirmationMessage = replaceRestore
        ? (copy.restoreReplaceConfirm || 'Mevcut veriler silinecektir. Devam edilsin mi?')
        : msg;

    if (!confirm(confirmationMessage)) {
        return false;
    }

    // 4. Çift tıklama engelleme & loading durumu
    const submitButtons = form.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('opacity-75', 'cursor-not-allowed');
    });

    const clickedBtn = document.activeElement && document.activeElement.tagName === 'BUTTON'
        ? document.activeElement
        : (submitButtons.length ? submitButtons[0] : null);

    if (clickedBtn) {
        const loadingText = actionVal === 'admin_clear_data'
            ? 'Temizleniyor...'
            : (actionVal === 'admin_advanced_fill' ? 'Oluşturuluyor...' : 'İşleniyor...');
        clickedBtn.innerHTML = `<svg class="w-3 h-3 mr-1.5 inline animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>${loadingText}`;
    }

    // 5. Formu güvenle gönder
    form.submit();
    return false;
}

/* Şifre eşleşme doğrulaması — client-side guard */
function validatePasswordForm(form) {
    const copy = getSettingsCopy();
    const currentPw = form.querySelector('[name="current_pw"]');
    const newPw = form.querySelector('[name="new_pw"]');
    const confirm = form.querySelector('#confirm_password');

    if (currentPw && !currentPw.value) {
        const msg = copy.currentPasswordRequired || 'Lütfen mevcut şifrenizi girin.';
        if (window.showToast) window.showToast(msg, 'error');
        else alert(msg);
        currentPw.focus();
        return false;
    }

    if (!newPw || !confirm) return true;
    if (newPw.value.length < 8) {
        if (window.showToast) window.showToast(copy.passwordMinimum || 'Şifre en az 8 karakter olmalıdır.', 'error');
        else alert(copy.passwordMinimum || 'Şifre en az 8 karakter olmalıdır.');
        newPw.focus();
        return false;
    }
    if (newPw.value !== confirm.value) {
        if (window.showToast) window.showToast(copy.passwordMismatch || 'Şifreler birbiriyle uyuşmuyor.', 'error');
        else alert(copy.passwordMismatch || 'Şifreler birbiriyle uyuşmuyor.');
        confirm.focus();
        return false;
    }
    return true;
}

/* File size validation for backup import (50MB limit) */
function checkImportFileSize(input) {
    const warn = document.getElementById('import_file_size_warn');
    const info = document.getElementById('import_file_size_info');
    const btn = document.getElementById('import_backup_btn');
    if (!input || !input.files || input.files.length === 0) {
        if (warn) warn.classList.add('hidden');
        if (info) info.textContent = '';
        if (btn) btn.disabled = false;
        return;
    }
    const file = input.files[0];
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > 50) {
        if (warn) warn.classList.remove('hidden');
        if (info) info.textContent = `Seçilen: ${file.name} (${sizeMb.toFixed(1)} MB)`;
        if (btn) btn.disabled = true;
    } else {
        if (warn) warn.classList.add('hidden');
        const sizeStr = sizeMb < 1 ? (file.size / 1024).toFixed(1) + ' KB' : sizeMb.toFixed(2) + ' MB';
        if (info) info.textContent = `Seçilen: ${file.name} (${sizeStr})`;
        if (btn) btn.disabled = false;
    }
}

/* Tenant Export */
function exportTenant() {
    const copy = getSettingsCopy();
    const button = document.getElementById('export_tenant_btn') || document.querySelector('button[onclick*="exportTenant"]');
    if (!button) return;
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<svg class="w-3 h-3 mr-2 inline animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>' + (copy.backupLoading || 'Hazırlanıyor...');

    fetch('/export_tenant_json', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(resp => {
        if (!resp.ok) throw new Error('Sunucu hatası: ' + resp.status);
        const cd = resp.headers.get('Content-Disposition') || '';
        const match = cd.match(/filename=([^;]+)/);
        const filename = match ? match[1].replace(/["']/g, '') : 'e_cuzdan_tenant_backup.json';
        return resp.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; a.click();
        setTimeout(() => URL.revokeObjectURL(url), 3000);
        button.disabled = false;
        button.innerHTML = originalHTML;
    })
    .catch(err => {
        console.error('Tenant export error:', err);
        button.disabled = false;
        button.innerHTML = originalHTML;
        if (window.showToast) window.showToast(copy.backupError || 'Dışa aktarma sırasında bir hata oluştu.', 'error');
        else alert(copy.backupError || 'Dışa aktarma sırasında bir hata oluştu.');
    });
}

/* Tam platform export — sistem yöneticisi */
function exportBackup() {
    const copy = getSettingsCopy();
    const button = document.querySelector('button[onclick="exportBackup()"]');
    if (!button) return;

    const encrypt = document.getElementById('encrypt_backup')?.checked;
    const password = document.getElementById('backup_password')?.value;

    if (encrypt && !password) {
        if (window.showToast) window.showToast(copy.backupPasswordRequired || 'Lütfen şifre girin.', 'error');
        else alert(copy.backupPasswordRequired || 'Lütfen şifre girin.');
        return;
    }

    if (encrypt && password.length < 8) {
        if (window.showToast) window.showToast(copy.backupPasswordWeak || 'Şifre en az 8 karakter olmalıdır.', 'error');
        else alert(copy.backupPasswordWeak || 'Şifre en az 8 karakter olmalıdır.');
        return;
    }

    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<svg class="w-3 h-3 mr-2 inline animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>' + (copy.backupLoading || 'Hazırlanıyor...');

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

    fetch('/export_db_json', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: new URLSearchParams({
            encrypt: encrypt ? '1' : '0',
            password: encrypt ? password : '',
            csrf_token: csrfToken
        })
    })
    .then(resp => {
        if (!resp.ok) throw new Error('Sunucu hatası: ' + resp.status);
        const cd = resp.headers.get('Content-Disposition') || '';
        const match = cd.match(/filename=([^;]+)/);
        const filename = match ? match[1].replace(/["']/g, '') : 'e_cuzdan_backup.json';
        return resp.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; a.click();
        setTimeout(() => URL.revokeObjectURL(url), 3000);
        button.disabled = false;
        button.innerHTML = originalHTML;
    })
    .catch(err => {
        console.error('Export error:', err);
        button.disabled = false;
        button.innerHTML = originalHTML;
        if (window.showToast) window.showToast(copy.backupError || 'Dışa aktarma sırasında bir hata oluştu.', 'error');
        else alert(copy.backupError || 'Dışa aktarma sırasında bir hata oluştu.');
    });
}

// One-click full database & storage tune-up
async function runDatabaseTuneUp() {
    const btn = document.getElementById('btn-db-tuneup');
    const statusText = document.getElementById('db-tuneup-status');
    const originalHTML = btn ? btn.innerHTML : '';

    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.innerHTML = '<svg class="w-3.5 h-3.5 mr-2 inline animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Bakım Yapılıyor...';
    }
    if (statusText) statusText.textContent = 'Veritabanı optimize ediliyor ve boş sayfalar temizleniyor...';

    try {
        const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
        const endpoint = (window.ECuzdanEndpoints?.settings?.tuneUp) || '/storage-health/api/tune-up';
        const response = await fetch(endpoint, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...(token ? { 'X-CSRF-Token': token } : {}),
            },
            body: JSON.stringify({ purge_cache: true, create_snapshot: true }),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            throw new Error(result.error || result.message || `HTTP ${response.status}`);
        }
        const freedKb = result.data?.total_bytes_freed ? (result.data.total_bytes_freed / 1024).toFixed(1) : '0';
        const msg = `Veritabanı optimizasyonu tamamlandı. ${freedKb} KB alan geri kazanıldı.`;
        if (window.showToast) window.showToast(msg, 'success');
        else alert(msg);
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = originalHTML;
        }
        if (statusText) statusText.textContent = '';
        const errMsg = 'Optimizasyon sırasında hata oluştu: ' + (err.message || err);
        if (window.showToast) window.showToast(errMsg, 'error');
        else alert(errMsg);
    }
}

/* Şifre Göster / Gizle */
function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    if (btn) {
        btn.setAttribute('aria-label', isPassword ? 'Şifreyi Gizle' : 'Şifreyi Göster');
        btn.innerHTML = isPassword
            ? '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"/></svg>'
            : '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>';
    }
}

/* Profil Resmi Anlık Önizleme */
function previewProfileImage(input) {
    if (!input || !input.files || !input.files[0]) return;
    const file = input.files[0];
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('profile-avatar-preview');
        const initial = document.getElementById('profile-avatar-initial');
        if (preview) {
            preview.src = e.target.result;
            preview.classList.remove('hidden');
        }
        if (initial) {
            initial.classList.add('hidden');
        }
    };
    reader.readAsDataURL(file);
}

/* Sayfa Yenilemesiz Tema Değişimi */
async function changeThemePreference(theme) {
    try {
        const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
        const response = await fetch('/save_theme_preference', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...(token ? { 'X-CSRF-Token': token } : {}),
            },
            body: JSON.stringify({ theme: theme }),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            throw new Error(result.message || 'Tema kaydedilemedi.');
        }
        document.documentElement.setAttribute('data-user-theme', theme);
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else if (theme === 'light') {
            document.documentElement.classList.remove('dark');
        } else {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.classList.toggle('dark', prefersDark);
        }
        try { localStorage.setItem('user_theme', theme); } catch (e) {}
        if (window.showToast) {
            const labels = { light: 'Açık tema uygulandı', dark: 'Koyu tema uygulandı', system: 'Sistem teması uygulandı' };
            window.showToast(labels[theme] || 'Tema güncellendi.', 'success');
        }
    } catch (err) {
        console.error('Theme save error:', err);
        const form = document.getElementById('themeForm');
        if (form) form.submit();
    }
}

/* Sayfa Yenilemesiz Gizlilik Modu Geçişi */
async function togglePrivacyPreference(enabled) {
    try {
        const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
        const response = await fetch('/toggle_privacy_mode', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...(token ? { 'X-CSRF-Token': token } : {}),
            },
            body: new URLSearchParams({
                privacy_mode: enabled ? 'on' : 'off',
                csrf_token: token,
            }),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            throw new Error(result.message || 'Gizlilik modu güncellenemedi.');
        }
        const newState = String(Boolean(result.privacy_mode));
        document.documentElement.setAttribute('data-privacy-mode', newState);
        document.body?.setAttribute('data-privacy-mode', newState);
        document.querySelectorAll('[data-privacy-control]').forEach(el => {
            if (el.type === 'checkbox') el.checked = result.privacy_mode;
            el.setAttribute('aria-checked', newState);
        });
        if (window.showToast) {
            window.showToast(result.privacy_mode ? 'Gizlilik modu açıldı.' : 'Gizlilik modu kapatıldı.', 'info');
        }
    } catch (err) {
        console.error('Privacy toggle error:', err);
        const form = document.getElementById('privacyForm');
        if (form) form.submit();
    }
}

// Global exposure
window.changeLang = changeLang;
window.checkPasswordStrength = checkPasswordStrength;
window.handleImportSubmit = handleImportSubmit;
window.confirmSettingSubmit = confirmSettingSubmit;
window.validatePasswordForm = validatePasswordForm;
window.checkImportFileSize = checkImportFileSize;
window.exportTenant = exportTenant;
window.exportTenantBackup = exportTenant;
window.exportBackup = exportBackup;
window.runDatabaseTuneUp = runDatabaseTuneUp;
window.togglePasswordVisibility = togglePasswordVisibility;
window.previewProfileImage = previewProfileImage;
window.changeThemePreference = changeThemePreference;
window.togglePrivacyPreference = togglePrivacyPreference;

