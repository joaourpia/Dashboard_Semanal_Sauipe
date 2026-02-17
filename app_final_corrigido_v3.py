import streamlit as st
import re
# A importação de components era utilizada apenas para acionar o print via JavaScript e foi removida.
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import datetime as dt
import numpy as np

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
    <h1>Dashboard janeiro 2026</h1>
    <p>Relatório de Contratação de Temporários - Mendes RH</p>
  </div>
  <div class="header-right">
    <p class="periodo-label">Período</p>
    <p class="periodo-value">janeiro/2026</p>
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
        st.markdown('<div class="graph-container"><div class="graph-title">Desempenho SLA - janeiro-26</div><div class="graph-content">', unsafe_allow_html=True)
        no_prazo = sla['No_prazo'].iloc[0]
        fora_prazo = sla['Fora_prazo'].iloc[0]
        fig_pie = px.pie(values=[no_prazo, fora_prazo], names=["No Prazo", "Fora do Prazo"], hole=0.40, color_discrete_sequence=['#2266ee','#f65054'])
        fig_pie.update_traces(textinfo="percent", textposition="inside", textfont=dict(size=14, color="#ffffff"), marker=dict(line=dict(color="#ffffff", width=2)), pull=[0.02,0.02])
        fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10,color="#1a1a1a")), margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=180)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div></div>', unsafe_allow_html=True)
    with col_bar:
        st.markdown('<div class="graph-container"><div class="graph-title">Diárias - janeiro-26</div><div class="graph-content">', unsafe_allow_html=True)
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
    <b>Observações Importantes - janeiro-26</b>
    <ul><li>SLA: 73,1% no mês de janeiro/26, com queda vs. meses anteriores (detalhes na aba SLA). Volume: diárias entregues 15,65% abaixo do solicitado (detalhes na aba Diárias).</li></ul>
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
    <li><b>STHS Complicadas:</b> Demanda de 10 camareiras aos sábados e domingos com baixíssima aderência, representando 27 entregas do total de 68 faltantes.</li><br>
    <li><b>Valor diária:</b> Ocorreram diversas desistências onde a maioria dos motivos alegados é o valor da diária e em muitos casos evidente falta de compromisso. Fizemos uma pesquisa com uma amostra dos desistentes, onde os principais motivos alegados foram: "Tempo longo de espera para efetivação e não acreditar na promessa (69,2%)" e "não queria ser efetivado (30,8%)"</li><br>
    <li><b>Baixa Conversão:</b> Absenteísmo de 70% nas entrevistas/treinamentos (convocação de 35/dia para 30% de presença). Baixa efetividade do SINE e indisponibilidade da base de temporários de Julho.</li><br>
    <li><b>Perfil:</b> Resistência do mercado local a contratos formais/efetivação em detrimento de modelos informais.</li><br>
    </div>""", unsafe_allow_html=True)

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
    st.markdown(f"""<div class="diarias-card-sucesso"><b>Desempenho abaixo</b><br> No mês de janeiro-26, não superamos as expectativas ao entregar <b>{entregues} diárias</b>, quando foram solicitadas <b>{solicitadas}</b>, resultando em uma diferença negativa de <b style='color:#12bb26;'>{saldo} diárias</b>.<br> Taxa de atendimento: <b>{taxa:.2f}%</b>.</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="diarias-motivos"><div class="diarias-motivos-title">Motivos para Diárias Abaixo do Solicitado</div><ol style="margin-top:0.1em;margin-bottom:0.1em;"><li>A partir da segunda metade de janeiro-26, tivemos diversos problemas, como: baixa procura de trabalho, desistências de contratações com menos de 5 dias em área e faltas ao trabalho, impactando diretamente na quantidade de diárias entregues.</li><li>Em relação às faltas, tivemos nesse período um absenteísmo de 30%.</li></ol></div>""", unsafe_allow_html=True)

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
    st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Prazos de Entregas (janeiro-26)</div></div>""", unsafe_allow_html=True)
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
    st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Diárias Entregues (Janeiro-26)</div></div>""", unsafe_allow_html=True)
    meses2 = ent_hist['Mês']
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=meses2, y=ent_hist['Solicitadas'], name='Solicitadas', marker_color='#FFA500', text=ent_hist['Solicitadas'], textposition='outside', textfont=dict(size=11,color="#222")))
    fig2.add_trace(go.Bar(x=meses2, y=ent_hist['Entregues'], name='Entregues', marker_color='#23B26D', text=ent_hist['Entregues'], textposition='outside', textfont=dict(size=11,color="#222")))
    fig2.add_trace(go.Scatter(x=meses2, y=ent_hist['Taxa_%'], mode='lines+markers+text', name='Taxa (%)', line=dict(color='#2266ee', width=2, shape='spline'), marker=dict(size=8,color='#2266ee'), text=[f"{tx:.2f}%" for tx in ent_hist['Taxa_%']], textposition="top center", textfont=dict(size=14,color="#fff")))
    fig2.update_layout(barmode='group', xaxis=dict(tickfont=dict(size=13)), yaxis=dict(title='', tickfont=dict(size=12), showgrid=True), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=13)), height=540, margin=dict(l=20,r=20,t=120,b=38), plot_bgcolor='#fff', paper_bgcolor='#fff')
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})


def _excel_serial_to_date(v):
    try:
        num = float(v)
        if num <= 0:
            return None
        return (dt.datetime(1899, 12, 30) + dt.timedelta(days=num)).date()
    except Exception:
        return None

def _parse_header_date(v, month_ref=None, year_ref=None, year_hint=None):
    if v is None:
        return None
    if isinstance(v, (dt.datetime, dt.date, pd.Timestamp)):
        d = pd.to_datetime(v, errors="coerce")
        if pd.isna(d):
            return None
        return d.date()
    if isinstance(v, (int, float)):
        return _excel_serial_to_date(v)
    s = str(v).strip()
    if not s:
        return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$", s)
    if m:
        dd = int(m.group(1)); mm = int(m.group(2)); yy = m.group(3)
        if yy:
            yy = int(yy)
            if yy < 100: yy += 2000
        else:
            yy = year_hint or dt.date.today().year
        try:
            return dt.date(yy, mm, dd)
        except Exception:
            return None
    return None

def _extract_subtotal_and_dates(hist_df: pd.DataFrame, sheet_name='HISTOGRAMA', month_ref=None, year_ref=None):
    col0 = hist_df.iloc[:, 0].astype(str).str.strip().str.upper()
    idx_sub = col0[col0 == "SUBTOTAL (FILTRO)"].index
    if len(idx_sub) == 0:
        idx_sub = col0[col0.str.contains("TOTAL SOLICITADO|SUBTOTAL", na=False)].index
        if len(idx_sub) == 0:
            raise ValueError(f"{sheet_name}: linha 'SUBTOTAL (FILTRO)' não encontrada.")
    sub_row_idx = int(idx_sub[0])

    year_hint = None
    for r in range(min(8, len(hist_df))):
        row_txt = " ".join(hist_df.iloc[r, :min(10, hist_df.shape[1])].astype(str).tolist())
        m = re.search(r"(20\d{2})", row_txt)
        if m:
            year_hint = int(m.group(1))
            break
    if year_hint is None:
        year_hint = dt.date.today().year

    best = None
    for hr in range(0, min(10, hist_df.shape[0])):
        cols, dates = [], []
        for c in range(3, hist_df.shape[1]):
            d = _parse_header_date(hist_df.iat[hr, c], month_ref=month_ref, year_ref=year_ref, year_hint=year_hint)
            if d is not None:
                cols.append(c); dates.append(d)
        if cols and (best is None or len(cols) > best[0]):
            best = (len(cols), hr, cols, dates)

    if best is None:
        raise ValueError(f"{sheet_name}: não encontrei colunas de datas no cabeçalho (linhas 1-10).")

    _, _, cols, dates = best
    vals = pd.to_numeric(hist_df.iloc[sub_row_idx, cols], errors="coerce").fillna(0).astype(float).tolist()
    datas = pd.to_datetime(dates).normalize()

    n = min(len(datas), len(vals))
    datas = pd.DatetimeIndex(datas[:n]); vals = vals[:n]
    order = sorted(range(n), key=lambda i: datas[i])
    datas = pd.DatetimeIndex([datas[i] for i in order])
    vals = [vals[i] for i in order]
    return datas, vals


# --- Nova função: Análise Entrega ---

def _infer_month_year_from_context(df_hist, periodo_texto=None):
    meses = {
        "janeiro":1,"fevereiro":2,"março":3,"marco":3,"abril":4,"maio":5,"junho":6,
        "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12
    }
    if periodo_texto:
        p = str(periodo_texto).strip().lower()
        m = re.search(r"(20\d{2})", p)
        ano = int(m.group(1)) if m else None
        mm = None
        for nome, num in meses.items():
            if nome in p:
                mm = num
                break
        if mm is None:
            m2 = re.search(r"\b(\d{1,2})\s*/\s*(20\d{2})\b", p)
            if m2:
                mm = int(m2.group(1)); ano = int(m2.group(2))
        if mm and ano:
            return mm, ano

    try:
        for r in range(min(8, df_hist.shape[0])):
            for c in range(3, df_hist.shape[1]):
                v = str(df_hist.iat[r, c]).strip()
                m = re.match(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$", v)
                if m:
                    mm = int(m.group(2))
                    yy = m.group(3)
                    if yy:
                        yy = int(yy)
                        if yy < 100: yy += 2000
                    else:
                        yy = None
                    if 1 <= mm <= 12:
                        return mm, (yy if yy else dt.date.today().year)
    except Exception:
        pass

    today = dt.date.today()
    return today.month, today.year


def render_analise_entrega():
    """
    Renderiza a aba de Análise de Entregas com comparação diária entre pedidos no prazo,
    entregas realizadas e pedidos fora do prazo. Os dados são lidos de planilhas Excel
    fornecidas pelo usuário. A função também calcula métricas de gap e exibe uma análise
    interpretativa abaixo do gráfico.
    """
    import datetime
    # Carregar dados de entregas (Total entregue por dia). Procura inicialmente em 'dados/ENTREGAS_DIA.xlsx'.
    try:
        entregas_df = pd.read_excel('dados/ENTREGAS_DIA.xlsx')
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
            entregas_df['Data'] = pd.to_datetime(entregas_df['Data'], errors='coerce').dt.normalize()
        except Exception:
            pass
    # Renomear a coluna de valor para 'entregas'
    entregas_df = entregas_df.rename(columns={col: 'entregas' for col in entregas_df.columns if 'Total' in col or 'entregue' in col})

    # Carregar dados de pedidos (dentro e fora do prazo)
    try:
        pedidos_xls = pd.ExcelFile('dados/PEDIDOS_DIA.xlsx')
    except Exception:
        # Caso não exista na pasta 'dados', tenta utilizar o arquivo original enviado
        try:
            pedidos_xls = pd.ExcelFile('5d357de9-4d77-42ad-8608-c81bc592a7f7.xlsx')
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
    
    # Garantir mês/ano de referência para parser de datas
    try:
        periodo_txt_ref = periodo if 'periodo' in locals() else (periodo_label if 'periodo_label' in locals() else None)
    except Exception:
        periodo_txt_ref = None
    mes_numero, ano_numero = _infer_month_year_from_context(hist, periodo_txt_ref)

# Extrair valores dinâmicos de pedidos no prazo e fora do prazo
    try:
        datas_no, values_no = _extract_subtotal_and_dates(
            hist, sheet_name='HISTOGRAMA', month_ref=mes_numero, year_ref=ano_numero
        )
        datas_out, values_out = _extract_subtotal_and_dates(
            ex, sheet_name='HISTOGRAMA_EXCEDENTE', month_ref=mes_numero, year_ref=ano_numero
        )
    except Exception as e:
        st.error(f"Falha ao extrair subtotais do histograma: {e}")
        return

    df_no = pd.DataFrame({'Data': datas_no, 'pedidos_no_prazo': values_no})
    df_out = pd.DataFrame({'Data': datas_out, 'pedidos_fora_prazo': values_out})
    pedidos_df = pd.merge(df_no, df_out, on='Data', how='outer').sort_values('Data')
    pedidos_df['pedidos_no_prazo'] = pd.to_numeric(pedidos_df['pedidos_no_prazo'], errors='coerce').fillna(0)
    pedidos_df['pedidos_fora_prazo'] = pd.to_numeric(pedidos_df['pedidos_fora_prazo'], errors='coerce').fillna(0)
    # Mesclar com entregas
    pedidos_df['Data'] = pd.to_datetime(pedidos_df['Data'], errors='coerce').dt.normalize()
    dados = pd.merge(pedidos_df, entregas_df, on='Data', how='left').sort_values('Data')
    dados['entregas'] = pd.to_numeric(dados['entregas'], errors='coerce').fillna(0.0)
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
        text=dados['pedidos_no_prazo'],
        textposition='top center',
        textfont=dict(size=10, color='#2266ee')
    ))
    # Entregas
    fig.add_trace(go.Scatter(
        x=dados['Data'],
        y=dados['entregas'],
        mode='lines+markers+text',
        name='Entregas',
        line=dict(color='#23B26D', width=2),
        marker=dict(size=6, color='#23B26D'),
        text=dados['entregas'],
        textposition='top center',
        textfont=dict(size=10, color='#23B26D')
    ))
    # Pedidos fora do prazo
    fig.add_trace(go.Scatter(
        x=dados['Data'],
        y=dados['pedidos_fora_prazo'],
        mode='lines+markers+text',
        name='Pedidos fora do Prazo',
        line=dict(color='#f65054', width=2, dash='dash'),
        marker=dict(size=6, color='#f65054'),
        text=dados['pedidos_fora_prazo'],
        textposition='top center',
        textfont=dict(size=10, color='#f65054')
    ))
    # Ajustes de layout
    fig.update_layout(
        title='',
        xaxis=dict(title='', tickformat='%d/%m', tickfont=dict(size=10)),
        yaxis=dict(title='Quantidade', tickfont=dict(size=10)),
        legend=dict(orientation='h', y=-0.25, x=0.5, xanchor='center', font=dict(size=10)),
        height=360,
        margin=dict(l=12, r=12, t=35, b=80),
        plot_bgcolor='#fff', paper_bgcolor='#fff'
    )
    # Container e título
    periodo_txt = f"{dados['Data'].min().strftime('%d/%m/%Y')} a {dados['Data'].max().strftime('%d/%m/%Y')}" if not dados.empty else "Sem período"
    st.markdown(f'<div class="graph-container"><div class="graph-title">Pedidos x Entregas x Pedidos Fora do Prazo ({periodo_txt})</div><div class="graph-content">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div></div>', unsafe_allow_html=True)
    # Cálculos para análise interpretativa
    gap = dados['pedidos_no_prazo'] - dados['entregas']
    avg_pedidos = dados['pedidos_no_prazo'].mean()
    avg_entregas = dados['entregas'].mean()
    avg_fora = dados['pedidos_fora_prazo'].mean()
    pos_days = (gap > 0).sum()
    neg_days = (gap < 0).sum()
    max_gap = gap.max(); max_gap_date = dados.loc[gap.idxmax(), 'Data'].strftime('%d/%m')
    min_gap = gap.min(); min_gap_date = dados.loc[gap.idxmin(), 'Data'].strftime('%d/%m')
    # Texto de análise manual construído a partir das métricas calculadas
    analise = f"""
    <ul>
      <li>Em média, foram solicitados <b>{avg_pedidos:.0f}</b> pedidos por dia dentro do prazo e entregues <b>{avg_entregas:.0f}</b> unidades, gerando um gap médio de <b>{(avg_pedidos-avg_entregas):.0f}</b> pedidos por dia.</li>
      <li>O número de pedidos dentro do prazo superou o total entregue em <b>{pos_days}</b> de 31 dias, indicando backlog frequente. O maior backlog ocorreu em <b>{max_gap_date}</b>, com <b>{max_gap:.0f}</b> pedidos a mais que entregas.</li>
      <li>Em <b>{neg_days}</b> dias, as entregas superaram os pedidos no prazo, sugerindo compensação de atrasos. A maior antecipação ocorreu em <b>{min_gap_date}</b>, com <b>{abs(min_gap):.0f}</b> entregas a mais que pedidos.</li>
      <li>O volume médio de pedidos fora do prazo foi de <b>{avg_fora:.0f}</b> unidades diárias, demonstrando que cerca de {(avg_fora/(avg_pedidos+avg_fora))*100:.0f}% da demanda total é solicitada após o prazo.</li>
    </ul>
    """
    
    # Exibe diretamente a análise calculada localmente. Este texto usa as métricas
    # extraídas do conjunto de dados para gerar uma interpretação automatizada sem
    # recorrer a serviços de IA externos. Se você desejar integrar a API
    # generativa futuramente, mantenha o bloco abaixo como base para o prompt
    # e substitua o markdown pelo resultado da IA.
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