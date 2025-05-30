// Lógica principal del juego GuessItYet - Solo IGDB
console.log('🎮 Cargando GuessItYet Game (IGDB)...');

class GuessItYetGame {
    constructor() {
        console.log('🔧 Inicializando juego...');
        console.log('📊 Estado del juego:', gameState);
        console.log('🎯 Datos del juego:', gameData);
        console.log('📸 Screenshots:', screenshots);

        this.searchTimeout = null;
        this.selectedGame = null;
        this.currentAttempt = gameState.current_attempt || 1;
        this.maxAttempts = this.calculateMaxAttempts();

        this.init();
    }

    calculateMaxAttempts() {
        // Si hay GIF disponible: 5 capturas + 1 GIF = 6 intentos
        // Si no hay GIF: 6 capturas = 6 intentos
        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';
        const maxAttempts = hasGif ? 6 : Math.min(screenshots.length, 6);

        console.log(`🎬 GIF disponible: ${hasGif ? 'Sí' : 'No'}`);
        console.log(`📸 Capturas disponibles: ${screenshots.length}`);
        console.log(`🎯 Máximo de intentos: ${maxAttempts}`);

        return maxAttempts;
    }

    init() {
        console.log('⚙️ Configurando event listeners...');
        this.setupEventListeners();
        this.updateAttemptIndicators();
        this.updateScreenshot();
        this.updateGameInfo();
        this.startCountdown();

        // Si el juego ya terminó, deshabilitar controles
        if (gameState.won || gameState.lost) {
            this.disableGameControls();
        }

        console.log('✅ Juego inicializado correctamente');
    }

    setupEventListeners() {
        const searchInput = document.getElementById('game-search');
        const submitBtn = document.getElementById('submit-btn');
        const skipBtn = document.getElementById('skip-btn');

        console.log('🔍 Configurando búsqueda...', { searchInput, submitBtn, skipBtn });

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e);
            });

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && this.selectedGame) {
                    console.log('⏎ Enter presionado, enviando respuesta');
                    this.submitGuess();
                }
            });

            document.addEventListener('click', (e) => {
                if (!e.target.closest('.search-container')) {
                    this.hideSuggestions();
                }
            });
        } else {
            console.error('❌ No se encontró el input de búsqueda');
        }

        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                console.log('🎯 Botón enviar clicked');
                this.submitGuess();
            });
        }

        if (skipBtn) {
            skipBtn.addEventListener('click', () => {
                console.log('⏭️ Botón saltar clicked');
                this.skipTurn();
            });
        }
    }

    handleSearchInput(e) {
        const query = e.target.value.trim();
        console.log('🔍 Buscando:', query);

        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        this.selectedGame = null;
        this.updateSubmitButton();

        if (query.length < 2) {
            this.hideSuggestions();
            return;
        }

        // Mostrar loading
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
        console.log('🌐 Buscando en IGDB:', query);

        try {
            // Aumentar significativamente el límite de resultados
            const url = `/guessityet/search-games/?q=${encodeURIComponent(query)}&service=igdb&limit=25`;
            console.log('📡 URL de búsqueda:', url);

            const response = await fetch(url);
            console.log('📨 Respuesta recibida:', response.status);

            const data = await response.json();
            console.log('📊 Datos recibidos:', data);

            if (data.games && data.games.length > 0) {
                this.showSuggestions(data.games);
            } else {
                console.log('😕 No se encontraron juegos');
                this.showNoResults();
            }
        } catch (error) {
            console.error('❌ Error buscando juegos:', error);
            this.showError();
        }
    }

    showSuggestions(games) {
        console.log('💡 Mostrando sugerencias:', games.length);
        const suggestionsContainer = document.getElementById('search-suggestions');

        if (!suggestionsContainer) {
            console.error('❌ No se encontró el contenedor de sugerencias');
            return;
        }

        suggestionsContainer.innerHTML = '';

        // Mostrar todos los juegos encontrados (hasta 25)
        games.forEach(game => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';

            // Solo mostrar título del juego limpio
            suggestionItem.innerHTML = `
                <div class="flex-grow-1">
                    <div class="fw-bold">${game.name}</div>
                </div>
                <div class="service-indicator">
                    <i class="fas fa-database text-success" title="IGDB"></i>
                </div>
            `;

            suggestionItem.addEventListener('click', () => {
                console.log('🎮 Juego seleccionado:', game.name);
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
        console.log('✅ Juego seleccionado:', game);
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
            console.log('🔘 Botón enviar actualizado:', !this.selectedGame ? 'deshabilitado' : 'habilitado');
        }
    }

    async submitGuess() {
        if (!this.selectedGame) {
            console.log('⚠️ No hay juego seleccionado');
            return;
        }

        console.log('🚀 Enviando respuesta:', this.selectedGame);

        try {
            const response = await fetch('/guessityet/submit-guess/', {
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

            console.log('📨 Respuesta del servidor:', response.status);
            const result = await response.json();
            console.log('📊 Resultado:', result);

            if (result.success) {
                this.handleGuessResult(result);
            } else {
                console.error('❌ Error en respuesta:', result);
                alert('Error al procesar la respuesta');
            }
        } catch (error) {
            console.error('❌ Error enviando respuesta:', error);
            alert('Error de conexión');
        }
    }

    async skipTurn() {
        console.log('⏭️ Saltando turno...');

        try {
            const response = await fetch('/guessityet/skip-turn/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            console.log('📨 Respuesta skip:', response.status);
            const result = await response.json();
            console.log('📊 Resultado skip:', result);

            if (result.success) {
                this.handleSkipResult(result);
            } else {
                console.error('❌ Error saltando:', result);
                alert('Error al saltar turno');
            }
        } catch (error) {
            console.error('❌ Error saltando turno:', error);
            alert('Error de conexión');
        }
    }

    handleGuessResult(result) {
        console.log('🎯 Procesando resultado de respuesta:', result);

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
        console.log('⏭️ Procesando resultado de skip:', result);

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
        console.log('🔄 Actualizando indicadores de intentos');

        for (let i = 1; i <= 6; i++) {
            const circle = document.getElementById(`attempt-${i}`);
            if (circle) {
                circle.classList.remove('current', 'correct', 'wrong', 'franchise', 'skipped');

                // Mostrar solo los círculos necesarios según el tipo de juego
                if (i > this.maxAttempts) {
                    circle.style.display = 'none';
                } else {
                    circle.style.display = 'flex';

                    if (i === this.currentAttempt && !gameState.won && !gameState.lost) {
                        circle.classList.add('current');
                    }
                }
            }
        }

        // Aplicar estados de intentos anteriores
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
        console.log('📸 Actualizando screenshot para intento:', this.currentAttempt);
        const screenshotImg = document.getElementById('current-screenshot');
        const contentIndicator = document.getElementById('content-type-indicator');

        // Verificar disponibilidad de GIF
        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';
        const isLastAttempt = this.currentAttempt === this.maxAttempts;

        console.log(`🎬 GIF disponible: ${hasGif}, último intento: ${isLastAttempt}, intento actual: ${this.currentAttempt}`);

        if (isLastAttempt && hasGif) {
            // Mostrar GIF en el último intento si está disponible
            console.log('🎬 Mostrando GIF en último intento');
            if (screenshotImg) {
                screenshotImg.src = `/media/${gameData.gif_path}`;
                screenshotImg.alt = 'GIF del juego';
            }
            // Mostrar indicador de GIF
            if (contentIndicator) {
                contentIndicator.style.display = 'block';
            }
        } else {
            // Mostrar captura normal según el intento actual
            const screenshot = screenshots.find(s => s.difficulty === this.currentAttempt);
            if (screenshot && screenshotImg) {
                console.log('🖼️ Cambiando a captura:', screenshot.url, 'Dificultad:', screenshot.difficulty);
                screenshotImg.src = screenshot.url;
                screenshotImg.alt = `Screenshot del juego - Nivel ${this.currentAttempt}`;
            } else {
                console.error('❌ No se encontró captura para dificultad:', this.currentAttempt);
                // Fallback: usar la última captura disponible
                const fallbackScreenshot = screenshots[screenshots.length - 1];
                if (fallbackScreenshot && screenshotImg) {
                    console.log('🔄 Usando captura de fallback:', fallbackScreenshot.url);
                    screenshotImg.src = fallbackScreenshot.url;
                    screenshotImg.alt = 'Screenshot del juego';
                }
            }
            // Ocultar indicador de GIF
            if (contentIndicator) {
                contentIndicator.style.display = 'none';
            }
        }
    }

    updateGameInfo() {
        console.log('ℹ️ Actualizando información del juego para intento:', this.currentAttempt);
        const infoContent = document.getElementById('info-content');
        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';
        const isLastAttempt = this.currentAttempt === this.maxAttempts;

        let infoText = '';

        if (isLastAttempt && hasGif) {
            infoText = `<i class="fas fa-film me-1"></i>GIF del juego`;
        } else {
            infoText = `<i class="fas fa-eye me-1"></i>Imagen ${this.currentAttempt}`;
        }

        // Mostrar información adicional según el intento
        switch(this.currentAttempt) {
            case 2:
                if (gameData.metacritic) {
                    infoText += `<br><i class="fas fa-star me-1"></i>Rating: ${gameData.metacritic}/100`;
                }
                break;
            case 3:
                if (gameData.platforms) {
                    infoText += `<br><i class="fas fa-desktop me-1"></i>${gameData.platforms}`;
                }
                break;
            case 4:
                if (gameData.genres) {
                    infoText += `<br><i class="fas fa-tags me-1"></i>${gameData.genres}`;
                }
                break;
            case 5:
                if (gameData.release_year) {
                    infoText += `<br><i class="fas fa-calendar me-1"></i>Año: ${gameData.release_year}`;
                }
                break;
            case 6:
                if (gameData.developer) {
                    infoText += `<br><i class="fas fa-code me-1"></i>${gameData.developer}`;
                }
                // Mostrar franquicia en el último intento si está disponible
                if (gameData.franchise_name) {
                    infoText += `<br><i class="fas fa-crown me-1"></i>Franquicia: ${gameData.franchise_name}`;
                }
                break;
        }

        if (infoContent) {
            infoContent.innerHTML = infoText;
        }
    }

    addAttemptToHistory(attempt) {
        console.log('📝 Añadiendo intento al historial:', attempt);
        const historyContainer = document.getElementById('attempts-history');

        if (!historyContainer) {
            console.error('❌ No se encontró el contenedor de historial');
            return;
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
            extraText = `<br><small class="text-muted">✨ ${franchiseName}</small>`;
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
    }

    nextAttempt() {
        console.log('➡️ Avanzando al siguiente intento:', this.currentAttempt);
        this.updateScreenshot();
        this.updateGameInfo();
        this.updateRemainingAttempts();
        this.clearSearchInput();
        this.updateAttemptIndicators();
    }

    updateRemainingAttempts() {
        const remainingDiv = document.getElementById('remaining-attempts');
        const remaining = this.maxAttempts + 1 - this.currentAttempt;

        if (remainingDiv && remaining > 0) {
            remainingDiv.textContent = `¡Te quedan ${remaining} intentos!`;
        } else if (remainingDiv) {
            remainingDiv.textContent = '';
        }
    }

    clearSearchInput() {
        console.log('🧹 Limpiando input de búsqueda');
        const searchInput = document.getElementById('game-search');
        if (searchInput) {
            searchInput.value = '';
        }
        this.selectedGame = null;
        this.updateSubmitButton();
        this.hideSuggestions();
    }

    handleWin(result) {
        console.log('🏆 ¡VICTORIA!', result);

        const attemptsContainer = document.querySelector('.attempts-indicator');
        if (attemptsContainer) {
            attemptsContainer.classList.add('game-won');
        }

        // Colorear círculos restantes de verde
        for (let i = 1; i <= this.maxAttempts; i++) {
            const circle = document.getElementById(`attempt-${i}`);
            if (circle && !circle.classList.contains('correct') && !circle.classList.contains('franchise')) {
                circle.classList.remove('current', 'wrong', 'skipped');
                circle.classList.add('correct');
            }
        }

        if (result.guessed_it) {
            this.showGuessedItMessage();
        }
        this.showWinMessage(result.game_name);
        this.disableGameControls();
        this.showEndGameButtons();
    }

    handleLose() {
        console.log('💀 Derrota...');

        const attemptsContainer = document.querySelector('.attempts-indicator');
        if (attemptsContainer) {
            attemptsContainer.classList.add('game-lost');
        }

        // Colorear círculos restantes de rojo
        for (let i = 1; i <= this.maxAttempts; i++) {
            const circle = document.getElementById(`attempt-${i}`);
            if (circle && !circle.classList.contains('correct') && !circle.classList.contains('franchise')) {
                circle.classList.remove('current');
                circle.classList.add('wrong');
            }
        }

        this.showLoseMessage();
        this.disableGameControls();
        this.showEndGameButtons();
    }

    showGuessedItMessage() {
        const gameArea = document.getElementById('game-area');
        const guessedItDiv = document.createElement('div');
        guessedItDiv.className = 'guessed-it';
        guessedItDiv.innerHTML = '<i class="fas fa-star me-2"></i>¡GUESSED IT!';

        gameArea.insertBefore(guessedItDiv, gameArea.firstChild);
    }

    showWinMessage(gameName) {
        const gameArea = document.getElementById('game-area');
        const winDiv = document.createElement('div');
        winDiv.className = 'alert alert-success text-center mt-3';
        winDiv.innerHTML = `
            <h4><i class="fas fa-trophy me-2"></i>¡Ganaste!</h4>
            <p class="mb-0">La respuesta correcta era: <strong>${gameName}</strong></p>
            ${gameData.franchise_name ? `<p class="mb-0"><i class="fas fa-crown me-1"></i>Franquicia: <strong>${gameData.franchise_name}</strong></p>` : ''}
        `;

        gameArea.appendChild(winDiv);
    }

    showLoseMessage() {
        const gameArea = document.getElementById('game-area');
        const loseDiv = document.createElement('div');
        loseDiv.className = 'alert alert-danger text-center mt-3';
        loseDiv.innerHTML = `
            <h4><i class="fas fa-skull me-2"></i>¡Perdiste!</h4>
            <p class="mb-0">La respuesta correcta era: <strong>${gameData.title}</strong></p>
            ${gameData.franchise_name ? `<p class="mb-0"><i class="fas fa-crown me-1"></i>Franquicia: <strong>${gameData.franchise_name}</strong></p>` : ''}
            <p class="mb-0">¡Más suerte la próxima vez!</p>
        `;

        gameArea.appendChild(loseDiv);
    }

    disableGameControls() {
        console.log('🚫 Deshabilitando controles del juego');
        const searchInput = document.getElementById('game-search');
        const submitBtn = document.getElementById('submit-btn');
        const skipBtn = document.getElementById('skip-btn');

        if (searchInput) searchInput.disabled = true;
        if (submitBtn) submitBtn.disabled = true;
        if (skipBtn) skipBtn.disabled = true;

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
                    <button class="btn btn-outline-primary" onclick="toggleAttemptsHistory()">
                        <i class="fas fa-list me-2"></i>Mostrar Intentos
                    </button>
                    <button class="btn btn-outline-secondary" onclick="showOtherDays()">
                        <i class="fas fa-calendar me-2"></i>Jugar Otros Días
                    </button>
                </div>
            `;

            gameArea.appendChild(endDiv);
        }
    }

    startCountdown() {
        console.log('⏰ Iniciando countdown');
        const countdownDisplay = document.getElementById('countdown-display');

        if (!countdownDisplay) {
            console.error('❌ No se encontró el display del countdown');
            return;
        }

        const updateCountdown = () => {
            const now = new Date();
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            tomorrow.setHours(0, 0, 0, 0);

            const timeLeft = tomorrow.getTime() - now.getTime();

            if (timeLeft <= 0) {
                countdownDisplay.textContent = 'Nuevo juego disponible - Recarga la página';
                return;
            }

            const hours = Math.floor(timeLeft / (1000 * 60 * 60));
            const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

            countdownDisplay.textContent = `Nuevo juego en: ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
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

        console.error('❌ No se pudo obtener el token CSRF');
        return '';
    }
}

// Funciones globales
function toggleAttemptsHistory() {
    const historyContainer = document.getElementById('attempts-history');
    if (historyContainer.style.display === 'none') {
        historyContainer.style.display = 'block';
    } else {
        historyContainer.style.display = 'none';
    }
}

function showOtherDays() {
    alert('Función "Jugar Otros Días" estará disponible próximamente');
}

// Inicializar el juego
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM cargado, inicializando juego IGDB...');

    if (typeof gameState === 'undefined') {
        console.error('❌ gameState no está definido');
        return;
    }

    if (typeof gameData === 'undefined') {
        console.error('❌ gameData no está definido');
        return;
    }

    if (typeof screenshots === 'undefined') {
        console.error('❌ screenshots no está definido');
        return;
    }

    const game = new GuessItYetGame();
    window.guessItYetGame = game;

    console.log('✅ Juego IGDB inicializado correctamente');
    console.log('👑 Franquicia:', gameData.franchise_name || 'No detectada');
    console.log('📸 Capturas disponibles:', screenshots.length);
    console.log('🎬 GIF disponible:', gameData.gif_path ? 'Sí' : 'No');
});