# guessityet/forms.py - Formularios personalizados para autenticación
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    """Formulario de registro personalizado con campos adicionales"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "tu@email.com"}
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre (opcional)"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Apellido (opcional)"}
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personalizar widgets de campos heredados
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Nombre de usuario"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Contraseña"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirmar contraseña"}
        )

        # Personalizar help_text
        self.fields["username"].help_text = (
            "Máximo 150 caracteres. Solo letras, números y @/./+/-/_."
        )
        self.fields["password1"].help_text = (
            "Mínimo 8 caracteres. No puede ser solo numérica."
        )

    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este email.")
        return email

    def save(self, commit=True):
        """Guardar usuario con campos adicionales"""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Formulario de login personalizado con estilos"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personalizar widgets
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Nombre de usuario",
                "autocomplete": "username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Contraseña",
                "autocomplete": "current-password",
            }
        )


class ProfileUpdateForm(forms.ModelForm):
    """Formulario para actualizar información del perfil"""

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Apellido"}
            ),
        }

    def clean_email(self):
        """Validar que el email sea único (excluyendo el usuario actual)"""
        email = self.cleaned_data.get("email")
        if email:
            # Excluir el usuario actual de la validación
            users_with_email = User.objects.filter(email=email)
            if self.instance:
                users_with_email = users_with_email.exclude(pk=self.instance.pk)

            if users_with_email.exists():
                raise ValidationError("Ya existe un usuario con este email.")
        return email
