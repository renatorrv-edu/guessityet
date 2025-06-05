// Utilidades adicionales para GuessItYet
console.log('Cargando Utils JS...');

// Formateo de números y estadísticas
const StatUtils = {
    // Formatear números grandes (1000 -> 1K)
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    // Calcular porcentaje de aciertos
    calculateWinRate(wins, total) {
        if (total === 0) return 0;
        return Math.round((wins / total) * 100);
    },

    // Formatear tiempo (segundos -> MM:SS)
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
};

// Utilidades de almacenamiento local (para configuraciones)
const StorageUtils = {
    // Guardar configuración
    saveConfig(key, value) {
        try {
            localStorage.setItem(`guessityet_${key}`, JSON.stringify(value));
        } catch (e) {
            console.warn('No se pudo guardar en localStorage:', e);
        }
    },

    // Cargar configuración
    loadConfig(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`guessityet_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('No se pudo cargar de localStorage:', e);
            return defaultValue;
        }
    },

    // Eliminar configuración
    removeConfig(key) {
        try {
            localStorage.removeItem(`guessityet_${key}`);
        } catch (e) {
            console.warn('No se pudo eliminar de localStorage:', e);
        }
    }
};

// Utilidades de validación
const ValidationUtils = {
    // Validar email
    isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },

    // Validar username
    isValidUsername(username) {
        return username.length >= 3 && username.length <= 20 && /^[a-zA-Z0-9_]+$/.test(username);
    },

    // Validar password
    isValidPassword(password) {
        return password.length >= 8;
    },

    // Sanitizar texto
    sanitizeText(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Utilidades de animación
const AnimationUtils = {
    // FadeIn
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';

        const start = performance.now();

        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = elapsed / duration;

            if (progress < 1) {
                element.style.opacity = progress;
                requestAnimationFrame(animate);
            } else {
                element.style.opacity = '1';
            }
        }

        requestAnimationFrame(animate);
    },

    // FadeOut
    fadeOut(element, duration = 300) {
        const start = performance.now();
        const startOpacity = parseFloat(window.getComputedStyle(element).opacity);

        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = elapsed / duration;

            if (progress < 1) {
                element.style.opacity = startOpacity * (1 - progress);
                requestAnimationFrame(animate);
            } else {
                element.style.opacity = '0';
                element.style.display = 'none';
            }
        }

        requestAnimationFrame(animate);
    },

    // SlideDown
    slideDown(element, duration = 300) {
        element.style.height = '0';
        element.style.overflow = 'hidden';
        element.style.display = 'block';

        const targetHeight = element.scrollHeight;
        const start = performance.now();

        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = elapsed / duration;

            if (progress < 1) {
                element.style.height = (targetHeight * progress) + 'px';
                requestAnimationFrame(animate);
            } else {
                element.style.height = '';
                element.style.overflow = '';
            }
        }

        requestAnimationFrame(animate);
    }
};

// Hacer utilidades disponibles globalmente
window.StatUtils = StatUtils;
window.StorageUtils = StorageUtils;
window.ValidationUtils = ValidationUtils;
window.AnimationUtils = AnimationUtils;