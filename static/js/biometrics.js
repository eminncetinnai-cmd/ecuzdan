/**
 * E-Cüzdan Biometric Vault Security (Face ID / Touch ID / WebAuthn)
 * Manages device-level cryptographic biometric authentication using W3C WebAuthn.
 */

(function () {
    'use strict';

    const STORAGE_ENABLED = 'ecuzdan_biometric_enabled';
    const STORAGE_CRED_ID = 'ecuzdan_biometric_cred_id';
    const SESSION_UNLOCKED = 'ecuzdan_biometric_unlocked';
    const STORAGE_LAST_ACTIVE = 'ecuzdan_biometric_last_active';
    const INACTIVITY_TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes away locks the app

    window.ECuzdanBiometrics = {
        /**
         * Check if biometric platform authenticator (Face ID / Touch ID) is available
         */
        isAvailable: async function () {
            if (window.PublicKeyCredential && typeof window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function') {
                try {
                    return await window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
                } catch (e) {
                    return false;
                }
            }
            return false;
        },

        isEnabled: function () {
            return localStorage.getItem(STORAGE_ENABLED) === 'true';
        },

        /**
         * Enable Face ID on this device by creating a hardware-backed WebAuthn credential
         */
        enable: async function () {
            const available = await this.isAvailable();
            if (!available) {
                if (window.showToast) {
                    window.showToast('Cihazınızda Face ID / Touch ID donanımı algılanamadı veya desteklenmiyor.', 'error');
                }
                return false;
            }

            try {
                const challenge = new Uint8Array(32);
                window.crypto.getRandomValues(challenge);
                const userId = new Uint8Array(16);
                window.crypto.getRandomValues(userId);

                const credential = await navigator.credentials.create({
                    publicKey: {
                        challenge: challenge,
                        rp: { name: 'E-Cüzdan Finansal Kasa' },
                        user: {
                            id: userId,
                            name: 'ecuzdan_user',
                            displayName: 'E-Cüzdan Kullanıcısı'
                        },
                        pubKeyCredParams: [
                            { alg: -7, type: 'public-key' },  // ES256
                            { alg: -257, type: 'public-key' } // RS256
                        ],
                        authenticatorSelection: {
                            authenticatorAttachment: 'platform',
                            userVerification: 'required'
                        },
                        timeout: 60000
                    }
                });

                if (credential) {
                    localStorage.setItem(STORAGE_ENABLED, 'true');
                    localStorage.setItem(STORAGE_CRED_ID, credential.id);
                    sessionStorage.setItem(SESSION_UNLOCKED, 'true');
                    localStorage.setItem(STORAGE_LAST_ACTIVE, Date.now().toString());

                    if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
                    if (window.showToast) {
                        window.showToast('Face ID / Biyometrik Kilit başarıyla aktifleştirildi!', 'success');
                    }
                    this.updateSettingsUI();
                    return true;
                }
            } catch (err) {
                console.warn('[Biometrics] Enrollment cancelled or failed:', err);
                if (window.showToast && err.name !== 'AbortError') {
                    window.showToast('Biyometrik doğrulama iptal edildi veya tamamlanamadı.', 'warning');
                }
                return false;
            }
        },

        /**
         * Disable Face ID lock
         */
        disable: function () {
            localStorage.removeItem(STORAGE_ENABLED);
            localStorage.removeItem(STORAGE_CRED_ID);
            sessionStorage.removeItem(SESSION_UNLOCKED);
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.light();
            if (window.showToast) {
                window.showToast('Face ID kilidi devre dışı bırakıldı.', 'info');
            }
            this.updateSettingsUI();
        },

        /**
         * Prompt Face ID to unlock the vault
         */
        verify: async function () {
            try {
                const challenge = new Uint8Array(32);
                window.crypto.getRandomValues(challenge);

                const assertion = await navigator.credentials.get({
                    publicKey: {
                        challenge: challenge,
                        userVerification: 'required',
                        timeout: 60000
                    }
                });

                if (assertion) {
                    sessionStorage.setItem(SESSION_UNLOCKED, 'true');
                    localStorage.setItem(STORAGE_LAST_ACTIVE, Date.now().toString());
                    this.hideLockOverlay();
                    if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
                    return true;
                }
            } catch (err) {
                console.warn('[Biometrics] Verification failed:', err);
                if (window.ECuzdanHaptics) window.ECuzdanHaptics.error();
                if (window.showToast && err.name !== 'AbortError') {
                    window.showToast('Yüz veya parmak izi doğrulanamadı. Lütfen tekrar deneyin.', 'error');
                }
                return false;
            }
        },

        showLockOverlay: function () {
            const modal = document.getElementById('biometricLockModal');
            if (modal) {
                modal.classList.remove('hidden');
                // Automatically prompt Face ID immediately for frictionless entry
                setTimeout(() => {
                    this.verify();
                }, 350);
            }
        },

        hideLockOverlay: function () {
            const modal = document.getElementById('biometricLockModal');
            if (modal) {
                modal.classList.add('hidden');
            }
        },

        lockNow: function () {
            sessionStorage.removeItem(SESSION_UNLOCKED);
            this.showLockOverlay();
        },

        updateSettingsUI: function () {
            const btnEnable = document.getElementById('btnEnableBiometrics');
            const btnDisable = document.getElementById('btnDisableBiometrics');
            const statusBadge = document.getElementById('biometricStatusBadge');
            const enabled = this.isEnabled();

            if (btnEnable) btnEnable.classList.toggle('hidden', enabled);
            if (btnDisable) btnDisable.classList.toggle('hidden', !enabled);
            if (statusBadge) {
                statusBadge.textContent = enabled ? 'Aktif (Korumalı) ✓' : 'Devre Dışı';
                statusBadge.className = enabled
                    ? 'text-xs font-bold text-emerald-600 dark:text-emerald-400'
                    : 'text-xs font-bold text-slate-400';
            }
        },

        init: function () {
            // Check if biometric lock should be engaged on load
            if (this.isEnabled()) {
                const unlocked = sessionStorage.getItem(SESSION_UNLOCKED) === 'true';
                const lastActive = parseInt(localStorage.getItem(STORAGE_LAST_ACTIVE) || '0', 10);
                const elapsed = Date.now() - lastActive;

                if (!unlocked || elapsed > INACTIVITY_TIMEOUT_MS) {
                    this.showLockOverlay();
                } else {
                    localStorage.setItem(STORAGE_LAST_ACTIVE, Date.now().toString());
                }
            }

            // Track visibility and user activity
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') {
                    if (this.isEnabled()) {
                        const lastActive = parseInt(localStorage.getItem(STORAGE_LAST_ACTIVE) || '0', 10);
                        if (Date.now() - lastActive > INACTIVITY_TIMEOUT_MS) {
                            this.showLockOverlay();
                        } else {
                            localStorage.setItem(STORAGE_LAST_ACTIVE, Date.now().toString());
                        }
                    }
                } else {
                    if (this.isEnabled()) {
                        localStorage.setItem(STORAGE_LAST_ACTIVE, Date.now().toString());
                    }
                }
            });

            this.updateSettingsUI();
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => window.ECuzdanBiometrics.init());
    } else {
        window.ECuzdanBiometrics.init();
    }
})();
