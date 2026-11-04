from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
from PyQt6.QtGui import QPixmap, QImage
from modules.temas import PALETA as CORES
def _stat(ico,val,lbl,delta,up):
    bg_d="#d4edda" if up else "#fde8e0"; fg_d=CORES["success"] if up else CORES["danger"]
    f=QFrame(); f.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:12px;")
    l=QVBoxLayout(f); l.setContentsMargins(16,16,16,16); l.setSpacing(3)
    for t,st in [(ico,"font-size:22px;"),(str(val),f"font-size:26px;font-weight:800;color:{CORES['aco']};"),(lbl,f"font-size:11px;color:{CORES['cinza']};")]:
        lb=QLabel(t); lb.setStyleSheet(st); l.addWidget(lb)
    d=QLabel(delta); d.setStyleSheet(f"background:{bg_d};color:{fg_d};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;"); l.addWidget(d)
    return f
def _mini_grafico_financeiro(receitas, despesas):
    """Devolve QPixmap com gráfico de barras receitas/despesas"""
    try:
        fig, ax = plt.subplots(figsize=(4, 2.2), facecolor=CORES["cartao"])
        bars = ax.bar(["Receitas", "Despesas"], [receitas, despesas],
                      color=[CORES["success"], CORES["danger"]], width=0.5, zorder=3)
        for bar, val in zip(bars, [receitas, despesas]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(receitas,despesas)*0.02,
                    f"{val:,.0f}€", ha="center", fontsize=8, fontweight="bold", color=CORES["aco"])
        ax.set_facecolor(CORES["cartao2"])
        ax.grid(axis="y", alpha=0.3, zorder=0, color=CORES["alum_mid"])
        ax.tick_params(labelsize=8, colors=CORES["aco"])
        for spine in ax.spines.values():
            spine.set_color(CORES["alum_mid"])
        ax.set_ylim(0, max(receitas, despesas, 1) * 1.2)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"{v:,.0f}€"))
        fig.tight_layout(pad=0.5)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        buf.seek(0); plt.close(fig)
        img = QImage.fromData(buf.read())
        return QPixmap.fromImage(img)
    except:
        return None

def _mini_grafico_obras(dados_estados):
    """Devolve QPixmap com gráfico de donut obras por estado"""
    try:
        LABELS = {"orcamento":"Orçamento","confirmada":"Confirmada","em_producao":"Em Produção",
                  "em_montagem":"Em Montagem","concluida":"Concluída","cancelada":"Cancelada","em_espera":"Em Espera"}
        CORES_E = {"orcamento":"#c8d4de","confirmada":"#ffc107","em_producao":"#28a745",
                   "em_montagem":"#17a2b8","concluida":"#1e7e44","cancelada":"#c0392b","em_espera":"#6b7c8e"}
        if not dados_estados:
            return None
        estados = list(dados_estados.keys())
        valores = list(dados_estados.values())
        cores   = [CORES_E.get(e, "#aabbcc") for e in estados]
        labels  = [LABELS.get(e, e) for e in estados]
        fig, ax = plt.subplots(figsize=(4, 2.8), facecolor=CORES["cartao"])
        wedges, texts, autotexts = ax.pie(valores, colors=cores, autopct="%1.0f%%",
            startangle=140, pctdistance=0.78,
            wedgeprops={"edgecolor":CORES["cartao"],"linewidth":1.5})
        for at in autotexts:
            at.set_fontsize(7); at.set_color("white"); at.set_fontweight("bold")
        ax.legend(wedges, [f"{l} ({v})" for l,v in zip(labels,valores)],
                  loc="lower center", bbox_to_anchor=(0.5,-0.28), ncol=2, fontsize=7, frameon=False,
                  labelcolor=CORES["aco"])
        fig.tight_layout(pad=0.3)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        buf.seek(0); plt.close(fig)
        img = QImage.fromData(buf.read())
        return QPixmap.fromImage(img)
    except:
        return None

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
        # Panel gráficos
        grf=QFrame(); grf.setStyleSheet(f"background:transparent;")
        self.graficos_body=QVBoxLayout(grf); grf.setLayout(self.graficos_body)
        self.main.addWidget(grf)
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
        # ── Gráficos ──────────────────────────────────────────────────────
        self._clear(self.graficos_body)
        try:
            from collections import defaultdict
            obras_all = self.dao.listar_obras()
            contagem = defaultdict(int)
            for o in obras_all:
                contagem[o.get("estado","outro")] += 1

            graf_row = QHBoxLayout()

            # Gráfico financeiro
            gf = QFrame(); gf.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:12px;")
            gfl = QVBoxLayout(gf); gfl.setContentsMargins(12,10,12,10); gfl.setSpacing(4)
            gfl.addWidget(QLabel("💶  Receitas vs Despesas"))
            px_fin = _mini_grafico_financeiro(s.get("receitas",0), s.get("despesas",0))
            if px_fin:
                lbl_fin = QLabel(); lbl_fin.setPixmap(px_fin); lbl_fin.setAlignment(Qt.AlignmentFlag.AlignCenter)
                gfl.addWidget(lbl_fin)

            # Gráfico obras por estado
            go = QFrame(); go.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:12px;")
            gol = QVBoxLayout(go); gol.setContentsMargins(12,10,12,10); gol.setSpacing(4)
            gol.addWidget(QLabel("🔨  Obras por Estado"))
            px_obras = _mini_grafico_obras(dict(contagem))
            if px_obras:
                lbl_obras = QLabel(); lbl_obras.setPixmap(px_obras); lbl_obras.setAlignment(Qt.AlignmentFlag.AlignCenter)
                gol.addWidget(lbl_obras)

            graf_row.addWidget(gf); graf_row.addWidget(go)
            w_graf = QWidget(); w_graf.setLayout(graf_row)
            self.graficos_body.addWidget(w_graf)
        except Exception as e:
            pass

        self._clear(self.alertas_body)
        try:
            alertas=[]
            from datetime import date, timedelta
            hoje = date.today()
            for o in self.dao.listar_obras():
                if o["estado"] in ("concluida","cancelada"):
                    continue
                # Urgentes
                if o["prioridade"]=="urgente":
                    alertas.append(("🔴",f"Obra urgente: {o['numero']} — {o['descricao'][:50]}",CORES["danger"]))
                # Prazo ultrapassado
                dp = o.get("data_prevista")
                if dp:
                    try:
                        from datetime import datetime
                        if hasattr(dp, "strftime"):
                            data_prev = dp
                        else:
                            data_prev = datetime.strptime(str(dp), "%Y-%m-%d").date()
                        dias = (data_prev - hoje).days
                        if dias < 0:
                            alertas.append(("🚨",f"Prazo ultrapassado há {abs(dias)} dias: {o['numero']} — {o['descricao'][:40]}",CORES["danger"]))
                        elif dias <= 3:
                            alertas.append(("⏰",f"Prazo em {dias} dia(s): {o['numero']} — {o['descricao'][:40]}",CORES["warning"]))
                        elif dias <= 7:
                            alertas.append(("📅",f"Prazo em {dias} dias: {o['numero']} — {o['descricao'][:40]}","#1a6fa8"))
                    except: pass
            for si in self.dao.listar_stock(baixo_stock=True)[:3]:
                alertas.append(("📦",f"Stock baixo: {si.get('nome','—')} ({int(float(si['quantidade']))} {si['unidade']})",CORES["warning"]))
            if not alertas:
                l=QLabel("✅  Sem alertas urgentes."); l.setStyleSheet(f"color:{CORES['success']};font-weight:600;"); self.alertas_body.addWidget(l)
            else:
                for ico,msg,cor in alertas[:6]:
                    row=QHBoxLayout(); il=QLabel(ico); il.setStyleSheet("font-size:16px;min-width:24px;")
                    ml=QLabel(msg); ml.setStyleSheet(f"font-size:13px;font-weight:500;color:{cor};")
                    row.addWidget(il); row.addWidget(ml); row.addStretch()
                    w=QWidget(); w.setLayout(row); self.alertas_body.addWidget(w)
        except: pass
