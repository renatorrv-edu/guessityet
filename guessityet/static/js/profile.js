// Funcionalidad para la página de perfil
console.log('Cargando Profile JS...');

document.addEventListener('DOMContentLoaded', function() {
    initializeProfile();
});

function initializeProfile() {
    // Configurar gráficos de estadísticas
    setupStatCharts();

    // Configurar formulario de perfil
    setupProfileForm();

    // Configurar cambio de avatar
    setupAvatarUpload();
}

function setupStatCharts() {
    // Crear gráficos con Chart.js o similar
    const ctx = document.getElementById('statsChart');
    if (ctx) {
        // Configuración del gráfico se implementará aquí
        console.log('Inicializando gráfico de estadísticas...');
    }
}

function setupProfileForm() {
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            updateProfile();
        });
    }
}

async function updateProfile() {
    const formData = new FormData(document.getElementById('profile-form'));

    try {
        const response = await fetch('/profile/update/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': GuessItYetUtils.getCSRFToken()
            },
            body: formData
        });

        if (response.ok) {
            showSuccessMessage('Perfil actualizado correctamente');
        } else {
            showErrorMessage('Error al actualizar el perfil');
        }
    } catch (error) {
        showErrorMessage('Error de conexión');
    }
}

function setupAvatarUpload() {
    const avatarInput = document.getElementById('avatar-input');
    if (avatarInput) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                previewAvatar(file);
            }
        });
    }
}

function previewAvatar(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('avatar-preview');
        if (preview) {
            preview.src = e.target.result;
        }
    };
    reader.readAsDataURL(file);
}