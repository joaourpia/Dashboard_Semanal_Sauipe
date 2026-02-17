import streamlit as st
# A importação de components era utilizada apenas para acionar o print via JavaScript e foi removida.
import pandas as pd
import datetime as dt
import re
import plotly.express as px
import numpy as np
from pathlib import Path
import importlib.util

def _labels_inteligentes(serie, max_labels=10):
    s = pd.to_numeric(serie, errors='coerce').fillna(0)
    n = len(s)
    labels = [''] * n
    if n == 0:
        return labels
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

def _posicoes_stagger(n, estilo='up'):
    if estilo == 'up':
        padrao = ['top center', 'top left', 'top right']
    elif estilo == 'down':
        padrao = ['bottom center', 'bottom left', 'bottom right']
    else:
        padrao = ['middle right', 'middle left']
    return [padrao[i % len(padrao)] for i in range(n)]
import plotly.graph_objects as go
import base64

# Este dashboard inclui uma função de exportação em PDF. Ao selecionar "Aba atual" ou "Todas as abas" e
# clicar em "Imprimir em PDF", o conteúdo renderizado será enviado ao navegador para impressão. Caso
# deseje salvar como PDF, escolha a opção correspondente no diálogo de impressão do navegador.

st.set_page_config(page_title="Dashboard Operacional", layout="wide")

def get_base64_image(image_path):
    """Lê uma imagem e retorna uma string base64 codificada. Em caso de erro, retorna vazio."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

# Carrega o logo, se existir
logo_base64 = get_base64_image("images/Logo_Parceria.png")
logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="max-width:300px;margin-bottom:10px;">' if logo_base64 else ""

# --- CSS para layout e componentes ---
st.markdown("""
<style>
body {background-color: #f4f9ff;}
div[data-testid="stHorizontalBlock"] > div {margin-bottom: -8px;}
.stButton>button {
  border-radius: 12px 12px 0 0 !important;
  padding: 7px 25px 5px 25px !important;
  margin: 0 6px 0 0 !important;
  border: none !important;
  font-size: 1em !important;
  font-weight: 700 !important;
  color: #2266ee !important;
  background: #e7eefb !important;
  transition: background .18s, color .18s;
}
.stButton>button.selected-tab {
  background: #2266ee !important;
  color: #fff !important;
  box-shadow: 0 4px 14px #2266ee47;
}
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
.diarias-motivos {background:#fff7e4; border-left:6px solid #ffba4f; border-radius:8px; padding:13px 19px 12px 19px; margin-bottom:18px; margin-top:1px; color:#b67804;}
.diarias-motivos-title {margin-bottom:7px; font-weight: 700; font-size:1.05em;}
.dashboard-header {background:#ffffff;padding:10px 20px;margin:-60px -60px 10px -60px;border-bottom:3px solid #2266ee;display:flex;justify-content:space-between;align-items:center;}
</style>
""", unsafe_allow_html=True)

# ------------ Cabeçalho do Dashboard ------------
st.markdown(f"""
<div style="text-align:center;margin-top:-60px;margin-bottom:5px;">
    {logo_html}
</div>
<div class="dashboard-header">
  <div class="header-left">
    <h1>Dashboard fevereiro 2026</h1>
    <p>Relatório de Contratação de Temporários - Mendes RH</p>
  </div>
  <div class="header-right">
    <p class="periodo-label">Período</p>
    <p class="periodo-value">01 a 14/02/2026</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ------------ Configuração de abas e estado ------------
# Definição das abas disponíveis no dashboard. A aba "Pesquisa Temporada" e a funcionalidade de impressão foram removidas conforme solicitação.
tab_names = ["Visão Geral", "Análise SLA", "Diárias", "Histórico", "Análise Entrega"]
if "current_tab" not in st.session_state:
    st.session_state.current_tab = tab_names[0]

def set_tab(tab):
    """Altera a aba atual armazenada na sessão."""
    st.session_state.current_tab = tab

# Renderiza botões das abas
tab_cols = st.columns(len(tab_names))
for i, tab in enumerate(tab_names):
    tab_cols[i].button(tab, key=tab, on_click=set_tab, args=(tab,), type="secondary")
    tab_cols[i].markdown(
        f"""<style>
        [data-testid="stButton"] button#{tab} {{ {'background:#2266ee !important;color:#fff !important;box-shadow:0 4px 14px #2266ee47;' if st.session_state.current_tab == tab else ''} }}
        </style>""",
        unsafe_allow_html=True,
    )

# A funcionalidade de exportação para PDF foi removida conforme solicitado.

# -------- Funções de renderização para cada aba --------
def render_visao_geral():
    sla = pd.read_csv('dados/SLA.csv', sep=';', decimal=',', encoding='latin1')
    pedidos = pd.read_csv('dados/ANALISE_PEDIDO.csv', sep=';', decimal=',', encoding='latin1')
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
        st.markdown('<div class="graph-container"><div class="graph-title">Desempenho SLA - 01 a 14/02</div><div class="graph-content">', unsafe_allow_html=True)
        no_prazo = sla['No_prazo'].iloc[0]
        fora_prazo = sla['Fora_prazo'].iloc[0]
        fig_pie = px.pie(values=[no_prazo, fora_prazo], names=["No Prazo", "Fora do Prazo"], hole=0.40, color_discrete_sequence=['#2266ee','#f65054'])
        fig_pie.update_traces(textinfo="percent", textposition="inside", textfont=dict(size=14, color="#ffffff"), marker=dict(line=dict(color="#ffffff", width=2)), pull=[0.02,0.02])
        fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10,color="#1a1a1a")), margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=180)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div></div>', unsafe_allow_html=True)
    with col_bar:
        st.markdown('<div class="graph-container"><div class="graph-title">Diárias - 01 a 14/02</div><div class="graph-content">', unsafe_allow_html=True)
        solicitadas = pedidos.Solicitado.iloc[0]
        entregues = pedidos.Entregue.iloc[0]
        saldo = entregues - solicitadas
        comp_df = pd.DataFrame({"Tipo":["Solicitadas","Entregues"],"Qtd":[solicitadas,entregues]})
        fig_bar = px.bar(comp_df, x="Tipo", y="Qtd", text_auto='.0f', color="Tipo", color_discrete_map={"Solicitadas":"#FFA500","Entregues":"#23B26D"})
        fig_bar.update_traces(texttemplate='<b>%{y}</b>', textposition='inside', textfont=dict(size=14, color="#fff"))
        fig_bar.update_layout(showlegend=False, xaxis=dict(title="", tickfont=dict(size=11, color="#1a1a1a")), yaxis=dict(title="", showticklabels=True, tickfont=dict(size=9, color="#1a1a1a"), range=[0,max(solicitadas,entregues)*1.15]), margin=dict(l=12,r=12,t=8,b=8), height=150, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})
        st.markdown(f"""<div class='diarias-card-sucesso' style='margin-top:8px;'>✅ Não superamos a meta! Entregamos {saldo} diárias a menos que o solicitado ({diaria_percent:.2f}%)</div></div></div>""", unsafe_allow_html=True)
    st.markdown("""<div class="obs-box">
    <b>Observações Importantes - 1 a 14/02/2026</b>
    <ul><li>SLA: 86,8% no periodo de 01 a 14/02. Importante ressaltar que esses dados estão sendo calculados mesmo que os pedidos de 01 a 09/02 tenham sido enviados fora do prazo da SLA (detalhes na aba SLA). Volume: diárias entregues 11,19% abaixo do solicitado, porém no mesmo cenário de diarias fora do prazo mencionadas acima. (detalhes na aba Diárias).</li></ul>
    </div>""", unsafe_allow_html=True)

def render_analise_sla():
    sla = pd.read_csv('dados/SLA.csv', sep=';', decimal=',', encoding='latin1')
    total = int(sla['Solicitado'].iloc[0]); dentro = int(sla['No_prazo'].iloc[0]); fora = int(sla['Fora_prazo'].iloc[0])
    perc_dentro = dentro/total*100; perc_fora = fora/total*100
    st.markdown(f"""<div class="kpi-row">
      <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Solicitações</span><span class="kpi-val">{total}</span></div>
      <div class="kpi-card kpi-green"><span class="kpi-title">Dentro do Prazo</span><span class="kpi-val">{dentro}</span><span style="font-size:0.92em;color:#e9ffe1;margin-left:2px;">{perc_dentro:.2f}% do total</span></div>
      <div class="kpi-card kpi-orange"><span class="kpi-title">Fora do Prazo</span><span class="kpi-val">{fora}</span><span style="font-size:0.92em;color:#fffbe5;margin-left:2px;">{perc_fora:.2f}% do total</span></div>
    </div>""", unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(mode="gauge+number+delta", value=perc_dentro, delta={'reference':100,'increasing':{'color':'#ff7927'},'decreasing':{'color':'#23B26D'}}, number={'suffix':' %','font':{'size':32}}, title={'text':'SLA Cumprido (%)','font':{'size':17}}, gauge={'axis':{'range':[0,100],'tickwidth':2},'bar':{'color':'#23B26D'},'bgcolor':'#eaeaee','steps':[{'range':[0,perc_dentro],'color':'#23B26D'},{'range':[perc_dentro,100],'color':'#ffebdf'}],'threshold':{'line':{'color':'#FF7927','width':4},'thickness':0.7,'value':perc_dentro}}))
    fig.update_layout(height=220, margin=dict(l=22,r=22,t=22,b=20), paper_bgcolor="#f6f9fd", font=dict(size=15))
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("""<div class="obs-box" style="background:#e8f1fd;border-left:5px solid #5aa7db;color:#164976;font-size:1.04em;margin-top:10px;font-weight:500;">
    <b>Contexto SLA</b><br>
    <li><b>Pedidos fora do prazo:</b> O total entregue de SLA foi de 86,8%, porém do total considerado no relatório de 2137, 67% ( 1432) dos pedidos foram enviados fora do prazo.</li><br>
    
    """, unsafe_allow_html=True)

def render_diarias():
    pedidos = pd.read_csv('dados/ANALISE_PEDIDO.csv', sep=';', decimal=',', encoding='latin1')
    solicitadas = int(pedidos.Solicitado.iloc[0]); entregues = int(pedidos.Entregue.iloc[0]); saldo = entregues - solicitadas
    taxa_raw = pedidos['Taxa'].iloc[0]; taxa = float(str(taxa_raw).replace(',', '.').replace('%','')) if '%' in str(taxa_raw) else float(taxa_raw) * 100
    st.markdown(f"""<div class="diarias-kpi-row">
        <div class="diarias-kpi-card diarias-kpi-blue"><span class="diarias-kpi-title">Solicitadas</span><span class="diarias-kpi-val">{solicitadas}</span></div>
        <div class="diarias-kpi-card diarias-kpi-green"><span class="diarias-kpi-title">Entregues</span><span class="diarias-kpi-val">{entregues}</span></div>
        <div class="diarias-kpi-card diarias-kpi-purple"><span class="diarias-kpi-title">Taxa de Atendimento</span><span class="diarias-kpi-val">{taxa:.2f}%</span></div>
    </div>""", unsafe_allow_html=True)
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(x=["novembro"], y=[solicitadas], name="Solicitadas", marker=dict(color="#FFA500"), text=[solicitadas], textposition="outside"))
    fig_barras.add_trace(go.Bar(x=["novembro"], y=[entregues], name="Entregues", marker=dict(color="#23B26D"), text=[entregues], textposition="outside"))
    fig_barras.update_layout(barmode='group', xaxis=dict(title="", tickfont=dict(size=13, color="#212121")), yaxis=dict(title="", showticklabels=True, tickfont=dict(size=13, color="#666"), range=[0,max(solicitadas,entregues)*1.15]), height=310, margin=dict(t=30,b=30,l=28,r=28), legend=dict(orientation='h', x=0.5, y=-0.20, xanchor='center', font=dict(size=13)), plot_bgcolor="#fff", paper_bgcolor="#fff")
    st.plotly_chart(fig_barras, use_container_width=True, config={"displayModeBar": False})
    st.markdown(f"""<div class="diarias-card-sucesso"><b>Desempenho abaixo</b><br> No perioso de 01 a 14/02/26, não superamos as expectativas ao entregar <b>{entregues} diárias</b>, quando foram solicitadas <b>{solicitadas}</b>, resultando em uma diferença negativa de <b style='color:#12bb26;'>{saldo} diárias</b>.<br> Taxa de atendimento: <b>{taxa:.2f}%</b>.</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="diarias-motivos"><div class="diarias-motivos-title">Motivos para Diárias Abaixo do Solicitado</div><ol style="margin-top:0.1em;margin-bottom:0.1em;"><li>A Os pedidos de 01 a 14/02/2026 foram enviados no dia 30/01/2026, portanto todos os pedidos de 01 a 09/02/2026 foram solicitados fora do prazo da sla. No periodo de 01 a 14/02 recebemos 3431 diárias fora do prazo da sla.</li></ol></div>""", unsafe_allow_html=True)

def render_pesquisa_temporada():
    """Renderiza a aba com resultados da pesquisa de temporários."""
    ativos_totais, desligados_totais = 61, 13
    # KPIs
    st.markdown(f"""<div class="kpi-row"><div class="kpi-card kpi-blue"><span class="kpi-title">Temporários Ativos</span><span class="kpi-val">{ativos_totais}</span></div><div class="kpi-card kpi-green"><span class="kpi-title">Temporários Desligados</span><span class="kpi-val">{desligados_totais}</span></div></div>""", unsafe_allow_html=True)
    # Texto descritivo
    st.markdown("""<div style="background:#f4faff;border-radius:8px;padding:16px;margin-bottom:12px;"><p style="margin:0;font-size:0.92em;">Esta aba apresenta de forma resumida os principais resultados da pesquisa de acompanhamento com temporários. Foram avaliados <b>61 colaboradores temporários ativos</b> e <b>13 desligados</b>. As respostas foram agrupadas e apresentadas em gráficos para facilitar a interpretação. As contagens abaixo são estimativas calculadas a partir das percentagens informadas nos relatórios.</p></div>""", unsafe_allow_html=True)
    # Onboarding & cultura
    st.markdown("<h3 style='color:#1a4d9e;margin-top:10px;'>Onboarding & Cultura</h3>", unsafe_allow_html=True)
    df_recepcao = pd.DataFrame({"Nota":["1","2","3","4","5"], "Quantidade":[1,2,10,6,42]})
    df_colegas = pd.DataFrame({"Nota":["1","2","3","4","5"], "Quantidade":[6,1,17,8,29]})
    df_rh = pd.DataFrame({"Categoria":["Ótima","Boa porém distante","Confusa","Ruim"], "Quantidade":[42,11,6,1]})
    col1,col2,col3 = st.columns(3)
    with col1:
        fig_rec = px.bar(df_recepcao, x="Nota", y="Quantidade", color="Nota", color_discrete_sequence=['#f65054','#ffa500','#ffd966','#ac7ef4','#23b26d'], text="Quantidade")
        fig_rec.update_traces(texttemplate="%{text}", textposition="outside")
        fig_rec.update_layout(showlegend=False, title_text="Recepção no Primeiro Dia", height=260, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="Nota", tickfont=dict(size=10)), yaxis=dict(title="Quantidade", range=[0,max(df_recepcao["Quantidade"])*1.2], tickfont=dict(size=10)))
        st.plotly_chart(fig_rec, use_container_width=True, config={"displayModeBar":False})
    with col2:
        fig_col = px.bar(df_colegas, x="Nota", y="Quantidade", color="Nota", color_discrete_sequence=['#f65054','#ffa500','#ffd966','#ac7ef4','#23b26d'], text="Quantidade")
        fig_col.update_traces(texttemplate="%{text}", textposition="outside")
        fig_col.update_layout(showlegend=False, title_text="Tratamento pelos Colegas Efetivos", height=260, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="Nota", tickfont=dict(size=10)), yaxis=dict(title="Quantidade", range=[0,max(df_colegas["Quantidade"])*1.2], tickfont=dict(size=10)))
        st.plotly_chart(fig_col, use_container_width=True, config={"displayModeBar":False})
    with col3:
        fig_rh_obj = px.bar(df_rh, x="Categoria", y="Quantidade", color="Categoria", color_discrete_sequence=['#23b26d','#ac7ef4','#ffa500','#f65054'], text="Quantidade")
        fig_rh_obj.update_traces(texttemplate="%{text}", textposition="outside")
        fig_rh_obj.update_layout(showlegend=False, title_text="Experiência com RH", height=260, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="", tickangle=-20, tickfont=dict(size=9)), yaxis=dict(title="Quantidade", range=[0,max(df_rh["Quantidade"])*1.2], tickfont=dict(size=10)))
        st.plotly_chart(fig_rh_obj, use_container_width=True, config={"displayModeBar":False})
    # Expectativas e remuneração
    st.markdown("<h3 style='color:#1a4d9e;margin-top:20px;'>Expectativas de Efetivação & Remuneração</h3>", unsafe_allow_html=True)
    df_confianca = pd.DataFrame({"Confiança":["Depende de mim","Tenho dúvidas","Não acredito"], "Quantidade":[44,7,10]})
    df_reacao = pd.DataFrame({"Reação":["Ficaria pela efetivação","Ficaria se mudasse algo","Sairia imediatamente"], "Quantidade":[41,15,5]})
    df_justica = pd.DataFrame({"Categoria":["Pagamento justo","É pouco e tenho melhores oportunidades","Trabalho mais que recebo"], "Quantidade":[27,22,12]})
    df_comp = pd.DataFrame({"Categoria":["Paga melhor e trabalho mais leve","Paga igual mas trabalho pesado","Paga pior que outros lugares"], "Quantidade":[39,14,8]})
    col4,col5 = st.columns(2)
    with col4:
        fig_conf = px.bar(df_confianca, x="Confiança", y="Quantidade", color="Confiança", color_discrete_sequence=['#23b26d','#ffa500','#f65054'], text="Quantidade")
        fig_conf.update_traces(texttemplate="%{text}", textposition="outside")
        fig_conf.update_layout(showlegend=False, title_text="Confiança na Efetivação", height=260, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="", tickangle=-10, tickfont=dict(size=10)), yaxis=dict(title="Quantidade", range=[0,max(df_confianca["Quantidade"])*1.2], tickfont=dict(size=10)))
        st.plotly_chart(fig_conf, use_container_width=True, config={"displayModeBar":False})
    with col5:
        fig_reac = px.bar(df_reacao, x="Reação", y="Quantidade", color="Reação", color_discrete_sequence=['#23b26d','#ffa500','#f65054'], text="Quantidade")
        fig_reac.update_traces(texttemplate="%{text}", textposition="outside")
        fig_reac.update_layout(showlegend=False, title_text="Reação a Ofertas Externas", height=260, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="", tickangle=-10, tickfont=dict(size=10)), yaxis=dict(title="Quantidade", range=[0,max(df_reacao["Quantidade"])*1.2], tickfont=dict(size=10)))
        st.plotly_chart(fig_reac, use_container_width=True, config={"displayModeBar":False})
    col6,col7 = st.columns(2)
    with col6:
        fig_just = px.bar(df_justica, x="Quantidade", y="Categoria", orientation='h', color="Categoria", color_discrete_sequence=['#23b26d','#ffa500','#f65054'], text="Quantidade")
        fig_just.update_traces(texttemplate="%{text}", textposition="outside")
        fig_just.update_layout(showlegend=False, title_text="Percepção de Justiça do Pagamento", height=280, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="Quantidade", range=[0,max(df_justica["Quantidade"])*1.2], tickfont=dict(size=10)), yaxis=dict(title="", tickfont=dict(size=9)))
        st.plotly_chart(fig_just, use_container_width=True, config={"displayModeBar":False})
    with col7:
        fig_comp_plot = px.bar(df_comp, x="Quantidade", y="Categoria", orientation='h', color="Categoria", color_discrete_sequence=['#23b26d','#ffa500','#f65054'], text="Quantidade")
        fig_comp_plot.update_traces(texttemplate="%{text}", textposition="outside")
        fig_comp_plot.update_layout(showlegend=False, title_text="Comparação com Empresas Concorrentes", height=280, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="Quantidade", range=[0,max(df_comp["Quantidade"])*1.2], tickfont=dict(size=10)), yaxis=dict(title="", tickfont=dict(size=9)))
        st.plotly_chart(fig_comp_plot, use_container_width=True, config={"displayModeBar":False})
    # Motivos de desligamento
    st.markdown("<h3 style='color:#1a4d9e;margin-top:20px;'>Motivos de Desligamento</h3>", unsafe_allow_html=True)
    df_motivos = pd.DataFrame({"Motivo":["Salário","Transporte/Distância","Chefia/Liderança","Ambiente/Colegas","Trabalho mais pesado","Efetivado na Aviva","Outro emprego"],"Quantidade":[4,1,1,1,1,3,4]})
    df_efet = pd.DataFrame({"Motivo":["Não acreditou","Tempo de espera muito longo","Não queria ser efetivado"],"Quantidade":[3,6,4]})
    col8,col9 = st.columns(2)
    with col8:
        fig_mot = px.bar(df_motivos, x="Quantidade", y="Motivo", orientation='h', color="Motivo", color_discrete_sequence=['#23b26d','#ac7ef4','#ffa500','#f65054','#ffd966','#8dd3c7','#fb8072'], text="Quantidade")
        fig_mot.update_traces(texttemplate="%{text}", textposition="outside")
        fig_mot.update_layout(showlegend=False, title_text="Motivos Reais da Saída", height=280, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="Quantidade", range=[0,max(df_motivos["Quantidade"])*1.2], tickfont=dict(size=10)), yaxis=dict(title="", tickfont=dict(size=9)))
        st.plotly_chart(fig_mot, use_container_width=True, config={"displayModeBar":False})
    with col9:
        fig_efet_bar = px.bar(df_efet, x="Quantidade", y="Motivo", orientation='h', color="Motivo", color_discrete_sequence=['#23b26d','#ffa500','#f65054'], text="Quantidade")
        fig_efet_bar.update_traces(texttemplate="%{text}", textposition="outside")
        fig_efet_bar.update_layout(showlegend=False, title_text="Por que a chance de efetivação não foi suficiente?", height=280, margin=dict(l=10,r=10,t=40,b=20), xaxis=dict(title="Quantidade", range=[0,max(df_efet["Quantidade"])*1.2], tickfont=dict(size=10)), yaxis=dict(title="", tickfont=dict(size=9)))
        st.plotly_chart(fig_efet_bar, use_container_width=True, config={"displayModeBar":False})
    # Análises & Recomendações
    st.markdown("<h3 style='color:#1a4d9e;margin-top:20px;'>Análises & Recomendações</h3>", unsafe_allow_html=True)
    st.markdown("""<ul style="font-size:0.92em;margin-left:18px;">
            <li><b>Padronizar o onboarding:</b> reforçar um roteiro de acolhimento e treinamento consistente para todos os temporários, garantindo que todos tenham acesso às mesmas informações e se sintam bem-vindos.</li>
            <li><b>Fortalecer a cultura de inclusão:</b> incentivar a convivência entre efetivos e temporários, promovendo eventos integrados e feedbacks constantes para reduzir percepções de distanciamento.</li>
            <li><b>Transparência na efetivação:</b> divulgar critérios claros de efetivação e promover conversas individuais para explicar expectativas, aumentando a confiança dos temporários no processo.</li>
            <li><b>Rever remuneração e benefícios:</b> embora a maioria perceba o pagamento como competitivo, 36% apontaram remuneração insuficiente; é importante avaliar salários, benefícios e equilíbrio entre exigência física e recompensa.</li>
            <li><b>Atenção aos motivos de saída:</b> a diversidade de motivos (salário, transporte, liderança, ambiente) indica necessidade de ações multifacetadas como, treinamento de gestores e melhoria do clima.</li>
            <li><b>Entrevistas de desligamento estruturadas:</b> implementar entrevistas de desligamento mais profundas para mapear causas reais de saída e antecipar ajustes necessários.</li>
        </ul>""", unsafe_allow_html=True)

def render_historico():
    sla_hist = pd.read_csv('dados/HISTORICO_SLA.csv', sep=';', encoding='latin1')
    sla_hist.columns = ['Mes','Taxa']
    sla_hist['Taxa'] = sla_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.').strip()))
    sla_hist['Fora'] = 1 - sla_hist['Taxa']
    sla_hist['No Prazo (%)'] = sla_hist['Taxa'] * 100
    sla_hist['Fora do Prazo (%)'] = sla_hist['Fora'] * 100
    st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Prazos de Entregas (01 a 14/02/2026)</div></div>""", unsafe_allow_html=True)
    meses = sla_hist['Mes']
    fig1 = go.Figure(data=[
        go.Bar(name='No Prazo', x=meses, y=sla_hist['No Prazo (%)'], marker_color='#2266ee', text=[f"{v:.1f}%" for v in sla_hist['No Prazo (%)']], textposition='inside', insidetextanchor='middle', textfont=dict(color="#fff",size=12)),
        go.Bar(name='Fora do Prazo', x=meses, y=sla_hist['Fora do Prazo (%)'], marker_color='#f65054', text=[f"{v:.1f}%" for v in sla_hist['Fora do Prazo (%)']], textposition='inside', insidetextanchor='middle', textfont=dict(color="#fff",size=12))
    ])
    fig1.update_layout(barmode='stack', xaxis=dict(tickfont=dict(size=15)), yaxis=dict(title='', range=[0,100], tickfont=dict(size=14)), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=13)), height=350, margin=dict(l=20,r=20,t=80,b=38), plot_bgcolor='#fff', paper_bgcolor='#fff')
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar':False})
    ent_hist = pd.read_csv('dados/HISTORICO_ENTREGA.csv', sep=';', encoding='latin1')
    ent_hist.columns = ['Mês','Solicitadas','Entregues','Taxa']
    ent_hist['Solicitadas'] = ent_hist['Solicitadas'].astype(int); ent_hist['Entregues'] = ent_hist['Entregues'].astype(int)
    ent_hist['Taxa_float'] = ent_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.')))
    ent_hist['Taxa_%'] = ent_hist['Taxa_float'] * 100
    st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Diárias Entregues (01 a 14/02/2026)</div></div>""", unsafe_allow_html=True)
    meses2 = ent_hist['Mês']
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=meses2, y=ent_hist['Solicitadas'], name='Solicitadas', marker_color='#FFA500', text=ent_hist['Solicitadas'], textposition='outside', textfont=dict(size=11,color="#222")))
    fig2.add_trace(go.Bar(x=meses2, y=ent_hist['Entregues'], name='Entregues', marker_color='#23B26D', text=ent_hist['Entregues'], textposition='outside', textfont=dict(size=11,color="#222")))
    fig2.add_trace(go.Scatter(x=meses2, y=ent_hist['Taxa_%'], mode='lines+markers+text', name='Taxa (%)', line=dict(color='#2266ee', width=2, shape='spline'), marker=dict(size=8,color='#2266ee'), text=[f"{tx:.2f}%" for tx in ent_hist['Taxa_%']], textposition="top center", textfont=dict(size=14,color="#fff")))
    fig2.update_layout(barmode='group', xaxis=dict(tickfont=dict(size=13)), yaxis=dict(title='', tickfont=dict(size=12), showgrid=True), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=13)), height=540, margin=dict(l=20,r=20,t=120,b=38), plot_bgcolor='#fff', paper_bgcolor='#fff')
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})

# --- Nova função: Análise Entrega ---

def _infer_period_from_histogram(hist_df: pd.DataFrame):
    if hist_df is None or hist_df.empty:
        raise ValueError("Histograma vazio.")
    year_hint = None
    month_hint = None
    meses = {"janeiro":1,"fevereiro":2,"março":3,"marco":3,"abril":4,"maio":5,"junho":6,"julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
    for r in range(min(8, hist_df.shape[0])):
        row_text = " ".join(hist_df.iloc[r, :min(12, hist_df.shape[1])].astype(str).tolist()).lower()
        m_year = re.search(r"(20\d{2})", row_text)
        if m_year and year_hint is None:
            year_hint = int(m_year.group(1))
        if month_hint is None:
            for nome, num in meses.items():
                if nome in row_text:
                    month_hint = num
                    break
    if year_hint is None:
        year_hint = dt.date.today().year
    found_dates = []
    for r in range(min(10, hist_df.shape[0])):
        for c in range(3, hist_df.shape[1]):
            v = hist_df.iat[r, c]
            if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)):
                d = pd.to_datetime(v, errors="coerce")
                if not pd.isna(d):
                    found_dates.append(d.normalize()); continue
            if isinstance(v, (int, float)):
                try:
                    iv = int(float(v))
                    if 1 <= iv <= 31:
                        mm = month_hint if month_hint else 1
                        found_dates.append(pd.Timestamp(year_hint, mm, iv).normalize()); continue
                except Exception:
                    pass
            s = str(v).strip()
            m = re.match(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$", s)
            if m:
                dd = int(m.group(1)); mm = int(m.group(2)); yy = m.group(3)
                if yy:
                    yy = int(yy); yy = yy + 2000 if yy < 100 else yy
                else:
                    yy = year_hint
                try: found_dates.append(pd.Timestamp(yy, mm, dd).normalize())
                except Exception: pass
    if not found_dates:
        today = pd.Timestamp.today().normalize()
        start = today.replace(day=1)
        end = (start + pd.offsets.MonthEnd(0)).normalize()
        return start, end
    return min(found_dates), max(found_dates)



def _project_root() -> Path:
    p = Path(__file__).resolve().parent
    for _ in range(6):
        if (p / "dados").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent

def _safe_data_path(filename: str) -> Path:
    return _project_root() / "dados" / filename

def _read_excel_safe(path: Path, **kwargs):
    return pd.read_excel(path, engine="openpyxl", **kwargs)

def _excel_file_safe(path: Path):
    return pd.ExcelFile(path, engine="openpyxl")

def render_analise_entrega():
    """
    Renderiza a aba de Análise de Entregas com comparação diária entre pedidos no prazo,
    entregas realizadas e pedidos fora do prazo. Os dados são lidos de planilhas Excel
    fornecidas pelo usuário. A função também calcula métricas de gap e exibe uma análise
    interpretativa abaixo do gráfico.
    """
    import datetime
    periodo_referencia = '01 a 14/02/2026'
    # Carregar dados de entregas (Total entregue por dia). Procura inicialmente em 'dados/ENTREGAS_DIA.xlsx'.
    try:
        entregas_df = _read_excel_safe(_safe_data_path('ENTREGAS_DIA.xlsx'))
    except Exception:
        # Caso não exista na pasta 'dados', tenta utilizar o arquivo original enviado. Isto permite que a aba funcione mesmo sem renomear o arquivo.
        try:
            entregas_df = pd.read_excel('7885c9e9-106d-4fe5-b69d-445a31d51a65.xlsx')
            st.warning("Utilizando arquivo de entregas original (7885c9e9-...). Para uso em produção, renomeie para 'dados/ENTREGAS_DIA.xlsx'.")
        except Exception:
            st.warning("Dados de entregas diárias não encontrados. Certifique-se de que o arquivo 'ENTREGAS_DIA.xlsx' esteja na pasta 'dados'.")
            return
    # Remover linha de total se existir e garantir conversão de datas
    if 'Data' in entregas_df.columns:
        entregas_df = entregas_df[entregas_df['Data'].astype(str).str.upper() != 'TOTAL']
        try:
            entregas_df['Data'] = pd.to_datetime(entregas_df['Data'])
        except Exception:
            pass
    # Renomear a coluna de valor para 'entregas'
    entregas_df = entregas_df.rename(columns={col: 'entregas' for col in entregas_df.columns if 'Total' in col or 'entregue' in col})

    # Carregar dados de pedidos (dentro e fora do prazo)
    try:
        pedidos_xls = _excel_file_safe(_safe_data_path('PEDIDOS_DIA.xlsx'))
    except Exception:
        # Caso não exista na pasta 'dados', tenta utilizar o arquivo original enviado
        try:
            pedidos_xls = pd.ExcelFile('5d357de9-4d77-42ad-8608-c81bc592a7f7.xlsx', engine='openpyxl')
            st.warning("Utilizando arquivo de pedidos original (5d357de9-...). Para uso em produção, renomeie para 'dados/PEDIDOS_DIA.xlsx'.")
        except Exception:
            st.warning("Dados de pedidos diários não encontrados. Certifique-se de que o arquivo 'PEDIDOS_DIA.xlsx' esteja na pasta 'dados'.")
            return
    # Ler as planilhas necessárias
    try:
        hist = pedidos_xls.parse('HISTOGRAMA', header=None)
        ex = pedidos_xls.parse('HISTOGRAMA_EXCEDENTE', header=None)
    except Exception:
        st.error("As planilhas 'HISTOGRAMA' ou 'HISTOGRAMA_EXCEDENTE' não foram encontradas no arquivo de pedidos.")
        return
    # Extrair valores de pedidos no prazo e fora do prazo (linhas SUBTOTAL (FILTRO)) - dinâmico por data
    def _parse_hdr_date(v, year_hint, month_hint):
        if pd.isna(v):
            return None
        if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)):
            return pd.to_datetime(v).normalize()
        s = str(v).strip()
        if not s:
            return None
        m = re.match(r'^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$', s)
        if m:
            dd = int(m.group(1)); mm = int(m.group(2)); yy = m.group(3)
            if yy is None:
                yy = year_hint
            else:
                yy = int(yy); yy = yy + 2000 if yy < 100 else yy
            try:
                return pd.Timestamp(int(yy), mm, dd).normalize()
            except Exception:
                return None
        try:
            day = int(float(s.replace(',', '.')))
            if 1 <= day <= 31:
                return pd.Timestamp(int(year_hint), int(month_hint), day).normalize()
        except Exception:
            return None
        return None

    # inferência de mês/ano pelo campo período no app
    meses = {'janeiro':1,'fevereiro':2,'março':3,'marco':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}
    periodo_txt = str(periodo_referencia).lower() if 'periodo_referencia' in locals() else ''
    mes_numero = next((n for k,n in meses.items() if k in periodo_txt), 1)
    m_ano = re.search(r'(20\d{2})', periodo_txt)
    ano_numero = int(m_ano.group(1)) if m_ano else pd.Timestamp.today().year

    try:
        row_no = hist[hist.iloc[:,0].astype(str).str.upper().str.strip() == 'SUBTOTAL (FILTRO)'].iloc[0]
        row_out = ex[ex.iloc[:,0].astype(str).str.upper().str.strip() == 'SUBTOTAL (FILTRO)'].iloc[0]
    except Exception:
        st.error("Não foi possível extrair os totais de pedidos no prazo/fora do prazo.")
        return

    datas, values_no, values_out = [], [], []
    header_row = 1 if hist.shape[0] > 1 else 0
    for c in range(3, hist.shape[1]):
        d = _parse_hdr_date(hist.iat[header_row, c], ano_numero, mes_numero)
        if d is None:
            continue
        vno = pd.to_numeric(row_no.iloc[c], errors='coerce')
        vout = pd.to_numeric(row_out.iloc[c], errors='coerce')
        datas.append(d)
        values_no.append(0 if pd.isna(vno) else float(vno))
        values_out.append(0 if pd.isna(vout) else float(vout))

    if not datas:
        st.error("Não encontrei datas válidas no cabeçalho do histograma.")
        return

    pedidos_df = pd.DataFrame({
        'Data': pd.to_datetime(datas).normalize(),
        'pedidos_no_prazo': values_no,
        'pedidos_fora_prazo': values_out
    }).groupby('Data', as_index=False).sum()

    period_start = pedidos_df['Data'].min()
    period_end = pedidos_df['Data'].max()
# Mesclar com entregas (com alinhamento robusto de período)
    entregas_df['Data'] = pd.to_datetime(entregas_df['Data'], errors='coerce').dt.normalize()
    entregas_df = entregas_df.dropna(subset=['Data']).copy()

    # Se não houver interseção de datas, realinha pedidos para o mês/ano dominante das entregas
    intersec = set(pd.to_datetime(pedidos_df['Data']).dt.normalize()) & set(entregas_df['Data'])
    if len(intersec) == 0 and not entregas_df.empty and not pedidos_df.empty:
        ano_ref = int(entregas_df['Data'].dt.year.mode().iloc[0])
        mes_ref = int(entregas_df['Data'].dt.month.mode().iloc[0])
        pedidos_df['Data'] = pd.to_datetime(pedidos_df['Data'], errors='coerce').apply(
            lambda d: pd.Timestamp(ano_ref, mes_ref, int(d.day)) if pd.notna(d) else pd.NaT
        )
        pedidos_df = pedidos_df.dropna(subset=['Data'])

    dados = pd.merge(pedidos_df, entregas_df[['Data', 'entregas']], on='Data', how='left')
    dados['entregas'] = pd.to_numeric(dados['entregas'], errors='coerce').fillna(0.0).astype(float)
    # --- Ajuste inteligente de legibilidade (mensal / parcial) ---
    def _smart_dtick_ms(n_points: int) -> int:
        # retorna dtick em milissegundos (dia(s))
        if n_points <= 14:
            d = 1
        elif n_points <= 31:
            d = 2
        elif n_points <= 62:
            d = 3
        else:
            d = 7
        return d * 24 * 60 * 60 * 1000

    def _sparse_labels(vals: pd.Series, n_points: int) -> list:
        # cliente solicitou TODOS os rótulos
        v = pd.to_numeric(vals, errors='coerce').fillna(0).tolist()
        return [f"{int(round(x))}" for x in v]

        # sempre mostrar o último
        out[-1] = f"{int(round(v[-1]))}"

        # se for curto, mostre mais
        if n_points <= 14:
            step = 1
        elif n_points <= 31:
            step = 2
        elif n_points <= 62:
            step = 3
        else:
            step = 7

        # marca pontos a cada step (mas evita poluir demais)
        for i in range(0, len(v), step):
            out[i] = f"{int(round(v[i]))}"

        # adiciona picos/vales locais
        for i in range(1, len(v)-1):
            if v[i] > v[i-1] and v[i] > v[i+1]:
                out[i] = f"{int(round(v[i]))}"
            if v[i] < v[i-1] and v[i] < v[i+1]:
                out[i] = f"{int(round(v[i]))}"

        return out

    n_points = int(len(dados))
    dtick_ms = _smart_dtick_ms(n_points)
    # folga no topo do Y para rótulos
    max_y = float(pd.concat([
        pd.to_numeric(dados['pedidos_no_prazo'], errors='coerce'),
        pd.to_numeric(dados['entregas'], errors='coerce'),
        pd.to_numeric(dados['pedidos_fora_prazo'], errors='coerce'),
    ]).fillna(0).max())
    y_max = max_y * (1.18 if max_y > 0 else 10)

    # Plot interativo com 3 séries
    fig = go.Figure()
    # Pedidos no prazo
    fig.add_trace(go.Scatter(
        x=dados['Data'],
        y=dados['pedidos_no_prazo'],
        mode='lines+markers+text',
        name='Pedidos no Prazo',
        line=dict(color='#2266ee', width=2),
        marker=dict(size=6, color='#2266ee'),
        text=_sparse_labels(dados['pedidos_no_prazo'], n_points),
        textposition='top center',
        textfont=dict(size=11, color='#2266ee'),
        cliponaxis=False
    ))
    # Entregas
    fig.add_trace(go.Scatter(
        x=dados['Data'],
        y=dados['entregas'],
        mode='lines+markers+text',
        name='Entregas',
        line=dict(color='#23B26D', width=2),
        marker=dict(size=6, color='#23B26D'),
        text=_sparse_labels(dados['entregas'], n_points),
        textposition='bottom center',
        textfont=dict(size=11, color='#23B26D'),
        cliponaxis=False
    ))
    # Pedidos fora do prazo
    fig.add_trace(go.Scatter(
        x=dados['Data'],
        y=dados['pedidos_fora_prazo'],
        mode='lines+markers+text',
        name='Pedidos fora do Prazo',
        line=dict(color='#f65054', width=2, dash='dash'),
        marker=dict(size=6, color='#f65054'),
        text=_sparse_labels(dados['pedidos_fora_prazo'], n_points),
        textposition='top right',
        textfont=dict(size=11, color='#f65054'),
        cliponaxis=False
    ))
    # Ajustes de layout
    fig.update_layout(
        title='',
        xaxis=dict(
            title='',
            tickformat='%d/%m',
            tickfont=dict(size=10),
            dtick=dtick_ms,
            showgrid=False
        ),
        yaxis=dict(
            title='Quantidade',
            tickfont=dict(size=10),
            range=[0, y_max],
            nticks=8,
            gridcolor='rgba(120,140,170,0.22)',
            zeroline=False
        ),
        legend=dict(orientation='h', y=-0.28, x=0.5, xanchor='center', font=dict(size=10)),
        height=620 if n_points > 20 else 480,
        margin=dict(l=18, r=18, t=35, b=95),
        hovermode='x unified',
        plot_bgcolor='#fff', paper_bgcolor='#fff'
    )
    # Container e título
    st.markdown(f"<div class='graph-container'><div class='graph-title'>Pedidos x Entregas x Pedidos Fora do Prazo ({period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')})</div><div class='graph-content'>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div></div>', unsafe_allow_html=True)
    # Cálculos para análise interpretativa
    gap = pd.to_numeric(dados['pedidos_no_prazo'], errors='coerce').fillna(0) - pd.to_numeric(dados['entregas'], errors='coerce').fillna(0)
    avg_pedidos = dados['pedidos_no_prazo'].mean()
    avg_entregas = float(pd.to_numeric(dados['entregas'], errors='coerce').fillna(0).mean())
    avg_fora = dados['pedidos_fora_prazo'].mean()
    avg_total_pedidos = float((pd.to_numeric(dados['pedidos_no_prazo'], errors='coerce').fillna(0) + pd.to_numeric(dados['pedidos_fora_prazo'], errors='coerce').fillna(0)).mean())
    pos_days = (gap > 0).sum()
    neg_days = (gap < 0).sum()
    # robustez: evita KeyError quando gap está vazio ou índice inválido
    if len(gap.dropna()) == 0:
        max_gap = 0
        min_gap = 0
        max_gap_date = "-"
        min_gap_date = "-"
    else:
        idx_max = gap.dropna().idxmax()
        idx_min = gap.dropna().idxmin()
        max_gap = float(gap.loc[idx_max]) if idx_max in gap.index else 0
        min_gap = float(gap.loc[idx_min]) if idx_min in gap.index else 0
        max_gap_date = dados.loc[idx_max, 'Data'].strftime('%d/%m') if idx_max in dados.index and pd.notna(dados.loc[idx_max, 'Data']) else "-"
        min_gap_date = dados.loc[idx_min, 'Data'].strftime('%d/%m') if idx_min in dados.index and pd.notna(dados.loc[idx_min, 'Data']) else "-"

    # Texto de análise (amplo e executável para gestão)
    pct_fora_media = (avg_fora / (avg_pedidos + avg_fora) * 100) if (avg_pedidos + avg_fora) > 0 else 0
    saldo_medio_sla = (avg_entregas - avg_pedidos)

    analise = f"""
    <ul>
      <li><b>Destaque do período:</b> no intervalo analisado, a média diária foi de <b>{avg_pedidos:.0f}</b> pedidos dentro do prazo, <b>{avg_fora:.0f}</b> pedidos fora do prazo e <b>{avg_entregas:.0f}</b> temporários entregues.</li>
      <li><b>Leitura de SLA:</b> o saldo médio entre entregas e obrigação SLA (<i>Entregas - Pedidos dentro do prazo</i>) foi de <b>{saldo_medio_sla:.0f}</b> por dia.</li>
      <li><b>Pressão por prazo:</b> o volume médio fora do prazo foi de <b>{avg_fora:.0f}</b> por dia, representando <b>{pct_fora_media:.0f}%</b> da demanda média total (<b>{avg_total_pedidos:.0f}</b>/dia).</li>
      <li><b>Pico de déficit frente à obrigação SLA:</b> em <b>{max_gap_date}</b> houve o maior backlog diário, com <b>{max_gap:.0f}</b> pedidos acima das entregas.</li>
      <li><b>Pico de superávit de entrega:</b> em <b>{min_gap_date}</b> as entregas superaram a obrigação SLA em <b>{abs(min_gap):.0f}</b>.</li>
      <li><b>Distribuição dos dias:</b> houve <b>{pos_days}</b> dias com déficit (entrega abaixo da obrigação SLA) e <b>{neg_days}</b> dias com superávit (entrega acima da obrigação SLA).</li>
    </ul>
    """
    st.markdown(f"<div class='obs-box'>{analise}</div>", unsafe_allow_html=True)

# ---- Função helper para renderizar de acordo com o nome ----
def render_tab(name):
    if name == "Visão Geral":
        render_visao_geral()
    elif name == "Análise SLA":
        render_analise_sla()
    elif name == "Diárias":
        render_diarias()
    elif name == "Histórico":
        render_historico()
    elif name == "Pesquisa Temporada":
        render_pesquisa_temporada()
    elif name == "Análise Entrega":
        # Chama a nova função de análise de entregas quando a aba correspondente é selecionada.
        render_analise_entrega()

# ---- Lógica principal de impressão e renderização ----
# Renderiza apenas a aba selecionada. A funcionalidade de impressão foi removida.
render_tab(st.session_state.current_tab)