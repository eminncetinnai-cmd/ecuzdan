/**
 * E-Cüzdan Shake-to-Privacy Shield
 * Listens to device motion (accelerometer) to instantly toggle Privacy Mode on phone shake.
 */

(function () {
    'use strict';

    let lastX = null, lastY = null, lastZ = null;
    let lastShakeTime = 0;
    const SHAKE_THRESHOLD = 22; // m/s^2 acceleration delta
    const DEBOUNCE_MS = 1400; // minimum time between shakes

    function onDeviceMotion(event) {
        const acceleration = event.accelerationIncludingGravity || event.acceleration;
        if (!acceleration) return;

        const { x, y, z } = acceleration;
        if (x === null || y === null || z === null) return;

        if (lastX !== null) {
            const deltaX = Math.abs(x - lastX);
            const deltaY = Math.abs(y - lastY);
            const deltaZ = Math.abs(z - lastZ);

            const speed = (deltaX + deltaY + deltaZ);
            const now = Date.now();

            if (speed > SHAKE_THRESHOLD && (now - lastShakeTime > DEBOUNCE_MS)) {
                lastShakeTime = now;
                handleShakeTrigger();
            }
        }

        lastX = x;
        lastY = y;
        lastZ = z;
    }

    function handleShakeTrigger() {
        if (window.privacyMode && typeof window.privacyMode.toggle === 'function') {
            window.privacyMode.toggle().then((data) => {
                if (window.ECuzdanHaptics) {
                    window.ECuzdanHaptics.medium();
                }
                const isPrivate = document.documentElement.classList.contains('privacy');
                if (window.showToast) {
                    window.showToast(
                        isPrivate 
                            ? 'Gizlilik Kalkanı Açıldı (Tutarlar Gizlendi) 🛡️' 
                            : 'Gizlilik Kalkanı Kapatıldı 👁️',
                        'info'
                    );
                }
            });
        }
    }

    function initShakePrivacy() {
        // Only on touch/mobile devices
        if (!('ondevicemotion' in window)) {
            return;
        }

        // iOS 13+ requires explicit user interaction to request DeviceMotionEvent permission
        if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
            const enableShakePermission = function () {
                DeviceMotionEvent.requestPermission()
                    .then((permissionState) => {
                        if (permissionState === 'granted') {
                            window.addEventListener('devicemotion', onDeviceMotion, false);
                        }
                    })
                    .catch(() => {});
                document.removeEventListener('click', enableShakePermission);
                document.removeEventListener('touchstart', enableShakePermission);
            };
            document.addEventListener('click', enableShakePermission, { once: true });
            document.addEventListener('touchstart', enableShakePermission, { once: true });
        } else {
            window.addEventListener('devicemotion', onDeviceMotion, false);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initShakePrivacy);
    } else {
        initShakePrivacy();
    }
})();
