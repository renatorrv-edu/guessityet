// Componentes reutilizables de JavaScript
console.log('Cargando Components JS...');

// Modal personalizado para confirmaciones
class ConfirmModal {
    constructor() {
        this.modalElement = null;
        this.createModal();
    }

    createModal() {
        const modalHTML = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Confirmar acción</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p id="confirmMessage">¿Estás seguro?</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-danger" id="confirmButton">Confirmar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modalElement = new bootstrap.Modal(document.getElementById('confirmModal'));
    }

    show(message, onConfirm) {
        document.getElementById('confirmMessage').textContent = message;

        const confirmButton = document.getElementById('confirmButton');
        const newButton = confirmButton.cloneNode(true);
        confirmButton.parentNode.replaceChild(newButton, confirmButton);

        newButton.addEventListener('click', () => {
            this.modalElement.hide();
            onConfirm();
        });

        this.modalElement.show();
    }
}

// Loading overlay
class LoadingOverlay {
    constructor() {
        this.overlay = null;
        this.createOverlay();
    }

    createOverlay() {
        const overlayHTML = `
            <div id="loadingOverlay" class="loading-overlay" style="display: none;">
                <div class="loading-spinner-container">
                    <div class="loading-spinner-large"></div>
                    <p class="loading-text">Cargando...</p>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', overlayHTML);
        this.overlay = document.getElementById('loadingOverlay');

        // Añadir estilos
        const styles = `
            <style>
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            }
            
            .loading-spinner-container {
                text-align: center;
                color: white;
            }
            
            .loading-spinner-large {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top-color: #fff;
                animation: spin 1s ease-in-out infinite;
                margin: 0 auto 1rem;
            }
            
            .loading-text {
                font-size: 1.1rem;
                margin: 0;
            }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    show(text = 'Cargando...') {
        document.querySelector('.loading-text').textContent = text;
        this.overlay.style.display = 'flex';
    }

    hide() {
        this.overlay.style.display = 'none';
    }
}

// Image lazy loading
function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Scroll to top button
function setupScrollToTop() {
    const scrollButton = document.createElement('button');
    scrollButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    scrollButton.className = 'btn btn-primary scroll-to-top';
    scrollButton.setAttribute('aria-label', 'Volver arriba');

    const styles = `
        <style>
        .scroll-to-top {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: none;
            z-index: 1000;
            transition: all 0.3s ease;
        }
        
        .scroll-to-top.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .scroll-to-top:hover {
            transform: translateY(-3px);
        }
        </style>
    `;

    document.head.insertAdjacentHTML('beforeend', styles);
    document.body.appendChild(scrollButton);

    scrollButton.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            scrollButton.classList.add('show');
        } else {
            scrollButton.classList.remove('show');
        }
    });
}

// Inicializar componentes cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Crear instancias globales
    window.confirmModal = new ConfirmModal();
    window.loadingOverlay = new LoadingOverlay();

    // Configurar funcionalidades
    setupLazyLoading();
    setupScrollToTop();
});