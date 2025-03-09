# Proyecto de desarrollo de Desarrollo de Aplicaciones Web

A falta de tener una tutoría con alguno de mis profesores, ahora mismo tengo tres ideas que me llevana rondando la cabeza unos cuantos meses. Intentaré describirlos de manera resumida y decidiré con mi tutor del proyecto cuál de ellos puede ser más interesante, desafiante y asequible.

Añado a continuación una breve descripción de los tres proyectos.

## Proyecto 1 - Aplicación Web para un restaurante

### Introducción

La idea detrás de esta aplicación web sería desplegar una página de un restaurante con sus distintas secciones (contacto, dónde estamos, carta...) y un apartado donde las cuentas de usuario podrán realizar pedidos.

También contaremos con una cuenta especial para el restaurante y otras para los repartidores, cada una con distintas funcionalidades.

### Finalidad

Esta idea podría servir como plataforma para restaurantes pequeños que quieran desplegar un servicio web para recibir pedidos, organizarlos y completarlos. Con distintos tipos de cuentas las cuales podrán realizar distintos tipos de acciones. Esta idea surgió a raíz de trabajar en la pollería de mi tía hace unos años, lo que me hizo pensar en cómo su negocio podría ser más sencillo y crecer con una plataforma de este tipo funcional y bien organizada.

### Objetivos

Además del resto de páginas estáticas, el servicio ofrecerá un apartado donde los usuarios podrán seleccionar los distintos elementos del menú que quieran, realicen un pago (simularemos una pasarela de pago para el proyecto) y a continuación tengan una sección con los pedidos en curso. Esto mostrará el precio pagado, cuánto tardará aproximadamente, el nombre de su repartidor y el estado del pedido ("recibido", "en preparación", "esperando repartidor", "en reparto", "completado"). Quizás se podría simular incluso sobre un mapa el trayecto del repartidor con el pedido.

También contaremos con cuentas para el restaurante (donde se mostrarán los pedidos que realizan los usuarios, el contenido del pedido, etc.) Y, por último, cuentas de tipo repartidor, quienes podrán ver en tiempo real los pedidos que surgen y "reclamarlos" para ellos. Un posible desafío será el de intentar calcular las rutas más óptimas para estos repartidores.

## Proyecto 2 - Aplicación Web para juego de adivinar el videojuego

### Introducción

Esta segunda aplicación web sería una especie de página-juego en el que el usuario debe intentar adivinar un videojuego, seleccionado a través de una API que contenga una base de datos de videojuegos, en un número determinado de intentos solo viendo capturas de pantalla de este. Algo similar a lo que podemos encontrar https://guessthe.game/.

### Finalidad

Se pretende ofrecer al usuario la posibilidad de jugar cada día a un nuevo desafío en el que tendrá que adivinar un videojuego a raíz de capturas de pantalla de este. También se pretende incluir otras secciones que funcionen de manera similar (adivina la canción, la portada, etc.). El usuario puede jugar de manera anónima. Pero si crea una cuenta, puede tener acceso a una serie de estadísticas, como la racha de aciertos o la media de intentos, comparar sus estadísticas con otros jugadores, enviar los desafíos a otras personas con un enlace y que el desafiado pueda ver cuántos intentos/tiempo le tomó al usuario principal resolver el enigma. Acceder también a las pruebas de otros días. 

También se ha valorado que los usuarios tengan perfiles y un sistema de comentarios similar a Facebook.

### Objetivos

Este proyecto se hace con la idea de tener un juego dinámico, divertido y que invite al usuario a visitar a menudo la página. Se ha valorado, una vez termine la entrega de proyecto, añadir publicidad y desplegar online con el objetivo de darle publicidad y, aunque sean mínimos, generar ingresos pasivos. La idea es automatizar este proceso de selección de videojuegos lo máximo posible.


## Proyecto 3 - Aplicación Web para informar sobre películas

### Introducción

Esta tercera y última aplicación web se trata de una página que estaría dividida en distintas secciones y que pretende dar la posibilidad a los usuarios de indicar cierto tipo de contenidos que podría tener una película para que otros lo consulten. Por ejemplo, "¿Tiene la película escena post-créditos?", "¿Muere algún perro/gato en la película?", "¿Esta película tiene sustos tipo 'jumpscare'? ¿Cuándo?".

### Finalidad

En esta aplicación los usuarios podrán crearse cuentas para contribuir. De una API llamada TMDB (The Movie DataBase) llamaríamos para tener acceso a una gran variedad de títulos. Los usuarios pueden entrar a cada película y votar en alguna de las secciones mencionadas anteriormente. Estos votos se recopilarían para hacer una media y mostrarla a los usuarios que quieran consultarla. Por ejemplo, si 80 usuarios votan que en "Spider-Man: No Way Home" hay una escena post-créditos y 20 votan que no, el usuario que entre verá que hay un 80% de los usuarios que indican que sí que la hay. Otro ejemplo podría ser el entrar a una película de miedo, como "Ju-On" y podrá ver qué porcentaje de usuarios han votado que tiene jumpscares y quizás ver en qué partes de la película ocurren. También se planifica la inserción de cuentas de moderador.

Para realizarlas necesitarás una cuenta de usuario, pero no para verlas. 

La gente puede votar a los usuarios dándole "kudos" o "gracias" por sus contribuciones, por lo que habría insignias y otras recompensas.

### Objetivos

Ofrecer una comunidad grande con usuarios que contribuyan a las estadísticas de las películas y que todos puedan consultar estas contribuciones.

Esta idea surge a raíz de haber tenido la duda, al terminar de ver alguna película en el cine, de si había una escena postcréditos por la que mereciera la pena quedarse un rato más. 

## Autor
Renato R. Romero Valencia

## Medios hardware y software

Como hardware, usaré mi ordenador personal, el cual cuenta con suficiente potencia para llevar a cabo el desarrollo de estas aplicaciones y ponerlas a prueba. Usaré GitHub para el repositorio donde guardaré las distintas versiones de este programa.

Y en cuestión de software usaré PyCharm Professional ya que pretendo desarrollar estas aplicaciones con Django. También usaré, probablemente, Visual Studio Code para el front-end (cuestiones de diseño con bootstrap y funcionalidades con JavaScript o ReactJS). Todo corriendo en Windows 11.

También, en las fases finales de desarrollo se tiene en cuenta la dockerización del proyecto para permitir su despliegue en un servidor Web (probablemente, una instancia AWS).

## Planificación

Tardaré apróximadamente unas once o doce semanas. Mi idea es dedicar todas las tardes entre semana, después de las prácticas, varias horas para desarrollar esta aplicación y ponerla a prueba. Según avance el desarrollo y tenga tutorias con mis profesores, este itinerario irá tomando más forma.
