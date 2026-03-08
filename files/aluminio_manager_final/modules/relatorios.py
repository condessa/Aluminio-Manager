from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QGridLayout,QDialog,QTextBrowser,QFileDialog,QMessageBox,QFrame,QScrollArea,QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter,QPrintDialog
from PyQt6.QtGui import QTextDocument
from datetime import date
CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b","success":"#1e7e44","warning":"#b8700a"}

def gerar_html_obras(dao):
    try: obras=dao.listar_obras()
    except: obras=[]
    rows="".join(f"<tr><td>{o['numero']}</td><td>{o.get('cliente_nome','—')}</td><td>{o['descricao']}</td><td>{o['estado'].replace('_',' ').title()}</td><td>{o.get('valor_orcamento',0):.2f} €</td><td>{o.get('data_entrada','—')}</td></tr>" for o in obras)
    return f"""<html><body style='font-family:Segoe UI,Arial;padding:20px;color:#1a2332'>
    <h2 style='color:#d4560a'>📋 Relatório de Obras — {date.today().strftime('%d/%m/%Y')}</h2>
    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;font-size:12px'>
    <tr style='background:#e8edf2;font-weight:bold'><th>Nº</th><th>Cliente</th><th>Descrição</th><th>Estado</th><th>Orçamento</th><th>Data</th></tr>
    {rows}</table><p style='font-size:11px;color:#6b7c8e'>Total: {len(obras)} obras</p></body></html>"""

def gerar_html_financeiro(dao):
    try:
        movs=dao.listar_financeiro(); res=dao.resumo_financeiro()
    except: movs=[]; res={"receitas":0,"despesas":0,"saldo":0}
    rows="".join(f"<tr><td>{m.get('data_mov','—')}</td><td style='color:{'green' if m['tipo']=='receita' else 'red'}'>{m['tipo'].title()}</td><td>{m.get('descricao','—')}</td><td style='text-align:right;font-weight:bold;color:{'green' if m['tipo']=='receita' else 'red'}'>{'+' if m['tipo']=='receita' else '-'}{float(m.get('valor',0)):.2f} €</td></tr>" for m in movs)
    return f"""<html><body style='font-family:Segoe UI,Arial;padding:20px;color:#1a2332'>
    <h2 style='color:#d4560a'>💶 Relatório Financeiro — {date.today().strftime('%d/%m/%Y')}</h2>
    <div style='display:flex;gap:20px;margin-bottom:16px'>
    <div style='background:#d4edda;border-radius:8px;padding:12px 20px'><div style='font-size:11px;color:#6b7c8e'>RECEITAS</div><div style='font-size:22px;font-weight:bold;color:#1e7e44'>{res['receitas']:.2f} €</div></div>
    <div style='background:#fde8e0;border-radius:8px;padding:12px 20px'><div style='font-size:11px;color:#6b7c8e'>DESPESAS</div><div style='font-size:22px;font-weight:bold;color:#c0392b'>{res['despesas']:.2f} €</div></div>
    <div style='background:#e8edf2;border-radius:8px;padding:12px 20px'><div style='font-size:11px;color:#6b7c8e'>SALDO</div><div style='font-size:22px;font-weight:bold;color:#1a2332'>{res['saldo']:.2f} €</div></div></div>
    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;font-size:12px'>
    <tr style='background:#e8edf2;font-weight:bold'><th>Data</th><th>Tipo</th><th>Descrição</th><th>Valor</th></tr>{rows}</table></body></html>"""

def gerar_html_stock(dao):
    try: items=dao.listar_stock()
    except: items=[]
    rows="".join(f"<tr {'style=background:#fde8e0' if float(s.get('quantidade',0))<=float(s.get('qtd_minima',0)) else ''}><td>{s['referencia']}</td><td>{s['descricao']}</td><td>{s.get('quantidade',0)} {s.get('unidade','')}</td><td>{s.get('qtd_minima',0)}</td><td>{float(s.get('preco_custo',0)):.2f} €</td><td>{s.get('fornecedor','—')}</td></tr>" for s in items)
    baixo=sum(1 for s in items if float(s.get("quantidade",0))<=float(s.get("qtd_minima",0)))
    return f"""<html><body style='font-family:Segoe UI,Arial;padding:20px;color:#1a2332'>
    <h2 style='color:#d4560a'>📦 Relatório de Stock — {date.today().strftime('%d/%m/%Y')}</h2>
    <p style='background:#fde8e0;border-radius:6px;padding:8px 14px;display:inline-block'><b>⚠️ {baixo} artigos</b> abaixo do stock mínimo (fundo vermelho)</p>
    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;font-size:12px'>
    <tr style='background:#e8edf2;font-weight:bold'><th>Referência</th><th>Descrição</th><th>Quantidade</th><th>Mín.</th><th>Custo</th><th>Fornecedor</th></tr>
    {rows}</table></body></html>"""

def gerar_html_sobras(dao):
    try: sobras=dao.listar_sobras()
    except: sobras=[]
    rows="".join(f"<tr><td>{s.get('material','—')}</td><td>{s.get('referencia','—')}</td><td>{s['quantidade']} {s.get('unidade','')}</td><td>{s.get('comprimento_cm','—')} cm</td><td>{s['estado']}</td><td>{s.get('obra_numero','—')}</td></tr>" for s in sobras)
    return f"""<html><body style='font-family:Segoe UI,Arial;padding:20px;color:#1a2332'>
    <h2 style='color:#d4560a'>♻️ Relatório de Sobras — {date.today().strftime('%d/%m/%Y')}</h2>
    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;font-size:12px'>
    <tr style='background:#e8edf2;font-weight:bold'><th>Material</th><th>Ref.</th><th>Quantidade</th><th>Comprimento</th><th>Estado</th><th>Obra</th></tr>
    {rows}</table><p style='font-size:11px;color:#6b7c8e'>Total: {len(sobras)} registos</p></body></html>"""

class RelatorioViewer(QDialog):
    def __init__(self, titulo, html, parent=None):
        super().__init__(parent); self.setWindowTitle(titulo); self.resize(820,620); self.html=html
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)
        self.browser=QTextBrowser(); self.browser.setHtml(html); lay.addWidget(self.browser)
        btn_row=QHBoxLayout()
        bp=QPushButton("🖨️  Imprimir"); bp.setObjectName("btn_primary"); bp.setCursor(Qt.CursorShape.PointingHandCursor); bp.clicked.connect(self._imprimir)
        bh=QPushButton("💾  Guardar HTML"); bh.setObjectName("btn_outline"); bh.setCursor(Qt.CursorShape.PointingHandCursor); bh.clicked.connect(self._guardar)
        bc=QPushButton("Fechar"); bc.setObjectName("btn_outline"); bc.setCursor(Qt.CursorShape.PointingHandCursor); bc.clicked.connect(self.reject)
        btn_row.addWidget(bp); btn_row.addWidget(bh); btn_row.addStretch(); btn_row.addWidget(bc)
        lay.addLayout(btn_row)
    def _imprimir(self):
        printer=QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg=QPrintDialog(printer,self)
        if dlg.exec()==QPrintDialog.DialogCode.Accepted:
            doc=QTextDocument(); doc.setHtml(self.html); doc.print(printer)
    def _guardar(self):
        path,_=QFileDialog.getSaveFileName(self,"Guardar HTML","","HTML (*.html)")
        if path:
            with open(path,"w",encoding="utf-8") as f: f.write(self.html)
            QMessageBox.information(self,"Guardado",f"Relatório guardado em:\n{path}")

class RelatoriosWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        sa=QScrollArea(self); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.Shape.NoFrame)
        QVBoxLayout(self).addWidget(sa); cw=QWidget(); sa.setWidget(cw)
        lay=QVBoxLayout(cw); lay.setContentsMargins(20,20,20,20); lay.setSpacing(16)
        tit=QLabel("Gerar Relatórios"); tit.setStyleSheet(f"font-size:16px;font-weight:700;color:{CORES['aco']};")
        lay.addWidget(tit)
        grid=QGridLayout(); grid.setSpacing(16)
        rels=[
            ("📋","Obras","Lista completa de obras com estados e valores","btn_primary",lambda: self._gerar("obras")),
            ("💶","Financeiro","Resumo de receitas, despesas e saldo","btn_primary",lambda: self._gerar("financeiro")),
            ("📦","Stock","Inventário completo com alertas de reposição","btn_primary",lambda: self._gerar("stock")),
            ("♻️","Sobras","Registo de sobras e desperdícios","btn_primary",lambda: self._gerar("sobras")),
        ]
        for i,(ico,nome,desc,obj,fn) in enumerate(rels):
            card=QFrame(); card.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:14px;")
            card.mousePressEvent=lambda e,f=fn: f()
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            cl=QVBoxLayout(card); cl.setContentsMargins(24,24,24,24); cl.setSpacing(8)
            il=QLabel(ico); il.setStyleSheet("font-size:36px;background:transparent;")
            nl=QLabel(nome); nl.setStyleSheet(f"font-size:15px;font-weight:700;color:{CORES['aco']};background:transparent;")
            dl=QLabel(desc); dl.setStyleSheet(f"font-size:12px;color:{CORES['cinza']};background:transparent;")
            dl.setWordWrap(True)
            btn=QPushButton("Gerar Relatório →"); btn.setObjectName(obj); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.clicked.connect(fn)
            for w in [il,nl,dl,btn]: cl.addWidget(w)
            grid.addWidget(card,i//2,i%2)
        lay.addLayout(grid); lay.addStretch()
    def refresh(self): pass
    def _gerar(self,tipo):
        geradores={"obras":("📋 Relatório de Obras",gerar_html_obras),"financeiro":("💶 Relatório Financeiro",gerar_html_financeiro),"stock":("📦 Relatório de Stock",gerar_html_stock),"sobras":("♻️ Relatório de Sobras",gerar_html_sobras)}
        titulo,fn=geradores[tipo]
        html=fn(self.dao)
        d=RelatorioViewer(titulo,html,parent=self); d.exec()
