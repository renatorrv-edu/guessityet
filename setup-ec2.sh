#!/bin/bash

echo "🔧 Configurando EC2 para GuessItYet..."

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y git nginx certbot python3-certbot-nginx curl ufw

# Configurar firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Verificar Docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Crear directorio del proyecto
sudo mkdir -p /var/www/guessityet
sudo chown ubuntu:ubuntu /var/www/guessityet

# Configurar Nginx
sudo tee /etc/nginx/sites-available/guessityet.renatorrv.tech > /dev/null << 'EOF'
server {
    listen 80;
    server_name guessityet.renatorrv.tech;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name guessityet.renatorrv.tech;

    ssl_certificate /etc/letsencrypt/live/guessityet.renatorrv.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/guessityet.renatorrv.tech/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    client_max_body_size 100M;

    access_log /var/log/nginx/guessityet_access.log;
    error_log /var/log/nginx/guessityet_error.log;

    location /static/ {
        alias /var/www/guessityet/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/guessityet/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/guessityet.renatorrv.tech /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar y reiniciar Nginx
sudo nginx -t
sudo systemctl reload nginx

echo "✅ Configuración completada!"
echo "📍 IP pública:"
curl -s http://checkip.amazonaws.com/