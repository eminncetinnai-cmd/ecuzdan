/**
 * E-CÜZDAN v15.0 - Forms JavaScript
 * Form validation and handling
 */

// Form Validation
export function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    let firstInvalid = null;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('ring-2', 'ring-rose-500');
            if (!firstInvalid) firstInvalid = input;
        } else {
            input.classList.remove('ring-2', 'ring-rose-500');
        }
    });
    
    if (firstInvalid) {
        firstInvalid.focus();
        return false;
    }
    
    return isValid;
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
        // Remove validation classes
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.classList.remove('ring-2', 'ring-rose-500');
        });
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
export function showFormLoading(formId, submitButtonId) {
    const form = document.getElementById(formId);
    const submitButton = document.getElementById(submitButtonId);
    
    if (form) {
        disableForm(formId);
    }
    
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Yükleniyor...';
        submitButton.classList.add('opacity-50');
    }
}

// Hide Form Loading State
export function hideFormLoading(formId, submitButtonId, originalText = 'Kaydet') {
    const form = document.getElementById(formId);
    const submitButton = document.getElementById(submitButtonId);
    
    if (form) {
        enableForm(formId);
    }
    
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = originalText;
        submitButton.classList.remove('opacity-50');
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
        const maxLength = parseInt(input.getAttribute('data-max-length'));
        const counterId = input.getAttribute('data-counter-id');
        
        if (counterId) {
            input.addEventListener('input', () => {
                updateCharacterCounter(input.id, counterId, maxLength);
            });
            updateCharacterCounter(input.id, counterId, maxLength);
        }
    });
}

// Form Submit Handler
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

// Export for global access
window.ECuzdanForms = {
    validateForm,
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
    handleFormSubmit
};
