// JavaScript base para GuessItYet
console.log('GuessItYet - Base JavaScript cargado');

// Utilidades globales
const GuessItYetUtils = {
    // Obtener token CSRF para peticiones AJAX
    getCSRFToken() {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }

        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }

        return '';
    },

    // Mostrar toast/notificación
    showToast(message, type = 'info', duration = 3000) {
        const toastContainer = this.getOrCreateToastContainer();

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });

        bsToast.show();

        // Limpiar el toast después de que se oculte
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Crear contenedor de toasts si no existe
    getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        return container;
    },

    // Formatear fecha
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };

        return new Date(date).toLocaleDateString('es-ES', {
            ...defaultOptions,
            ...options
        });
    },

    // Debounce para búsquedas
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Validar formularios básicos
    validateForm(formElement) {
        const inputs = formElement.querySelectorAll('input[required], textarea[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });

        return isValid;
    },

    // Confirmar acción destructiva
    confirmAction(message = '¿Estás seguro?') {
        return confirm(message);
    }
};

// Configuración global cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado - Inicializando configuración base');

    // Configurar tooltips de Bootstrap si existen
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Configurar popovers de Bootstrap si existen
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-cerrar alerts después de un tiempo
    const autoCloseAlerts = document.querySelectorAll('.alert[data-auto-close]');
    autoCloseAlerts.forEach(alert => {
        const delay = parseInt(alert.dataset.autoClose) || 5000;
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, delay);
    });

    // Marcar enlace activo en la navegación
    highlightActiveNavLink();

    // Configurar formularios con validación básica
    setupFormValidation();

    // Configurar botones de confirmación
    setupConfirmButtons();
});

// Marcar enlace activo en la navegación
function highlightActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Configurar validación básica de formularios
function setupFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!GuessItYetUtils.validateForm(form)) {
                e.preventDefault();
                GuessItYetUtils.showToast('Por favor, completa todos los campos requeridos', 'warning');
            }
        });

        // Limpiar errores al escribir
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.value.trim()) {
                    this.classList.remove('is-invalid');
                }
            });
        });
    });
}

// Configurar botones que requieren confirmación
function setupConfirmButtons() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');

    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || '¿Estás seguro?';
            if (!GuessItYetUtils.confirmAction(message)) {
                e.preventDefault();
            }
        });
    });
}

// Funciones globales para uso en plantillas
window.GuessItYetUtils = GuessItYetUtils;

// Manejar errores AJAX globalmente
window.addEventListener('unhandledrejection', function(event) {
    console.error('Error no manejado:', event.reason);
    GuessItYetUtils.showToast('Ha ocurrido un error inesperado', 'danger');
});

// Funciones de utilidad adicionales
window.showSuccessMessage = (message) => GuessItYetUtils.showToast(message, 'success');
window.showErrorMessage = (message) => GuessItYetUtils.showToast(message, 'danger');
window.showWarningMessage = (message) => GuessItYetUtils.showToast(message, 'warning');
window.showInfoMessage = (message) => GuessItYetUtils.showToast(message, 'info');