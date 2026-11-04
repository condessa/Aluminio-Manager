"""
validacoes.py — Validações e formatação de campos
"""
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator

def aplicar_mascara_cp(inp: QLineEdit):
    """Aplica validação de código postal xxxx-xxx"""
    inp.setPlaceholderText("0000-000")
    inp.setMaxLength(8)
    inp.textChanged.connect(lambda t: _aplicar_cp(inp, t))

def _aplicar_cp(inp, texto):
    # Extrair só dígitos
    digits = ''.join(c for c in texto if c.isdigit())[:7]
    if len(digits) > 4:
        novo = digits[:4] + '-' + digits[4:]
    else:
        novo = digits
    if texto != novo:
        inp.blockSignals(True)
        inp.setText(novo)
        inp.setCursorPosition(len(novo))
        inp.blockSignals(False)

def aplicar_mascara_telefone(inp: QLineEdit):
    """Só permite 9 dígitos"""
    inp.setMaxLength(9)
    validator = QRegularExpressionValidator(QRegularExpression(r'[0-9]{0,9}'))
    inp.setValidator(validator)
    inp.setPlaceholderText("9 dígitos")

def aplicar_validacao_email(inp: QLineEdit):
    """Valida email em tempo real — fica vermelho se inválido"""
    from modules.temas import PALETA as _C

    def _verificar(texto):
        if texto and "@" not in texto:
            inp.setStyleSheet(
                f"border:1px solid {_C['danger']}; background:{_C['erro_fundo']};"
                f"color:{_C['aco']}; border-radius:4px; padding:4px 8px;")
        else:
            inp.setStyleSheet(
                f"border:1px solid {_C['alum_mid']}; background:{_C['cartao']};"
                f"color:{_C['aco']}; border-radius:4px; padding:4px 8px;")
    inp.textChanged.connect(_verificar)

def validar_cp(texto):
    import re
    return bool(re.match(r'^\d{4}-\d{3}$', texto)) or texto == ""

def validar_telefone(texto):
    return (len(texto) == 9 and texto.isdigit()) or texto == ""

def validar_email(texto):
    return "@" in texto or texto == ""

def aplicar_mascara_nif(inp: QLineEdit):
    """Só permite 9 dígitos para NIF"""
    inp.setMaxLength(9)
    validator = QRegularExpressionValidator(QRegularExpression(r'[0-9]{0,9}'))
    inp.setValidator(validator)
    inp.setPlaceholderText("9 dígitos")

def aplicar_mascara_ss(inp: QLineEdit):
    """Só permite 11 dígitos para Nº Seg. Social"""
    inp.setMaxLength(11)
    validator = QRegularExpressionValidator(QRegularExpression(r'[0-9]{0,11}'))
    inp.setValidator(validator)
    inp.setPlaceholderText("11 dígitos")

def aplicar_mascara_iban(inp: QLineEdit):
    """Formata IBAN português: PT50 XXXX XXXX XXXX XXXX XXXX X (25 chars + 5 espaços = 30)"""
    inp.setMaxLength(31)
    inp.setPlaceholderText("PT50 0000 0000 0000 0000 0000 0")
    inp.textChanged.connect(lambda t: _aplicar_iban(inp, t))

def _aplicar_iban(inp, texto):
    chars = ''.join(c for c in texto.upper() if c.isalnum())[:25]
    grupos = [chars[i:i+4] for i in range(0, len(chars), 4)]
    novo = ' '.join(grupos)
    if texto != novo:
        inp.blockSignals(True)
        inp.setText(novo)
        inp.setCursorPosition(len(novo))
        inp.blockSignals(False)
