#!/bin/bash
# Script para instalar Docker y Portainer en Kali Linux
# Autor: ChatGPT (GPT-5)
# Fecha: 2025-10-27

echo "=== Actualizando el sistema ==="
sudo apt-get update -y

echo "=== Instalando Docker ==="
sudo apt-get install docker.io -y

echo "=== Habilitando y arrancando el servicio Docker ==="
sudo systemctl enable --now docker

echo "=== Verificando el estado de Docker ==="
sudo systemctl status docker --no-pager

echo "=== Desplegando Portainer ==="
sudo docker run -d -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  --name portainer portainer/portainer-ce

echo ""
echo "✅ Instalación completada."
echo "Puedes acceder a Portainer abriendo en tu navegador:"
echo "👉 http://localhost:9000"
echo ""
echo "Si lo ejecutas en una máquina remota, reemplaza 'localhost' por la IP de tu servidor."
