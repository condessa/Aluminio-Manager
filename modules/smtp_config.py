"""Envio de email por SMTP genérico (conta da oficina).

Permite usar qualquer fornecedor: Outlook/Microsoft 365, SAPO, domínio próprio, etc.
A configuração fica guardada na tabela «oficina».
"""

import smtplib
import ssl

SEGURANCA = {
    "starttls": "STARTTLS (normalmente porta 587)",
    "ssl": "SSL (normalmente porta 465)",
    "nenhuma": "Sem segurança (normalmente porta 25)",
}


def configurado(oficina):
    return bool(
        (oficina.get("smtp_host") or "").strip()
        and (oficina.get("smtp_user") or "").strip()
        and (oficina.get("smtp_pass") or "").strip()
    )


def valores(oficina):
    try:
        porta = int(oficina.get("smtp_port") or 587)
    except (TypeError, ValueError):
        porta = 587
    return {
        "host": (oficina.get("smtp_host") or "").strip(),
        "port": porta,
        "user": (oficina.get("smtp_user") or "").strip(),
        "password": oficina.get("smtp_pass") or "",
        "security": (oficina.get("smtp_seguranca") or "starttls").strip() or "starttls",
        "email": (oficina.get("email") or "").strip(),
    }


def _ligar(cfg):
    if cfg["security"] == "ssl":
        return smtplib.SMTP_SSL(
            cfg["host"], cfg["port"], timeout=20, context=ssl.create_default_context())
    ligacao = smtplib.SMTP(cfg["host"], cfg["port"], timeout=20)
    if cfg["security"] == "starttls":
        ligacao.starttls(context=ssl.create_default_context())
    return ligacao


def testar(cfg):
    try:
        with _ligar(cfg) as ligacao:
            if cfg["user"]:
                ligacao.login(cfg["user"], cfg["password"])
        return True, "Ligação ao servidor de email bem-sucedida."
    except Exception as erro:
        return False, _mensagem(erro)


def enviar(msg, cfg):
    with _ligar(cfg) as ligacao:
        ligacao.login(cfg["user"], cfg["password"])
        ligacao.send_message(msg)


def _mensagem(erro):
    texto = str(erro)
    baixo = texto.lower()
    if "authentication" in baixo or "535" in texto or "534" in texto or "username" in baixo:
        return ("O servidor recusou o utilizador ou a palavra-passe.\n\n"
                "Muitos fornecedores exigem uma «palavra-passe de aplicação» em vez da "
                "palavra-passe normal da conta.")
    if "timed out" in baixo or "110" in texto or "getaddrinfo" in baixo:
        return "O servidor não respondeu. Verifique o endereço, a porta e a ligação à Internet."
    if "certificate" in baixo or "ssl" in baixo:
        return ("Falha na ligação segura. Experimente outra opção de segurança "
                "(STARTTLS em vez de SSL, ou o contrário).")
    return texto


def guardar(cfg):
    from modules.configuracao import guardar_oficina

    guardar_oficina({
        "smtp_host": cfg["host"],
        "smtp_port": str(cfg["port"]),
        "smtp_user": cfg["user"],
        "smtp_pass": cfg["password"],
        "smtp_seguranca": cfg["security"],
        "email": cfg.get("email") or "",
    })


def desligar():
    from modules.configuracao import guardar_oficina

    guardar_oficina({
        "smtp_host": "", "smtp_port": "", "smtp_user": "",
        "smtp_pass": "", "smtp_seguranca": "",
    })
