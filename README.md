# Guess It Yet?

### Introducción

**Guess It Yet?** ("*¿Ya lo has adivinado?*") es una aplicación web pensada como una especie de juego diario en el que el jugador debe intentar adivinar un videojuego elegido al azar a través de la API de **RAWG** (una base de datos masiva de videojuegos) gracias a una serie de capturas de pantalla, que se irán mostrando de menos a más reveladoras. 

También tendrá integrado un sistema de perfiles que mantengan un histórico de hitos y récords de los usuarios, aunque se permitirá jugar de manera anónima y guardar el progreso de manera más sencilla a través de las sesiones. Además, pretendo incluir un sistema de juego multijugador basado en lobbies similar a los usados en **Kahoot.it**, donde los jugadores se enfrentarán a otros tratando de adivinar el juego por las imágenes en partidas rápidas de unos cinco minutos apróximadamente.

### Finalidad

No hay muchas más pretensiones más allá de crear una página que se actualice diariamente y ofrezca a los jugadores una experiencia jugable y agradable todos los días. También se planea que el usuario tenga acceso a los días anteriores. Es un modelo de juego muy popular, como **Wordle** o el propio **Guess The Game**, página en la que me he inspirado mucho. La intención es que el usuario tenga ganas cada día de volver a jugar un rato, a revisar su histórico, sus récords y rachas y retar a sus amigos o crear una sala online para jugar con ellos.

### Objetivos

Desde el punto de vista técnico, la intención principal es desarrollar el backend con Python y Django. Este backend se encargará, todos los días, de elegir un videojuego al azar de la base de datos (que no haya surgido antes) y mostrarlo ante el usuario (ya sea registrado o no) con una interfaz que le permita intentar adivinarlo hasta 5 veces. A cada intento fallido, se mostrará una nueva imagen más clara y se otorgará alguna pista, como el año de salida del videojuego o su desarrolladora. Como última pista se permitirá preguntar a la IA (probablemente, ChatGPT) en un pequeño recuadro de chat hasta 5 preguntas sobre el juego y la IA tendrá estrictamente prohibido decir el título del juego, su saga u otra información que facilite mucho adivinarlo. Se podrán acceder a los juegos de días anteriores y jugarlos también. Se mantendrá un histórico del progreso del jugador (tanto si está registrado como si no).

Los jugadores registrados podrán acceder a su perfil, y ver sus récords y rachas, conseguir medallas y títulos e incluso retar a otros jugadores a hacerlo mejor que ellos (se creará un enlace con la entrada seleccionada para enviarlo a otras personas y se intentará guardar registro de esto).

También se planea, aunque sea ambicioso, crear un sistema de lobbies para jugar online de forma asíncrona con otros jugadores (que podrán ser registrados o no). Sería algo similar a Kahoot, donde las imágenes de los juegos elegidos irían apareciendo y los usuarios intentarían adivinarlo lo antes posible para ganar puntos. La idea es que sean partidas rápidas de unos 5 minutos. Se baraja la posibilidad de guardar el progreso de estas partidas en el perfil de cada usuario.

El front-end intentará realizarse con ReactJS para tratar la información de manera eficiente y presentarla de forma atractiva y optimizada al usuario. Se usará Bootstrap y clases CSS personalizadas para darle un aspecto moderno, joven, intuitivo y conciso.

## Autor

Renato R. Romero Valencia

## Medios hardware y software

Como hardware, usaré mi ordenador personal, el cual cuenta con suficiente potencia para llevar a cabo el desarrollo de estas aplicaciones y ponerlas a prueba. Usaré GitHub para alojar el repositorio donde guardaré las distintas versiones de esta aplicación.

Y en cuestión de software usaré PyCharm Professional ya que pretendo desarrollar estas aplicaciones con Django. También usaré, probablemente, Visual Studio Code para el front-end (cuestiones de diseño con bootstrap y funcionalidades con JavaScript o ReactJS). Todo corriendo en Windows 11.

También, en las fases finales de desarrollo se tiene en cuenta la dockerización del proyecto para permitir su despliegue en un servidor Web (probablemente, una instancia AWS).

## Planificación

Tardaré apróximadamente unas once o doce semanas. Mi idea es dedicar todas las tardes entre semana, después de las prácticas, varias horas para desarrollar esta aplicación y ponerla a prueba. Según avance el desarrollo y tenga tutorias con mis profesores, este itinerario irá tomando más forma.

Se planea documentar correcta y abundantemente los pasos del proceso de desarrrollo. Adjuntar diagramas y otra información que ayude a comprender su funcionamiento.

## Enlace a Kanban de Taiga.io

https://tree.taiga.io/project/renatorrv-edu-guess-it-yet/kanban
