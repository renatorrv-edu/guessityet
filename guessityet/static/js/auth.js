// Funcionalidad para páginas de autenticación
console.log('Cargando Auth JS...');

document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
});

function initializeAuth() {
    // Configurar formularios de autenticación
    setupAuthForms();

    // Configurar validación en tiempo real
    setupRealTimeValidation();

    // Configurar toggle de password
    setupPasswordToggle();
}

function setupAuthForms() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

function handleLogin(e) {
    e.preventDefault();
    const form = e.target;

    if (!GuessItYetUtils.validateForm(form)) {
        return;
    }

    // Procesar login
    form.submit();
}

function handleRegister(e) {
    e.preventDefault();
    const form = e.target;

    if (!GuessItYetUtils.validateForm(form)) {
        return;
    }

    // Validaciones adicionales específicas del registro
    if (!validatePasswordMatch()) {
        return;
    }

    // Procesar registro
    form.submit();
}

function validatePasswordMatch() {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm-password');

    if (password && confirmPassword) {
        if (password.value !== confirmPassword.value) {
            confirmPassword.classList.add('is-invalid');
            showErrorMessage('Las contraseñas no coinciden');
            return false;
        } else {
            confirmPassword.classList.remove('is-invalid');
        }
    }

    return true;
}

function setupRealTimeValidation() {
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

function validateField(field) {
    // Validación específica por tipo de campo
    if (field.type === 'email') {
        return validateEmail(field);
    } else if (field.name === 'username') {
        return validateUsername(field);
    } else if (field.type === 'password') {
        return validatePassword(field);
    }

    return true;
}

function validateEmail(field) {
    const email = field.value;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(email)) {
        field.classList.add('is-invalid');
        return false;
    } else {
        field.classList.remove('is-invalid');
        return true;
    }
}

function validateUsername(field) {
    const username = field.value;

    if (username.length < 3) {
        field.classList.add('is-invalid');
        return false;
    } else {
        field.classList.remove('is-invalid');
        return true;
    }
}

function validatePassword(field) {
    const password = field.value;

    if (password.length < 8) {
        field.classList.add('is-invalid');
        return false;
    } else {
        field.classList.remove('is-invalid');
        return true;
    }
}

function setupPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const passwordField = document.getElementById(targetId);

            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                passwordField.type = 'password';
                this.innerHTML = '<i class="fas fa-eye"></i>';
            }
        });
    });
}