// static/js/auth.js - Funcionalidad mejorada para páginas de autenticación

document.addEventListener('DOMContentLoaded', function() {
    console.log('Cargando funcionalidad de autenticación...');

    // Configurar toggles de contraseña
    setupPasswordToggles();

    // Configurar validación de contraseñas
    setupPasswordValidation();

    // Configurar validación en tiempo real
    setupRealTimeValidation();

    // Configurar formularios
    setupAuthForms();
});

/**
 * Configurar los botones de mostrar/ocultar contraseña
 */
function setupPasswordToggles() {
    const passwordToggles = document.querySelectorAll('.password-toggle');

    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('data-target');
            const passwordField = document.getElementById(targetId);
            const icon = this.querySelector('i');

            if (!passwordField || !icon) return;

            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
                this.setAttribute('aria-label', 'Ocultar contraseña');
            } else {
                passwordField.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
                this.setAttribute('aria-label', 'Mostrar contraseña');
            }
        });
    });
}

/**
 * Configurar validación de contraseñas con requisitos de seguridad
 */
function setupPasswordValidation() {
    const passwordFields = document.querySelectorAll('input[type="password"]');

    passwordFields.forEach(field => {
        // Solo aplicar validación estricta a campos de nueva contraseña
        if (field.name.includes('password1') || field.name.includes('new_password1')) {
            setupStrongPasswordValidation(field);
        }

        // Configurar validación de confirmación de contraseña
        if (field.name.includes('password2') || field.name.includes('new_password2')) {
            setupPasswordConfirmation(field);
        }
    });
}

/**
 * Configurar validación de contraseña fuerte
 */
function setupStrongPasswordValidation(passwordField) {
    // Crear contenedor de indicadores de validación
    const validationContainer = createPasswordValidationIndicator(passwordField);

    passwordField.addEventListener('input', function() {
        const password = this.value;
        const isValid = validatePasswordStrength(password, validationContainer);

        if (password.length > 0) {
            if (isValid) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        } else {
            this.classList.remove('is-valid', 'is-invalid');
        }
    });
}

/**
 * Crear indicador visual de validación de contraseña
 */
function createPasswordValidationIndicator(passwordField) {
    // Buscar si ya existe
    let container = passwordField.parentNode.parentNode.querySelector('.password-requirements');

    if (!container) {
        container = document.createElement('div');
        container.className = 'password-requirements mt-2';
        container.innerHTML = `
            <small class="text-muted">La contraseña debe tener:</small>
            <ul class="list-unstyled small mt-1">
                <li id="req-length"><i class="fas fa-times text-danger me-1"></i> Al menos 8 caracteres</li>
                <li id="req-uppercase"><i class="fas fa-times text-danger me-1"></i> Una letra mayúscula</li>
                <li id="req-lowercase"><i class="fas fa-times text-danger me-1"></i> Una letra minúscula</li>
                <li id="req-number"><i class="fas fa-times text-danger me-1"></i> Un número</li>
                <li id="req-symbol"><i class="fas fa-times text-danger me-1"></i> Un símbolo (!@#$%^&*)</li>
            </ul>
        `;

        // Insertar después del campo de contraseña
        passwordField.parentNode.parentNode.appendChild(container);
    }

    return container;
}

/**
 * Validar fortaleza de contraseña
 */
function validatePasswordStrength(password, container) {
    const requirements = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        symbol: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
    };

    // Actualizar indicadores visuales
    Object.keys(requirements).forEach(req => {
        const element = container.querySelector(`#req-${req}`);
        const icon = element.querySelector('i');

        if (requirements[req]) {
            icon.className = 'fas fa-check text-success me-1';
            element.classList.remove('text-muted');
            element.classList.add('text-success');
        } else {
            icon.className = 'fas fa-times text-danger me-1';
            element.classList.remove('text-success');
            element.classList.add('text-muted');
        }
    });

    // Retornar si todos los requisitos se cumplen
    return Object.values(requirements).every(req => req);
}

/**
 * Configurar validación de confirmación de contraseña
 */
function setupPasswordConfirmation(confirmField) {
    const passwordField = findMainPasswordField(confirmField);

    if (passwordField) {
        const validateMatch = () => {
            if (confirmField.value && passwordField.value) {
                if (confirmField.value === passwordField.value) {
                    confirmField.classList.remove('is-invalid');
                    confirmField.classList.add('is-valid');
                    removeCustomError(confirmField, 'password-match');
                } else {
                    confirmField.classList.remove('is-valid');
                    confirmField.classList.add('is-invalid');
                    showCustomError(confirmField, 'password-match', 'Las contraseñas no coinciden');
                }
            } else {
                confirmField.classList.remove('is-valid', 'is-invalid');
                removeCustomError(confirmField, 'password-match');
            }
        };

        confirmField.addEventListener('input', validateMatch);
        passwordField.addEventListener('input', validateMatch);
    }
}

/**
 * Encontrar el campo principal de contraseña
 */
function findMainPasswordField(confirmField) {
    const form = confirmField.closest('form');
    if (!form) return null;

    // Buscar campos de contraseña que no sean de confirmación
    const passwordFields = form.querySelectorAll('input[type="password"]');

    for (let field of passwordFields) {
        if (!field.name.includes('2') && !field.name.includes('confirm') && field !== confirmField) {
            return field;
        }
    }

    return null;
}

/**
 * Mostrar error personalizado
 */
function showCustomError(field, errorType, message) {
    removeCustomError(field, errorType);

    const errorDiv = document.createElement('div');
    errorDiv.className = `invalid-feedback custom-error-${errorType}`;
    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i>${message}`;

    field.parentNode.appendChild(errorDiv);
}

/**
 * Remover error personalizado
 */
function removeCustomError(field, errorType) {
    const existingError = field.parentNode.querySelector(`.custom-error-${errorType}`);
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Configurar validación en tiempo real
 */
function setupRealTimeValidation() {
    const inputs = document.querySelectorAll('.auth-form-control');

    inputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid') && this.value.trim()) {
                this.classList.remove('is-invalid');

                // Ocultar errores de Django si existen
                const feedback = this.parentNode.querySelector('.invalid-feedback:not([class*="custom-error"])');
                if (feedback) {
                    feedback.style.display = 'none';
                }
            }
        });

        input.addEventListener('blur', function() {
            if (this.value.trim() && !this.classList.contains('is-invalid')) {
                this.classList.add('valid');
            } else {
                this.classList.remove('valid');
            }
        });
    });
}

/**
 * Configurar formularios de autenticación
 */
function setupAuthForms() {
    const forms = document.querySelectorAll('form[data-validate], #login-form, #register-form');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;

            // Validar contraseñas fuertes si es registro
            const passwordField = form.querySelector('input[name*="password1"]');
            if (passwordField && passwordField.value) {
                const container = form.querySelector('.password-requirements');
                if (container && !validatePasswordStrength(passwordField.value, container)) {
                    isValid = false;
                    passwordField.classList.add('is-invalid');
                    showCustomError(passwordField, 'strength', 'La contraseña no cumple con los requisitos de seguridad');
                }
            }

            // Validar confirmación de contraseña
            const confirmField = form.querySelector('input[name*="password2"]');
            if (confirmField && passwordField && confirmField.value !== passwordField.value) {
                isValid = false;
                confirmField.classList.add('is-invalid');
                showCustomError(confirmField, 'match', 'Las contraseñas no coinciden');
            }

            if (!isValid) {
                e.preventDefault();
                return false;
            }

            // Mostrar estado de carga
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;

                // Restaurar botón después de 5 segundos como fallback
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });
}

// Utilidades adicionales
window.AuthUtils = {
    validatePasswordStrength,
    setupPasswordToggles,
    setupPasswordValidation
};