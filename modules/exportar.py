"""
exportar.py — Exportação de dados para Excel e CSV
Aluminio-Manager
"""
import csv
import io
from datetime import datetime
from pathlib import Path

def _timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def exportar_excel(titulo, colunas, linhas, caminho):
    """Gera ficheiro Excel com formatação básica."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = titulo[:31]

    # Cabeçalho
    fill_header = PatternFill("solid", fgColor="1A2332")
    font_header = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        bottom=Side(style="thin", color="D4560A")
    )

    for c, col in enumerate(colunas, 1):
        cell = ws.cell(row=1, column=c, value=col)
        cell.fill = fill_header
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    # Linhas alternadas
    fill_alt = PatternFill("solid", fgColor="F0F4F8")
    font_normal = Font(size=10)

    for r, linha in enumerate(linhas, 2):
        for c, val in enumerate(linha, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.font = font_normal
            cell.alignment = Alignment(vertical="center")
            if r % 2 == 0:
                cell.fill = fill_alt

    # Ajustar largura das colunas
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    # Linha de rodapé com data
    ws.freeze_panes = "A2"
    wb.save(caminho)
    return caminho

def exportar_csv(colunas, linhas, caminho):
    """Gera ficheiro CSV."""
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(colunas)
        writer.writerows(linhas)
    return caminho

def dialogo_exportar(parent, titulo, colunas, linhas):
    """Mostra diálogo de escolha de formato e guarda o ficheiro."""
    from PyQt6.QtWidgets import QFileDialog, QMessageBox
    import subprocess, platform

    nome_default = f"{titulo.lower().replace(' ','_')}_{_timestamp()}"

    caminho, filtro = QFileDialog.getSaveFileName(
        parent,
        f"Exportar {titulo}",
        nome_default,
        "Excel (*.xlsx);;CSV (*.csv)"
    )
    if not caminho:
        return

    try:
        if filtro.startswith("Excel") or caminho.endswith(".xlsx"):
            if not caminho.endswith(".xlsx"):
                caminho += ".xlsx"
            exportar_excel(titulo, colunas, linhas, caminho)
        else:
            if not caminho.endswith(".csv"):
                caminho += ".csv"
            exportar_csv(colunas, linhas, caminho)

        resposta = QMessageBox.question(
            parent, "✅ Exportado com sucesso",
            f"Ficheiro guardado em:\n{caminho}\n\nAbrir agora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            if platform.system() == "Windows":
                import os; os.startfile(caminho)
            else:
                subprocess.Popen(["xdg-open", caminho])
    except Exception as e:
        QMessageBox.critical(parent, "Erro ao exportar", str(e))
