#!/usr/bin/env python3
"""
merge_nmap_xml_full_merge_hosts.py

Fusiona múltiples archivos XML de Nmap en uno solo con toda la información.

Funciones principales:
✅ Combina todos los <host> (sin perder ninguno)
✅ Si un mismo host aparece en varios XML, fusiona sus puertos y scripts
✅ Fusiona <scaninfo>, <taskbegin>, <taskend>
✅ Recalcula <runstats> (up/down/total)
✅ Mantiene el resto de metadatos del primer XML
✅ Formatea (indent) el XML final

Uso:
    python3 merge_nmap_xml_full_merge_hosts.py -o merged.xml *.xml
"""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def indent(elem, level=0):
    """Pretty print XML."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level + 1)
        if not e.tail or not e.tail.strip():
            e.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

def host_key(host_elem):
    """Clave única de host basada en direcciones IP."""
    addrs = []
    for a in host_elem.findall("address"):
        addrs.append((a.get("addrtype"), a.get("addr")))
    return tuple(sorted(addrs))

def clone(elem):
    """Clona un elemento XML completo."""
    return ET.fromstring(ET.tostring(elem, encoding="utf-8"))

def merge_ports(target_host, new_host):
    """Fusiona los puertos de new_host en target_host (sin duplicar por protocol/portid)."""
    target_ports_elem = target_host.find("ports")
    new_ports_elem = new_host.find("ports")
    if new_ports_elem is None:
        return
    if target_ports_elem is None:
        target_host.append(clone(new_ports_elem))
        return

    existing_ports = {(p.get("protocol"), p.get("portid")) for p in target_ports_elem.findall("port")}
    for port in new_ports_elem.findall("port"):
        key = (port.get("protocol"), port.get("portid"))
        if key not in existing_ports:
            target_ports_elem.append(clone(port))
            existing_ports.add(key)
        else:
            # Si ya existe ese puerto, podemos fusionar información adicional como <script>
            existing_port = next((p for p in target_ports_elem.findall("port") if (p.get("protocol"), p.get("portid")) == key), None)
            if existing_port is not None:
                merge_scripts(existing_port, port)

def merge_scripts(target_elem, new_elem):
    """Fusiona etiquetas <script> dentro de puertos o hosts sin duplicar por id."""
    target_scripts = target_elem.findall("script")
    new_scripts = new_elem.findall("script")
    existing_ids = {s.get("id") for s in target_scripts if s.get("id")}
    for s in new_scripts:
        sid = s.get("id")
        if sid not in existing_ids:
            target_elem.append(clone(s))
            existing_ids.add(sid)

def merge_host_info(target, new):
    """Fusiona información general de un host existente."""
    # Fusionar status si el nuevo host está up
    new_status = new.find("status")
    old_status = target.find("status")
    if new_status is not None and (old_status is None or new_status.get("state") == "up"):
        if old_status is None:
            target.insert(0, clone(new_status))
        else:
            old_status.attrib.update(new_status.attrib)

    # Fusionar hostnames
    target_hostnames = target.find("hostnames")
    new_hostnames = new.find("hostnames")
    if new_hostnames is not None:
        if target_hostnames is None:
            target.append(clone(new_hostnames))
        else:
            existing_names = {h.get("name") for h in target_hostnames.findall("hostname")}
            for hn in new_hostnames.findall("hostname"):
                if hn.get("name") not in existing_names:
                    target_hostnames.append(clone(hn))
                    existing_names.add(hn.get("name"))

    # Fusionar puertos y scripts
    merge_ports(target, new)
    merge_scripts(target, new)

def merge_scaninfo(root, other_root):
    """Fusiona scaninfo por (type, protocol)."""
    existing = {(s.get("type"), s.get("protocol")) for s in root.findall("scaninfo")}
    for s in other_root.findall("scaninfo"):
        key = (s.get("type"), s.get("protocol"))
        if key not in existing:
            root.insert(0, clone(s))
            existing.add(key)

def merge_tasks(root, other_root):
    """Fusiona taskbegin/taskend sin duplicar."""
    def task_key(elem):
        return (elem.tag, tuple(sorted(elem.attrib.items())))
    existing = {task_key(e) for e in root.findall("taskbegin") + root.findall("taskend")}
    insert_pos = 0
    first_host = root.find("host")
    if first_host is not None:
        insert_pos = list(root).index(first_host)
    for t in other_root.findall("taskbegin") + other_root.findall("taskend"):
        k = task_key(t)
        if k not in existing:
            root.insert(insert_pos, clone(t))
            insert_pos += 1
            existing.add(k)

def merge_runstats(root):
    """Recalcula runstats (up/down/total)."""
    all_hosts = root.findall("host")
    up = down = unknown = 0
    for h in all_hosts:
        st = h.find("status")
        state = st.get("state") if st is not None else "unknown"
        if state == "up":
            up += 1
        elif state == "down":
            down += 1
        else:
            unknown += 1
    total = up + down + unknown

    runstats = root.find("runstats")
    if runstats is None:
        runstats = ET.SubElement(root, "runstats")

    finished = runstats.find("finished")
    if finished is None:
        finished = ET.SubElement(runstats, "finished")
    finished.set("summary", "runstats recalculado por merge_nmap_xml_full_merge_hosts.py")

    hosts = runstats.find("hosts")
    if hosts is None:
        hosts = ET.SubElement(runstats, "hosts")
    hosts.set("up", str(up))
    hosts.set("down", str(down))
    hosts.set("total", str(total))

def main():
    parser = argparse.ArgumentParser(description="Fusiona múltiples archivos XML de Nmap en uno con todos los hosts y datos combinados.")
    parser.add_argument("files", nargs="+", help="Archivos XML de Nmap")
    parser.add_argument("-o", "--output", default="merged.xml", help="Archivo de salida (por defecto merged.xml)")
    args = parser.parse_args()

    files = [Path(f) for f in args.files if Path(f).exists()]
    if not files:
        print("❌ No se encontraron archivos válidos.", file=sys.stderr)
        sys.exit(1)
    files.sort()

    # Cargar archivo base
    root_tree = ET.parse(files[0])
    root = root_tree.getroot()

    hosts_by_key = {host_key(h): h for h in root.findall("host")}

    for f in files[1:]:
        try:
            t = ET.parse(f)
            r = t.getroot()
        except ET.ParseError as e:
            print(f"⚠️  Error al parsear {f}: {e}", file=sys.stderr)
            continue

        merge_scaninfo(root, r)
        merge_tasks(root, r)

        for host in r.findall("host"):
            key = host_key(host)
            if key not in hosts_by_key:
                root.append(clone(host))
                hosts_by_key[key] = root.findall("host")[-1]
            else:
                merge_host_info(hosts_by_key[key], host)

    merge_runstats(root)
    indent(root)
    xml_out = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml_out)

    print(f"✅ Archivo combinado generado: {args.output}")
    print(f"   Total de hosts: {len(root.findall('host'))}")

if __name__ == "__main__":
    main()
