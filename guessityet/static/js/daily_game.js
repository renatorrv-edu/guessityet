// Lógica principal del juego GuessItYet - Solo IGDB
console.log('Cargando GuessItYet Game...');

class GuessItYetGame {
    constructor() {
        this.searchTimeout = null;
        this.selectedGame = null;
        this.currentAttempt = gameState.current_attempt || 1;
        this.maxAttempts = this.calculateMaxAttempts();
        this.gameEnded = gameState.won || gameState.lost;
        this.currentViewingAttempt = this.currentAttempt;

        this.init();
    }

    calculateMaxAttempts() {
        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';
        return hasGif ? 6 : Math.min(screenshots.length, 6);
    }

    init() {
        this.setupEventListeners();
        this.updateAttemptIndicators();
        this.updateScreenshot();
        this.updateGameInfo();
        this.loadExistingAttempts();
        this.startCountdown();

        if (this.gameEnded) {
            this.disableGameControls();
        }
    }

    setupEventListeners() {
        const searchInput = document.getElementById('game-search');
        const submitBtn = document.getElementById('submit-btn');
        const skipBtn = document.getElementById('skip-btn');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e);
            });

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && this.selectedGame) {
                    this.submitGuess();
                }
            });

            document.addEventListener('click', (e) => {
                if (!e.target.closest('.search-container')) {
                    this.hideSuggestions();
                }
            });
        }

        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.submitGuess();
            });
        }

        if (skipBtn) {
            skipBtn.addEventListener('click', () => {
                this.skipTurn();
            });
        }
    }

    handleSearchInput(e) {
        const query = e.target.value.trim();

        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        this.selectedGame = null;
        this.updateSubmitButton();

        if (query.length < 2) {
            this.hideSuggestions();
            return;
        }

        this.showLoading();

        this.searchTimeout = setTimeout(() => {
            this.searchGames(query);
        }, 300);
    }

    showLoading() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = `
            <div class="loading-container text-center py-3">
                <i class="fas fa-gamepad fa-spin text-primary me-2"></i>
                <span class="text-muted">Buscando juegos...</span>
            </div>
        `;
        suggestionsContainer.style.display = 'block';
    }

    async searchGames(query) {
        try {
            const url = `/search-games/?q=${encodeURIComponent(query)}&service=igdb&limit=25`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }

            const data = await response.json();

            if (data.games && data.games.length > 0) {
                this.showSuggestions(data.games);
            } else {
                this.showNoResults();
            }
        } catch (error) {
            console.error('Error buscando juegos:', error);
            this.showError();
        }
    }

    showSuggestions(games) {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = '';

        games.forEach(game => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';

            let releaseYear = '';
            if (game.first_release_date) {
                if (typeof game.first_release_date === 'number') {
                    releaseYear = new Date(game.first_release_date * 1000).getFullYear();
                }
            } else if (game.released) {
                if (typeof game.released === 'number') {
                    releaseYear = new Date(game.released * 1000).getFullYear();
                } else {
                    const year = new Date(game.released).getFullYear();
                    if (!isNaN(year)) {
                        releaseYear = year;
                    }
                }
            }

            let additionalInfo = [];
            if (game.franchise) {
                additionalInfo.push(`<span class="text-primary"><i class="fas fa-crown me-1"></i>${game.franchise}</span>`);
            }
            if (releaseYear) {
                additionalInfo.push(`<span class="text-muted">(${releaseYear})</span>`);
            }

            const additionalInfoHtml = additionalInfo.length > 0
                ? `<div class="small mt-1">${additionalInfo.join(' ')}</div>`
                : '';

            suggestionItem.innerHTML = `
                <div class="flex-grow-1">
                    <div class="fw-bold">${game.name}</div>
                    ${additionalInfoHtml}
                </div>
                <div class="service-indicator">
                    <i class="fas fa-database text-success" title="IGDB"></i>
                </div>
            `;

            suggestionItem.addEventListener('click', () => {
                this.selectGame(game);
            });

            suggestionsContainer.appendChild(suggestionItem);
        });

        suggestionsContainer.style.display = 'block';
    }

    showNoResults() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = `
            <div class="no-results text-center py-3 text-muted">
                <i class="fas fa-search me-2"></i>
                No se encontraron juegos
            </div>
        `;
        suggestionsContainer.style.display = 'block';
    }

    showError() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = `
            <div class="error-results text-center py-3 text-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error en la búsqueda
            </div>
        `;
        suggestionsContainer.style.display = 'block';
    }

    hideSuggestions() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }

    selectGame(game) {
        this.selectedGame = { ...game, service: 'igdb' };

        const searchInput = document.getElementById('game-search');
        if (searchInput) {
            searchInput.value = game.name;
        }

        this.hideSuggestions();
        this.updateSubmitButton();
    }

    updateSubmitButton() {
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = !this.selectedGame;
        }
    }

    async submitGuess() {
        if (!this.selectedGame) return;

        try {
            const response = await fetch('/submit-guess/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    game_name: this.selectedGame.name,
                    game_id: this.selectedGame.id,
                    service: 'igdb'
                })
            });

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.handleGuessResult(result);
            } else {
                console.error('Error en resultado:', result);
                alert('Error al procesar la respuesta: ' + (result.error || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Error en submitGuess:', error);
        }
    }

    async skipTurn() {
        try {
            const response = await fetch('/skip-turn/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.handleSkipResult(result);
            } else {
                console.error('Error en skip:', result);
                alert('Error al saltar turno: ' + (result.error || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Error en skipTurn:', error);
        }
    }

    handleGuessResult(result) {
        this.addAttemptToHistory({
            attempt: this.currentAttempt,
            type: 'guess',
            game_name: this.selectedGame.name,
            correct: result.correct,
            franchise_match: result.franchise_match,
            franchise_name: result.franchise_name
        });

        this.updateAttemptIndicator(this.currentAttempt, result);

        if (result.correct) {
            this.handleWin(result);
        } else {
            this.currentAttempt = result.current_attempt;

            if (result.lost) {
                this.handleLose();
            } else {
                this.nextAttempt();
            }
        }
    }

    handleSkipResult(result) {
        this.addAttemptToHistory({
            attempt: this.currentAttempt,
            type: 'skipped',
            game_name: 'Turno saltado',
            correct: false,
            franchise_match: false
        });

        this.updateAttemptIndicator(this.currentAttempt, {skipped: true});
        this.currentAttempt = result.current_attempt;

        if (result.game_ended) {
            this.handleLose();
        } else {
            this.nextAttempt();
        }
    }

    updateAttemptIndicators() {
        for (let i = 1; i <= 6; i++) {
            const circle = document.getElementById(`attempt-${i}`);
            if (circle) {
                circle.classList.remove('current', 'correct', 'wrong', 'franchise', 'skipped', 'clickable', 'disabled', 'selected');

                if (i > this.maxAttempts) {
                    circle.style.display = 'none';
                } else {
                    circle.style.display = 'flex';

                    // Determinar si es clicable
                    const maxAvailable = this.gameEnded ? this.maxAttempts : this.currentAttempt;
                    if (i <= maxAvailable) {
                        circle.classList.add('clickable');
                        circle.style.cursor = 'pointer';
                    } else {
                        circle.classList.add('disabled');
                        circle.style.cursor = 'not-allowed';
                    }

                    // Marcar el turno actual
                    if (i === this.currentAttempt && !this.gameEnded) {
                        circle.classList.add('current');
                    }

                    // Resaltar la posición actual de visualización
                    if (i === this.currentViewingAttempt) {
                        circle.style.fontWeight = '900';
                        circle.style.textShadow = '0 0 2px rgba(0,0,0,0.5)';
                        circle.style.transform = 'translateY(4px)';
                        circle.style.fontSize = '18px';
                    } else {
                        circle.style.fontWeight = 'bold';
                        circle.style.textShadow = 'none';
                        circle.style.transform = 'translateY(0)';
                        circle.style.fontSize = '14px';
                    }
                }
            }
        }

        if (gameState.attempts) {
            gameState.attempts.forEach(attempt => {
                this.updateAttemptIndicator(attempt.attempt, attempt);
            });
        }
    }

    updateAttemptIndicator(attemptNum, result) {
        const circle = document.getElementById(`attempt-${attemptNum}`);
        if (!circle) return;

        circle.classList.remove('current');

        if (result.correct) {
            circle.classList.add('correct');
        } else if (result.franchise_match) {
            circle.classList.add('franchise');
        } else if (result.skipped || result.type === 'skipped') {
            circle.classList.add('skipped');
        } else {
            circle.classList.add('wrong');
        }
    }

    updateScreenshot() {
        this.currentViewingAttempt = this.currentAttempt;
        this.showScreenshotForAttempt(this.currentAttempt);
    }

    showScreenshotForAttempt(attemptNum) {
        const screenshotImg = document.getElementById('current-screenshot');
        const contentIndicator = document.getElementById('content-type-indicator');

        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';
        const isLastAttempt = attemptNum === this.maxAttempts;

        if (isLastAttempt && hasGif) {
            if (screenshotImg) {
                screenshotImg.src = `/media/${gameData.gif_path}`;
                screenshotImg.alt = 'GIF del juego';
            }
            if (contentIndicator) {
                contentIndicator.style.display = 'block';
            }
        } else {
            const screenshot = screenshots.find(s => s.difficulty === attemptNum);
            if (screenshot && screenshotImg) {
                screenshotImg.src = screenshot.url;
                screenshotImg.alt = `Screenshot del juego - Nivel ${attemptNum}`;
            }
            if (contentIndicator) {
                contentIndicator.style.display = 'none';
            }
        }

        this.currentViewingAttempt = attemptNum;
    }

    updateGameInfo() {
        const infoContent = document.getElementById('info-content');
        const infoOverlay = document.getElementById('game-info-overlay');
        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';
        const isLastAttempt = this.currentViewingAttempt === this.maxAttempts;

        let infoText = '';

        if (this.currentViewingAttempt === 1) {
            // Primera imagen: sin información
            infoOverlay.style.display = 'none';
            return;
        } else if (isLastAttempt && hasGif) {
            // Último intento con GIF: mostrar desarrolladora
            if (gameData.developer) {
                infoText = `Desarrolladora: ${gameData.developer}`;
            }
        } else {
            // Resto de imágenes según el número
            switch(this.currentViewingAttempt) {
                case 2:
                    if (gameData.genres) {
                        infoText = `Géneros: ${gameData.genres}`;
                    }
                    break;
                case 3:
                    if (gameData.platforms) {
                        infoText = `Plataformas: ${gameData.platforms}`;
                    }
                    break;
                case 4:
                    if (gameData.metacritic) {
                        infoText = `Nota en Metacritic: ${gameData.metacritic}/100`;
                    }
                    break;
                case 5:
                    if (gameData.release_year) {
                        infoText = `Año de salida: ${gameData.release_year}`;
                    }
                    break;
                case 6:
                    if (gameData.developer) {
                        infoText = `Desarrolladora: ${gameData.developer}`;
                    }
                    break;
            }
        }

        if (infoText && infoContent) {
            infoContent.innerHTML = infoText;
            infoOverlay.style.display = 'block';
        } else {
            infoOverlay.style.display = 'none';
        }
    }

    addAttemptToHistory(attempt) {
        const historyContainer = document.getElementById('attempts-history-content');
        const historySection = document.getElementById('attempts-history');

        if (!historyContainer || !historySection) return;

        // Mostrar el historial si es el primer intento
        if (historySection.style.display === 'none') {
            historySection.style.display = 'block';
        }

        const attemptDiv = document.createElement('div');
        let className = 'attempt-result ';
        let icon = '';
        let extraText = '';

        if (attempt.correct) {
            className += 'correct';
            icon = '<i class="fas fa-check text-success"></i>';
        } else if (attempt.franchise_match) {
            className += 'franchise';
            icon = '<i class="fas fa-exclamation-triangle text-warning"></i>';
            const franchiseName = attempt.franchise_name || 'Franquicia correcta';
            extraText = `<br><small class="text-muted">${franchiseName}</small>`;
        } else if (attempt.type === 'skipped') {
            className += 'skipped';
            icon = '<i class="fas fa-forward text-muted"></i>';
        } else {
            className += 'wrong';
            icon = '<i class="fas fa-times text-danger"></i>';
        }

        attemptDiv.className = className;
        attemptDiv.innerHTML = `
            <div class="result-icon">${icon}</div>
            <div class="flex-grow-1">
                <strong>Intento ${attempt.attempt}:</strong> ${attempt.game_name}
                <span class="badge bg-success ms-2" title="IGDB"><i class="fas fa-database"></i></span>
                ${extraText}
            </div>
        `;

        historyContainer.insertBefore(attemptDiv, historyContainer.firstChild);
    }

    loadExistingAttempts() {
        const historyContainer = document.getElementById('attempts-history-content');
        const historySection = document.getElementById('attempts-history');

        if (!historyContainer || !historySection) return;

        historyContainer.innerHTML = '';

        if (!gameState.attempts || gameState.attempts.length === 0) {
            // Mantener oculto si no hay intentos
            historySection.style.display = 'none';
            return;
        }

        // Mostrar historial si hay intentos
        historySection.style.display = 'block';

        const reversedAttempts = [...gameState.attempts].reverse();

        reversedAttempts.forEach(attempt => {
            const attemptDiv = document.createElement('div');
            let className = 'attempt-result ';
            let icon = '';
            let extraText = '';

            if (attempt.correct) {
                className += 'correct';
                icon = '<i class="fas fa-check text-success"></i>';
            } else if (attempt.franchise_match) {
                className += 'franchise';
                icon = '<i class="fas fa-exclamation-triangle text-warning"></i>';
                const franchiseName = attempt.franchise_name || 'Franquicia correcta';
                extraText = `<br><small class="text-muted">${franchiseName}</small>`;
            } else if (attempt.type === 'skipped') {
                className += 'skipped';
                icon = '<i class="fas fa-forward text-muted"></i>';
            } else {
                className += 'wrong';
                icon = '<i class="fas fa-times text-danger"></i>';
            }

            attemptDiv.className = className;
            attemptDiv.innerHTML = `
                <div class="result-icon">${icon}</div>
                <div class="flex-grow-1">
                    <strong>Intento ${attempt.attempt}:</strong> ${attempt.game_name}
                    <span class="badge bg-success ms-2" title="IGDB"><i class="fas fa-database"></i></span>
                    ${extraText}
                </div>
            `;

            historyContainer.appendChild(attemptDiv);
        });
    }

    nextAttempt() {
        this.updateScreenshot();
        this.updateGameInfo();
        this.updateRemainingAttempts();
        this.clearSearchInput();
        this.updateAttemptIndicators();
    }

    updateRemainingAttempts() {
        const remainingDiv = document.getElementById('remaining-attempts');

        if (remainingDiv && !this.gameEnded) {
            // Siempre empezar con 6 intentos
            const remaining = 6 - this.currentAttempt + 1;

            if (remaining > 0) {
                remainingDiv.innerHTML = `¡Te quedan ${remaining} intentos!`;
            }
        }
    }

    handleWin(result) {
        this.gameEnded = true;

        // Actualizar el mensaje de intentos restantes
        const remainingDiv = document.getElementById('remaining-attempts');
        if (remainingDiv) {
            if (result.guessed_it) {
                remainingDiv.innerHTML = `
                    <div class="alert alert-success text-center mb-0">
                        <h4><i class="fas fa-star me-2"></i>GUESSED IT!</h4>
                        <p class="mb-0">¡Acertaste en el primer intento!</p>
                    </div>
                `;
            } else {
                remainingDiv.innerHTML = `
                    <div class="alert alert-success text-center mb-0">
                        <h4><i class="fas fa-trophy me-2"></i>¡Ganaste!</h4>
                        <p class="mb-0">La respuesta correcta era: <strong>${result.game_name}</strong></p>
                    </div>
                `;
            }
        }

        const attemptsContainer = document.querySelector('.attempts-indicator');
        if (attemptsContainer) {
            attemptsContainer.classList.add('game-won');
        }

        for (let i = 1; i <= this.maxAttempts; i++) {
            const circle = document.getElementById(`attempt-${i}`);
            if (circle && !circle.classList.contains('franchise')) {
                circle.classList.remove('current', 'wrong', 'skipped');
                circle.classList.add('correct');
                circle.style.backgroundColor = '#28a745';
                circle.style.borderColor = '#28a745';
                circle.style.cursor = 'pointer';
            }
        }

        this.disableGameControls();
        this.showEndGameButtons();
    }

    handleLose() {
        this.gameEnded = true;

        // Actualizar el mensaje de intentos restantes
        const remainingDiv = document.getElementById('remaining-attempts');
        if (remainingDiv) {
            remainingDiv.innerHTML = `
                <div class="alert alert-danger text-center mb-0">
                    <h4><i class="fas fa-skull me-2"></i>¡Perdiste!</h4>
                    <p class="mb-0">La respuesta correcta era: <strong>${gameData.title}</strong></p>
                </div>
            `;
        }

        const attemptsContainer = document.querySelector('.attempts-indicator');
        if (attemptsContainer) {
            attemptsContainer.classList.add('game-lost');
        }

        for (let i = 1; i <= this.maxAttempts; i++) {
            const circle = document.getElementById(`attempt-${i}`);
            if (circle && !circle.classList.contains('correct') && !circle.classList.contains('franchise')) {
                circle.classList.remove('current');
                circle.classList.add('wrong');
            }
        }

        this.disableGameControls();
        this.showEndGameButtons();
    }

    clearSearchInput() {
        const searchInput = document.getElementById('game-search');
        if (searchInput) {
            searchInput.value = '';
        }
        this.selectedGame = null;
        this.updateSubmitButton();
        this.hideSuggestions();
    }

    showEndGameButtons() {
        const gameEndedDiv = document.querySelector('.game-ended');
        if (!gameEndedDiv) {
            const gameArea = document.getElementById('game-area');
            const endDiv = document.createElement('div');
            endDiv.className = 'game-ended text-center mt-4';
            endDiv.innerHTML = `
                <div class="d-flex justify-content-center gap-3">
                    <button class="btn btn-outline-secondary" onclick="showOtherDays()">
                        <i class="fas fa-calendar me-2"></i>Ir a días anteriores
                    </button>
                </div>
            `;

            gameArea.appendChild(endDiv);
        }
    }

    disableGameControls() {
        const searchInput = document.getElementById('game-search');
        const submitBtn = document.getElementById('submit-btn');
        const skipBtn = document.getElementById('skip-btn');

        if (searchInput) searchInput.disabled = true;
        if (submitBtn) submitBtn.disabled = true;
        if (skipBtn) skipBtn.disabled = true;

        this.hideSuggestions();
    }

    startCountdown() {
        const countdownDisplay = document.getElementById('countdown-display');
        if (!countdownDisplay) return;

        const updateCountdown = () => {
            try {
                const now = new Date();
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                tomorrow.setHours(0, 0, 0, 0);

                const timeLeft = tomorrow.getTime() - now.getTime();

                if (timeLeft <= 0) {
                    countdownDisplay.textContent = 'Un nuevo juego disponible - Recarga la página';
                    return;
                }

                const hours = Math.floor(timeLeft / (1000 * 60 * 60));
                const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

                countdownDisplay.textContent = `Un nuevo juego en ${hours.toString().padStart(2, '0')}h ${minutes.toString().padStart(2, '0')}m ${seconds.toString().padStart(2, '0')}s`;
            } catch (error) {
                console.error('Error en countdown:', error);
                countdownDisplay.textContent = 'Error calculando tiempo';
            }
        };

        updateCountdown();
        setInterval(updateCountdown, 1000);
    }

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
    }
}

// Función global para navegar a un intento específico
function navigateToAttempt(attemptNum) {
    const game = window.guessItYetGame;
    if (!game) return;

    const maxAvailable = game.gameEnded ? game.maxAttempts : game.currentAttempt;

    if (attemptNum >= 1 && attemptNum <= maxAvailable) {
        game.currentViewingAttempt = attemptNum;
        game.showScreenshotForAttempt(attemptNum);
        game.updateGameInfo();
        game.updateAttemptIndicators();
    }
}

// Función para generar nuevo juego de prueba con IGDB
async function generateNewTestGame() {
    const button = event.target;
    const originalText = button.innerHTML;

    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generando...';
    button.disabled = true;

    try {
        const response = await fetch('/nuevo-juego-igdb/', {
            method: 'GET'
        });

        if (response.ok) {
            window.location.reload();
        } else {
            alert('Error al generar nuevo juego');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    } catch (error) {
        console.error('Error:', error);
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Funciones globales adicionales
function showOtherDays() {
    alert('Función "Ir a días anteriores" estará disponible próximamente');
}

// Inicializar el juego cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    if (typeof gameState === 'undefined' || typeof gameData === 'undefined' || typeof screenshots === 'undefined') {
        console.error('Variables del juego no están definidas');
        return;
    }

    const game = new GuessItYetGame();
    window.guessItYetGame = game;

    console.log('Juego IGDB inicializado correctamente');
});