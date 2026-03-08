import os
import json
import hashlib
import urllib.request
import urllib.error
import uuid
from datetime import datetime

SERVIDOR = "https://condessa.pythonanywhere.com"
LICENCA_FILE = os.path.expanduser("~/.config/stockpro/licenca.json")

def get_machine_id():
    """ID único da máquina"""
    try:
        with open("/etc/machine-id") as f:
            return f.read().strip()
    except:
        return str(uuid.getnode())

def _post(endpoint, dados):
    """Faz POST ao servidor de licenças"""
    url = f"{SERVIDOR}{endpoint}"
    body = json.dumps(dados).encode()
    req = urllib.request.Request(url, data=body,
          headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except:
        return None

def _carregar_local():
    """Carrega licença guardada localmente"""
    try:
        with open(LICENCA_FILE) as f:
            return json.load(f)
    except:
        return {}

def _guardar_local(dados):
    """Guarda licença localmente"""
    os.makedirs(os.path.dirname(LICENCA_FILE), exist_ok=True)
    with open(LICENCA_FILE, "w") as f:
        json.dump(dados, f, indent=2)

def inicializar():
    """Regista trial no servidor se for primeira execução"""
    machine_id = get_machine_id()
    resultado = _post("/api/trial", {"machine_id": machine_id})
    if resultado and resultado.get("ok"):
        _guardar_local({
            "machine_id": machine_id,
            "estado": resultado["estado"],
            "dias_restantes": resultado["dias_restantes"],
            "expira": resultado.get("expira",""),
            "ultima_verificacao": datetime.utcnow().isoformat()
        })
        return resultado
    return None

def verificar():
    """Verifica estado da licença — online ou local"""
    machine_id = get_machine_id()
    local = _carregar_local()

    # Tentar verificar online
    resultado = _post("/api/verificar", {"machine_id": machine_id})

    if resultado:
        dados = {
            "machine_id": machine_id,
            "estado": resultado.get("estado","desconhecido"),
            "dias_restantes": resultado.get("dias_restantes", 0),
            "expira": local.get("expira",""),
            "ultima_verificacao": datetime.utcnow().isoformat()
        }
        _guardar_local(dados)
        return dados

    # Sem internet — usar cache local
    if local:
        # Calcular dias restantes localmente
        try:
            expira = datetime.fromisoformat(local["expira"])
            dias = max(0, (expira - datetime.utcnow()).days)
            local["dias_restantes"] = dias
            if dias == 0 and local.get("estado") == "trial":
                local["estado"] = "expirado"
        except:
            pass
        local["offline"] = True
        return local

    # Nunca registado e sem internet
    return {"estado": "nao_registado", "dias_restantes": 0}

def ativar(email, chave):
    """Activa licença com email e chave"""
    machine_id = get_machine_id()
    resultado = _post("/api/ativar", {
        "machine_id": machine_id,
        "email": email,
        "chave": chave
    })
    if resultado and resultado.get("ok"):
        local = _carregar_local()
        local["estado"] = "ativo"
        local["email"] = email
        _guardar_local(local)
    return resultado

def licenca_valida():
    """Retorna True se pode usar a app (trial válido ou activo)"""
    estado = verificar()
    return estado.get("estado") in ("trial","ativo") and estado.get("dias_restantes",0) > 0
