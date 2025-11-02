#!/usr/bin/env bash
# extraer_ips.sh
# Interactivo: pide el fichero hasta que exista (en la carpeta del script o ruta indicada)
# Extrae IPs únicas (última aparición) e ignora .0 y .255

set -euo pipefail

# Directorio del script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
echo "=== Extracción de IPs detectadas ==="
echo "Por defecto buscará el fichero en: $script_dir"
echo "También puedes introducir una ruta completa o relativa diferente."

# Pedir el fichero hasta que exista
while true; do
  read -rp "Introduce el nombre o ruta del fichero (ej: ipsdetectadasSN.txt o /ruta/archivo.txt): " input_name

  # Si el usuario introduce ruta absoluta o relativa, usarla directamente
  if [[ "$input_name" == /* || "$input_name" == ./* || "$input_name" == ../* ]]; then
    input_path="$input_name"
  else
    input_path="$script_dir/$input_name"
  fi

  if [ -f "$input_path" ]; then
    echo "✅ Fichero encontrado: $input_path"
    break
  else
    echo "❌ No se encontró el fichero. Intenta de nuevo."
  fi
done

# Archivo de salida
out_path="$script_dir/ipsdetectadas.txt"
echo "Procesando IPs únicas (ignorando .0 y .255)..."

# Extraer IPs únicas e ignorar .0 y .255
awk '
{
  for (i=1; i<=NF; i++) {
    if (match($i, /[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/)) {
      ip = substr($i, RSTART, RLENGTH)
      if (ip ~ /\.0$/ || ip ~ /\.255$/) next  # ignorar red/broadcast
      seen[ip] = 1
    }
  }
}
END {
  for (ip in seen) print ip
}
' "$input_path" | sort -V | tee "$out_path"

echo "✅ IPs guardadas en: $out_path"
