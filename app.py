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

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard Operacional Mendes RH", layout="wide")

# --- CSS Customizado ---
st.markdown("""
<style>
body {background-color: #f4f9ff;}
div[data-testid="stHorizontalBlock"] > div {margin-bottom: -8px;}
.stButton>button {border-radius: 12px 12px 0 0 !important; padding: 7px 25px 5px 25px !important; margin: 0 6px 0 0 !important; border: none !important; font-size: 1em !important; font-weight: 700 !important; color: #2266ee !important; background: #e7eefb !important; transition: background .18s, color .18s;}
.stButton>button.selected-tab {background: #2266ee !important; color: #fff !important; box-shadow: 0 4px 14px #2266ee47;}
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
</style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
    except: return ""

base_dados = Path(__file__).resolve().parent / "dados"

def safe_read_csv(caminho):
    try: return pd.read_csv(caminho, sep=';', decimal=',', encoding='latin1')
    except:
        try: return pd.read_csv(caminho, sep=',', decimal='.', encoding='utf-8')
        except: return None

# --- INTELIGÊNCIA DE PASTAS ---
def obter_periodos():
    if not base_dados.exists(): return []
    pastas = []
    for item in base_dados.iterdir():
        if item.is_dir() and item.name.lower() != "solicitacoes" and not item.name.startswith('.'):
            pastas.append(item.name)
    if any(base_dados.glob("*.csv")) or any(base_dados.glob("*.xlsx")):
        if "." not in pastas: pastas.append(".")
    return sorted(pastas, reverse=True)

periodos_disponiveis = obter_periodos()

if not periodos_disponiveis:
    lista_opcoes = ["Nenhuma pasta de dados encontrada"]
else:
    lista_opcoes = ["Acumulado (Todas as Semanas)"] + [p for p in periodos_disponiveis if p != "."]
    if "." in periodos_disponiveis and len(periodos_disponiveis) == 1:
        lista_opcoes = ["Dados Atuais (Arquivos soltos na Raiz)"]

# --- CABEÇALHO ---
logo_html = f'<div style="text-align: center;"><img src="data:image/png;base64,{get_base64_image("images/Logo_Parceria.png")}" style="max-width:350px;"></div>'

col_title, col_logo, col_filter = st.columns([2.5, 3, 1.5])
with col_title: 
    st.markdown("<h2 style='margin-bottom:0; padding-top:20px;'>Dashboard Gestão de Temporários</h2>", unsafe_allow_html=True)
with col_logo: 
    st.markdown(logo_html, unsafe_allow_html=True)
with col_filter:
    st.markdown("<div style='padding-top:25px;'>", unsafe_allow_html=True)
    periodo_selecionado = st.selectbox("Filtro de Período:", lista_opcoes, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 1px solid #ccc;'>", unsafe_allow_html=True)

def obter_caminhos_alvo():
    if periodo_selecionado == "Nenhuma pasta de dados encontrada": return []
    if periodo_selecionado == "Acumulado (Todas as Semanas)":
        pastas_reais = [p for p in periodos_disponiveis if p != "."]
        return pastas_reais if pastas_reais else ["."]
    if periodo_selecionado == "Dados Atuais (Arquivos soltos na Raiz)": 
        return ["."]
    return [periodo_selecionado]

alvos_ativos = obter_caminhos_alvo()

# --- NAVEGAÇÃO DE ABAS ---
tab_names = ["Visão Geral", "Análise SLA", "Diárias", "Histórico Mensal", "Análise Entrega"]
if "current_tab" not in st.session_state: st.session_state.current_tab = tab_names[0]
def set_tab(tab): st.session_state.current_tab = tab

tab_cols = st.columns(len(tab_names))
for i, tab in enumerate(tab_names):
    tab_cols[i].button(tab, key=tab, on_click=set_tab, args=(tab,), type="secondary")
    tab_cols[i].markdown(f"""<style>[data-testid="stButton"] button#{tab.replace(' ', '')} {{ {'background:#2266ee !important;color:#fff !important;box-shadow:0 4px 14px #2266ee47;' if st.session_state.current_tab == tab else ''} }}</style>""", unsafe_allow_html=True)

# --- FUNÇÕES DE CARREGAMENTO AGREGADO ---
def load_sla_agregado(alvos):
    sol, no, fora = 0, 0, 0
    for p in alvos:
        caminho = base_dados / p / "SLA.csv" if p != "." else base_dados / "SLA.csv"
        if caminho.exists():
            df = safe_read_csv(caminho)
            if df is not None and not df.empty:
                sol += float(df['Solicitado'].iloc[0])
                no += float(df['No_prazo'].iloc[0])
                fora += float(df['Fora_prazo'].iloc[0])
    taxa = (no / sol) if sol > 0 else 0
    return pd.DataFrame({"Solicitado": [sol], "No_prazo": [no], "Fora_prazo": [fora], "taxa": [taxa]})

def load_analise_pedido_agregado(alvos):
    sol, ent = 0, 0
    for p in alvos:
        caminho = base_dados / p / "ANALISE_PEDIDO.csv" if p != "." else base_dados / "ANALISE_PEDIDO.csv"
        if caminho.exists():
            df = safe_read_csv(caminho)
            if df is not None and not df.empty:
                sol += float(df['Solicitado'].iloc[0])
                ent += float(df['Entregue'].iloc[0])
    taxa = (ent / sol) if sol > 0 else 0
    return pd.DataFrame({"Solicitado": [sol], "Entregue": [ent], "Taxa": [taxa]})

# --- RENDERIZAÇÃO DAS ABAS ---
def render_visao_geral(alvos):
    if not alvos:
        st.warning("Crie as pastas das semanas dentro de 'dados/' e insira seus arquivos.")
        return
        
    sla = load_sla_agregado(alvos)
    pedidos = load_analise_pedido_agregado(alvos)
    
    if sla['Solicitado'].iloc[0] == 0:
        st.warning("Não foram encontrados dados para o período selecionado.")
        return
        
    sla_percent = sla['taxa'].iloc[0] * 100
    diaria_percent = pedidos['Taxa'].iloc[0] * 100
    
    st.markdown(f"""<div class="kpi-row">
      <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Pedidos</span><span class="kpi-val">{int(sla['Solicitado'].iloc[0])}</span></div>
      <div class="kpi-card kpi-green"><span class="kpi-title">Taxa SLA</span><span class="kpi-val">{sla_percent:.1f}%</span></div>
      <div class="kpi-card kpi-purple"><span class="kpi-title">Diárias Entregues</span><span class="kpi-val">{int(pedidos['Entregue'].iloc[0])}</span></div>
      <div class="kpi-card kpi-orange"><span class="kpi-title">Taxa Diárias</span><span class="kpi-val">{diaria_percent:.2f}%</span></div>
    </div>""", unsafe_allow_html=True)
    
    col_pie, col_bar = st.columns(2, gap="medium")
    with col_pie:
        st.markdown('<div class="graph-container"><div class="graph-title">Desempenho de Prazo SLA</div><div class="graph-content">', unsafe_allow_html=True)
        fig_pie = px.pie(values=[sla['No_prazo'].iloc[0], sla['Fora_prazo'].iloc[0]], names=["No Prazo", "Fora do Prazo"], hole=0.40, color_discrete_sequence=['#2266ee','#f65054'])
        fig_pie.update_traces(textinfo="percent", textposition="inside", textfont=dict(size=14, color="#ffffff"), marker=dict(line=dict(color="#ffffff", width=2)), pull=[0.02,0.02])
        fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10,color="#1a1a1a")), margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=180)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div></div>', unsafe_allow_html=True)
    with col_bar:
        st.markdown('<div class="graph-container"><div class="graph-title">Balanço de Diárias</div><div class="graph-content">', unsafe_allow_html=True)
        solicitadas, entregues = pedidos['Solicitado'].iloc[0], pedidos['Entregue'].iloc[0]
        saldo = entregues - solicitadas
        fig_bar = px.bar(pd.DataFrame({"Tipo":["Solicitadas","Entregues"],"Qtd":[solicitadas,entregues]}), x="Tipo", y="Qtd", text_auto='.0f', color="Tipo", color_discrete_map={"Solicitadas":"#FFA500","Entregues":"#23B26D"})
        fig_bar.update_traces(texttemplate='<b>%{y}</b>', textposition='inside', textfont=dict(size=14, color="#fff"))
        fig_bar.update_layout(showlegend=False, xaxis=dict(title="", tickfont=dict(size=11, color="#1a1a1a")), yaxis=dict(title="", showticklabels=True, range=[0,max(solicitadas,entregues)*1.15]), margin=dict(l=12,r=12,t=8,b=8), height=150, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})
        if saldo >= 0: msg = f"✅ Superamos a meta em {int(saldo)} diárias!"
        else: msg = f"⚠️ Déficit de {int(abs(saldo))} diárias em relação à demanda."
        st.markdown(f"""<div class='diarias-card-sucesso' style='margin-top:8px;'>{msg}</div></div></div>""", unsafe_allow_html=True)

    info_saldo = f"superando a demanda em {int(saldo)} profissionais" if saldo >= 0 else f"entregando {int(abs(saldo))} posições a menos que o solicitado"
    texto_resumo = f"""<div class="obs-box"><b>Resumo Executivo - Período Selecionado</b><br>
    <ul>
        <li><b>Cumprimento SLA:</b> O nível de serviço foi de <b>{sla_percent:.1f}%</b>. Foram computados {int(sla['No_prazo'].iloc[0])} pedidos dentro do prazo contra {int(sla['Fora_prazo'].iloc[0])} extemporâneos.</li>
        <li><b>Volume de Diárias:</b> A operação apresentou uma taxa de entrega de <b>{diaria_percent:.1f}%</b>, {info_saldo}.</li>
    </ul></div>"""
    st.markdown(texto_resumo, unsafe_allow_html=True)

def render_analise_sla(alvos):
    if not alvos: return
    sla = load_sla_agregado(alvos)
    if sla['Solicitado'].iloc[0] == 0: return
    total, dentro, fora = int(sla['Solicitado'].iloc[0]), int(sla['No_prazo'].iloc[0]), int(sla['Fora_prazo'].iloc[0])
    perc_dentro, perc_fora = dentro/total*100, fora/total*100
    st.markdown(f"""<div class="kpi-row">
      <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Solicitações</span><span class="kpi-val">{total}</span></div>
      <div class="kpi-card kpi-green"><span class="kpi-title">Dentro do Prazo</span><span class="kpi-val">{dentro}</span><span style="font-size:0.92em;color:#e9ffe1;">{perc_dentro:.2f}% do total</span></div>
      <div class="kpi-card kpi-orange"><span class="kpi-title">Fora do Prazo</span><span class="kpi-val">{fora}</span><span style="font-size:0.92em;color:#fffbe5;">{perc_fora:.2f}% do total</span></div>
    </div>""", unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(mode="gauge+number", value=perc_dentro, number={'suffix':' %','font':{'size':32}}, title={'text':'SLA Cumprido (%)','font':{'size':17}}, gauge={'axis':{'range':[0,100],'tickwidth':2},'bar':{'color':'#23B26D'},'bgcolor':'#eaeaee','steps':[{'range':[0,perc_dentro],'color':'#23B26D'},{'range':[perc_dentro,100],'color':'#ffebdf'}],'threshold':{'line':{'color':'#FF7927','width':4},'thickness':0.7,'value':perc_dentro}}))
    fig.update_layout(height=220, margin=dict(l=22,r=22,t=22,b=20), paper_bgcolor="#f6f9fd", font=dict(size=15))
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    alerta_fora = f"Atenção: Um volume crítico de {fora} pedidos ocorreu fora do escopo contratual de prazo, exigindo mobilização extraordinária da operação." if perc_fora > 20 else f"O volume de pedidos fora do prazo manteve-se sob controle (abaixo de 20%)."
    texto_sla = f"""<div class="obs-box" style="background:#e8f1fd;border-left:5px solid #5aa7db;color:#164976;font-size:1.04em;margin-top:10px;font-weight:500;">
    <b>Contexto SLA Gerencial</b><br>
    <ul>
        <li><b>Respeito ao Prazo:</b> {perc_dentro:.1f}% da demanda foi enviada com o aviso prévio exigido.</li>
        <li><b>Impacto Extemporâneo:</b> {alerta_fora}</li>
    </ul></div>"""
    st.markdown(texto_sla, unsafe_allow_html=True)

def render_diarias(alvos):
    if not alvos: return
    pedidos = load_analise_pedido_agregado(alvos)
    if pedidos['Solicitado'].iloc[0] == 0: return
    solicitadas, entregues = int(pedidos['Solicitado'].iloc[0]), int(pedidos['Entregue'].iloc[0])
    saldo = entregues - solicitadas
    taxa = pedidos['Taxa'].iloc[0] * 100
    st.markdown(f"""<div class="diarias-kpi-row"><div class="diarias-kpi-card diarias-kpi-blue"><span class="diarias-kpi-title">Solicitadas</span><span class="diarias-kpi-val">{solicitadas}</span></div><div class="diarias-kpi-card diarias-kpi-green"><span class="diarias-kpi-title">Entregues</span><span class="diarias-kpi-val">{entregues}</span></div><div class="diarias-kpi-card diarias-kpi-purple"><span class="diarias-kpi-title">Taxa de Atendimento</span><span class="diarias-kpi-val">{taxa:.2f}%</span></div></div>""", unsafe_allow_html=True)
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(x=["Volume Global Selecionado"], y=[solicitadas], name="Solicitadas", marker=dict(color="#FFA500"), text=[solicitadas], textposition="outside"))
    fig_barras.add_trace(go.Bar(x=["Volume Global Selecionado"], y=[entregues], name="Entregues", marker=dict(color="#23B26D"), text=[entregues], textposition="outside"))
    fig_barras.update_layout(barmode='group', yaxis=dict(range=[0,max(solicitadas,entregues)*1.15]), height=310, margin=dict(t=30,b=30,l=28,r=28), legend=dict(orientation='h', x=0.5, y=-0.20, xanchor='center'), plot_bgcolor="#fff", paper_bgcolor="#fff")
    st.plotly_chart(fig_barras, use_container_width=True, config={"displayModeBar": False})

    if saldo >= 0:
        texto_diarias = f"<b>Performance de Sucesso!</b><br> A equipe superou as expectativas ao entregar <b>{entregues} diárias</b> contra <b>{solicitadas} solicitadas</b>, gerando um saldo positivo operacional de <b style='color:#12bb26;'>{saldo} diárias</b>."
    else:
        texto_diarias = f"<b>Desempenho Abaixo da Meta</b><br> Entregamos <b>{entregues} diárias</b> de um total de <b>{solicitadas} solicitadas</b>, resultando em um déficit de <b style='color:#d93025;'>{abs(saldo)} diárias</b>."
        
    st.markdown(f"""<div class="diarias-card-sucesso">{texto_diarias}<br> Taxa final de atendimento: <b>{taxa:.2f}%</b>.</div>""", unsafe_allow_html=True)

def render_historico(alvos):
    if not alvos: return
    p_alvo = alvos[0] 
    p_dir = base_dados / p_alvo if p_alvo != "." else base_dados
    try:
        sla_hist = safe_read_csv(p_dir / 'HISTORICO_SLA.csv')
        ent_hist = safe_read_csv(p_dir / 'HISTORICO_ENTREGA.csv')
        
        if sla_hist is None or ent_hist is None:
            st.warning(f"Planilhas de histórico não encontradas na pasta base.")
            return

        # Limpeza SLA
        sla_hist.columns = ['Mes','Taxa']
        sla_hist['Taxa'] = sla_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.').strip()))
        sla_hist['No Prazo (%)'] = sla_hist['Taxa'] * 100
        sla_hist['Fora do Prazo (%)'] = (1 - sla_hist['Taxa']) * 100
        
        # Limpeza Entrega
        ent_hist.columns = ['Mês','Solicitadas','Entregues','Taxa']
        ent_hist['Solicitadas'] = pd.to_numeric(ent_hist['Solicitadas'], errors='coerce').fillna(0)
        ent_hist['Entregues'] = pd.to_numeric(ent_hist['Entregues'], errors='coerce').fillna(0)
        ent_hist['Taxa_%'] = ent_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.'))) * 100

        # GRÁFICO 1: SLA (BARMODE RELATIVE PARA QUE O AZUL CRESÇA SEM ESCONDER O VERMELHO)
        st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:12px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Prazos de Entregas</div></div>""", unsafe_allow_html=True)
        
        fig1 = go.Figure()
        # Azul (No prazo)
        fig1.add_trace(go.Bar(name='No Prazo', x=sla_hist['Mes'], y=sla_hist['No Prazo (%)'], marker_color='#2266ee', text=[f"<b>{v:.1f}%</b>" for v in sla_hist['No Prazo (%)']], textposition='inside', textfont=dict(color='white', size=13)))
        # Vermelho (Fora do Prazo) - Deslocado no eixo para não esmagar o Azul
        fig1.add_trace(go.Bar(name='Fora do Prazo', x=sla_hist['Mes'], y=sla_hist['Fora do Prazo (%)'], marker_color='#f65054', text=[f"<b>{v:.1f}%</b>" if v > 5 else "" for v in sla_hist['Fora do Prazo (%)']], textposition='inside', textfont=dict(color='white', size=13)))
        
        # Linha limite de 100%
        fig1.add_hline(y=100, line_dash="dash", line_color="#000", annotation_text="Meta (100%)", annotation_position="top left")
        
        fig1.update_layout(barmode='relative', height=400, margin=dict(l=20,r=20,t=40,b=38), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'), plot_bgcolor='#fff', yaxis=dict(title='SLA (%)'))
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar':False})
        
        # GRÁFICO 2: ENTREGAS
        st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-top:28px;margin-bottom:12px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Diárias Entregues</div></div>""", unsafe_allow_html=True)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=ent_hist['Mês'], y=ent_hist['Solicitadas'], name='Solicitadas', marker_color='#FFA500', text=[f"<b>{v}</b>" for v in ent_hist['Solicitadas']], textposition='auto'))
        fig2.add_trace(go.Bar(x=ent_hist['Mês'], y=ent_hist['Entregues'], name='Entregues', marker_color='#23B26D', text=[f"<b>{v}</b>" for v in ent_hist['Entregues']], textposition='auto'))
        fig2.add_trace(go.Scatter(x=ent_hist['Mês'], y=ent_hist['Taxa_%'], mode='lines+markers+text', name='Taxa (%)', line=dict(color='#9b1de9', width=2), marker=dict(size=8,color='#9b1de9'), text=[f"<b>{tx:.1f}%</b>" for tx in ent_hist['Taxa_%']], textposition="top center", yaxis="y2"))
        
        max_vol = max(ent_hist['Solicitadas'].max(), ent_hist['Entregues'].max())
        fig2.update_layout(barmode='group', height=400, margin=dict(l=20,r=20,t=40,b=38), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'), plot_bgcolor='#fff', yaxis=dict(range=[0, max_vol * 1.3]), yaxis2=dict(range=[0, max(110, ent_hist['Taxa_%'].max()*1.2)], overlaying='y', side='right', showgrid=False, visible=False))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})

        # --- INTELIGÊNCIA DINÂMICA DO HISTÓRICO ---
        tot_solicitado = ent_hist['Solicitadas'].sum()
        tot_entregue = ent_hist['Entregues'].sum()
        tx_global = (tot_entregue / tot_solicitado * 100) if tot_solicitado > 0 else 0
        
        melhor_semana_ent = ent_hist.loc[ent_hist['Taxa_%'].idxmax()]
        pior_semana_ent = ent_hist.loc[ent_hist['Taxa_%'].idxmin()]
        melhor_semana_sla = sla_hist.loc[sla_hist['No Prazo (%)'].idxmax()]
        pior_semana_sla = sla_hist.loc[sla_hist['No Prazo (%)'].idxmin()]
        
        html_inteligencia = f"""
        <div style="display:flex; gap:20px; margin-top:20px;">
            <div style="flex:1; background:#eafff1; border-left:6px solid #23b26d; border-radius:8px; padding:20px;">
                <h4 style="color:#117b46; margin-top:0; margin-bottom:15px;">🚀 Pontos Fortes & Retenção</h4>
                <ul style="color:#1a1a1a; font-size:0.95em; line-height:1.6;">
                    <li><b>Pico de Atendimento:</b> O melhor resultado da equipe ocorreu em <b>{melhor_semana_ent['Mês']}</b>, alcançando <b>{melhor_semana_ent['Taxa_%']:.1f}%</b> de suprimento das vagas.</li>
                    <li><b>Engajamento de SLA:</b> O período de <b>{melhor_semana_sla['Mes']}</b> obteve a maior organização do cliente, com <b>{melhor_semana_sla['No Prazo (%)']:.1f}%</b> dos pedidos no prazo.</li>
                    <li><b>Volume Acumulado:</b> No cenário total deste histórico, entregamos <b>{int(tot_entregue)}</b> de <b>{int(tot_solicitado)}</b> posições (Média Global de {tx_global:.1f}%).</li>
                </ul>
            </div>
            <div style="flex:1; background:#fff2f2; border-left:6px solid #f65054; border-radius:8px; padding:20px;">
                <h4 style="color:#b32629; margin-top:0; margin-bottom:15px;">⚠️ Pontos de Atenção & Gargalos</h4>
                <ul style="color:#1a1a1a; font-size:0.95em; line-height:1.6;">
                    <li><b>Queda de Retenção:</b> O período de <b>{pior_semana_ent['Mês']}</b> apresentou o pior índice de cobertura, caindo para apenas <b>{pior_semana_ent['Taxa_%']:.1f}%</b>.</li>
                    <li><b>Quebra Crítica de SLA:</b> O maior estrangulamento da equipe ocorreu em <b>{pior_semana_sla['Mes']}</b>, onde <b>{pior_semana_sla['Fora do Prazo (%)']:.1f}%</b> dos pedidos entraram fora do prazo contratual.</li>
                    <li><b>Fechamento Atual:</b> A última medição registrada ({ent_hist['Mês'].iloc[-1]}) aponta entrega de <b>{ent_hist['Taxa_%'].iloc[-1]:.1f}%</b> e SLA de <b>{sla_hist['No Prazo (%)'].iloc[-1]:.1f}%</b>.</li>
                </ul>
            </div>
        </div>
        """
        st.markdown(html_inteligencia, unsafe_allow_html=True)

    except Exception as e: st.warning(f"Erro ao gerar a aba de Histórico. Detalhe: {e}")

# --- SUPER CARREGADOR DA ANÁLISE DE ENTREGA ---
def parse_hdr_date(v):
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

def load_all_entrega_data(alvos):
    df_entregas_list, df_pedidos_list, df_sth_list = [], [], []
    
    for p in alvos:
        p_dir = base_dados / p if p != "." else base_dados
        
        file_entregas = p_dir / 'ENTREGAS_DIA.xlsx'
        if file_entregas.exists():
            try:
                df_e = pd.read_excel(file_entregas, engine="openpyxl")
                if 'Data' in df_e.columns:
                    df_e = df_e[df_e['Data'].astype(str).str.upper() != 'TOTAL']
                    df_e['Data'] = pd.to_datetime(df_e['Data'], errors='coerce')
                    df_e = df_e.rename(columns={col: 'entregas' for col in df_e.columns if 'Total' in col or 'entregue' in col}).dropna(subset=['Data'])
                    df_entregas_list.append(df_e)
            except: pass

        file_pedidos = p_dir / 'PEDIDOS_DIA.xlsx'
        if file_pedidos.exists():
            try:
                xls = pd.ExcelFile(file_pedidos, engine="openpyxl")
                hist = xls.parse('HISTOGRAMA', header=None)
                ex = xls.parse('HISTOGRAMA_EXCEDENTE', header=None)
                
                row_no = hist[hist.iloc[:,0].astype(str).str.upper().str.strip() == 'SUBTOTAL (FILTRO)'].iloc[0]
                row_out = ex[ex.iloc[:,0].astype(str).str.upper().str.strip() == 'SUBTOTAL (FILTRO)'].iloc[0]
                
                header_row = None
                for i in range(min(10, hist.shape[0])):
                    if parse_hdr_date(hist.iat[i, 3]) is not None:
                        header_row = i
                        break
                if header_row is not None:
                    datas, val_no, val_out = [], [], []
                    for c in range(3, hist.shape[1]):
                        d = parse_hdr_date(hist.iat[header_row, c])
                        if d:
                            datas.append(d)
                            val_no.append(pd.to_numeric(row_no.iloc[c], errors='coerce'))
                            val_out.append(pd.to_numeric(row_out.iloc[c], errors='coerce'))
                    
                    df_p = pd.DataFrame({'Data': pd.to_datetime(datas).normalize(), 'pedidos_no_prazo': val_no, 'pedidos_fora_prazo': val_out}).fillna(0)
                    df_pedidos_list.append(df_p)
            except: pass

        p_sth = p_dir / 'solicitacoes'
        if not p_sth.exists() and p == ".": p_sth = base_dados / 'solicitacoes'
            
        if p_sth.exists():
            for arq in glob.glob(os.path.join(p_sth, '*.xlsx')):
                try:
                    df_s = pd.read_excel(arq, sheet_name='STH_PLANEJAMENTO', usecols=['DT RECEBIMENTO', 'INICIO', 'FIM'], engine='openpyxl')
                    df_sth_list.append(df_s)
                except: pass

    df_entregas = pd.concat(df_entregas_list).groupby('Data', as_index=False).sum() if df_entregas_list else pd.DataFrame()
    df_pedidos = pd.concat(df_pedidos_list).groupby('Data', as_index=False).sum() if df_pedidos_list else pd.DataFrame()
    df_sth = pd.concat(df_sth_list, ignore_index=True) if df_sth_list else pd.DataFrame()
    
    return df_pedidos, df_entregas, df_sth

def render_analise_entrega(alvos):
    if not alvos: return
    pedidos_df, entregas_df, sth_plan = load_all_entrega_data(alvos)

    if pedidos_df.empty or entregas_df.empty:
        st.warning(f"Certifique-se de que os arquivos 'ENTREGAS_DIA.xlsx' e 'PEDIDOS_DIA.xlsx' estão dentro das pastas selecionadas.")
        return

    dados = pd.merge(pedidos_df, entregas_df[['Data', 'entregas']], on='Data', how='outer').fillna(0)
    tem_prazo = False
    
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
                            prazo_dias = (d - row['DT RECEBIMENTO']).days
                            categoria = 'No Prazo' if prazo_dias >= 10 else 'Fora do Prazo'
                            lead_times.append({'Data': d.normalize(), 'Prazo': prazo_dias, 'Categoria': categoria})
                except: pass
        
        if lead_times:
            tem_prazo = True
            df_lead = pd.DataFrame(lead_times)
            df_lead['Critico'] = df_lead['Prazo'] < 3
            
            agrup_geral = df_lead.groupby('Data').agg(Prazo_Medio=('Prazo', 'mean'), Total=('Prazo', 'count'), Criticos=('Critico', 'sum')).reset_index()
            agrup_geral['Pct_Critico'] = (agrup_geral['Criticos'] / agrup_geral['Total']) * 100
            
            lead_pivot = df_lead.pivot_table(index='Data', columns='Categoria', values='Prazo', aggfunc='mean').reset_index()
            if 'No Prazo' in lead_pivot.columns: lead_pivot = lead_pivot.rename(columns={'No Prazo': 'Mean_No_Prazo'})
            if 'Fora do Prazo' in lead_pivot.columns: lead_pivot = lead_pivot.rename(columns={'Fora do Prazo': 'Mean_Fora_Prazo'})
                
            dados = pd.merge(dados, agrup_geral[['Data', 'Prazo_Medio', 'Pct_Critico']], on='Data', how='left')
            dados = pd.merge(dados, lead_pivot, on='Data', how='left')

    if len(dados) == 0: return
    
    dados = dados.sort_values('Data')
    period_start, period_end = dados['Data'].min(), dados['Data'].max()
    str_start, str_end = period_start.strftime('%d/%m'), period_end.strftime('%d/%m')
    
    # --- GRÁFICO 1: VOLUME ---
    max_y = float(dados[['pedidos_no_prazo', 'entregas', 'pedidos_fora_prazo']].max().max())
    y_max = max_y * (1.18 if max_y > 0 else 10)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=dados['Data'], y=dados['pedidos_no_prazo'], mode='lines+markers+text', name='Pedidos no Prazo', line=dict(color='#2266ee', width=2), marker=dict(size=6, color='#2266ee'), text=[f"<b>{int(round(v))}</b>" if v > 0 else "" for v in dados['pedidos_no_prazo']], textposition='top center', textfont=dict(size=11, color='#2266ee'), cliponaxis=False))
    fig1.add_trace(go.Scatter(x=dados['Data'], y=dados['entregas'], mode='lines+markers+text', name='Entregas', line=dict(color='#23B26D', width=2), marker=dict(size=6, color='#23B26D'), text=[f"<b>{int(round(v))}</b>" if v > 0 else "" for v in dados['entregas']], textposition='bottom center', textfont=dict(size=11, color='#23B26D'), cliponaxis=False))
    fig1.add_trace(go.Scatter(x=dados['Data'], y=dados['pedidos_fora_prazo'], mode='lines+markers+text', name='Fora do Prazo', line=dict(color='#f65054', width=2, dash='dash'), marker=dict(size=6, color='#f65054'), text=[f"<b>{int(round(v))}</b>" if v > 0 else "" for v in dados['pedidos_fora_prazo']], textposition='top center', textfont=dict(size=11, color='#f65054'), cliponaxis=False))
    fig1.update_layout(xaxis=dict(tickformat='%d/%m', showgrid=False, dtick=86400000.0), yaxis=dict(title='Qtd. Diárias', range=[0, y_max], showgrid=True, gridcolor='rgba(120,140,170,0.22)'), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=11)), height=450, margin=dict(l=18, r=18, t=35, b=65), hovermode='x unified', plot_bgcolor='#fff', paper_bgcolor='#fff')

    st.markdown(f"<div class='graph-container'><div style='font-weight:700; font-size:1.1em; color:#1a1a1a; margin-bottom:10px;'>Pedidos x Entregas ({str_start} a {str_end})</div>", unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

    # --- GRÁFICO 2: LEAD TIME E METAS ---
    if tem_prazo:
        fig2 = go.Figure()
        
        if 'Mean_No_Prazo' in dados.columns and not dados['Mean_No_Prazo'].isna().all():
            texto_no_prazo = [f"<b>{int(qtd)}</b><br>{v:.1f}d" if pd.notna(v) and qtd > 0 else "" for qtd, v in zip(dados['pedidos_no_prazo'], dados['Mean_No_Prazo'])]
            fig2.add_trace(go.Scatter(x=dados['Data'], y=dados['Mean_No_Prazo'], mode='lines+markers+text', name='Prazo - Regra SLA', line=dict(color='#23b26d', width=3), marker=dict(size=8, color='#23b26d'), text=texto_no_prazo, textposition='top center', textfont=dict(size=10, color='#23b26d'), cliponaxis=False))
        
        if 'Mean_Fora_Prazo' in dados.columns and not dados['Mean_Fora_Prazo'].isna().all():
            texto_fora_prazo = [f"<b>{int(qtd)}</b><br>{v:.1f}d" if pd.notna(v) and qtd > 0 else "" for qtd, v in zip(dados['pedidos_fora_prazo'], dados['Mean_Fora_Prazo'])]
            fig2.add_trace(go.Scatter(x=dados['Data'], y=dados['Mean_Fora_Prazo'], mode='lines+markers+text', name='Prazo - Quebra SLA', line=dict(color='#ff7927', width=3), marker=dict(size=8, color='#ff7927'), text=texto_fora_prazo, textposition='bottom center', textfont=dict(size=10, color='#ff7927'), cliponaxis=False))
            
        fig2.add_hline(y=10, line_dash="dash", line_color="#1a1a1a", annotation_text="Meta SLA (10 dias)", annotation_position="top left", annotation_font_size=11)

        cols_lead = [c for c in ['Mean_No_Prazo', 'Mean_Fora_Prazo'] if c in dados.columns]
        max_y_lead = dados[cols_lead].max().max() if cols_lead else 15
        max_y_lead = 15 if pd.isna(max_y_lead) else max_y_lead

        fig2.update_layout(xaxis=dict(tickformat='%d/%m', showgrid=False, dtick=86400000.0), yaxis=dict(title='Dias de Antecedência', range=[-0.5, max(12, max_y_lead * 1.35)], zeroline=True, zerolinewidth=1, zerolinecolor='rgba(0,0,0,0.15)', showgrid=True, gridcolor='rgba(120,140,170,0.22)'), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=11)), height=350, margin=dict(l=18, r=18, t=35, b=65), hovermode='x unified', plot_bgcolor='#fff', paper_bgcolor='#fff')

        st.markdown(f"<div class='graph-container' style='margin-top:20px;'><div style='font-weight:700; font-size:1.1em; color:#1a1a1a; margin-bottom:10px;'>Prazo para contratação - {str_start} a {str_end}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ANÁLISE ESCRITA ---
    avg_pedidos, avg_entregas, avg_fora = dados['pedidos_no_prazo'].mean(), dados['entregas'].mean(), dados['pedidos_fora_prazo'].mean()
    analise = f"<ul><li><b>Destaque Operacional:</b> Média de <b>{avg_pedidos:.0f}</b> no prazo e <b>{avg_fora:.0f}</b> fora do prazo/dia.</li><li><b>Termômetro SLA:</b> Saldo médio foi de <b>{(avg_entregas - avg_pedidos):.0f}</b>/dia.</li>"
    
    if tem_prazo:
        avg_lead, avg_crit = dados['Prazo_Medio'].mean(), dados['Pct_Critico'].mean()
        idx_crit = dados['Prazo_Medio'].idxmin()
        if pd.notna(idx_crit):
            dia_crit, val_crit = dados.loc[idx_crit, 'Data'].strftime('%d/%m'), dados.loc[idx_crit, 'Prazo_Medio']
            analise += f"<li><b>SLA Real Global (Misto):</b> Ao somar pedidos bons e ruins, a equipe teve <b>{avg_lead:.1f} dias reais</b> de antecedência média para trabalhar.</li><li><b>Risco e Sobrecarga (< 3 dias):</b> O índice de requisições críticas representou <b>{avg_crit:.1f}%</b> de todas as vagas diárias. O pior pico crítico ocorreu no dia <b>{dia_crit}</b>, com média geral de apenas <b>{val_crit:.1f} dias</b> de manobra.</li>"
    st.markdown(f"<div class='obs-box'>{analise}</ul></div>", unsafe_allow_html=True)

# ---- ROTEAMENTO ----
aba_ativa = st.session_state.current_tab
alvos_ativos = obter_caminhos_alvo()

if aba_ativa == "Visão Geral": render_visao_geral(alvos_ativos)
elif aba_ativa == "Análise SLA": render_analise_sla(alvos_ativos)
elif aba_ativa == "Diárias": render_diarias(alvos_ativos)
elif aba_ativa == "Histórico Mensal": render_historico(alvos_ativos)
elif aba_ativa == "Análise Entrega": render_analise_entrega(alvos_ativos)