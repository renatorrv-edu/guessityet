// profile.js - Funcionalidad para la página de perfil

document.addEventListener('DOMContentLoaded', function() {
    // Animaciones para las tarjetas de estadísticas
    animateStatCards();

    // Configurar tooltips para elementos con información adicional
    setupTooltips();

    // Animar barras de progreso
    animateProgressBars();

    // Configurar carga lazy para elementos pesados
    setupLazyLoading();
});

function animateStatCards() {
    const statCards = document.querySelectorAll('.stat-card');

    statCards.forEach((card, index) => {
        // Animar números de estadísticas
        const numberElement = card.querySelector('.stat-number');
        if (numberElement) {
            const finalNumber = parseInt(numberElement.textContent);
            animateNumber(numberElement, finalNumber, index * 100);
        }

        // Añadir efecto de entrada escalonado
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';

        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function animateNumber(element, finalNumber, delay = 0) {
    setTimeout(() => {
        let currentNumber = 0;
        const increment = Math.ceil(finalNumber / 30); // 30 pasos de animación
        const timer = setInterval(() => {
            currentNumber += increment;
            if (currentNumber >= finalNumber) {
                currentNumber = finalNumber;
                clearInterval(timer);
            }
            element.textContent = currentNumber;
        }, 50);
    }, delay);
}

function setupTooltips() {
    // Crear tooltips personalizados para elementos con atributo data-tooltip
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        let tooltip = null;

        element.addEventListener('mouseenter', (e) => {
            const tooltipText = element.getAttribute('data-tooltip');
            if (!tooltipText) return;

            tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = tooltipText;
            tooltip.style.cssText = `
                position: absolute;
                background: var(--bg-surface-3);
                color: var(--text-primary);
                padding: 0.5rem 1rem;
                border-radius: var(--radius-md);
                font-size: 0.8rem;
                z-index: 1000;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--border-color);
                white-space: nowrap;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s ease;
            `;

            document.body.appendChild(tooltip);

            const rect = element.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.bottom + 10 + 'px';

            setTimeout(() => {
                if (tooltip) tooltip.style.opacity = '1';
            }, 50);
        });

        element.addEventListener('mouseleave', () => {
            if (tooltip) {
                tooltip.style.opacity = '0';
                setTimeout(() => {
                    if (tooltip && tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 200);
            }
        });
    });
}

function animateProgressBars() {
    const progressBars = document.querySelectorAll('.attempt-fill');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target;
                const width = bar.style.width;

                // Reset width para animación
                bar.style.width = '0%';
                bar.style.transition = 'width 1s ease-out';

                // Animar a la anchura final
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);

                observer.unobserve(bar);
            }
        });
    }, { threshold: 0.5 });

    progressBars.forEach(bar => observer.observe(bar));
}

function setupLazyLoading() {
    // Carga lazy para tarjetas de juegos recientes
    const gameCards = document.querySelectorAll('.game-card');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const card = entry.target;
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'all 0.4s ease';

                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50);

                observer.unobserve(card);
            }
        });
    }, { threshold: 0.1 });

    gameCards.forEach(card => observer.observe(card));
}

// Función para compartir perfil
function shareProfile(username) {
    if (navigator.share) {
        navigator.share({
            title: `Perfil de ${username} en Guess It Yet?`,
            text: `Mira las estadísticas de ${username} en Guess It Yet!`,
            url: window.location.href
        });
    } else {
        // Fallback: copiar al portapapeles
        navigator.clipboard.writeText(window.location.href).then(() => {
            showNotification('Enlace copiado al portapapeles');
        });
    }
}

// Función para mostrar notificaciones temporales
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'var(--success-color)' : 'var(--error-color)'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);

    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Función para alternar vista de estadísticas detalladas
function toggleDetailedStats() {
    const detailedSection = document.getElementById('detailed-stats');
    const toggleButton = document.getElementById('toggle-stats-btn');

    if (detailedSection) {
        if (detailedSection.style.display === 'none') {
            detailedSection.style.display = 'block';
            toggleButton.innerHTML = '<i class="fas fa-eye-slash me-2"></i>Ocultar detalles';
        } else {
            detailedSection.style.display = 'none';
            toggleButton.innerHTML = '<i class="fas fa-eye me-2"></i>Ver detalles';
        }
    }
}

// Función para filtrar juegos recientes
function filterRecentGames(filter) {
    const gameCards = document.querySelectorAll('.game-card');

    gameCards.forEach(card => {
        let shouldShow = true;

        switch(filter) {
            case 'won':
                shouldShow = card.classList.contains('success');
                break;
            case 'lost':
                shouldShow = card.classList.contains('failed');
                break;
            case 'guessed-it':
                shouldShow = card.querySelector('.guessed-it') !== null;
                break;
            case 'all':
            default:
                shouldShow = true;
                break;
        }

        card.style.display = shouldShow ? 'block' : 'none';
    });

    // Actualizar botones de filtro
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
}

// Función para exportar estadísticas (preparación para futuras funcionalidades)
function exportStats() {
    const stats = {
        username: document.querySelector('.profile-header h1').textContent,
        totalGames: parseInt(document.querySelector('.stat-card .stat-number').textContent),
        // Aquí se añadirían más estadísticas...
    };

    const dataStr = JSON.stringify(stats, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});

    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `${stats.username}_estadisticas.json`;
    link.click();
}

// Exponer funciones globalmente para uso en templates
window.shareProfile = shareProfile;
window.toggleDetailedStats = toggleDetailedStats;
window.filterRecentGames = filterRecentGames;
window.exportStats = exportStats;