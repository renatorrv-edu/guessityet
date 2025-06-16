// Base JavaScript para GuessItYet
console.log('🎮 GuessItYet - Base JS cargado');

// Utilidades globales
const GuessItYetUtils = {
    // Mostrar toast/notificación
    showToast: function(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${this.getToastColor(type)};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: 1050;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 350px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        `;

        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
            <button class="btn-close btn-close-white ms-2" onclick="this.parentElement.remove()"></button>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }
        }, duration);
    },

    getToastColor: function(type) {
        const colors = {
            success: '#48bb78',
            error: '#f56565',
            warning: '#ed8936',
            info: '#4299e1'
        };
        return colors[type] || colors.info;
    },

    getToastIcon: function(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    },

    // Validar formulario
    validateForm: function(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');

                // Crear mensaje de error si no existe
                let errorMsg = field.parentNode.querySelector('.invalid-feedback');
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'invalid-feedback';
                    errorMsg.textContent = 'Este campo es obligatorio';
                    field.parentNode.appendChild(errorMsg);
                }
            } else {
                field.classList.remove('is-invalid');
                const errorMsg = field.parentNode.querySelector('.invalid-feedback');
                if (errorMsg) {
                    errorMsg.remove();
                }
            }
        });

        return isValid;
    },

    // Formatear fecha
    formatDate: function(date) {
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        return new Date(date).toLocaleDateString('es-ES', options);
    },

    // Copiar al portapapeles
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copiado al portapapeles', 'success');
        }).catch(() => {
            this.showToast('Error al copiar', 'error');
        });
    },

    // Confirmar acción
    confirm: function(message) {
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
                    const errorMsg = this.parentNode.querySelector('.invalid-feedback');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
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
            if (!GuessItYetUtils.confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// Función para mostrar notificación de "próximamente"
function showComingSoon(feature) {
    const notification = document.createElement('div');
    notification.className = 'coming-soon-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        transform: translateX(100%);
        transition: all 0.3s ease;
        max-width: 300px;
        border-left: 4px solid var(--primary-light);
    `;

    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-clock me-2"></i>
            <div>
                <strong>${feature}</strong><br>
                <small>Esta función estará disponible pronto</small>
            </div>
            <button class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }, 4000);
}

// Función para generar enlace de perfil público
function generateProfileLink(username) {
    const baseUrl = window.location.origin;
    return `${baseUrl}/usuario/${username}/`;
}

// Función para mostrar estadísticas rápidas en tooltips
function showQuickStats(element, stats) {
    if (!element || !stats) return;

    const tooltip = document.createElement('div');
    tooltip.className = 'quick-stats-tooltip';
    tooltip.style.cssText = `
        position: absolute;
        background: var(--bg-surface-2);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        min-width: 200px;
        font-size: 0.85rem;
    `;

    tooltip.innerHTML = `
        <div class="quick-stats-content">
            <div class="mb-2"><strong>Estadísticas Rápidas</strong></div>
            <div class="d-flex justify-content-between mb-1">
                <span>Juegos:</span>
                <span>${stats.total || 0}</span>
            </div>
            <div class="d-flex justify-content-between mb-1">
                <span>Ganados:</span>
                <span>${stats.won || 0}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>Racha:</span>
                <span>${stats.streak || 0}</span>
            </div>
        </div>
    `;

    document.body.appendChild(tooltip);

    // Posicionar tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = rect.bottom + 10 + 'px';

    // Eliminar después de 3 segundos o al hacer click fuera
    const removeTooltip = () => {
        if (tooltip.parentNode) {
            tooltip.parentNode.removeChild(tooltip);
        }
        document.removeEventListener('click', removeTooltip);
    };

    setTimeout(removeTooltip, 3000);
    setTimeout(() => {
        document.addEventListener('click', removeTooltip);
    }, 100);
}

// Función para validar formularios de perfil
function validateProfileForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Función para previsualizar cambios del perfil
function previewProfileChanges(formData) {
    // Esta función se expandirá cuando se añadan más campos editables
    console.log('Previsualizando cambios del perfil:', formData);
}

// Función para manejar errores de carga de imágenes
function handleImageError(img) {
    img.style.display = 'none';

    // Mostrar placeholder si existe
    const placeholder = img.parentNode.querySelector('.image-placeholder');
    if (placeholder) {
        placeholder.style.display = 'flex';
    }
}

// Función para lazy loading de imágenes
function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Función para smooth scroll
function smoothScrollTo(target) {
    const element = document.querySelector(target);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth'
        });
    }
}

// Función para obtener cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Configurar CSRF para requests AJAX
const csrftoken = getCookie('csrftoken');

// Función para hacer requests AJAX seguros
function safeAjax(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
    };

    return fetch(url, { ...defaultOptions, ...options });
}

// Función para manejar errores de red
function handleNetworkError(error) {
    console.error('Error de red:', error);
    GuessItYetUtils.showToast('Error de conexión. Inténtalo de nuevo.', 'error');
}

// Función para detectar si es móvil
function isMobile() {
    return window.innerWidth <= 768;
}

// Función para detectar tema del sistema
function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

// Exponer funciones globalmente
window.GuessItYetUtils = GuessItYetUtils;
window.showComingSoon = showComingSoon;
window.generateProfileLink = generateProfileLink;
window.showQuickStats = showQuickStats;
window.validateProfileForm = validateProfileForm;
window.previewProfileChanges = previewProfileChanges;
window.handleImageError = handleImageError;
window.setupLazyLoading = setupLazyLoading;
window.smoothScrollTo = smoothScrollTo;
window.safeAjax = safeAjax;
window.handleNetworkError = handleNetworkError;
window.isMobile = isMobile;
window.getSystemTheme = getSystemTheme;