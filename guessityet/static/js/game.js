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
        this.gameEnded = gameState.won || gameState.lost;
        this.currentViewingAttempt = this.currentAttempt;

        this.init();
    }

    calculateMaxAttempts() {
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
        this.setupScreenshotNavigation();
        this.updateScreenshot();
        this.updateGameInfo();
        this.loadExistingAttempts();
        this.setupHistoryToggle();
        this.startCountdown();

        if (this.gameEnded) {
            this.disableGameControls();
            this.minimizeHistoryForEndedGame();
        } else {
            this.ensureHistoryVisible();
        }

        console.log('✅ Juego inicializado correctamente');
    }

    setupEventListeners() {
        const searchInput = document.getElementById('game-search');
        const submitBtn = document.getElementById('submit-btn');
        const skipBtn = document.getElementById('skip-btn');

        console.log('🔍 Elementos encontrados:', {
            searchInput: !!searchInput,
            submitBtn: !!submitBtn,
            skipBtn: !!skipBtn
        });

        if (searchInput) {
            console.log('📝 Configurando eventos de búsqueda...');

            searchInput.addEventListener('input', (e) => {
                console.log('📝 Evento input disparado');
                this.handleSearchInput(e);
            });

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && this.selectedGame) {
                    console.log('⏎ Enter presionado con juego seleccionado');
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
        } else {
            console.error('❌ No se encontró el botón de envío');
        }

        if (skipBtn) {
            skipBtn.addEventListener('click', () => {
                console.log('⏭️ Botón saltar clicked');
                this.skipTurn();
            });
        } else {
            console.error('❌ No se encontró el botón de saltar');
        }
    }

    setupScreenshotNavigation() {
        const screenshotContainer = document.querySelector('.screenshot-container');
        if (!screenshotContainer) return;

        // Crear controles de navegación
        const navControls = document.createElement('div');
        navControls.className = 'screenshot-nav-controls';
        navControls.innerHTML = `
            <button class="nav-btn prev-btn" id="prev-screenshot">
                <i class="fas fa-chevron-left"></i>
            </button>
            <span class="nav-indicator" id="screenshot-indicator">1/${this.maxAttempts}</span>
            <button class="nav-btn next-btn" id="next-screenshot">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        screenshotContainer.appendChild(navControls);

        // Añadir estilos inline
        const style = document.createElement('style');
        style.textContent = `
            .screenshot-nav-controls {
                position: absolute;
                bottom: 15px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.8);
                padding: 8px 15px;
                border-radius: 25px;
                display: flex;
                gap: 15px;
                align-items: center;
                z-index: 10;
                backdrop-filter: blur(5px);
            }
            .nav-btn {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                width: 35px;
                height: 35px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .nav-btn:hover:not(:disabled) {
                background: rgba(255,255,255,0.4);
                transform: scale(1.1);
            }
            .nav-btn:disabled {
                opacity: 0.3;
                cursor: not-allowed;
            }
            .nav-indicator {
                color: white;
                font-size: 14px;
                font-weight: bold;
                min-width: 50px;
                text-align: center;
            }
        `;
        document.head.appendChild(style);

        // Event listeners
        document.getElementById('prev-screenshot').addEventListener('click', () => {
            this.navigateScreenshot(-1);
        });

        document.getElementById('next-screenshot').addEventListener('click', () => {
            this.navigateScreenshot(1);
        });

        this.updateNavigationControls();
    }

    navigateScreenshot(direction) {
        const newAttempt = this.currentViewingAttempt + direction;
        const maxAvailable = this.gameEnded ? this.maxAttempts : this.currentAttempt;

        if (newAttempt >= 1 && newAttempt <= maxAvailable) {
            this.currentViewingAttempt = newAttempt;
            this.showScreenshotForAttempt(this.currentViewingAttempt);
            this.updateNavigationControls();
            this.updateGameInfoForViewing();
            this.updateAttemptIndicators(); // Actualizar los indicadores para mostrar la negrita
        }
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
    }

    updateNavigationControls() {
        const indicator = document.getElementById('screenshot-indicator');
        const prevBtn = document.getElementById('prev-screenshot');
        const nextBtn = document.getElementById('next-screenshot');

        if (!indicator) return;

        const maxAvailable = this.gameEnded ? this.maxAttempts : this.currentAttempt;
        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';

        if (this.currentViewingAttempt === this.maxAttempts && hasGif) {
            indicator.textContent = `GIF (${this.currentViewingAttempt}/${maxAvailable})`;
        } else {
            indicator.textContent = `${this.currentViewingAttempt}/${maxAvailable}`;
        }

        if (prevBtn) prevBtn.disabled = this.currentViewingAttempt <= 1;
        if (nextBtn) nextBtn.disabled = this.currentViewingAttempt >= maxAvailable;
    }

    updateGameInfoForViewing() {
        const infoContent = document.getElementById('info-content');
        const hasGif = gameData.gif_path && gameData.gif_path.trim() !== '';
        const isLastAttempt = this.currentViewingAttempt === this.maxAttempts;

        let infoText = '';

        // Solo mostrar "GIF del juego" si es el último intento con GIF
        if (isLastAttempt && hasGif) {
            infoText = 'GIF del juego';
        }

        // Información adicional según el intento - SIN MOSTRAR "Imagen X"
        let additionalInfo = [];

        if (this.currentViewingAttempt === 1) {
            // Para la imagen 1, no mostrar información extra
            infoText = '';
        } else {
            switch(this.currentViewingAttempt) {
                case 2:
                    if (gameData.genres) {
                        additionalInfo.push(`Géneros: ${gameData.genres}`);
                    }
                    break;
                case 3:
                    if (gameData.platforms) {
                        additionalInfo.push(`Plataformas: ${gameData.platforms}`);
                    }
                    break;
                case 4:
                    if (gameData.metacritic) {
                        additionalInfo.push(`Rating: ${gameData.metacritic}/100`);
                    }
                    break;
                case 5:
                    if (gameData.release_year) {
                        additionalInfo.push(`Año: ${gameData.release_year}`);
                    }
                    break;
                case 6:
                    if (gameData.developer) {
                        additionalInfo.push(`Desarrollador: ${gameData.developer}`);
                    }
                    if (gameData.franchise_name) {
                        additionalInfo.push(`Franquicia: ${gameData.franchise_name}`);
                    }
                    break;
            }
        }

        // Combinar información
        if (additionalInfo.length > 0) {
            if (infoText) {
                infoText += ' • ' + additionalInfo.join(' • ');
            } else {
                infoText = additionalInfo.join(' • ');
            }
        }

        if (infoContent) {
            infoContent.innerHTML = infoText;
        }
    }

    handleSearchInput(e) {
        const query = e.target.value.trim();
        console.log('🔍 Texto de búsqueda:', query);

        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        this.selectedGame = null;
        this.updateSubmitButton();

        if (query.length < 2) {
            console.log('📝 Query muy corto, ocultando sugerencias');
            this.hideSuggestions();
            return;
        }

        console.log('📝 Mostrando loading y preparando búsqueda...');
        this.showLoading();

        this.searchTimeout = setTimeout(() => {
            console.log('⏰ Ejecutando búsqueda después del timeout');
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
            const url = `/guessityet/search-games/?q=${encodeURIComponent(query)}&service=igdb&limit=25`;
            console.log('📡 URL de búsqueda:', url);

            const response = await fetch(url);
            console.log('📨 Respuesta recibida:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('📊 Datos recibidos:', data);

            if (data.games && data.games.length > 0) {
                console.log('💡 Primeros resultados:', data.games.slice(0, 3));
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
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = '';

        games.forEach(game => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';

            // Extraer año - adaptado a la estructura de datos de IGDB del backend
            let releaseYear = '';
            if (game.first_release_date) {
                // IGDB envía timestamp Unix
                if (typeof game.first_release_date === 'number') {
                    releaseYear = new Date(game.first_release_date * 1000).getFullYear();
                }
            } else if (game.released) {
                // Fallback para otros formatos
                if (typeof game.released === 'number') {
                    releaseYear = new Date(game.released * 1000).getFullYear();
                } else {
                    const year = new Date(game.released).getFullYear();
                    if (!isNaN(year)) {
                        releaseYear = year;
                    }
                }
            }

            // Información adicional con franquicia y año
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
        console.log('✅ Juego seleccionado:', game);
        this.selectedGame = { ...game, service: 'igdb' };

        const searchInput = document.getElementById('game-search');
        if (searchInput) {
            searchInput.value = game.name;
            console.log('📝 Input actualizado con:', game.name);
        }

        this.hideSuggestions();
        this.updateSubmitButton();
        console.log('🔘 Juego listo para enviar');
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

            const result = await response.json();

            if (result.success) {
                this.handleGuessResult(result);
            } else {
                alert('Error al procesar la respuesta');
            }
        } catch (error) {
            alert('Error de conexión');
        }
    }

    async skipTurn() {
        try {
            const response = await fetch('/guessityet/skip-turn/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const result = await response.json();

            if (result.success) {
                this.handleSkipResult(result);
            } else {
                alert('Error al saltar turno');
            }
        } catch (error) {
            alert('Error de conexión');
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
                circle.classList.remove('current', 'correct', 'wrong', 'franchise', 'skipped');

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
        this.updateNavigationControls();
        this.updateAttemptIndicators(); // Asegurar que se actualicen los indicadores
    }

    updateGameInfo() {
        this.updateGameInfoForViewing();
    }

    addAttemptToHistory(attempt) {
        const historyContainer = document.getElementById('attempts-history');
        if (!historyContainer) return;

        if (!this.gameEnded) {
            historyContainer.style.display = 'block';
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

        historyContainer.appendChild(attemptDiv);
    }

    setupHistoryToggle() {
        const gameArea = document.getElementById('game-area');
        if (!gameArea) return;

        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'history-toggle-btn';
        toggleBtn.className = 'btn btn-outline-primary mt-3';
        toggleBtn.innerHTML = '<i class="fas fa-list me-2"></i>Mostrar intentos de la partida';
        toggleBtn.style.display = 'none';

        toggleBtn.addEventListener('click', () => {
            this.toggleHistory();
        });

        const countdown = document.querySelector('.countdown-timer');
        if (countdown) {
            gameArea.insertBefore(toggleBtn, countdown);
        } else {
            gameArea.appendChild(toggleBtn);
        }
    }

    toggleHistory() {
        const historyContainer = document.getElementById('attempts-history');
        const toggleBtn = document.getElementById('history-toggle-btn');

        if (!historyContainer || !toggleBtn) return;

        if (historyContainer.style.display === 'none') {
            historyContainer.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fas fa-eye-slash me-2"></i>Ocultar intentos de la partida';
        } else {
            historyContainer.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-list me-2"></i>Mostrar intentos de la partida';
        }
    }

    minimizeHistoryForEndedGame() {
        const historyContainer = document.getElementById('attempts-history');
        const toggleBtn = document.getElementById('history-toggle-btn');

        if (historyContainer) {
            historyContainer.style.display = 'none';
        }

        if (toggleBtn) {
            toggleBtn.style.display = 'inline-block';
        }
    }

    ensureHistoryVisible() {
        const historyContainer = document.getElementById('attempts-history');
        const toggleBtn = document.getElementById('history-toggle-btn');

        if (historyContainer) {
            historyContainer.style.display = 'block';
        }

        if (toggleBtn) {
            toggleBtn.style.display = 'none';
        }
    }

    loadExistingAttempts() {
        const historyContainer = document.getElementById('attempts-history');
        if (!historyContainer) return;

        historyContainer.innerHTML = '';

        if (!gameState.attempts || gameState.attempts.length === 0) {
            if (!this.gameEnded) {
                historyContainer.style.display = 'block';
            }
            return;
        }

        gameState.attempts.forEach(attempt => {
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
        const remaining = this.maxAttempts + 1 - this.currentAttempt;

        if (remainingDiv && remaining > 0) {
            remainingDiv.textContent = `¡Te quedan ${remaining} intentos!`;
        } else if (remainingDiv) {
            remainingDiv.textContent = '';
        }
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

    handleWin(result) {
        this.gameEnded = true;

        const attemptsContainer = document.querySelector('.attempts-indicator');
        if (attemptsContainer) {
            attemptsContainer.classList.add('game-won');
        }

        for (let i = 1; i <= this.maxAttempts; i++) {
            const circle = document.getElementById(`attempt-${i}`);
            if (circle && !circle.classList.contains('correct') && !circle.classList.contains('franchise')) {
                circle.classList.remove('current', 'wrong', 'skipped');
                circle.classList.add('correct');
            }
        }

        this.updateNavigationControls();

        if (result.guessed_it) {
            this.showGuessedItMessage();
        }
        this.showWinMessage(result.game_name);
        this.disableGameControls();
        this.minimizeHistoryForEndedGame();
        this.showEndGameButtons();
    }

    handleLose() {
        this.gameEnded = true;

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

        this.updateNavigationControls();

        this.showLoseMessage();
        this.disableGameControls();
        this.minimizeHistoryForEndedGame();
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
            ${gameData.franchise_name ? `<p class="mb-0">Franquicia: <strong>${gameData.franchise_name}</strong></p>` : ''}
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
            ${gameData.franchise_name ? `<p class="mb-0">Franquicia: <strong>${gameData.franchise_name}</strong></p>` : ''}
            <p class="mb-0">¡Más suerte la próxima vez!</p>
        `;

        gameArea.appendChild(loseDiv);
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

            const toggleBtn = document.getElementById('history-toggle-btn');
            if (toggleBtn) {
                gameArea.insertBefore(endDiv, toggleBtn);
            } else {
                gameArea.appendChild(endDiv);
            }
        }
    }

    startCountdown() {
        const countdownDisplay = document.getElementById('countdown-display');
        if (!countdownDisplay) return;

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

        return '';
    }
}

// Funciones globales
function toggleAttemptsHistory() {
    const game = window.guessItYetGame;
    if (game) {
        game.toggleHistory();
    }
}

function showOtherDays() {
    alert('Función "Ir a días anteriores" estará disponible próximamente');
}

// Inicializar el juego
document.addEventListener('DOMContentLoaded', function() {
    if (typeof gameState === 'undefined' || typeof gameData === 'undefined' || typeof screenshots === 'undefined') {
        console.error('Variables del juego no están definidas');
        return;
    }

    const game = new GuessItYetGame();
    window.guessItYetGame = game;

    console.log('✅ Juego IGDB inicializado correctamente');
});