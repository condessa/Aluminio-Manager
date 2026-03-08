from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,
    QComboBox,QDateEdit,QTextEdit,QFrame,QScrollArea,QTabWidget,QDoubleSpinBox,
    QGroupBox,QMessageBox,QSplitter)
from PyQt6.QtCore import Qt,QDate
from PyQt6.QtGui import QColor
CORES={"aco":"#1a2332","aco_mid":"#2c3e55","laranja":"#d4560a","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","success":"#1e7e44","danger":"#c0392b","warning":"#b8700a","info":"#1a6fa8"}
ESTADOS=["orcamento","confirmada","em_producao","em_montagem","concluida","cancelada","em_espera"]
TIPOS=["porta","janela","marquise","porta_de_correr","gradeamento","portao","cobertura","outro"]
PRIORIDADES=["normal","urgente","critica"]
ESTADO_COR={"orcamento":("#e8edf2","#4a6080"),"confirmada":("#fff3cd","#b8700a"),"em_producao":("#d4edda","#1e7e44"),"em_montagem":("#e8f0fa","#1a6fa8"),"concluida":("#d4edda","#1e7e44"),"cancelada":("#fde8e0","#c0392b"),"em_espera":("#e8edf2","#6b7c8e")}
PRI_COR={"normal":("#e8edf2","#4a6080"),"urgente":("#fff3cd","#b8700a"),"critica":("#fde8e0","#c0392b")}

def _btn(txt,obj): b=QPushButton(txt); b.setObjectName(obj); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

class ObraDialog(QDialog):
    def __init__(self,dao,user,obra=None,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.obra=obra
        self.setWindowTitle("Nova Obra" if not obra else f"Editar — {obra['numero']}")
        self.setMinimumWidth(620); self.resize(660,620)
        self._build()
        if obra: self._preencher()

    def _build(self):
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        tabs=QTabWidget(); lay.addWidget(tabs)
        # Tab 1 — Dados gerais
        t1=QWidget(); t1l=QFormLayout(t1); t1l.setSpacing(10)
        self.inp_num=QLineEdit(); self.inp_num.setReadOnly(bool(self.obra))
        self.inp_num.setText(self.dao.proximo_numero_obra() if not self.obra else self.obra["numero"])
        self.cmb_cli=QComboBox(); self._load_clientes()
        self.inp_desc=QLineEdit(); self.inp_desc.setPlaceholderText("Descrição da obra")
        self.cmb_tipo=QComboBox(); [self.cmb_tipo.addItem(t) for t in TIPOS]
        self.cmb_estado=QComboBox(); [self.cmb_estado.addItem(e) for e in ESTADOS]
        self.cmb_pri=QComboBox(); [self.cmb_pri.addItem(p) for p in PRIORIDADES]
        self.dt_entrada=QDateEdit(QDate.currentDate()); self.dt_entrada.setCalendarPopup(True)
        self.dt_prevista=QDateEdit(QDate.currentDate().addDays(30)); self.dt_prevista.setCalendarPopup(True)
        for lbl,w in [("Número",self.inp_num),("Cliente",self.cmb_cli),("Descrição",self.inp_desc),
                      ("Tipo",self.cmb_tipo),("Estado",self.cmb_estado),("Prioridade",self.cmb_pri),
                      ("Data entrada",self.dt_entrada),("Data prevista",self.dt_prevista)]:
            t1l.addRow(lbl,w)
        tabs.addTab(t1,"📋  Geral")
        # Tab 2 — Especificações
        t2=QWidget(); t2l=QFormLayout(t2); t2l.setSpacing(10)
        self.inp_cor=QLineEdit(); self.inp_cor.setPlaceholderText("ex: RAL 9016 Branco")
        self.inp_acab=QLineEdit(); self.inp_acab.setPlaceholderText("ex: Lacado, Termolacado, Anodizado")
        self.inp_vidro=QLineEdit(); self.inp_vidro.setPlaceholderText("ex: Duplo 4/16/4")
        self.inp_medidas=QTextEdit(); self.inp_medidas.setPlaceholderText("Medidas, quantidades, observações técnicas...")
        self.inp_medidas.setMaximumHeight(100)
        self.inp_morada=QLineEdit(); self.inp_morada.setPlaceholderText("Morada da instalação")
        for lbl,w in [("Cor / RAL",self.inp_cor),("Acabamento",self.inp_acab),("Vidro",self.inp_vidro),
                      ("Medidas/Qtds",self.inp_medidas),("Morada obra",self.inp_morada)]:
            t2l.addRow(lbl,w)
        tabs.addTab(t2,"📐  Especificações")
        # Tab 3 — Financeiro
        t3=QWidget(); t3l=QFormLayout(t3); t3l.setSpacing(10)
        self.inp_orc=QDoubleSpinBox(); self.inp_orc.setMaximum(999999); self.inp_orc.setSuffix(" €"); self.inp_orc.setDecimals(2)
        self.inp_fat=QDoubleSpinBox(); self.inp_fat.setMaximum(999999); self.inp_fat.setSuffix(" €"); self.inp_fat.setDecimals(2)
        self.inp_pago=QDoubleSpinBox(); self.inp_pago.setMaximum(999999); self.inp_pago.setSuffix(" €"); self.inp_pago.setDecimals(2)
        self.inp_notas=QTextEdit(); self.inp_notas.setPlaceholderText("Notas internas...")
        self.inp_notas.setMaximumHeight(80)
        for lbl,w in [("Orçamento",self.inp_orc),("Faturado",self.inp_fat),("Pago",self.inp_pago),("Notas",self.inp_notas)]:
            t3l.addRow(lbl,w)
        tabs.addTab(t3,"💶  Financeiro")
        # Botões
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)

    def _load_clientes(self):
        self.cmb_cli.addItem("— Sem cliente —",None)
        try:
            for c in self.dao.listar_clientes(): self.cmb_cli.addItem(c["nome"],c["id"])
        except: pass

    def _preencher(self):
        o=self.obra
        self.inp_desc.setText(o.get("descricao",""))
        idx=TIPOS.index(o["tipo_obra"]) if o.get("tipo_obra") in TIPOS else 0; self.cmb_tipo.setCurrentIndex(idx)
        idx=ESTADOS.index(o["estado"]) if o.get("estado") in ESTADOS else 0; self.cmb_estado.setCurrentIndex(idx)
        idx=PRIORIDADES.index(o["prioridade"]) if o.get("prioridade") in PRIORIDADES else 0; self.cmb_pri.setCurrentIndex(idx)
        if o.get("data_entrada"):
            try: self.dt_entrada.setDate(QDate.fromString(str(o["data_entrada"]),"yyyy-MM-dd"))
            except: pass
        if o.get("data_prevista"):
            try: self.dt_prevista.setDate(QDate.fromString(str(o["data_prevista"]),"yyyy-MM-dd"))
            except: pass
        self.inp_cor.setText(o.get("cor_perfil",""))
        self.inp_acab.setText(o.get("acabamento",""))
        self.inp_vidro.setText(o.get("vidro",""))
        self.inp_medidas.setPlainText(o.get("medidas",""))
        self.inp_morada.setText(o.get("morada_obra",""))
        self.inp_orc.setValue(float(o.get("valor_orcamento",0)))
        self.inp_fat.setValue(float(o.get("valor_faturado",0)))
        self.inp_pago.setValue(float(o.get("valor_pago",0)))
        self.inp_notas.setPlainText(o.get("notas",""))
        # cliente
        for i in range(self.cmb_cli.count()):
            if self.cmb_cli.itemData(i)==o.get("cliente_id"): self.cmb_cli.setCurrentIndex(i); break

    def _guardar(self):
        if not self.inp_desc.text().strip(): QMessageBox.warning(self,"Erro","Preencha a descrição."); return
        d={"descricao":self.inp_desc.text().strip(),"numero":self.inp_num.text().strip(),
           "cliente_id":self.cmb_cli.currentData(),"tipo_obra":self.cmb_tipo.currentText(),
           "estado":self.cmb_estado.currentText(),"prioridade":self.cmb_pri.currentText(),
           "data_entrada":self.dt_entrada.date().toString("yyyy-MM-dd"),
           "data_prevista":self.dt_prevista.date().toString("yyyy-MM-dd"),
           "cor_perfil":self.inp_cor.text(),"acabamento":self.inp_acab.text(),
           "vidro":self.inp_vidro.text(),"medidas":self.inp_medidas.toPlainText(),
           "morada_obra":self.inp_morada.text(),"valor_orcamento":self.inp_orc.value(),
           "valor_faturado":self.inp_fat.value(),"valor_pago":self.inp_pago.value(),
           "notas":self.inp_notas.toPlainText(),"responsavel_id":self.user.get("id")}
        if self.obra: d["id"]=self.obra["id"]
        try:
            obra_anterior = self.obra
            oid = self.dao.salvar_obra(d)
            if not obra_anterior:
                self.dao.criar_fases_obra(oid)

            # Sincronizar financeiro automaticamente
            from datetime import date as _date
            orc_novo = d["valor_orcamento"]
            fat_novo = d["valor_faturado"]
            pago_novo = d["valor_pago"]

            # Verificar o que já existe no financeiro para esta obra
            if oid:
                existente = self.dao.fetchone(
                    "SELECT SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END) AS rec FROM financeiro WHERE obra_id=%s",
                    (oid,))
                ja_recebido = float(existente["rec"] or 0) if existente else 0

                # Se valor pago aumentou, criar registo de recebimento
                if pago_novo > ja_recebido:
                    delta = pago_novo - ja_recebido
                    cat = "Adiantamento" if ja_recebido == 0 else "Pagamento parcial"
                    self.dao.salvar_financeiro({
                        "tipo": "receita",
                        "categoria": cat,
                        "descricao": f"Recebimento obra {d['numero']}",
                        "valor": delta,
                        "data": str(_date.today()),
                        "obra_id": oid,
                        "pago": 1
                    })

            self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))

class ObrasWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        # Filtros
        fbar=QWidget(); fbar.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fbar); fl.setContentsMargins(16,10,16,10); fl.setSpacing(10)
        self.inp_filtro=QLineEdit(); self.inp_filtro.setPlaceholderText("🔍  Pesquisar obra, cliente...")
        self.inp_filtro.setMaximumWidth(260); self.inp_filtro.textChanged.connect(self.refresh)
        self.cmb_estado=QComboBox(); self.cmb_estado.addItem("Todos os estados",None)
        [self.cmb_estado.addItem(e,e) for e in ESTADOS]; self.cmb_estado.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.inp_filtro); fl.addWidget(self.cmb_estado); fl.addStretch()
        lay.addWidget(fbar)
        # Tabela
        self.table=QTableWidget(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Número","Cliente","Descrição","Tipo","Estado","Prioridade","Data Entrada","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._abrir_detalhe)
        lay.addWidget(self.table)

    def refresh(self):
        filtro=self.inp_filtro.text(); estado=self.cmb_estado.currentData()
        try: obras=self.dao.listar_obras(filtro,estado)
        except: obras=[]
        self.table.setRowCount(len(obras))
        for r,o in enumerate(obras):
            bg_e,fg_e=ESTADO_COR.get(o["estado"],("#e8edf2","#4a6080"))
            bg_p,fg_p=PRI_COR.get(o["prioridade"],("#e8edf2","#4a6080"))
            vals=[o["numero"],o.get("cliente_nome","—"),o["descricao"],o.get("tipo_obra",""),
                  "","",(str(o["data_entrada"]) if o.get("data_entrada") else "—")]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,o["id"])
                self.table.setItem(r,c,item)
            # badge estado
            est_lbl=QLabel(o["estado"].replace("_"," ").title())
            est_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            est_lbl.setStyleSheet(f"background:{bg_e};color:{fg_e};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,4,est_lbl)
            pri_lbl=QLabel(o["prioridade"])
            pri_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pri_lbl.setStyleSheet(f"background:{bg_p};color:{fg_p};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,5,pri_lbl)
            # ações — menu dropdown
            from PyQt6.QtWidgets import QMenu
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2)
            bmenu=QPushButton("Ações ▾"); bmenu.setFixedHeight(28)
            bmenu.setStyleSheet("background:#e8edf2;border:1px solid #c8d4de;border-radius:6px;padding:0 10px;font-size:12px;font-weight:600;color:#1a2332;")
            bmenu.setCursor(Qt.CursorShape.PointingHandCursor)
            def _show_menu(checked, oid=o["id"], estado=o["estado"], btn=bmenu):
                menu=QMenu(btn)
                menu.addAction("✏️  Editar", lambda: self._editar(oid))
                menu.addAction("🖨️  Imprimir Orçamento", lambda: self._imprimir_orcamento(oid))
                menu.addAction("📋  Fases de produção", lambda: self._fases(oid))
                menu.addSeparator()
                ESTADOS_MAP={"orcamento":"Orçamento","confirmada":"Confirmada","em_producao":"Em Produção",
                             "em_montagem":"Em Montagem","concluida":"Concluída","cancelada":"Cancelada"}
                sub=menu.addMenu("🔄  Mudar estado")
                for est_key,est_label in ESTADOS_MAP.items():
                    a=sub.addAction(("✓  " if est_key==estado else "    ")+est_label)
                    a.triggered.connect(lambda checked,ek=est_key,oid2=oid: self.dao.execute("UPDATE obras SET estado=%s WHERE id=%s",(ek,oid2)) or self.refresh())
                menu.addSeparator()
                menu.addAction("🗑️  Eliminar", lambda: self._eliminar(oid))
                menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
            bmenu.clicked.connect(_show_menu)
            al.addWidget(bmenu)
            self.table.setCellWidget(r,7,acoes)
        self.table.resizeRowsToContents()

    def _imprimir_orcamento(self,oid):
        try: obra=self.dao.get_obra(oid)
        except: return
        from modules.orcamento import OrcamentoDialog
        d=OrcamentoDialog(self.dao,obra,parent=self)
        d.exec()

    def _mudar_estado(self,oid,estado_atual):
        from PyQt6.QtWidgets import QInputDialog
        ESTADOS_LISTA=["orcamento","confirmada","em_producao","em_montagem","concluida","cancelada"]
        LABELS={"orcamento":"Orçamento","confirmada":"Confirmada","em_producao":"Em Produção",
                "em_montagem":"Em Montagem","concluida":"Concluída","cancelada":"Cancelada"}
        # Próximo estado sugerido
        idx=ESTADOS_LISTA.index(estado_atual) if estado_atual in ESTADOS_LISTA else 0
        opcoes=[LABELS[e] for e in ESTADOS_LISTA]
        escolha,ok=QInputDialog.getItem(self,"Mudar Estado","Novo estado da obra:",opcoes,idx,False)
        if ok:
            novo=ESTADOS_LISTA[opcoes.index(escolha)]
            try:
                self.dao.execute("UPDATE obras SET estado=%s WHERE id=%s",(novo,oid))
                self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))

    def novo(self):
        d=ObraDialog(self.dao,self.user,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _editar(self,oid):
        try: obra=self.dao.get_obra(oid)
        except: return
        d=ObraDialog(self.dao,self.user,obra,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _eliminar(self,oid):
        r=QMessageBox.question(self,"Eliminar obra","Tem a certeza? Esta acção não pode ser desfeita.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.execute("DELETE FROM obras WHERE id=%s",(oid,)); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))

    def _fases(self,oid):
        try: obra=self.dao.get_obra(oid)
        except: return
        d=FasesDialog(self.dao,self.user,obra,parent=self); d.exec()

    def _abrir_detalhe(self,idx):
        oid=self.table.item(idx.row(),0).data(Qt.ItemDataRole.UserRole)
        if oid: self._editar(oid)

class FasesDialog(QDialog):
    FASE_ICO={"corte":"✂️","furação":"🔩","montagem":"🔧","vidro":"🪟","acabamento":"🎨","instalacao":"🏗️","revisao":"🔍","entrega":"🚚"}
    FASE_ESTADOS=[("pendente","Pendente"),("em_curso","Em Curso"),("concluida","Concluída"),("bloqueada","Bloqueada")]
    FASE_COR={"pendente":("#e8edf2","#4a6080"),"em_curso":("#fff3cd","#b8700a"),"concluida":("#d4edda","#1e7e44"),"bloqueada":("#fde8e0","#c0392b")}
    FASES_STD=["corte","furação","montagem","vidro","acabamento","instalacao","revisao","entrega"]

    def __init__(self,dao,user,obra,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.obra=obra
        self.setWindowTitle(f"Fases — {obra['numero']}"); self.setMinimumWidth(560); self.resize(600,520)
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        tit=QLabel(f"🔨  {obra['descricao']}"); tit.setStyleSheet(f"font-size:14px;font-weight:700;color:{CORES['aco']};")
        lay.addWidget(tit)
        self.fases_lay=QVBoxLayout(); self.fases_lay.setSpacing(6)
        cw=QWidget(); cw.setLayout(self.fases_lay)
        sa=QScrollArea(); sa.setWidget(cw); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.Shape.NoFrame)
        lay.addWidget(sa)
        self._garantir_fases()
        self._load()
        # Botão fechar
        bw=QWidget(); bl=QHBoxLayout(bw); bl.setContentsMargins(0,4,0,0)
        info=QLabel("✅  As alterações são guardadas automaticamente.")
        info.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};")
        btn_fechar=QPushButton("✔  Guardar e Fechar")
        btn_fechar.setFixedHeight(36)
        btn_fechar.setStyleSheet(f"background:{CORES['laranja']};color:white;border:none;border-radius:8px;padding:0 20px;font-weight:600;font-size:13px;")
        btn_fechar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fechar.clicked.connect(self.accept)
        bl.addWidget(info); bl.addStretch(); bl.addWidget(btn_fechar)
        lay.addWidget(bw)

    def _garantir_fases(self):
        """Garante que existem fases para esta obra na BD"""
        from db.database import get_connection
        conn=get_connection(); cur=conn.cursor()
        for i,fase in enumerate(self.FASES_STD):
            cur.execute("INSERT IGNORE INTO obra_fases (obra_id,fase,estado,ordem) VALUES(%s,%s,'pendente',%s)",
                (self.obra["id"],fase,i))
        conn.commit(); cur.close(); conn.close()

    def _load(self):
        while self.fases_lay.count():
            it=self.fases_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        from db.database import get_connection
        conn=get_connection(); cur=conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM obra_fases WHERE obra_id=%s ORDER BY ordem",(self.obra["id"],))
        fases=cur.fetchall(); cur.close(); conn.close()
        for f in fases:
            card=QFrame()
            bg_c,_=self.FASE_COR.get(f["estado"],("#e8edf2","#4a6080"))
            card.setStyleSheet(f"background:{bg_c};border:1px solid {CORES['alum_mid']};border-radius:10px;")
            cl=QHBoxLayout(card); cl.setContentsMargins(14,10,14,10)
            ico=self.FASE_ICO.get(f["fase"],"⚙️")
            il=QLabel(f"{ico}  {f['fase'].replace('_',' ').title()}")
            il.setStyleSheet(f"font-size:13px;font-weight:600;color:{CORES['aco']};min-width:160px;")
            bg,fg=self.FASE_COR.get(f["estado"],("#e8edf2","#4a6080"))
            sl=QLabel(f["estado"].replace("_"," ").title())
            sl.setStyleSheet(f"background:white;color:{fg};border-radius:10px;padding:2px 9px;font-size:11px;font-weight:600;min-width:80px;")
            sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cmb=QComboBox()
            for est_key,est_label in self.FASE_ESTADOS:
                cmb.addItem(est_label,est_key)
            # Seleccionar estado actual
            for i in range(cmb.count()):
                if cmb.itemData(i)==f["estado"]:
                    cmb.setCurrentIndex(i); break
            cmb.setMaximumWidth(140)
            fid=f["id"]
            cmb.currentIndexChanged.connect(lambda _,fid=fid,c=cmb: self._update_fase(fid,c.currentData()))
            cl.addWidget(il); cl.addWidget(sl); cl.addStretch(); cl.addWidget(cmb)
            self.fases_lay.addWidget(card)

    def _update_fase(self,fid,estado):
        from db.database import get_connection
        try:
            # Actualizar fase
            conn=get_connection(); cur=conn.cursor()
            cur.execute("UPDATE obra_fases SET estado=%s WHERE id=%s",(estado,fid))
            conn.commit(); cur.close(); conn.close()

            # Verificar estados de todas as fases para actualizar obra
            conn2=get_connection(); cur2=conn2.cursor()
            cur2.execute("SELECT estado FROM obra_fases WHERE obra_id=%s",(self.obra["id"],))
            rows=cur2.fetchall(); estados=[r[0] for r in rows]
            if all(e=="concluida" for e in estados):
                cur2.execute("UPDATE obras SET estado='concluida' WHERE id=%s",(self.obra["id"],))
            elif any(e=="em_curso" for e in estados):
                cur2.execute("UPDATE obras SET estado='em_producao' WHERE id=%s AND estado NOT IN ('concluida','cancelada')",(self.obra["id"],))
            conn2.commit(); cur2.close(); conn2.close()
            self._load()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
