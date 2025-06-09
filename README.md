# Guess It Yet? 🎮

<p align="center">
  <img src="media/logo-documentacion.png" alt="Guess It Yet Logo" width="300"/>
</p>


Un juego diario de adivinanza de videojuegos que desafía a los jugadores a identificar títulos a través de capturas de pantalla progresivamente más reveladoras.

## ¿Qué es Guess It Yet?

Guess It Yet es una aplicación web diseñada como un juego diario donde los jugadores intentan adivinar un videojuego seleccionado aleatoriamente de la base de datos de IGDB. El concepto es simple pero adictivo: cada día se presenta un nuevo juego con una serie de imágenes que van de menos a más reveladoras, dando a los jugadores hasta 5 intentos para acertar.

La inspiración viene directamente de juegos virales como Wordle y Guess The Game, con la idea de crear esa experiencia diaria que hace que los usuarios quieran volver cada día para probar suerte, revisar sus estadísticas y competir con amigos.

## Características principales

### Modo de juego diario
- Un videojuego diferente cada día seleccionado automáticamente
- Hasta 5 intentos para adivinar el juego
- Imágenes progresivamente más claras con cada intento fallido
- Pistas adicionales como año de lanzamiento y desarrolladora
- Asistente de IA integrado para hacer hasta 5 preguntas sobre el juego

### Sistema de usuarios
- Registro opcional para mantener histórico completo
- Juego anónimo con progreso guardado en sesión
- Perfiles personalizados con estadísticas detalladas
- Sistema de medallas y títulos por logros
- Seguimiento de rachas y récords personales

### Archivo histórico
- Acceso a todos los juegos de días anteriores
- Posibilidad de rejugar cualquier desafío pasado
- Estadísticas completas por juego y período

### Funciones sociales
- Enlaces compartibles para retar a amigos
- Sistema de clasificación de jugadores
- Sistema de desafíos personalizados

## Arquitectura técnica

### Backend - Django + Python
El corazón del sistema está construido con Django, que se encarga de:
- Selección diaria automatizada de videojuegos desde la API de IGDB
- Gestión de usuarios y autenticación
- Almacenamiento de estadísticas y progreso
- API para comunicación con el frontend
- Integración con IA para el sistema de pistas

#### Vistas principales
- **HomeView**: Página principal con el juego del día
- **GameView**: Interfaz de juego con manejo de intentos y pistas
- **ProfileView**: Perfil de usuario con estadísticas y logros
- **HistoryView**: Archivo de juegos anteriores
- **LeaderboardView**: Rankings y comparativas sociales

#### Servicios del backend
- **GameService**: Lógica central del juego, validación de respuestas y progreso
- **IGDBService**: Integración con la API de IGDB para obtención de datos de juegos
- **UserService**: Gestión de perfiles, autenticación y estadísticas
- **AIService**: Comunicación con OpenAI para el sistema de pistas inteligentes
- **NotificationService**: Sistema de notificaciones y alertas
- **CacheService**: Optimización de rendimiento con Redis para datos frecuentes

### Frontend - JavaScript + Bootstrap
Una interfaz moderna y responsiva que incluye:
- Componentes JavaScript optimizados para una experiencia fluida
- Diseño responsive con Bootstrap y CSS personalizado
- Interfaz intuitiva adaptada tanto a desktop como móvil
- Sistema de navegación fluido entre secciones

#### Componentes principales
- **GameBoard**: Componente central del juego con imágenes y controles
- **GuessInput**: Campo de entrada con autocompletado y validación
- **ProgressIndicator**: Barra de progreso visual con intentos restantes
- **HintPanel**: Panel de pistas con información progresiva del juego
- **UserProfile**: Dashboard completo de estadísticas y logros
- **HistoryBrowser**: Navegador de juegos anteriores con filtros
- **StatsWidget**: Widgets reutilizables para mostrar métricas

#### Servicios del frontend
- **ApiService**: Centralización de todas las llamadas a la API del backend
- **AuthService**: Manejo de autenticación, tokens y sesiones de usuario
- **GameStateService**: Gestión del estado del juego y sincronización
- **LocalStorageService**: Persistencia de datos locales y preferencias
- **NotificationService**: Sistema de notificaciones toast y alertas
- **AnalyticsService**: Tracking de eventos y métricas de uso

### Integración con servicios externos
- **API de IGDB**: Base de datos completa de videojuegos para contenido diario
- **OpenAI/ChatGPT**: Sistema de pistas inteligente con restricciones específicas
- **Redis**: Cache distribuido para optimización de rendimiento
- **PostgreSQL**: Base de datos principal para persistencia de datos

## Instalación y configuración

### Requisitos previos
- Python 3.8+
- Node.js 14+
- Base de datos PostgreSQL (recomendado para producción)

### Configuración del backend
```bash
# Clonar el repositorio
git clone https://github.com/renatorrv-edu/guessityet.git
cd guessityet

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves de API (RAWG, OpenAI, etc.)

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor de desarrollo
python manage.py runserver
```

### Configuración del frontend
```bash
# Desde el directorio del frontend
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm start
```

## Variables de entorno necesarias

Crear un archivo `.env` en la raíz del proyecto con:

```env
SECRET_KEY=tu_clave_secreta_django
DEBUG=True
DATABASE_URL=postgresql://usuario:password@localhost/guessityet
IGDB_CLIENT_ID=tu_client_id_igdb
IGDB_CLIENT_SECRET=tu_client_secret_igdb
OPENAI_API_KEY=tu_clave_api_openai
REDIS_URL=redis://localhost:6379/0
```

## Despliegue con Docker

El proyecto incluye configuración para Docker que facilita el despliegue:

```bash
# Construir y ejecutar con docker-compose
docker-compose up --build

# Para producción
docker-compose -f docker-compose.prod.yml up -d
```

## Estructura del proyecto

```
guessityet/
├── backend/                 # Aplicación Django
│   ├── core/               # Lógica principal del juego
│   │   ├── views/          # Vistas del juego principal
│   │   ├── services/       # GameService, IGDBService
│   │   └── models/         # Modelos de juego y estadísticas
│   ├── users/              # Gestión de usuarios
│   │   ├── views/          # ProfileView, autenticación
│   │   ├── services/       # UserService, AuthService
│   │   └── models/         # User, Profile, Achievement
│   ├── ai/                 # Integración con IA
│   │   ├── services/       # AIService, OpenAI integration
│   │   └── prompts/        # Templates para prompts de IA
│   └── api/                # Endpoints de la API
│       ├── serializers/    # Serialización de datos
│       ├── viewsets/       # ViewSets de DRF
│       └── urls/           # Routing de API
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── components/     # Componentes reutilizables
│   │   │   ├── game/       # GameBoard, GuessInput, HintPanel
│   │   │   ├── user/       # UserProfile, StatsWidget
│   │   │   └── common/     # Componentes compartidos
│   │   ├── pages/          # Páginas principales
│   │   │   ├── HomePage/   # Juego del día
│   │   │   ├── ProfilePage/ # Perfil y estadísticas
│   │   │   └── HistoryPage/ # Archivo de juegos
│   │   ├── services/       # ApiService, AuthService, etc.
│   │   ├── hooks/          # Custom hooks para estado
│   │   ├── contexts/       # Context providers (Auth, Game)
│   │   └── utils/          # Utilidades y helpers
├── docker-compose.yml      # Configuración Docker
├── nginx/                  # Configuración del servidor web
└── docs/                   # Documentación adicional
```

## Desarrollo y contribución

### Flujo de trabajo
1. Fork del repositorio
2. Crear rama para nueva funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Hacer commits descriptivos
4. Push a tu fork (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Estándares de código
- Backend: Seguir PEP 8 para Python
- Frontend: Usar ESLint y Prettier
- Comentarios en español siguiendo el estilo del proyecto
- Tests unitarios para funcionalidades críticas

### Testing
```bash
# Tests del backend
python manage.py test

# Tests del frontend
cd frontend && npm test
```

## Roadmap

### Versión 1.0 (Actual)
- [x] Juego diario básico
- [x] Sistema de usuarios
- [x] Histórico de juegos
- [x] Sistema de pistas con IA

### Versión 1.1 (Próxima)
- [ ] Sistema multijugador con lobbies
- [ ] Temas personalizables
- [ ] Más tipos de pistas

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contacto y soporte

- **Autor**: Renato R. Romero Valencia
- **Email**: renatorrv.dev@gmail.com
- **GitHub**: [@renatorrv-edu](https://github.com/renatorrv-edu)
- **Gestión del proyecto**: [Taiga Board](https://tree.taiga.io/project/renatorrv-edu-guess-it-yet/kanban)

## Agradecimientos

- [IGDB.com](https://igdb.com) por proporcionar la API completa de videojuegos
- [Guess The Game](https://guessthe.game) por la inspiración

---

¿Ya lo has adivinado? 🎯