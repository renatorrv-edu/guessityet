# guessityet/validators.py - Validadores personalizados
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomPasswordValidator:
    """
    Validador de contraseña personalizado que requiere:
    - Al menos 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un símbolo especial
    """

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        errors = []

        # Verificar longitud mínima
        if len(password) < self.min_length:
            errors.append(_('La contraseña debe tener al menos %(min_length)d caracteres.') % {
                'min_length': self.min_length
            })

        # Verificar mayúscula
        if not re.search(r'[A-Z]', password):
            errors.append(_('La contraseña debe contener al menos una letra mayúscula.'))

        # Verificar minúscula
        if not re.search(r'[a-z]', password):
            errors.append(_('La contraseña debe contener al menos una letra minúscula.'))

        # Verificar número
        if not re.search(r'\d', password):
            errors.append(_('La contraseña debe contener al menos un número.'))

        # Verificar símbolo especial
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append(_('La contraseña debe contener al menos un símbolo especial (!@#$%^&*).'))

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            'Tu contraseña debe tener al menos %(min_length)d caracteres, '
            'incluyendo una letra mayúscula, una minúscula, un número y un símbolo especial.'
        ) % {'min_length': self.min_length}


class NoCommonPasswordValidator:
    """
    Validador que evita contraseñas demasiado comunes en español
    """

    COMMON_PASSWORDS = [
        'password', 'contraseña', '12345678', 'qwerty123',
        'admin123', 'usuario123', 'password123', 'contraseña123',
        'abcdefgh', '87654321', 'password1', 'contraseña1',
        'administrador', 'invitado', 'guest123', 'test123'
    ]

    def validate(self, password, user=None):
        if password.lower() in [p.lower() for p in self.COMMON_PASSWORDS]:
            raise ValidationError(
                _('Esta contraseña es demasiado común. Elige una más segura.'),
                code='password_too_common',
            )

    def get_help_text(self):
        return _('Tu contraseña no puede ser una contraseña común.')


class UserAttributeSimilarityValidator:
    """
    Validador que evita que la contraseña sea similar al nombre de usuario o email
    """

    def __init__(self, user_attributes=['username', 'first_name', 'last_name', 'email'], max_similarity=0.7):
        self.user_attributes = user_attributes
        self.max_similarity = max_similarity

    def validate(self, password, user=None):
        if not user:
            return

        password_lower = password.lower()

        for attribute_name in self.user_attributes:
            value = getattr(user, attribute_name, None)
            if not value or len(value) < 3:
                continue

            value_lower = value.lower()

            # Verificar si la contraseña contiene el atributo o viceversa
            if value_lower in password_lower or password_lower in value_lower:
                raise ValidationError(
                    _('La contraseña es demasiado similar a tu %(verbose_name)s.') % {
                        'verbose_name': attribute_name
                    },
                    code='password_too_similar',
                    )

            # Verificar similitud por caracteres comunes
            similarity = self._calculate_similarity(password_lower, value_lower)
            if similarity > self.max_similarity:
                raise ValidationError(
                    _('La contraseña es demasiado similar a tu %(verbose_name)s.') % {
                        'verbose_name': attribute_name
                    },
                    code='password_too_similar',
                    )

    def _calculate_similarity(self, password, value):
        """Calcular similitud entre dos strings"""
        if len(password) == 0 or len(value) == 0:
            return 0

        common_chars = set(password) & set(value)
        total_chars = set(password) | set(value)

        return len(common_chars) / len(total_chars) if total_chars else 0

    def get_help_text(self):
        return _('Tu contraseña no puede ser muy similar a tu información personal.')


# Validador adicional para evitar secuencias
class NoSequentialPasswordValidator:
    """
    Validador que evita secuencias comunes como 123456, abcdef, etc.
    """

    def validate(self, password, user=None):
        password_lower = password.lower()

        # Verificar secuencias numéricas
        for i in range(len(password_lower) - 3):
            substring = password_lower[i:i+4]
            if substring.isdigit():
                # Verificar secuencia ascendente
                if all(int(substring[j]) == int(substring[0]) + j for j in range(4)):
                    raise ValidationError(
                        _('La contraseña no puede contener secuencias numéricas simples.'),
                        code='sequential_numbers',
                    )

                # Verificar secuencia descendente
                if all(int(substring[j]) == int(substring[0]) - j for j in range(4)):
                    raise ValidationError(
                        _('La contraseña no puede contener secuencias numéricas simples.'),
                        code='sequential_numbers',
                    )

        # Verificar secuencias alfabéticas
        for i in range(len(password_lower) - 3):
            substring = password_lower[i:i+4]
            if substring.isalpha():
                # Verificar secuencia ascendente
                if all(ord(substring[j]) == ord(substring[0]) + j for j in range(4)):
                    raise ValidationError(
                        _('La contraseña no puede contener secuencias alfabéticas simples.'),
                        code='sequential_letters',
                    )

        # Verificar repetición de caracteres
        for i in range(len(password) - 3):
            if password[i] == password[i+1] == password[i+2] == password[i+3]:
                raise ValidationError(
                    _('La contraseña no puede tener más de 3 caracteres iguales consecutivos.'),
                    code='repeated_characters',
                )

    def get_help_text(self):
        return _('Tu contraseña no puede contener secuencias simples o caracteres repetidos.')