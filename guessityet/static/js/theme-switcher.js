// Cambio de tema con guardado en sessionStorage
console.log('Theme Switcher cargado');

class ThemeSwitcher {
    constructor() {
        this.currentTheme = 'dark'; // Tema por defecto
        this.init();
    }

    init() {
        // Cargar tema guardado o usar el por defecto
        this.loadSavedTheme();

        // Configurar event listeners
        this.setupEventListeners();

        // Aplicar tema inicial
        this.applyTheme(this.currentTheme);

        console.log(`Tema inicializado: ${this.currentTheme}`);
    }

    loadSavedTheme() {
        try {
            // Intentar cargar desde sessionStorage
            const savedTheme = sessionStorage.getItem('guessityet_theme');

            if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
                this.currentTheme = savedTheme;
                console.log(`Tema cargado desde sessionStorage: ${savedTheme}`);
            } else {
                // Si no hay tema guardado, detectar preferencia del sistema
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                this.currentTheme = prefersDark ? 'dark' : 'light';
                console.log(`Tema detectado desde sistema: ${this.currentTheme}`);
            }
        } catch (error) {
            console.warn('Error cargando tema:', error);
            this.currentTheme = 'dark'; // Fallback
        }
    }

    saveTheme(theme) {
        try {
            sessionStorage.setItem('guessityet_theme', theme);
            console.log(`Tema guardado en sessionStorage: ${theme}`);
        } catch (error) {
            console.warn('Error guardando tema:', error);
        }
    }

    setupEventListeners() {
        const themeToggle = document.getElementById('theme-toggle');

        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });

            // Keyboard support
            themeToggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });

            console.log('Event listeners configurados');
        } else {
            console.warn('Botón de tema no encontrado');
        }

        // Escuchar cambios en las preferencias del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Solo cambiar automáticamente si no hay tema guardado manualmente
            const savedTheme = sessionStorage.getItem('guessityet_theme');
            if (!savedTheme) {
                const newTheme = e.matches ? 'dark' : 'light';
                this.currentTheme = newTheme;
                this.applyTheme(newTheme);
                console.log(`Tema cambiado automáticamente por sistema: ${newTheme}`);
            }
        });
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.currentTheme = newTheme;

        // Aplicar y guardar tema
        this.applyTheme(newTheme);
        this.saveTheme(newTheme);

        // Feedback visual
        this.showThemeChangeNotification(newTheme);

        console.log(`Tema cambiado a: ${newTheme}`);
    }

    applyTheme(theme) {
        const html = document.documentElement;

        // Cambiar el atributo data-theme
        html.setAttribute('data-theme', theme);

        // Actualizar el botón si existe
        this.updateThemeButton(theme);

        // Aplicar transición suave
        this.addThemeTransition();
    }

    updateThemeButton(theme) {
        const themeToggle = document.getElementById('theme-toggle');
        if (!themeToggle) return;

        // Actualizar aria-label para accesibilidad
        const nextTheme = theme === 'dark' ? 'claro' : 'oscuro';
        themeToggle.setAttribute('aria-label', `Cambiar a tema ${nextTheme}`);

        // Añadir clase para animación
        themeToggle.classList.add('theme-changing');

        setTimeout(() => {
            themeToggle.classList.remove('theme-changing');
        }, 300);
    }

    addThemeTransition() {
        const style = document.createElement('style');
        style.textContent = `
            *, *::before, *::after {
                transition: background-color 0.3s ease, 
                           color 0.3s ease, 
                           border-color 0.3s ease,
                           box-shadow 0.3s ease !important;
            }
        `;
        document.head.appendChild(style);

        // Remover la transición después de un tiempo
        setTimeout(() => {
            style.remove();
        }, 500);
    }

    showThemeChangeNotification(theme) {
        // Solo mostrar notificación si GuessItYetUtils está disponible
        if (typeof GuessItYetUtils !== 'undefined' && GuessItYetUtils.showToast) {
            const themeText = theme === 'dark' ? 'oscuro' : 'claro';
            const icon = theme === 'dark' ? '🌙' : '☀️';

            // Crear toast personalizado con color azul más oscuro y agradable
            const toastContainer = document.getElementById('toast-container') || document.body;

            const toast = document.createElement('div');
            toast.className = 'toast align-items-center border-0 theme-change-toast';
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${icon} Tema ${themeText} activado
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;

            // Estilos personalizados para el toast
            toast.style.cssText = `
                background: #1E5F8B !important;
                color: white !important;
                box-shadow: 0 4px 12px rgba(30, 95, 139, 0.3) !important;
                border: 1px solid #2E86AB !important;
                margin-bottom: 0.5rem;
            `;

            toastContainer.appendChild(toast);

            const bsToast = new bootstrap.Toast(toast, {
                autohide: true,
                delay: 2500
            });

            bsToast.show();

            // Limpiar el toast después de que se oculte
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        }
    }

    // Método público para obtener el tema actual
    getCurrentTheme() {
        return this.currentTheme;
    }

    // Método público para forzar un tema específico
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.currentTheme = theme;
            this.applyTheme(theme);
            this.saveTheme(theme);
            console.log(`Tema forzado a: ${theme}`);
        } else {
            console.warn('Tema inválido:', theme);
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Crear instancia global del theme switcher
    window.themeSwitcher = new ThemeSwitcher();

    console.log('ThemeSwitcher inicializado');
});

// Hacer disponibles algunas funciones globalmente
window.toggleTheme = function() {
    if (window.themeSwitcher) {
        window.themeSwitcher.toggleTheme();
    }
};

window.setTheme = function(theme) {
    if (window.themeSwitcher) {
        window.themeSwitcher.setTheme(theme);
    }
};

window.getCurrentTheme = function() {
    return window.themeSwitcher ? window.themeSwitcher.getCurrentTheme() : 'dark';
};