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
            # Generar URL de confirmación
            confirmation_url = EmailService._build_confirmation_url(token.token)

            # Contexto para las plantillas
            context = {
                "user": user,
                "confirmation_url": confirmation_url,
                "site_name": "Guess It Yet?",
                "token_expires_hours": 24,
            }

            # Renderizar plantillas HTML y texto
            html_message = render_to_string("emails/confirmation_email.html", context)
            text_message = render_to_string("emails/confirmation_email.txt", context)

            # Enviar email
            success = send_mail(
                subject="Confirma tu cuenta en Guess It Yet?",
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            if success:
                logger.info(f"Email de confirmación enviado a {user.email}")
                return True
            else:
                logger.error(f"Falló el envío de email a {user.email}")
                return False

        except Exception as e:
            logger.error(
                f"Error enviando email de confirmación a {user.email}: {str(e)}"
            )
            return False

    @staticmethod
    def send_welcome_email(user):
        """Enviar email de bienvenida después de la confirmación"""
        try:
            context = {
                "user": user,
                "site_name": "Guess It Yet?",
                "login_url": EmailService._build_url("login"),
                "daily_game_url": EmailService._build_url("daily_game"),
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
        relative_url = reverse("confirm_email", kwargs={"token": str(token)})
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
