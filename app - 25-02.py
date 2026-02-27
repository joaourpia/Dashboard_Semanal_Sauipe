import streamlit as st
import pandas as pd
import datetime as dt
import re
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
import base64
import os
import glob

# --- Funções Utilitárias ---
def _labels_inteligentes(serie, max_labels=10):
    s = pd.to_numeric(serie, errors='coerce').fillna(0)
    n = len(s)
    labels = [''] * n
    if n == 0: return labels
    labels[0] = f"{int(s.iloc[0])}"
    labels[-1] = f"{int(s.iloc[-1])}"
    idx_candidates = {0, n-1}
    for i in range(1, n-1):
        if (s.iloc[i] > s.iloc[i-1] and s.iloc[i] > s.iloc[i+1]) or (s.iloc[i] < s.iloc[i-1] and s.iloc[i] < s.iloc[i+1]):
            idx_candidates.add(i)
    idx_sorted = sorted(idx_candidates)
    if len(idx_sorted) > max_labels:
        amostra = np.linspace(0, len(idx_sorted)-1, max_labels, dtype=int)
        idx_sorted = [idx_sorted[i] for i in amostra]
    for i in idx_sorted:
        labels[i] = f"{int(s.iloc[i])}"
    return labels

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard Operacional", layout="wide")
logo_base64 = get_base64_image("images/Logo_Parceria.png")
logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="max-width:300px;margin-bottom:10px;">' if logo_base64 else ""

# --- CSS Customizado ---
st.markdown("""
<style>
body {background-color: #f4f9ff;}
div[data-testid="stHorizontalBlock"] > div {margin-bottom: -8px;}
.stButton>button {border-radius: 12px 12px 0 0 !important; padding: 7px 25px 5px 25px !important; margin: 0 6px 0 0 !important; border: none !important; font-size: 1em !important; font-weight: 700 !important; color: #2266ee !important; background: #e7eefb !important; transition: background .18s, color .18s;}
.stButton>button.selected-tab {background: #2266ee !important; color: #fff !important; box-shadow: 0 4px 14px #2266ee47;}
.stButton>button:focus {outline: 2px solid #205491;}
.kpi-row {display:flex;gap:12px;margin-bottom:8px;}
.kpi-card {flex:1;background:#fff;padding:10px 0 8px 12px;border-radius:10px;color:#fff;display:flex;flex-direction:column;align-items:flex-start;box-shadow:0 2px 8px #0003;font-size:0.85em;}
.kpi-blue {background:#2266ee;}
.kpi-green {background:#23b26d;}
.kpi-purple {background:#9b1de9;}
.kpi-orange {background:#ff7927;}
.kpi-val {font-size:1.5em;font-weight:800;}
.kpi-title {font-size:0.85em;font-weight:600;}
.diarias-kpi-row {display: flex; gap: 18px; margin-bottom: 14px;}
.diarias-kpi-card {flex: 1; padding: 18px 0 10px 0; border-radius: 10px; display: flex; flex-direction: column; align-items: center; box-shadow: 0 2px 8px #0001;}
.diarias-kpi-blue {background: #e8f0fe; color: #205891;}
.diarias-kpi-green {background: #e6f8ef; color: #178655;}
.diarias-kpi-purple {background: #f3e9fd; color: #781bc4;}
.diarias-kpi-title {font-size: 1.01em; font-weight: 600; margin-bottom:2px;}
.diarias-kpi-val {font-size: 2.3em; font-weight:900; line-height:1;}
.diarias-card-sucesso {background:#eaffee; border-left:6px solid #19bb62; border-radius:8px; padding:13px 18px 12px 18px; margin-bottom:16px; margin-top:2px; font-weight:500; color:#178655;}
.obs-box {background:#fff; border-left:5px solid #2266ee; border-radius:8px; padding:15px; margin-top:10px; font-size:0.95em; color:#333; box-shadow:0 1px 5px #0001;}
.dashboard-header {background:#ffffff;padding:10px 20px;margin:-60px -60px 10px -60px;border-bottom:3px solid #2266ee;display:flex;justify-content:space-between;align-items:center;}
</style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
st.markdown(f"""
<div style="text-align:center;margin-top:-60px;margin-bottom:5px;">{logo_html}</div>
<div class="dashboard-header">
  <div class="header-left">
    <h1>Dashboard fevereiro 2026</h1>
    <p>Relatório de Contratação de Temporários - Mendes RH</p>
  </div>
  <div class="header-right">
    <p class="periodo-label">Período</p>
    <p class="periodo-value">16 a 22/02/2026</p>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Navegação de Abas ---
tab_names = ["Visão Geral", "Análise SLA", "Diárias", "Histórico", "Pesquisa Temporada", "Análise Entrega"]
if "current_tab" not in st.session_state:
    st.session_state.current_tab = tab_names[0]

def set_tab(tab): 
    st.session_state.current_tab = tab

tab_cols = st.columns(len(tab_names))
for i, tab in enumerate(tab_names):
    tab_cols[i].button(tab, key=tab, on_click=set_tab, args=(tab,), type="secondary")
    tab_cols[i].markdown(f"""<style>[data-testid="stButton"] button#{tab.replace(' ', '')} {{ {'background:#2266ee !important;color:#fff !important;box-shadow:0 4px 14px #2266ee47;' if st.session_state.current_tab == tab else ''} }}</style>""", unsafe_allow_html=True)

# --- Caminhos Base ---
def _project_root() -> Path: 
    return Path(__file__).resolve().parent

def _safe_data_path(filename: str) -> Path: 
    return _project_root() / "dados" / filename

# --- Funções de Renderização Antigas ---
def render_visao_geral():
    try:
        sla = pd.read_csv(_safe_data_path('SLA.csv'), sep=';', decimal=',', encoding='latin1')
        pedidos = pd.read_csv(_safe_data_path('ANALISE_PEDIDO.csv'), sep=';', decimal=',', encoding='latin1')
        sla_percent = sla['taxa'].iloc[0] * 100
        diaria_val = pedidos['Taxa'].iloc[0]
        diaria_percent = float(str(diaria_val).replace(',', '.').replace('%','')) if '%' in str(diaria_val) else float(diaria_val) * 100
        st.markdown(f"""<div class="kpi-row">
          <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Pedidos</span><span class="kpi-val">{sla['Solicitado'].iloc[0]}</span></div>
          <div class="kpi-card kpi-green"><span class="kpi-title">Taxa SLA</span><span class="kpi-val">{sla_percent:.1f}%</span></div>
          <div class="kpi-card kpi-purple"><span class="kpi-title">Diárias Entregues</span><span class="kpi-val">{pedidos['Entregue'].iloc[0]}</span></div>
          <div class="kpi-card kpi-orange"><span class="kpi-title">Taxa Diárias</span><span class="kpi-val">{diaria_percent:.2f}%</span></div>
        </div>""", unsafe_allow_html=True)
        col_pie, col_bar = st.columns(2, gap="medium")
        with col_pie:
            st.markdown('<div class="graph-container"><div class="graph-title">Desempenho SLA - 16 a 22/02</div><div class="graph-content">', unsafe_allow_html=True)
            fig_pie = px.pie(values=[sla['No_prazo'].iloc[0], sla['Fora_prazo'].iloc[0]], names=["No Prazo", "Fora do Prazo"], hole=0.40, color_discrete_sequence=['#2266ee','#f65054'])
            fig_pie.update_traces(textinfo="percent", textposition="inside", textfont=dict(size=14, color="#ffffff"), marker=dict(line=dict(color="#ffffff", width=2)), pull=[0.02,0.02])
            fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10,color="#1a1a1a")), margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=180)
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})
            st.markdown('</div></div>', unsafe_allow_html=True)
        with col_bar:
            st.markdown('<div class="graph-container"><div class="graph-title">Diárias - 16 a 22/02</div><div class="graph-content">', unsafe_allow_html=True)
            solicitadas, entregues = pedidos.Solicitado.iloc[0], pedidos.Entregue.iloc[0]
            saldo = entregues - solicitadas
            comp_df = pd.DataFrame({"Tipo":["Solicitadas","Entregues"],"Qtd":[solicitadas,entregues]})
            fig_bar = px.bar(comp_df, x="Tipo", y="Qtd", text_auto='.0f', color="Tipo", color_discrete_map={"Solicitadas":"#FFA500","Entregues":"#23B26D"})
            fig_bar.update_traces(texttemplate='<b>%{y}</b>', textposition='inside', textfont=dict(size=14, color="#fff"))
            fig_bar.update_layout(showlegend=False, xaxis=dict(title="", tickfont=dict(size=11, color="#1a1a1a")), yaxis=dict(title="", showticklabels=True, tickfont=dict(size=9, color="#1a1a1a"), range=[0,max(solicitadas,entregues)*1.15]), margin=dict(l=12,r=12,t=8,b=8), height=150, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})
            st.markdown(f"""<div class='diarias-card-sucesso' style='margin-top:8px;'>✅ Não superamos a meta! Entregamos {saldo} diárias a menos que o solicitado ({diaria_percent:.2f}%)</div></div></div>""", unsafe_allow_html=True)
        st.markdown("""<div class="obs-box"><b>Observações Importantes - 16 a 22/02/2026</b><ul><li>SLA: 108,5% no periodo de 16 a 22/02 (detalhes na aba SLA). Volume: diárias entregues 19,13% acima do solicitado (detalhes na aba Diárias). Importante ressaltar que esses dados estão sendo calculados somente com relação aos pedidos dentro do prazo da SLA de 10 dias</li></ul></div>""", unsafe_allow_html=True)
    except Exception as e: st.warning(f"Erro Visão Geral: {e}")

def render_analise_sla():
    try:
        sla = pd.read_csv(_safe_data_path('SLA.csv'), sep=';', decimal=',', encoding='latin1')
        total, dentro, fora = int(sla['Solicitado'].iloc[0]), int(sla['No_prazo'].iloc[0]), int(sla['Fora_prazo'].iloc[0])
        perc_dentro, perc_fora = dentro/total*100, fora/total*100
        st.markdown(f"""<div class="kpi-row">
          <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Solicitações</span><span class="kpi-val">{total}</span></div>
          <div class="kpi-card kpi-green"><span class="kpi-title">Dentro do Prazo</span><span class="kpi-val">{dentro}</span><span style="font-size:0.92em;color:#e9ffe1;">{perc_dentro:.2f}% do total</span></div>
          <div class="kpi-card kpi-orange"><span class="kpi-title">Fora do Prazo</span><span class="kpi-val">{fora}</span><span style="font-size:0.92em;color:#fffbe5;">{perc_fora:.2f}% do total</span></div>
        </div>""", unsafe_allow_html=True)
        fig = go.Figure(go.Indicator(mode="gauge+number+delta", value=perc_dentro, delta={'reference':100,'increasing':{'color':'#ff7927'},'decreasing':{'color':'#23B26D'}}, number={'suffix':' %','font':{'size':32}}, title={'text':'SLA Cumprido (%)','font':{'size':17}}, gauge={'axis':{'range':[0,100],'tickwidth':2},'bar':{'color':'#23B26D'},'bgcolor':'#eaeaee','steps':[{'range':[0,perc_dentro],'color':'#23B26D'},{'range':[perc_dentro,100],'color':'#ffebdf'}],'threshold':{'line':{'color':'#FF7927','width':4},'thickness':0.7,'value':perc_dentro}}))
        fig.update_layout(height=220, margin=dict(l=22,r=22,t=22,b=20), paper_bgcolor="#f6f9fd", font=dict(size=15))
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div><div class="obs-box" style="background:#e8f1fd;border-left:5px solid #5aa7db;color:#164976;font-size:1.04em;margin-top:10px;font-weight:500;"><b>Contexto SLA</b><br><ul><li><b>Pedidos fora do prazo:</b> O total entregue de SLA foi de 108,46%, considerando os pedidos dentro do prazo.</li></ul></div>', unsafe_allow_html=True)
    except Exception as e: st.warning(f"Erro SLA: {e}")

def render_diarias():
    try:
        pedidos = pd.read_csv(_safe_data_path('ANALISE_PEDIDO.csv'), sep=';', decimal=',', encoding='latin1')
        solicitadas, entregues = int(pedidos.Solicitado.iloc[0]), int(pedidos.Entregue.iloc[0])
        saldo = entregues - solicitadas
        taxa = float(str(pedidos['Taxa'].iloc[0]).replace(',', '.').replace('%','')) if '%' in str(pedidos['Taxa'].iloc[0]) else float(pedidos['Taxa'].iloc[0]) * 100
        st.markdown(f"""<div class="diarias-kpi-row"><div class="diarias-kpi-card diarias-kpi-blue"><span class="diarias-kpi-title">Solicitadas</span><span class="diarias-kpi-val">{solicitadas}</span></div><div class="diarias-kpi-card diarias-kpi-green"><span class="diarias-kpi-title">Entregues</span><span class="diarias-kpi-val">{entregues}</span></div><div class="diarias-kpi-card diarias-kpi-purple"><span class="diarias-kpi-title">Taxa de Atendimento</span><span class="diarias-kpi-val">{taxa:.2f}%</span></div></div>""", unsafe_allow_html=True)
        fig_barras = go.Figure()
        fig_barras.add_trace(go.Bar(x=["fevereiro"], y=[solicitadas], name="Solicitadas", marker=dict(color="#FFA500"), text=[solicitadas], textposition="outside"))
        fig_barras.add_trace(go.Bar(x=["fevereiro"], y=[entregues], name="Entregues", marker=dict(color="#23B26D"), text=[entregues], textposition="outside"))
        fig_barras.update_layout(barmode='group', yaxis=dict(range=[0,max(solicitadas,entregues)*1.15]), height=310, margin=dict(t=30,b=30,l=28,r=28), legend=dict(orientation='h', x=0.5, y=-0.20, xanchor='center'), plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig_barras, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"""<div class="diarias-card-sucesso"><b>Desempenho abaixo</b><br> No perioso de 16 a 22/02/26, não superamos as expectativas ao entregar <b>{entregues} diárias</b>, quando foram solicitadas <b>{solicitadas}</b>, resultando em uma diferença negativa de <b style='color:#12bb26;'>{saldo} diárias</b>.<br> Taxa de atendimento: <b>{taxa:.2f}%</b>.</div>""", unsafe_allow_html=True)
    except Exception as e: st.warning(f"Erro Diárias: {e}")

def render_historico():
    try:
        sla_hist = pd.read_csv(_safe_data_path('HISTORICO_SLA.csv'), sep=';', encoding='latin1')
        sla_hist.columns = ['Mes','Taxa']
        sla_hist['Taxa'] = sla_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.').strip()))
        sla_hist['No Prazo (%)'] = sla_hist['Taxa'] * 100
        sla_hist['Fora do Prazo (%)'] = (1 - sla_hist['Taxa']) * 100
        st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Prazos de Entregas (16 a 22/02/2026)</div></div>""", unsafe_allow_html=True)
        fig1 = go.Figure(data=[
            go.Bar(name='No Prazo', x=sla_hist['Mes'], y=sla_hist['No Prazo (%)'], marker_color='#2266ee', text=[f"{v:.1f}%" for v in sla_hist['No Prazo (%)']], textposition='inside'),
            go.Bar(name='Fora do Prazo', x=sla_hist['Mes'], y=sla_hist['Fora do Prazo (%)'], marker_color='#f65054', text=[f"{v:.1f}%" for v in sla_hist['Fora do Prazo (%)']], textposition='inside')
        ])
        fig1.update_layout(barmode='stack', height=350, margin=dict(l=20,r=20,t=80,b=38), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'), plot_bgcolor='#fff')
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar':False})
        
        ent_hist = pd.read_csv(_safe_data_path('HISTORICO_ENTREGA.csv'), sep=';', encoding='latin1')
        ent_hist.columns = ['Mês','Solicitadas','Entregues','Taxa']
        ent_hist['Solicitadas'] = ent_hist['Solicitadas'].astype(int)
        ent_hist['Entregues'] = ent_hist['Entregues'].astype(int)
        ent_hist['Taxa_%'] = ent_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.'))) * 100
        st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Diárias Entregues (16 a 22/02/2026)</div></div>""", unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=ent_hist['Mês'], y=ent_hist['Solicitadas'], name='Solicitadas', marker_color='#FFA500', text=ent_hist['Solicitadas'], textposition='outside'))
        fig2.add_trace(go.Bar(x=ent_hist['Mês'], y=ent_hist['Entregues'], name='Entregues', marker_color='#23B26D', text=ent_hist['Entregues'], textposition='outside'))
        fig2.add_trace(go.Scatter(x=ent_hist['Mês'], y=ent_hist['Taxa_%'], mode='lines+markers+text', name='Taxa (%)', line=dict(color='#2266ee', width=2), marker=dict(size=8,color='#2266ee'), text=[f"{tx:.2f}%" for tx in ent_hist['Taxa_%']], textposition="top center"))
        fig2.update_layout(barmode='group', height=540, margin=dict(l=20,r=20,t=120,b=38), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'), plot_bgcolor='#fff')
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
    except Exception as e: st.warning(f"Erro Histórico: {e}")

def render_pesquisa_temporada():
    st.markdown("""<div style="background:#f4faff;border-radius:8px;padding:16px;margin-bottom:12px;"><p style="margin:0;font-size:0.92em;">Resultados da pesquisa de acompanhamento com temporários. Foram avaliados <b>61 ativos</b> e <b>13 desligados</b>.</p></div>""", unsafe_allow_html=True)
    df_recepcao = pd.DataFrame({"Nota":["1","2","3","4","5"], "Quantidade":[1,2,10,6,42]})
    fig_rec = px.bar(df_recepcao, x="Nota", y="Quantidade", color="Nota", color_discrete_sequence=['#f65054','#ffa500','#ffd966','#ac7ef4','#23b26d'], text="Quantidade")
    fig_rec.update_traces(texttemplate="%{text}", textposition="outside")
    fig_rec.update_layout(showlegend=False, title_text="Recepção no Primeiro Dia", height=300)
    st.plotly_chart(fig_rec, use_container_width=True, config={"displayModeBar":False})

# --- ANÁLISE ENTREGA (COM GRÁFICO DUPLO E PRAZO MÉDIO) ---

@st.cache_data(ttl=3600)
def load_historical_sth_data(pasta_path):
    arquivos = glob.glob(os.path.join(pasta_path, '*.xlsx'))
    df_list = []
    for arq in arquivos:
        try:
            tmp = pd.read_excel(arq, sheet_name='STH_PLANEJAMENTO', usecols=['DT RECEBIMENTO', 'INICIO', 'FIM'], engine='openpyxl')
            df_list.append(tmp)
        except Exception: pass
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

def render_analise_entrega():
    caminho_entregas = _safe_data_path('ENTREGAS_DIA.xlsx')
    try:
        entregas_df = pd.read_excel(caminho_entregas, engine="openpyxl")
    except Exception:
        st.warning(f"Dados não encontrados em: {caminho_entregas}")
        return

    if 'Data' in entregas_df.columns:
        entregas_df = entregas_df[entregas_df['Data'].astype(str).str.upper() != 'TOTAL']
        entregas_df['Data'] = pd.to_datetime(entregas_df['Data'], errors='coerce')
    entregas_df = entregas_df.rename(columns={col: 'entregas' for col in entregas_df.columns if 'Total' in col or 'entregue' in col}).dropna(subset=['Data'])

    caminho_pedidos = _safe_data_path('PEDIDOS_DIA.xlsx')
    try:
        pedidos_xls = pd.ExcelFile(caminho_pedidos, engine="openpyxl")
        hist = pedidos_xls.parse('HISTOGRAMA', header=None)
        ex = pedidos_xls.parse('HISTOGRAMA_EXCEDENTE', header=None)
    except Exception:
        st.warning(f"Abas HISTOGRAMA não encontradas em: {caminho_pedidos}")
        return

    def _parse_hdr_date(v):
        if pd.isna(v): return None
        if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)): return pd.to_datetime(v).normalize()
        s = str(v).strip()
        m = re.match(r'^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$', s)
        if m:
            dd, mm, yy = int(m.group(1)), int(m.group(2)), m.group(3)
            yy = int(yy) if yy else 2026
            yy = yy + 2000 if yy < 100 else yy
            try: return pd.Timestamp(yy, mm, dd).normalize()
            except: pass
        return None

    try:
        row_no = hist[hist.iloc[:,0].astype(str).str.upper().str.strip() == 'SUBTOTAL (FILTRO)'].iloc[0]
        row_out = ex[ex.iloc[:,0].astype(str).str.upper().str.strip() == 'SUBTOTAL (FILTRO)'].iloc[0]
    except Exception:
        st.error("Linha 'SUBTOTAL (FILTRO)' não encontrada no Histograma.")
        return

    header_row = None
    for i in range(min(10, hist.shape[0])):
        if _parse_hdr_date(hist.iat[i, 3]) is not None:
            header_row = i
            break
            
    if header_row is None:
        st.warning("O formato do cabeçalho mudou. Não encontrei a linha de datas (ex: 01/02) nas primeiras 10 linhas da planilha.")
        return

    datas, values_no, values_out = [], [], []
    for c in range(3, hist.shape[1]):
        d = _parse_hdr_date(hist.iat[header_row, c])
        if d:
            datas.append(d)
            values_no.append(pd.to_numeric(row_no.iloc[c], errors='coerce'))
            values_out.append(pd.to_numeric(row_out.iloc[c], errors='coerce'))

    pedidos_df = pd.DataFrame({'Data': pd.to_datetime(datas).normalize(), 'pedidos_no_prazo': values_no, 'pedidos_fora_prazo': values_out}).fillna(0).groupby('Data', as_index=False).sum()
    dados = pd.merge(pedidos_df, entregas_df[['Data', 'entregas']], on='Data', how='left').fillna(0)
    
    pasta_solicitacoes = str(_project_root() / "dados" / "solicitacoes")
    sth_plan = load_historical_sth_data(pasta_solicitacoes)
    
    if not sth_plan.empty:
        sth_plan = sth_plan.dropna(subset=['DT RECEBIMENTO', 'INICIO', 'FIM'])
        sth_plan['DT RECEBIMENTO'] = pd.to_datetime(sth_plan['DT RECEBIMENTO'], errors='coerce')
        sth_plan['INICIO'] = pd.to_datetime(sth_plan['INICIO'], errors='coerce')
        sth_plan['FIM'] = pd.to_datetime(sth_plan['FIM'], errors='coerce')
        sth_plan = sth_plan.dropna()
        
        lead_times = []
        for _, row in sth_plan.iterrows():
            if row['INICIO'] <= row['FIM']:
                try:
                    if 0 <= (row['FIM'] - row['INICIO']).days <= 120:  
                        for d in pd.date_range(row['INICIO'], row['FIM']):
                            lead_times.append({'Data': d.normalize(), 'Prazo': (d - row['DT RECEBIMENTO']).days})
                except: pass
        
        if lead_times:
            df_lead = pd.DataFrame(lead_times)
            df_lead['Critico'] = df_lead['Prazo'] < 3
            agrupado_lead = df_lead.groupby('Data').agg(Prazo_Medio=('Prazo', 'mean'), Total=('Prazo', 'count'), Criticos=('Critico', 'sum')).reset_index()
            agrupado_lead['Pct_Critico'] = (agrupado_lead['Criticos'] / agrupado_lead['Total']) * 100
            dados = pd.merge(dados, agrupado_lead[['Data', 'Prazo_Medio', 'Pct_Critico']], on='Data', how='left')
    else:
        st.info(f"Aviso: Não encontrei planilhas com a aba STH_PLANEJAMENTO na pasta '{pasta_solicitacoes}'.")

    if len(dados) == 0:
        st.warning("Sem dados no período.")
        return
    
    max_y = float(dados[['pedidos_no_prazo', 'entregas', 'pedidos_fora_prazo']].max().max())
    y_max = max_y * (1.18 if max_y > 0 else 10)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dados['Data'], y=dados['pedidos_no_prazo'], mode='lines+markers+text', name='Pedidos no Prazo', line=dict(color='#2266ee', width=2), marker=dict(size=6, color='#2266ee'), text=[f"{int(round(v))}" for v in dados['pedidos_no_prazo']], textposition='top center', textfont=dict(size=11, color='#2266ee'), cliponaxis=False))
    fig.add_trace(go.Scatter(x=dados['Data'], y=dados['entregas'], mode='lines+markers+text', name='Entregas', line=dict(color='#23B26D', width=2), marker=dict(size=6, color='#23B26D'), text=[f"{int(round(v))}" for v in dados['entregas']], textposition='bottom center', textfont=dict(size=11, color='#23B26D'), cliponaxis=False))
    fig.add_trace(go.Scatter(x=dados['Data'], y=dados['pedidos_fora_prazo'], mode='lines+markers+text', name='Fora do Prazo', line=dict(color='#f65054', width=2, dash='dash'), marker=dict(size=6, color='#f65054'), text=[f"{int(round(v))}" for v in dados['pedidos_fora_prazo']], textposition='top right', textfont=dict(size=11, color='#f65054'), cliponaxis=False))
    
    tem_prazo = 'Prazo_Medio' in dados.columns and not dados['Prazo_Medio'].isna().all()
    if tem_prazo:
        fig.add_trace(go.Scatter(x=dados['Data'], y=dados['Prazo_Medio'], mode='lines+markers+text', name='Prazo Médio (Dias)', yaxis='y2', line=dict(color='#9b1de9', width=2, dash='dot'), marker=dict(size=6, color='#9b1de9', symbol='diamond'), text=[f"{v:.1f}d" if pd.notna(v) else "" for v in dados['Prazo_Medio']], textposition='bottom right', textfont=dict(size=10, color='#9b1de9'), cliponaxis=False))
        max_y_lead = dados['Prazo_Medio'].max()
    else: max_y_lead = 10

    # A correção está aqui: title_font com underline (aceito pelas bibliotecas mais novas)
    fig.update_layout(xaxis=dict(tickformat='%d/%m', showgrid=False, dtick=86400000.0), yaxis=dict(title='Qtd. Diárias', range=[0, y_max], showgrid=True, gridcolor='rgba(120,140,170,0.22)'), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=11)), height=550, margin=dict(l=18, r=18, t=35, b=65), hovermode='x unified', plot_bgcolor='#fff', paper_bgcolor='#fff')
    if tem_prazo: fig.update_layout(yaxis2=dict(title='Prazo Lead Time (Dias)', tickfont=dict(size=10, color='#9b1de9'), title_font=dict(size=12, color='#9b1de9'), overlaying='y', side='right', range=[0, max_y_lead * 1.3] if max_y_lead > 0 else [0, 10], showgrid=False, zeroline=False))

    period_start, period_end = dados['Data'].min(), dados['Data'].max()
    st.markdown(f"<div class='graph-container'><div style='font-weight:700; font-size:1.1em; color:#1a1a1a; margin-bottom:10px;'>Pedidos x Entregas x Prazo de Contratação ({period_start.strftime('%d/%m')} a {period_end.strftime('%d/%m')})</div>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

    avg_pedidos, avg_entregas, avg_fora = dados['pedidos_no_prazo'].mean(), dados['entregas'].mean(), dados['pedidos_fora_prazo'].mean()
    analise = f"<ul><li><b>Destaque Operacional:</b> Média de <b>{avg_pedidos:.0f}</b> no prazo e <b>{avg_fora:.0f}</b> fora do prazo/dia.</li><li><b>Termômetro SLA:</b> Saldo médio foi de <b>{(avg_entregas - avg_pedidos):.0f}</b>/dia.</li>"
    if tem_prazo:
        avg_lead, avg_crit = dados['Prazo_Medio'].mean(), dados['Pct_Critico'].mean()
        idx_crit = dados['Prazo_Medio'].idxmin()
        if pd.notna(idx_crit):
            dia_crit, val_crit = dados.loc[idx_crit, 'Data'].strftime('%d/%m'), dados.loc[idx_crit, 'Prazo_Medio']
            analise += f"<li><b>SLA Real (Lead Time):</b> <b>{avg_lead:.1f} dias reais</b> de antecedência média para recrutamento das vagas.</li><li><b>Risco e Sobrecarga (< 3 dias):</b> O índice de requisições críticas representou <b>{avg_crit:.1f}%</b> das vagas diárias. O pico crítico ocorreu no dia <b>{dia_crit}</b>, onde o prazo médio despencou para apenas <b>{val_crit:.1f} dias</b> de manobra.</li>"
    st.markdown(f"<div class='obs-box'>{analise}</ul></div>", unsafe_allow_html=True)

# ---- Função de Roteamento de Abas ----
aba_ativa = st.session_state.current_tab

if aba_ativa == "Visão Geral":
    render_visao_geral()
elif aba_ativa == "Análise SLA":
    render_analise_sla()
elif aba_ativa == "Diárias":
    render_diarias()
elif aba_ativa == "Histórico":
    render_historico()
elif aba_ativa == "Pesquisa Temporada":
    render_pesquisa_temporada()
elif aba_ativa == "Análise Entrega":
    render_analise_entrega()