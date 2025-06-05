// Funcionalidad para la página de historial de juegos
console.log('Cargando Game History JS...');

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar funcionalidad del historial
    initializeGameHistory();
});

function initializeGameHistory() {
    // Configurar filtros de búsqueda
    setupHistoryFilters();

    // Configurar paginación
    setupPagination();

    // Configurar items clicables
    setupGameHistoryItems();
}

function setupHistoryFilters() {
    const searchInput = document.getElementById('history-search');
    const dateFilter = document.getElementById('date-filter');
    const resultFilter = document.getElementById('result-filter');

    if (searchInput) {
        searchInput.addEventListener('input', GuessItYetUtils.debounce(filterHistory, 300));
    }

    if (dateFilter) {
        dateFilter.addEventListener('change', filterHistory);
    }

    if (resultFilter) {
        resultFilter.addEventListener('change', filterHistory);
    }
}

function filterHistory() {
    // Lógica de filtrado se implementará aquí
    console.log('Filtrando historial...');
}

function setupPagination() {
    const paginationButtons = document.querySelectorAll('.pagination-btn');
    paginationButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.dataset.page;
            loadHistoryPage(page);
        });
    });
}

function loadHistoryPage(page) {
    // Cargar página del historial via AJAX
    console.log(`Cargando página ${page}...`);
}

function setupGameHistoryItems() {
    const historyItems = document.querySelectorAll('.game-history-item');
    historyItems.forEach(item => {
        item.addEventListener('click', function() {
            const gameId = this.dataset.gameId;
            const gameDate = this.dataset.gameDate;
            showGameDetails(gameId, gameDate);
        });
    });
}

function showGameDetails(gameId, gameDate) {
    // Mostrar detalles del juego en modal o página separada
    console.log(`Mostrando detalles del juego ${gameId} del ${gameDate}`);
}