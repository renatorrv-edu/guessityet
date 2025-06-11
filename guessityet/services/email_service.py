# guessityet/services/email_service.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para envío de emails de confirmación y notificaciones"""

    @staticmethod
    def send_confirmation_email(user, token):
        """Enviar email de confirmación al usuario"""
        try:
            print(f"🔍 DEBUG: Iniciando envío de email para {user.email}")

            # Generar URL de confirmación
            confirmation_url = EmailService._build_confirmation_url(token.token)
            print(f"🔍 DEBUG: URL de confirmación: {confirmation_url}")

            # Contexto para las plantillas
            context = {
                "user": user,
                "confirmation_url": confirmation_url,
                "site_name": "Guess It Yet?",
                "token_expires_hours": 24,
            }
            print(f"🔍 DEBUG: Contexto creado")

            # Renderizar plantillas HTML y texto
            try:
                html_message = render_to_string(
                    "emails/confirmation_email.html", context
                )
                print(f"🔍 DEBUG: HTML renderizado correctamente")
            except Exception as e:
                print(f"❌ ERROR: No se pudo renderizar HTML: {str(e)}")
                html_message = None

            try:
                text_message = render_to_string(
                    "emails/confirmation_email.txt", context
                )
                print(f"🔍 DEBUG: Texto renderizado correctamente")
            except Exception as e:
                print(f"❌ ERROR: No se pudo renderizar texto: {str(e)}")
                text_message = f"Confirma tu cuenta en: {confirmation_url}"

            print(f"🔍 DEBUG: Configuración de email:")
            print(f"  - EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            print(
                f"  - EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No configurado')}"
            )
            print(
                f"  - EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'No configurado')}"
            )
            print(
                f"  - DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')}"
            )

            # Enviar email
            print(f"🔍 DEBUG: Intentando enviar email...")
            success = send_mail(
                subject="Confirma tu cuenta en Guess It Yet?",
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            print(f"🔍 DEBUG: Resultado del envío: {success}")

            if success:
                logger.info(f"Email de confirmación enviado a {user.email}")
                print(f"✅ SUCCESS: Email enviado correctamente")
                return True
            else:
                logger.error(f"Falló el envío de email a {user.email}")
                print(f"❌ ERROR: El envío falló")
                return False

        except Exception as e:
            error_msg = f"Error enviando email de confirmación a {user.email}: {str(e)}"
            logger.error(error_msg)
            print(f"❌ EXCEPTION: {error_msg}")
            import traceback

            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            return False

    @staticmethod
    def send_welcome_email(user):
        """Enviar email de bienvenida después de la confirmación"""
        try:
            context = {
                "user": user,
                "site_name": "Guess It Yet?",
                "login_url": EmailService._build_url_from_name("guessityet:login"),
                "daily_game_url": EmailService._build_url_from_name(
                    "guessityet:daily_game"
                ),
            }

            html_message = render_to_string("emails/welcome_email.html", context)
            text_message = render_to_string("emails/welcome_email.txt", context)

            success = send_mail(
                subject="¡Bienvenido a Guess It Yet?!",
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,  # No fallar si no se puede enviar el welcome
            )

            if success:
                logger.info(f"Email de bienvenida enviado a {user.email}")

            return success

        except Exception as e:
            logger.error(f"Error enviando email de bienvenida a {user.email}: {str(e)}")
            return False

    @staticmethod
    def resend_confirmation_email(user):
        """Reenviar email de confirmación"""
        from ..models import EmailConfirmationToken

        # Invalidar tokens existentes
        EmailConfirmationToken.objects.filter(user=user, is_used=False).update(
            is_used=True
        )

        # Crear nuevo token
        new_token = EmailConfirmationToken.objects.create(user=user)

        # Enviar email
        return EmailService.send_confirmation_email(user, new_token)

    @staticmethod
    def _build_confirmation_url(token):
        """Construir URL completa de confirmación"""
        relative_url = reverse("guessityet:confirm_email", kwargs={"token": str(token)})
        return EmailService._build_url(relative_url)

    @staticmethod
    def _build_url(path):
        """Construir URL completa con dominio"""
        try:
            # Intentar obtener el dominio desde Sites framework
            current_site = Site.objects.get_current()
            domain = current_site.domain
        except:
            # Fallback a localhost para desarrollo
            domain = "localhost:8000"

        # Usar HTTPS en producción
        protocol = "https" if not settings.DEBUG else "http"

        if path.startswith("/"):
            return f"{protocol}://{domain}{path}"
        else:
            return f"{protocol}://{domain}/{path}"

    @staticmethod
    def _build_url_from_name(url_name):
        """Construir URL completa desde nombre de URL"""
        try:
            relative_url = reverse(url_name)
            return EmailService._build_url(relative_url)
        except Exception as e:
            logger.error(f"Error construyendo URL para {url_name}: {str(e)}")
            return "http://localhost:8000/"
