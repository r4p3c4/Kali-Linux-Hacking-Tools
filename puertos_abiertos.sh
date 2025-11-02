#!/usr/bin/env bash
# extrae_puertos.sh — versión corregida
# Extrae los puertos abiertos de un archivo .gnmap de Nmap.

set -euo pipefail

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Función para pedir el fichero hasta que exista
pedir_fichero() {
  local fichero
  while true; do
    read -rp "Introduce el nombre del fichero gnmap (ej: scan.gnmap): " fichero

    if [[ -z "$fichero" ]]; then
      echo "❌ No has introducido ningún nombre. Inténtalo de nuevo."
      continue
    fi

    # Si el archivo existe en el directorio actual
    if [[ -f "$fichero" ]]; then
      echo "$fichero"
      return
    fi

    # Si el archivo existe en el mismo directorio que el script
    if [[ -f "${SCRIPT_DIR}/${fichero}" ]]; then
      echo "${SCRIPT_DIR}/${fichero}"
      return
    fi

    echo "⚠️  No se encontró '$fichero' ni en el directorio actual ni en ${SCRIPT_DIR}."
  done
}

# Pedir fichero al usuario
FICHERO=$(pedir_fichero)
echo "✅ Usando fichero: $FICHERO"

# Detectar si grep soporta -P
if echo "test" | grep -P "t" >/dev/null 2>&1; then
  echo "🔍 Extrayendo puertos con grep..."
  grep -oP '\d+(?=/open/)' "$FICHERO" | sort -n -u | paste -sd "," -
else
  echo "🔍 grep -P no disponible, usando awk..."
  awk '/\/(tcp|udp)[[:space:]]+open/ {
        split($1,a,"/")
        print a[1]
      }' "$FICHERO" | sort -n -u | paste -sd "," -
fi
