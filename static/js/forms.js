/**
 * E-CÜZDAN v15.0 - Forms JavaScript
 * Form validation, dynamic field feedback, loading states, and modal handling
 */

// Field Validation
export function validateField(input) {
    if (!input || input.disabled || input.type === 'hidden') {
        return { isValid: true };
    }

    // Skip validation for inputs in closed templates or inactive tabs
    if (!input.offsetParent && input.type !== 'file') {
        // Hidden element
    }

    const value = (input.value || '').trim();
    let isValid = true;
    let errorMessage = '';

    // 1. Required Check
    if (input.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'Bu alan zorunludur.';
    }

    // 2. Numeric / Currency / Quantity Checks
    if (isValid && value && (input.type === 'number' || input.inputMode === 'decimal')) {
        const num = parseFloat(value);
        if (isNaN(num)) {
            isValid = false;
            errorMessage = 'Geçerli bir sayı giriniz.';
        } else {
            const minAttr = input.getAttribute('min');
            const maxAttr = input.getAttribute('max');
            
            if (minAttr !== null && num < parseFloat(minAttr)) {
                isValid = false;
                errorMessage = `Değer en az ${minAttr} olmalıdır.`;
            } else if (maxAttr !== null && num > parseFloat(maxAttr)) {
                isValid = false;
                errorMessage = `Değer en fazla ${maxAttr} olmalıdır.`;
            } else {
                // If it's a financial field without negative allowance, ensure > 0
                const fieldName = (input.name || input.id || '').toLowerCase();
                const isFinancialAmount = /amount|tutar|fiyat|price|quantity|adet|miktar|purchase_cost|maliyet|value|deger/.test(fieldName);
                if (isFinancialAmount && minAttr === null && num <= 0) {
                    isValid = false;
                    errorMessage = 'Tutar veya miktar 0\'dan büyük olmalıdır.';
                }
            }
        }
    }

    // 3. Email Check
    if (isValid && value && input.type === 'email') {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!re.test(value)) {
            isValid = false;
            errorMessage = 'Geçerli bir e-posta adresi giriniz.';
        }
    }

    // 4. Date Check
    if (isValid && value && input.type === 'date') {
        const d = new Date(value);
        if (isNaN(d.getTime())) {
            isValid = false;
            errorMessage = 'Geçerli bir tarih seçiniz.';
        }
    }

    // Apply or clean visual feedback
    if (!isValid) {
        input.classList.add('form-input-error', 'ring-2', 'ring-rose-500', 'border-rose-500');
        input.setAttribute('aria-invalid', 'true');
        setFieldErrorDisplay(input, errorMessage);
    } else {
        clearFieldValidation(input);
    }

    return { isValid, message: errorMessage };
}

// Display error badge/text under the input
function setFieldErrorDisplay(input, message) {
    let errorSpan = findFieldErrorElement(input);
    if (!errorSpan) {
        errorSpan = document.createElement('span');
        errorSpan.className = 'field-error-message text-rose-500 text-[10px] font-semibold flex items-center gap-1 mt-1 animate-fade-in';
        errorSpan.setAttribute('role', 'alert');
        errorSpan.innerHTML = `
            <svg class="w-3 h-3 flex-shrink-0 text-rose-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <span class="error-text">${message}</span>
        `;
        // Insert right after the input or its parent container if input is inside an input-group
        const parent = input.parentElement;
        if (parent && parent.classList.contains('relative')) {
            parent.parentElement.appendChild(errorSpan);
        } else if (parent) {
            parent.appendChild(errorSpan);
        }
    } else {
        const textElem = errorSpan.querySelector('.error-text') || errorSpan;
        textElem.textContent = message;
        errorSpan.style.display = 'flex';
    }
}

// Find existing error message element for input
function findFieldErrorElement(input) {
    const parent = input.parentElement;
    if (!parent) return null;
    let span = parent.querySelector('.field-error-message, .form-error');
    if (!span && parent.parentElement) {
        span = parent.parentElement.querySelector('.field-error-message, .form-error');
    }
    return span;
}

// Clear single field validation
export function clearFieldValidation(input) {
    if (!input) return;
    input.classList.remove('form-input-error', 'ring-2', 'ring-rose-500', 'border-rose-500');
    input.removeAttribute('aria-invalid');
    const errorSpan = findFieldErrorElement(input);
    if (errorSpan) {
        errorSpan.remove();
    }
}

// Form Validation
export function validateForm(formOrId) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    if (!form) return false;

    const inputs = form.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea');
    let isValid = true;
    let firstInvalid = null;

    inputs.forEach(input => {
        const res = validateField(input);
        if (!res.isValid) {
            isValid = false;
            if (!firstInvalid) firstInvalid = input;
        }
    });

    if (!isValid && firstInvalid) {
        firstInvalid.focus();
        
        // Shake animation
        const shakeContainer = firstInvalid.closest('.form-group') || firstInvalid.parentElement || firstInvalid;
        shakeContainer.classList.remove('animate-shake');
        void shakeContainer.offsetWidth; // Force reflow
        shakeContainer.classList.add('animate-shake');

        if (window.showToast) {
            window.showToast('Lütfen formdaki eksik veya hatalı alanları kontrol ediniz.', 'warning');
        }
        return false;
    }

    return isValid;
}

// Set custom error on a field (e.g. from server response)
export function setFormFieldError(inputOrName, message, formElement) {
    let input = null;
    if (typeof inputOrName === 'string') {
        const scope = formElement || document;
        input = scope.querySelector(`[name="${inputOrName}"]`) || scope.getElementById(inputOrName);
    } else {
        input = inputOrName;
    }

    if (input) {
        input.classList.add('form-input-error', 'ring-2', 'ring-rose-500', 'border-rose-500');
        input.setAttribute('aria-invalid', 'true');
        setFieldErrorDisplay(input, message);
    }
}

// Clear all form errors
export function clearFormErrors(formOrId) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    if (!form) return;
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => clearFieldValidation(input));
}

// Validate Email
export function validateEmail(input) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = re.test(input.value);
    if (!isValid) {
        input.classList.add('ring-2', 'ring-rose-500');
    } else {
        input.classList.remove('ring-2', 'ring-rose-500');
    }
    return isValid;
}

// Validate Phone
export function validatePhone(input) {
    const re = /^(\+90|0)?[0-9]{10}$/;
    const isValid = re.test(input.value.replace(/\s/g, ''));
    if (!isValid) {
        input.classList.add('ring-2', 'ring-rose-500');
    } else {
        input.classList.remove('ring-2', 'ring-rose-500');
    }
    return isValid;
}

// Validate Number Range
export function validateNumberRange(input, min, max) {
    const value = parseFloat(input.value);
    const isValid = value >= min && value <= max;
    if (!isValid) {
        input.classList.add('ring-2', 'ring-rose-500');
    } else {
        input.classList.remove('ring-2', 'ring-rose-500');
    }
    return isValid;
}

// Reset Form
export function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        clearFormErrors(form);
    }
}

// Get Form Data as Object
export function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    return data;
}

// Set Form Data from Object
export function setFormData(formId, data) {
    const form = document.getElementById(formId);
    if (!form) return;
    Object.keys(data).forEach(key => {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = data[key];
        }
    });
}

// Disable Form
export function disableForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            input.disabled = true;
        });
    }
}

// Enable Form
export function enableForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            input.disabled = false;
        });
    }
}

// Show Form Loading State
export function showFormLoading(formOrId, submitButtonOrId) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    let submitButton = null;
    if (submitButtonOrId) {
        submitButton = typeof submitButtonOrId === 'string' ? document.getElementById(submitButtonOrId) : submitButtonOrId;
    } else if (form) {
        submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    }

    if (form) {
        form.dataset.submitting = 'true';
    }

    if (submitButton && !submitButton.classList.contains('btn-loading')) {
        submitButton.disabled = true;
        submitButton.classList.add('btn-loading', 'opacity-75', 'pointer-events-none');
        if (!submitButton.getAttribute('data-original-html')) {
            submitButton.setAttribute('data-original-html', submitButton.innerHTML);
        }
        submitButton.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Kaydediliyor...</span>
        `;

        // Safety timeout: restore after 8 seconds in case of slow connection or unhandled client state
        setTimeout(() => {
            if (submitButton && submitButton.classList.contains('btn-loading')) {
                hideFormLoading(form, submitButton);
            }
        }, 8000);
    }
}

// Hide Form Loading State
export function hideFormLoading(formOrId, submitButtonOrId, originalText = null) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    let submitButton = null;
    if (submitButtonOrId) {
        submitButton = typeof submitButtonOrId === 'string' ? document.getElementById(submitButtonOrId) : submitButtonOrId;
    } else if (form) {
        submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    }

    if (form) {
        form.dataset.submitting = 'false';
        delete form.dataset.submitting;
    }

    if (submitButton) {
        submitButton.disabled = false;
        submitButton.classList.remove('btn-loading', 'opacity-75', 'pointer-events-none');
        const origHtml = submitButton.getAttribute('data-original-html');
        if (originalText) {
            submitButton.textContent = originalText;
        } else if (origHtml) {
            submitButton.innerHTML = origHtml;
            submitButton.removeAttribute('data-original-html');
        }
    }

    if (form) {
        enableForm(form.id || form);
    }
}

// Auto-resize Textarea
export function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Initialize Auto-resize Textareas
export function initAutoResizeTextareas() {
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', () => autoResizeTextarea(textarea));
        autoResizeTextarea(textarea);
    });
}

// Character Counter
export function updateCharacterCounter(inputId, counterId, maxLength) {
    const input = document.getElementById(inputId);
    const counter = document.getElementById(counterId);
    if (input && counter) {
        const remaining = maxLength - input.value.length;
        counter.textContent = `${remaining} karakter kaldı`;
        if (remaining < 0) {
            counter.classList.add('text-rose-600');
        } else {
            counter.classList.remove('text-rose-600');
        }
    }
}

// Initialize Character Counters
export function initCharacterCounters() {
    const inputs = document.querySelectorAll('input[data-max-length], textarea[data-max-length]');
    inputs.forEach(input => {
        const maxLength = parseInt(input.getAttribute('data-max-length'), 10);
        const counterId = input.getAttribute('data-counter-id');
        if (counterId) {
            input.addEventListener('input', () => {
                updateCharacterCounter(input.id, counterId, maxLength);
            });
            updateCharacterCounter(input.id, counterId, maxLength);
        }
    });
}

// Form Submit Handler helper
export function handleFormSubmit(formId, callback) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (validateForm(formId)) {
            const formData = getFormData(formId);
            callback(formData);
        }
    });
}

// Global Validation Initializer: automatically watches forms & inputs
export function initGlobalFormValidation() {
    // 0. Disable browser native bubbles on target forms so our custom validator takes control
    const setupNovalidate = () => {
        document.querySelectorAll('form[data-validate="true"], form[method="POST"], form[method="post"], .modal form, .edit-modal-body').forEach(form => {
            if (form.getAttribute('data-no-validate') !== 'true') {
                form.setAttribute('novalidate', 'true');
            }
        });
    };
    setupNovalidate();

    // Catch any native invalid events before browser default tooltips
    document.addEventListener('invalid', (e) => {
        const form = e.target.form;
        if (form && form.getAttribute('data-no-validate') !== 'true') {
            e.preventDefault();
            validateField(e.target);
            form.setAttribute('novalidate', 'true');
        }
    }, true);

    // Ensure novalidate is on form before submit button click triggers validation
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('button[type="submit"], input[type="submit"]');
        if (btn && btn.form && btn.form.getAttribute('data-no-validate') !== 'true') {
            btn.form.setAttribute('novalidate', 'true');
        }
    }, true);

    // 1. Live clear on input/change
    document.addEventListener('input', (e) => {
        if (e.target.matches('input, select, textarea')) {
            if (e.target.classList.contains('form-input-error')) {
                validateField(e.target);
            }
        }
    });

    document.addEventListener('change', (e) => {
        if (e.target.matches('select, input[type="date"], input[type="checkbox"], input[type="radio"]')) {
            if (e.target.classList.contains('form-input-error')) {
                validateField(e.target);
            }
        }
    });

    // 2. Intercept submit on forms that need validation
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (!form || form.tagName !== 'FORM') return;

        // Skip forms marked with data-no-validate
        if (form.getAttribute('data-no-validate') === 'true') return;

        // Prevent double form submission if form is already in-flight
        if (form.dataset.submitting === 'true') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        // Only validate POST forms or forms marked with data-validate or modal forms
        const isPost = (form.method || '').toUpperCase() === 'POST';
        const isModalForm = !!form.closest('.modal-content, .edit-modal-content, .asset-modal-body, .edit-modal-body, .modal');
        const hasValidateAttr = form.getAttribute('data-validate') === 'true';

        if (isPost || isModalForm || hasValidateAttr) {
            const isValid = validateForm(form);
            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }

            // Valid form: show loading state on submit button
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                showFormLoading(form, submitBtn);
            }
        }
    });
}

// Self-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initGlobalFormValidation();
        initAutoResizeTextareas();
        initCharacterCounters();
    });
} else {
    initGlobalFormValidation();
    initAutoResizeTextareas();
    initCharacterCounters();
}

// Export for global access
window.ECuzdanForms = {
    validateField,
    validateForm,
    clearFieldValidation,
    setFormFieldError,
    clearFormErrors,
    validateEmail,
    validatePhone,
    validateNumberRange,
    resetForm,
    getFormData,
    setFormData,
    disableForm,
    enableForm,
    showFormLoading,
    hideFormLoading,
    autoResizeTextarea,
    initAutoResizeTextareas,
    updateCharacterCounter,
    initCharacterCounters,
    handleFormSubmit,
    initGlobalFormValidation
};
