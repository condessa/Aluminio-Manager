from modules.temas import cor_texto
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDoubleSpinBox,
    QDateEdit,QTextEdit,QMessageBox,QFrame,QTabWidget,QDialogButtonBox)
from PyQt6.QtCore import Qt,QDate

CATS_RECEITA=["Adiantamento","Pagamento final","Pagamento parcial","Serviço","Venda material","Outro"]
CATS_DESPESA=["Material","Mão de obra","Equipamento","Combustível","Fornecedor","Subcontratado","Impostos","Outro"]
METODOS=["Numerário","Transferência","Cheque","MB","MBWay","Outro"]

def _btn(t,o):
    b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

class FinanceiroDialog(QDialog):
    def __init__(self,dao,user,mov=None,obra_id=None,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.mov=mov
        self.setWindowTitle("Novo Movimento" if not mov else "Editar Movimento")
        self.setMinimumWidth(500); self.resize(520,540)
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)

        # Tipo
        tw=QWidget(); tl=QHBoxLayout(tw); tl.setContentsMargins(0,0,0,0); tl.setSpacing(12)
        self.cmb_tipo=QComboBox(); self.cmb_tipo.addItems(["receita","despesa"])
        tl.addWidget(QLabel("Tipo:")); tl.addWidget(self.cmb_tipo); tl.addStretch()
        lay.addWidget(tw)

        form=QFormLayout(); form.setSpacing(10)

        # Categoria
        self.cmb_cat=QComboBox()
        form.addRow("Categoria:",self.cmb_cat)

        # Descrição
        self.txt_desc=QLineEdit(); self.txt_desc.setPlaceholderText("Descrição do movimento")
        form.addRow("Descrição:",self.txt_desc)

        # Valor
        self.spn_valor=QDoubleSpinBox(); self.spn_valor.setMaximum(999999); self.spn_valor.setDecimals(2); self.spn_valor.setSuffix(" €")
        form.addRow("Valor:",self.spn_valor)

        # Data
        self.dte_data=QDateEdit(); self.dte_data.setCalendarPopup(True); self.dte_data.setDate(QDate.currentDate())
        form.addRow("Data:",self.dte_data)

        # Método pagamento
        self.cmb_metodo=QComboBox(); self.cmb_metodo.addItems(METODOS)
        form.addRow("Método:",self.cmb_metodo)

        # Obra associada
        self.cmb_obra=QComboBox(); self.cmb_obra.addItem("— Sem obra —", None)
        try:
            obras=dao.listar_obras()
            for o in obras:
                self.cmb_obra.addItem(f"Obra #{o['numero']} – {o.get('cliente_nome','')}", o['id'])
        except: pass
        form.addRow("Obra:",self.cmb_obra)

        # Pago
        self.cmb_pago=QComboBox(); self.cmb_pago.addItems(["Sim","Não"])
        form.addRow("Pago:",self.cmb_pago)

        # Notas
        self.txt_notas=QTextEdit(); self.txt_notas.setMaximumHeight(70)
        form.addRow("Notas:",self.txt_notas)

        lay.addLayout(form)

        # Botões
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject)
        lay.addWidget(bb)

        # Ligar sinal tipo
        self.cmb_tipo.currentTextChanged.connect(self._atualizar_cats)
        self._atualizar_cats(self.cmb_tipo.currentText())

        # Preencher se editar
        if mov:
            self.cmb_tipo.setCurrentText(mov.get("tipo","receita"))
            self.txt_desc.setText(mov.get("descricao",""))
            self.spn_valor.setValue(float(mov.get("valor",0)))
            if mov.get("data"):
                try:
                    from datetime import date
                    d=str(mov["data"])[:10].split("-")
                    self.dte_data.setDate(QDate(int(d[0]),int(d[1]),int(d[2])))
                except: pass
            if mov.get("metodo"): self.cmb_metodo.setCurrentText(mov["metodo"])
            if mov.get("categoria"): self.cmb_cat.setCurrentText(mov["categoria"])
            self.cmb_pago.setCurrentText("Sim" if mov.get("pago") else "Não")
            if mov.get("obra_id"):
                idx=self.cmb_obra.findData(mov["obra_id"])
                if idx>=0: self.cmb_obra.setCurrentIndex(idx)
            if mov.get("notas"): self.txt_notas.setPlainText(mov["notas"])

        # Pré-seleccionar obra
        if obra_id and not mov:
            idx=self.cmb_obra.findData(obra_id)
            if idx>=0: self.cmb_obra.setCurrentIndex(idx)

    def _atualizar_cats(self,tipo):
        self.cmb_cat.clear()
        self.cmb_cat.addItems(CATS_RECEITA if tipo=="receita" else CATS_DESPESA)

    def _guardar(self):
        if not self.txt_desc.text().strip():
            QMessageBox.warning(self,"Atenção","Preenche a descrição."); return
        if self.spn_valor.value()<=0:
            QMessageBox.warning(self,"Atenção","O valor deve ser maior que zero."); return
        d={
            "tipo":self.cmb_tipo.currentText(),
            "categoria":self.cmb_cat.currentText(),
            "descricao":self.txt_desc.text().strip(),
            "valor":self.spn_valor.value(),
            "data":self.dte_data.date().toString("yyyy-MM-dd"),
            "metodo":self.cmb_metodo.currentText(),
            "obra_id":self.cmb_obra.currentData(),
            "pago":1 if self.cmb_pago.currentText()=="Sim" else 0,
            "notas":self.txt_notas.toPlainText().strip(),
        }
        if self.mov: d["id"]=self.mov["id"]
        try:
            self.dao.salvar_financeiro(d); self.accept()
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e))


class ObraFinanceiroDialog(QDialog):
    """Diálogo de detalhe financeiro de uma obra"""
    def __init__(self,dao,obra,parent=None):
        super().__init__(parent); self.dao=dao; self.obra=obra
        self.setWindowTitle(f"Financeiro — Obra #{obra['numero']}")
        self.setMinimumWidth(600); self.resize(650,500)
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)

        # Resumo
        orcamento=float(obra.get("valor_orcamento") or obra.get("valor") or 0)
        try:
            movs=self.dao.listar_financeiro(obra_id=obra["id"])
        except:
            movs=[]
        total_rec=sum(float(m["valor"]) for m in movs if m["tipo"]=="receita")
        total_desp=sum(float(m["valor"]) for m in movs if m["tipo"]=="despesa")
        saldo=orcamento-total_rec

        frame=QFrame(); frame.setStyleSheet("QFrame{background:#1a2332;border-radius:8px;padding:8px;}")
        fl=QHBoxLayout(frame)
        for label,val,cor in [
            ("Orçamento",f"{orcamento:,.2f} €","#e8edf2"),
            ("Recebido",f"{total_rec:,.2f} €","#1e7e44"),
            ("Despesas",f"{total_desp:,.2f} €","#c0392b"),
            ("Em falta",f"{saldo:,.2f} €","#d4560a" if saldo>0 else "#1e7e44"),
        ]:
            col=QWidget(); cl=QVBoxLayout(col); cl.setSpacing(2)
            lv=QLabel(f"{val}"); lv.setStyleSheet(f"color:{cor};font-size:16px;font-weight:bold;")
            ll=QLabel(label); ll.setStyleSheet("color:#8899aa;font-size:11px;")
            cl.addWidget(lv); cl.addWidget(ll); fl.addWidget(col)
        lay.addWidget(frame)

        # Tabela movimentos
        self.tbl=QTableWidget(0,5)
        self.tbl.setHorizontalHeaderLabels(["Tipo","Categoria","Descrição","Valor","Data"])
        self.tbl.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.tbl)

        # Botão novo
        btn_novo=_btn("+ Novo movimento","btn_primary")
        btn_novo.clicked.connect(self._novo_mov)
        lay.addWidget(btn_novo)

        self._preencher(movs)

    def _preencher(self,movs):
        self.tbl.setRowCount(0)
        for m in movs:
            r=self.tbl.rowCount(); self.tbl.insertRow(r)
            tipo=m.get("tipo","")
            cor="#1e7e44" if tipo=="receita" else "#c0392b"
            for c,v in enumerate([tipo,m.get("categoria",""),m.get("descricao",""),
                                   f"{float(m.get('valor',0)):,.2f} €",str(m.get("data",""))[:10]]):
                item=QTableWidgetItem(v); item.setForeground(QColor(cor if c==0 else cor_texto()))
                self.tbl.setItem(r,c,item)

    def _exportar(self):
        try:
            colunas = ["Tipo","Categoria","Descrição","Valor (€)","Data","Pago","Obra"]
            linhas = [[
                m.get("tipo",""), m.get("categoria",""), m.get("descricao",""),
                float(m.get("valor",0)), str(m.get("data",""))[:10],
                "Sim" if m.get("pago") else "Não",
                m.get("obra_numero","") or ""
            ] for m in self._movs]
            from modules.exportar import dialogo_exportar
            dialogo_exportar(self, "Financeiro", colunas, linhas)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro", str(e))

    def _novo_mov(self):
        d=FinanceiroDialog(self.dao,None,obra_id=self.obra["id"],parent=self)
        if d.exec():
            try: movs=self.dao.listar_financeiro(obra_id=self.obra["id"]); self._preencher(movs)
            except: pass


class FinanceiroWidget(QWidget):
    def __init__(self,dao,user,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)

        # Título e botão
        top=QHBoxLayout()
        tit=QLabel("💰 Financeiro"); tit.setStyleSheet("font-size:20px;font-weight:bold;color:#1a2332;")
        top.addWidget(tit); top.addStretch()
        btn_novo=_btn("+ Novo Movimento","btn_primary")
        btn_novo.clicked.connect(self._novo_mov)
        top.addWidget(btn_novo)
        lay.addLayout(top)

        # Resumo cards
        self.frame_resumo=QFrame()
        self.frame_resumo.setStyleSheet("QFrame{background:#1a2332;border-radius:8px;padding:4px;}")
        self.frame_resumo.setFixedHeight(70)
        self.lay_resumo=QHBoxLayout(self.frame_resumo)
        self.lay_resumo.setContentsMargins(8,4,8,4)
        lay.addWidget(self.frame_resumo)

        # Filtros
        fil=QHBoxLayout()
        self.txt_filtro=QLineEdit(); self.txt_filtro.setPlaceholderText("🔍 Pesquisar..."); self.txt_filtro.textChanged.connect(self.refresh)
        self.cmb_filtro_tipo=QComboBox(); self.cmb_filtro_tipo.addItems(["Todos","receita","despesa"]); self.cmb_filtro_tipo.currentTextChanged.connect(self.refresh)
        fil.addWidget(self.txt_filtro); fil.addWidget(self.cmb_filtro_tipo)
        lay.addLayout(fil)

        # Tabela
        self.tbl=QTableWidget(0,7)
        self.tbl.setHorizontalHeaderLabels(["Tipo","Categoria","Descrição","Valor","Data","Pago","Obra"])
        hh=self.tbl.horizontalHeader()
        hh.setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3,QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5,QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(6,QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.setColumnWidth(5,55)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.doubleClicked.connect(self._ver_detalhe)
        lay.addWidget(self.tbl)

        # Acções
        ac=QHBoxLayout()
        btn_exp=_btn("📤 Exportar","btn_outline"); btn_exp.clicked.connect(self._exportar)
        btn_ed=_btn("✏️ Editar","btn_secondary"); btn_ed.clicked.connect(self._editar)
        btn_del=_btn("🗑️ Eliminar","btn_danger"); btn_del.clicked.connect(self._eliminar)
        ac.addStretch(); ac.addWidget(btn_exp); ac.addWidget(btn_ed); ac.addWidget(btn_del)
        lay.addLayout(ac)

        self.refresh()

    def refresh(self):
        tipo=self.cmb_filtro_tipo.currentText()
        tipo=None if tipo=="Todos" else tipo
        filtro=self.txt_filtro.text().strip()
        try:
            movs=self.dao.listar_financeiro(filtro=filtro,tipo=tipo)
        except Exception as e:
            movs=[]

        # Atualizar resumo
        total_rec=sum(float(m["valor"]) for m in movs if m["tipo"]=="receita")
        total_desp=sum(float(m["valor"]) for m in movs if m["tipo"]=="despesa")
        saldo=total_rec-total_desp
        # limpar cards anteriores
        for i in reversed(range(self.lay_resumo.count())):
            item=self.lay_resumo.itemAt(i)
            if item and item.widget(): item.widget().deleteLater()
        for label,val,cor in [
            ("Total Receitas",f"{total_rec:,.2f} €","#1e7e44"),
            ("Total Despesas",f"{total_desp:,.2f} €","#c0392b"),
            ("Saldo",f"{saldo:,.2f} €","#1e7e44" if saldo>=0 else "#c0392b"),
        ]:
            col=QWidget(); cl=QVBoxLayout(col); cl.setSpacing(2)
            lv=QLabel(val); lv.setStyleSheet(f"color:{cor};font-size:15px;font-weight:bold;")
            ll=QLabel(label); ll.setStyleSheet("color:#8899aa;font-size:11px;")
            cl.addWidget(lv); cl.addWidget(ll); self.lay_resumo.addWidget(col)
        self.lay_resumo.addStretch()

        # Preencher tabela
        self.tbl.setRowCount(0)
        self._movs=movs
        for m in movs:
            r=self.tbl.rowCount(); self.tbl.insertRow(r)
            tipo_m=m.get("tipo","")
            cor="#1e7e44" if tipo_m=="receita" else "#c0392b"
            pago="✅" if m.get("pago") else "⏳"
            obra=m.get("obra_numero","") or ""
            pass  # obra já tem o número correto
            from PyQt6.QtGui import QColor
            bg_cor = QColor("#f0fff4") if tipo_m=="receita" else QColor("#fff5f5")
            for c,v in enumerate([tipo_m,m.get("categoria",""),m.get("descricao",""),
                                   f"{float(m.get('valor',0)):,.2f} €",
                                   str(m.get("data",""))[:10],pago,obra]):
                item=QTableWidgetItem(str(v))
                if c==0: item.setForeground(QColor(cor))
                if c==5: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(bg_cor)
                self.tbl.setItem(r,c,item)

    def _ver_detalhe(self, index):
        row = index.row()
        if row < 0 or row >= len(self._movs): return
        m = self._movs[row]
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLabel, QDialogButtonBox
        dlg = QDialog(self); dlg.setWindowTitle("Detalhe do Movimento"); dlg.setMinimumWidth(420)
        lay = QVBoxLayout(dlg); lay.setContentsMargins(20,20,20,20); lay.setSpacing(8)
        fl = QFormLayout(); fl.setSpacing(8)
        tipo_m = m.get("tipo","—")
        cor = "#1e7e44" if tipo_m=="receita" else "#c0392b"
        lbl_tipo = QLabel(tipo_m.upper())
        lbl_tipo.setStyleSheet(f"color:white;background:{cor};border-radius:6px;padding:2px 10px;font-weight:700;")
        fl.addRow("Tipo:", lbl_tipo)
        fl.addRow("Categoria:", QLabel(m.get("categoria","—")))
        fl.addRow("Descrição:", QLabel(m.get("descricao","—")))
        fl.addRow("Valor:", QLabel(f"{float(m.get('valor',0)):,.2f} €"))
        fl.addRow("Data:", QLabel(str(m.get("data","—"))[:10]))
        fl.addRow("Pago:", QLabel("✅ Sim" if m.get("pago") else "⏳ Não"))
        if m.get("obra_numero"):
            fl.addRow("Nº Obra:", QLabel(m.get("obra_numero","")))
        if m.get("obra_id"):
            try:
                obra = self.dao.get_obra(m["obra_id"])
                if obra:
                    fl.addRow("Cliente:", QLabel(obra.get("cliente_nome","—")))
                    fl.addRow("Descrição obra:", QLabel(obra.get("descricao","—")))
                    fl.addRow("Estado:", QLabel(obra.get("estado","—")))
                    val_orc = float(obra.get("valor_orcamento",0) or 0)
                    fl.addRow("Valor orçamento:", QLabel(f"{val_orc:,.2f} €"))
            except: pass
        lay.addLayout(fl)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(dlg.reject); lay.addWidget(bb)
        dlg.exec()

    def _exportar(self):
        try:
            colunas = ["Tipo","Categoria","Descrição","Valor (€)","Data","Pago","Obra"]
            linhas = [[
                m.get("tipo",""), m.get("categoria",""), m.get("descricao",""),
                float(m.get("valor",0)), str(m.get("data",""))[:10],
                "Sim" if m.get("pago") else "Não",
                m.get("obra_numero","") or ""
            ] for m in self._movs]
            from modules.exportar import dialogo_exportar
            dialogo_exportar(self, "Financeiro", colunas, linhas)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro", str(e))

    def _novo_mov(self):
        d=FinanceiroDialog(self.dao,self.user,parent=self)
        if d.exec(): self.refresh()

    def _editar(self):
        row=self.tbl.currentRow()
        if row<0: QMessageBox.information(self,"Info","Selecciona um movimento."); return
        mov=self._movs[row]
        d=FinanceiroDialog(self.dao,self.user,mov=mov,parent=self)
        if d.exec(): self.refresh()

    def _eliminar(self):
        row=self.tbl.currentRow()
        if row<0: QMessageBox.information(self,"Info","Selecciona um movimento."); return
        mov=self._movs[row]
        r=QMessageBox.question(self,"Confirmar",f"Eliminar '{mov.get('descricao','')}'?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.execute("DELETE FROM financeiro WHERE id=%s",(mov["id"],)); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
