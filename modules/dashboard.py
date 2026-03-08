from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
CORES={"aco":"#1a2332","aco_mid":"#2c3e55","laranja":"#d4560a","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","success":"#1e7e44","danger":"#c0392b","warning":"#b8700a"}
def _stat(ico,val,lbl,delta,up):
    bg_d="#d4edda" if up else "#fde8e0"; fg_d=CORES["success"] if up else CORES["danger"]
    f=QFrame(); f.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:12px;")
    l=QVBoxLayout(f); l.setContentsMargins(16,16,16,16); l.setSpacing(3)
    for t,st in [(ico,"font-size:22px;"),(str(val),f"font-size:26px;font-weight:800;color:{CORES['aco']};"),(lbl,f"font-size:11px;color:{CORES['cinza']};")]:
        lb=QLabel(t); lb.setStyleSheet(st); l.addWidget(lb)
    d=QLabel(delta); d.setStyleSheet(f"background:{bg_d};color:{fg_d};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;"); l.addWidget(d)
    return f
class DashboardWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        sa=QScrollArea(self); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.Shape.NoFrame)
        QVBoxLayout(self).addWidget(sa); cw=QWidget(); sa.setWidget(cw)
        self.main=QVBoxLayout(cw); self.main.setContentsMargins(20,20,20,20); self.main.setSpacing(16)
        self.grid=QGridLayout(); self.grid.setSpacing(14); self.main.addLayout(self.grid)
        # Panel obras
        pf=QFrame(); pf.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:12px;")
        pl=QVBoxLayout(pf); pl.setContentsMargins(0,0,0,0)
        ph=QWidget(); ph.setStyleSheet(f"border-bottom:1px solid {CORES['alum_mid']};")
        phl=QHBoxLayout(ph); phl.setContentsMargins(16,10,16,10)
        phl.addWidget(QLabel("🔨  Obras em Curso")); self.obras_body=QVBoxLayout()
        self.obras_body.setContentsMargins(16,10,16,14)
        pl.addWidget(ph); pl.addLayout(self.obras_body); self.main.addWidget(pf)
        # Panel alertas
        af=QFrame(); af.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:12px;")
        al2=QVBoxLayout(af); al2.setContentsMargins(0,0,0,0)
        ah=QWidget(); ah.setStyleSheet(f"border-bottom:1px solid {CORES['alum_mid']};")
        ahl=QHBoxLayout(ah); ahl.setContentsMargins(16,10,16,10)
        ahl.addWidget(QLabel("⚠️  Alertas")); self.alertas_body=QVBoxLayout()
        self.alertas_body.setContentsMargins(16,10,16,14)
        al2.addWidget(ah); al2.addLayout(self.alertas_body); self.main.addWidget(af)
        self.main.addStretch()
    def _clear(self,layout):
        while layout.count():
            it=layout.takeAt(0)
            if it.widget(): it.widget().deleteLater()
    def refresh(self):
        self._clear(self.grid)
        try: s=self.dao.stats_dashboard()
        except: s={"obras_ativas":0,"obras_urgentes":0,"tarefas_pendentes":0,"stock_baixo":0,"saldo":0,"obras_mes":0}
        cards=[("🔨",s["obras_ativas"],"Obras activas","↑ em produção",True),("⚡",s["obras_urgentes"],"Urgentes","↑ atenção",s["obras_urgentes"]==0),
               ("💶",f"{s['saldo']:.0f} €","Saldo","↑ positivo" if s["saldo"]>=0 else "↓ negativo",s["saldo"]>=0),
               ("✓",s["tarefas_pendentes"],"Tarefas pend.","sem pendentes",s["tarefas_pendentes"]==0),
               ("📦",s["stock_baixo"],"Stock baixo","reposição",s["stock_baixo"]==0),("📅",s["obras_mes"],"Obras/mês","↑ activo",True)]
        for i,(ico,val,lbl,d,up) in enumerate(cards): self.grid.addWidget(_stat(ico,val,lbl,d,up),i//3,i%3)
        self._clear(self.obras_body)
        try:
            ativas=[o for o in self.dao.listar_obras() if o["estado"] in ("confirmada","em_producao","em_montagem")][:5]
            if not ativas:
                l=QLabel("Sem obras activas."); l.setStyleSheet(f"color:{CORES['cinza']};font-style:italic;"); self.obras_body.addWidget(l)
            else:
                EC={"confirmada":("#fff3cd","#b8700a"),"em_producao":("#d4edda","#1e7e44"),"em_montagem":("#e8f0fa","#1a6fa8")}
                for o in ativas:
                    row=QHBoxLayout(); bg,fg=EC.get(o["estado"],("#e8edf2","#4a6080"))
                    for t,st in [(o["numero"],"font-size:11px;font-weight:700;min-width:110px;"),(o["descricao"],"font-size:13px;font-weight:500;"),(o.get("cliente_nome","—"),"font-size:12px;color:#6b7c8e;")]:
                        lb=QLabel(t); lb.setStyleSheet(st); row.addWidget(lb)
                    row.addStretch(); est=QLabel(o["estado"].replace("_"," ").title())
                    est.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 9px;font-size:11px;font-weight:600;"); row.addWidget(est)
                    w=QWidget(); w.setLayout(row); w.setStyleSheet(f"border-bottom:1px solid {CORES['alum_mid']};padding:5px 0;"); self.obras_body.addWidget(w)
        except: pass
        self._clear(self.alertas_body)
        try:
            alertas=[]
            for o in self.dao.listar_obras():
                if o["prioridade"]=="urgente" and o["estado"] not in ("concluida","cancelada"):
                    alertas.append(("🔴",f"Obra urgente: {o['numero']} — {o['descricao'][:50]}",CORES["danger"]))
            for si in self.dao.listar_stock(baixo_stock=True)[:3]:
                alertas.append(("📦",f"Stock baixo: {si['descricao']} ({si['quantidade']} {si['unidade']})",CORES["warning"]))
            if not alertas:
                l=QLabel("✅  Sem alertas urgentes."); l.setStyleSheet(f"color:{CORES['success']};font-weight:600;"); self.alertas_body.addWidget(l)
            else:
                for ico,msg,cor in alertas[:6]:
                    row=QHBoxLayout(); il=QLabel(ico); il.setStyleSheet("font-size:16px;min-width:24px;")
                    ml=QLabel(msg); ml.setStyleSheet(f"font-size:13px;font-weight:500;color:{cor};")
                    row.addWidget(il); row.addWidget(ml); row.addStretch()
                    w=QWidget(); w.setLayout(row); self.alertas_body.addWidget(w)
        except: pass
