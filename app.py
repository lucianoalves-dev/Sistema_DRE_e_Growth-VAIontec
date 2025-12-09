import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Vaiontec | CFO Dashboard", 
    layout="wide", 
    page_icon="💎",
    initial_sidebar_state="collapsed" # Sidebar escondida para focar no app
)

# --- 2. DESIGN SYSTEM (CSS TEMA LIGHT/BLUE) ---
st.markdown("""
    <style>
        /* TEMA GERAL */
        [data-testid="stAppViewContainer"] { background-color: #f4f7f6; color: #2c3e50; }
        [data-testid="stHeader"] { background-color: transparent; }
        
        /* CARDS KPI */
        .metric-container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #1f497d;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }
        .metric-label { font-size: 13px; color: #7f8c8d; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
        .metric-value { font-size: 28px; color: #1f497d; font-weight: 800; margin: 8px 0; }
        .metric-sub { font-size: 13px; font-weight: 500; }
        .sub-good { color: #27ae60; }
        .sub-bad { color: #c0392b; }
        .sub-neutral { color: #7f8c8d; }
        
        /* BOTÕES */
        .stButton>button { background-color: #1f497d; color: white; border-radius: 6px; border: none; font-weight: 600; }
        .stButton>button:hover { background-color: #15325b; color: white; }
        
        /* INPUTS E LABELS */
        .stNumberInput label { font-weight: 600; color: #1f497d; }
        
        /* ABAS */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: white; border-radius: 6px; padding: 10px 20px; font-weight: 600; color: #555; border: 1px solid #ddd;}
        .stTabs [aria-selected="true"] { background-color: #1f497d !important; color: white !important; border: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DE ESTADO (SESSION STATE) ---
# Mapeamento interno vs Nome legível para CSV
key_map = {
    'cli_ini': 'Clientes Iniciais',
    'cresc': 'Crescimento Mensal (%)',
    'churn': 'Churn Rate (%)',
    'ticket': 'Ticket Médio (R$)',
    'upsell': 'Upsell (% MRR)',
    'cogs': 'COGS Unitário (R$)',
    'comissao': 'Comissão Vendas (%)',
    'imposto': 'Simples Nacional (%)',
    'taxa': 'Taxa Meios Pagto (%)',
    'mkt': 'Budget Marketing (R$)',
    'outros': 'Despesas Fixas (R$)',
    'encargos': 'Encargos Folha (%)',
    'deprec': 'Depreciação (R$)',
    'amort': 'Amortização (R$)',
    'fin': 'Resultado Financeiro (R$)',
    'irpj': 'IRPJ Extra (%)',
    's_socio': 'Salário Sócio', 'q_socio': 'Qtd Sócios',
    's_dev': 'Salário Dev', 'q_dev': 'Qtd Devs',
    's_cs': 'Salário CS', 'q_cs': 'Qtd CS',
    's_venda': 'Salário Vendas', 'q_venda': 'Qtd Vendas'
}

defaults = {
    'cli_ini': 50, 'cresc': 0.10, 'churn': 0.03, 'ticket': 500.0, 'upsell': 0.05,
    'cogs': 30.0, 'comissao': 0.05, 'imposto': 0.06, 'taxa': 0.02,
    'mkt': 5000.0, 'outros': 3000.0, 'encargos': 0.35,
    'deprec': 400.0, 'amort': 600.0, 'fin': 0.0, 'irpj': 0.0,
    's_socio': 8000.0, 'q_socio': 2,
    's_dev': 5000.0, 'q_dev': 2,
    's_cs': 2500.0, 'q_cs': 1,
    's_venda': 3000.0, 'q_venda': 1
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- 4. FUNÇÕES AUXILIARES ---

def gerar_template_csv():
    """Gera um DataFrame com os valores atuais para servir de template"""
    data = []
    for k, v in defaults.items():
        val_atual = st.session_state[k]
        nome_legivel = key_map.get(k, k)
        data.append({'Parametro': nome_legivel, 'Valor': val_atual, 'Codigo_Interno': k})
    return pd.DataFrame(data)

def processar_upload(df_upload):
    """Lê o CSV e atualiza o Session State"""
    try:
        # Cria dicionário reverso (Nome Legivel -> Valor) e (Codigo -> Valor)
        updates = {}
        for index, row in df_upload.iterrows():
            # Tenta pegar pelo código interno primeiro, se não pelo nome
            codigo = row.get('Codigo_Interno')
            valor = row['Valor']
            if codigo and codigo in defaults:
                updates[codigo] = valor
        
        # Atualiza o estado
        for k, v in updates.items():
            st.session_state[k] = float(v)
        
        st.toast("✅ Dados atualizados com sucesso via Upload!", icon="🚀")
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")

def calcular_dre():
    s = st.session_state
    meses = list(range(1, 13))
    dados = []
    
    cli_atual = s['cli_ini']
    custo_folha_base = (s['s_socio']*s['q_socio']) + (s['s_dev']*s['q_dev']) + (s['s_cs']*s['q_cs']) + (s['s_venda']*s['q_venda'])
    nrr_rate = 1 + s['upsell'] - s['churn']

    for m in meses:
        # Growth
        novos = int(cli_atual * s['cresc'])
        perda = int(cli_atual * s['churn'])
        cli_fim = cli_atual + novos - perda
        
        # Receita
        mrr = cli_fim * s['ticket']
        expansao = mrr * s['upsell']
        rec_bruta = mrr + expansao
        
        # Custos
        imp = rec_bruta * s['imposto']
        rec_liq = rec_bruta - imp
        cogs = cli_fim * s['cogs']
        comissao = rec_bruta * s['comissao']
        taxa = rec_bruta * s['taxa']
        
        margem_cont = rec_liq - (cogs + comissao + taxa)
        mc_pct = margem_cont / rec_liq if rec_liq > 0 else 0
        
        # Fixos
        encargos = custo_folha_base * s['encargos']
        folha_total = custo_folha_base + encargos
        desp_op = folha_total + s['mkt'] + s['outros']
        
        # Resultados
        ebitda = margem_cont - desp_op
        ebit = ebitda - (s['deprec'] + s['amort'])
        lair = ebit + s['fin']
        irpj = lair * s['irpj'] if lair > 0 else 0
        lucro = lair - irpj
        
        # KPIs
        fator_r = folha_total / rec_bruta if rec_bruta > 0 else 0
        
        fixos_totais_pe = desp_op + s['deprec'] + s['amort'] - s['fin']
        mb_pct = margem_cont / rec_bruta if rec_bruta > 0 else 0
        pe_val = fixos_totais_pe / mb_pct if mb_pct > 0 else 0
        
        cac = (s['mkt'] + comissao) / novos if novos > 0 else 0
        ltv = (s['ticket'] * mc_pct) / s['churn'] if s['churn'] > 0 else 0
        payback = cac / (s['ticket'] * mc_pct) if (s['ticket'] * mc_pct) > 0 else 0
        
        dados.append({
            'Mês': m,
            'Clientes': cli_fim,
            'Novos': novos,
            'Churn': perda,
            'MRR': mrr,
            'Receita Bruta': rec_bruta,
            'Receita Líquida': rec_liq,
            'COGS': cogs,
            'Margem Contrib.': margem_cont,
            'EBITDA': ebitda,
            'Lucro Líquido': lucro,
            'Ponto Equilíbrio': pe_val,
            'Fator R': fator_r,
            'CAC': cac,
            'LTV': ltv,
            'Payback': payback,
            'NRR Estimado': nrr_rate,
            'Folha Total': folha_total
        })
        cli_atual = cli_fim
        
    return pd.DataFrame(dados)

# --- 5. INTERFACE DO USUÁRIO ---

# Header
c1, c2 = st.columns([0.5, 5])
with c1: st.markdown("# 💎")
with c2: 
    st.markdown("## Vaiontec | Sistema de Gestão Financeira")
    st.caption("Environment: Production | Mode: Executive View")

# Menu de Abas
tab_dash, tab_dre, tab_input, tab_gloss = st.tabs([
    "📊 Dashboard", 
    "📑 Relatório DRE", 
    "⚙️ Atualizar Dados (Manual/Upload)", 
    "📚 Glossário"
])

# --- ABA 1: DASHBOARD ---
df = calcular_dre()
f = df.iloc[-1] # Dados do mês 12

with tab_dash:
    def card(label, value, sub, color="neutral", is_money=True):
        fmt_val = f"R$ {value:,.2f}" if is_money else f"{value}"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{fmt_val}</div>
            <div class="metric-sub sub-{color}">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    # LINHA 1: KPIs Principais (Solicitados: Faturamento, Clientes)
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        # Faturamento (Receita Bruta)
        card("Faturamento Mensal (Bruto)", f['Receita Bruta'], f"Projeção Mês 12", "neutral")
    with c2:
        # Quantidade de Clientes
        card("Base de Clientes Ativos", int(f['Clientes']), f"Novos: +{int(f['Novos'])} este mês", "neutral", is_money=False)
    with c3:
        # Lucro Líquido
        cor = "good" if f['Lucro Líquido'] > 0 else "bad"
        card("Lucro Líquido", f['Lucro Líquido'], f"Margem Líq: {(f['Lucro Líquido']/f['Receita Bruta'])*100:.1f}%", cor)
    with c4:
        # Ponto de Equilíbrio
        card("Ponto de Equilíbrio (Meta)", f['Ponto Equilíbrio'], "Necessário para zerar custos", "neutral")

    # LINHA 2: Eficiência & Growth
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("LTV (Valor Vitalício)", f['LTV'], "Lucro por cliente")
    with c2: card("CAC (Custo Aquisição)", f['CAC'], "Mkt + Comissões")
    with c3: card("Payback (Retorno)", f"{f['Payback']:.1f} Meses", "Meta < 12 meses", "good" if f['Payback']<12 else "bad", is_money=False)
    with c4: card("Fator R (Imposto)", f"{f['Fator R']*100:.1f}%", "Anexo III (>28%)" if f['Fator R']>=0.28 else "Anexo V (Alerta)", "good" if f['Fator R']>=0.28 else "bad", is_money=False)

    st.markdown("---")
    
    # GRÁFICOS
    g1, g2 = st.columns([2, 1])
    with g1:
        st.subheader("Evolução: Faturamento vs Ponto de Equilíbrio")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Mês'], y=df['Receita Bruta'], name='Faturamento', marker_color='#1f497d'))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['Ponto Equilíbrio'], name='Ponto de Equilíbrio', line=dict(color='#e74c3c', width=3, dash='dot')))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['Lucro Líquido'], name='Lucro/Prejuízo', line=dict(color='#2ecc71', width=3)))
        fig.update_layout(template="plotly_white", height=400, margin=dict(t=30), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        
    with g2:
        st.subheader("Unit Economics")
        fig_u = go.Figure()
        fig_u.add_trace(go.Bar(name='CAC', x=df['Mês'], y=df['CAC'], marker_color='#e67e22'))
        fig_u.add_trace(go.Bar(name='LTV', x=df['Mês'], y=df['LTV'], marker_color='#2980b9'))
        fig_u.update_layout(barmode='group', template="plotly_white", height=400, margin=dict(t=30), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_u, use_container_width=True)

# --- ABA 2: DRE ---
with tab_dre:
    st.markdown("### 📑 Detalhamento Financeiro")
    
    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar DRE Completo (.csv)", data=csv, file_name="Vaiontec_DRE_Full.csv", mime="text/csv")
    
    # Visualização
    df_show = df.copy()
    format_money = lambda x: f"R$ {x:,.2f}"
    format_pct = lambda x: f"{x*100:.1f}%"
    
    cols_money = ['MRR', 'Receita Bruta', 'Receita Líquida', 'COGS', 'Margem Contrib.', 'EBITDA', 'Lucro Líquido', 'Ponto Equilíbrio', 'CAC', 'LTV']
    for c in cols_money: df_show[c] = df_show[c].apply(format_money)
    
    df_show['Fator R'] = df_show['Fator R'].apply(format_pct)
    df_show['NRR Estimado'] = df_show['NRR Estimado'].apply(format_pct)
    
    st.dataframe(df_show, use_container_width=True, height=600)

# --- ABA 3: INPUTS (ATUALIZAÇÃO) ---
with tab_input:
    st.markdown("### ⚙️ Centro de Atualização de Dados")
    
    # SELETOR DE MODO
    modo = st.radio("Como deseja atualizar?", ["📝 Edição Manual", "📂 Upload de Planilha Padrão"], horizontal=True)
    st.markdown("---")

    if modo == "📂 Upload de Planilha Padrão":
        c_down, c_up = st.columns(2)
        with c_down:
            st.info("Passo 1: Baixe o modelo atual com os metadados corretos.")
            df_template = gerar_template_csv()
            csv_template = df_template.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Modelo de Planilha (.csv)",
                data=csv_template,
                file_name="template_vaiontec.csv",
                mime="text/csv",
            )
            st.caption("O arquivo contém as colunas: Parametro, Valor e Codigo_Interno.")
            
        with c_up:
            st.info("Passo 2: Faça o upload do arquivo preenchido.")
            uploaded_file = st.file_uploader("Carregar arquivo .csv", type=['csv'])
            if uploaded_file is not None:
                df_up = pd.read_csv(uploaded_file)
                processar_upload(df_up)
                
    else:
        # MODO MANUAL COM METADADOS
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("1. Vendas & Growth")
            st.session_state['cli_ini'] = st.number_input("Clientes Iniciais", value=st.session_state['cli_ini'], help="Número total de clientes ativos no início do período.")
            st.session_state['cresc'] = st.number_input("Crescimento Mensal (%)", value=st.session_state['cresc'], format="%.2f", help="Taxa percentual de novos clientes adquiridos sobre a base.")
            st.session_state['churn'] = st.number_input("Churn Rate (%)", value=st.session_state['churn'], format="%.2f", help="Percentual de cancelamento mensal da base.")
            st.session_state['ticket'] = st.number_input("Ticket Médio (R$)", value=st.session_state['ticket'], help="Valor médio da assinatura mensal cobrada.")
            st.session_state['upsell'] = st.number_input("Upsell (% da Rec.)", value=st.session_state['upsell'], format="%.2f", help="Receita adicional gerada na base atual (Expansão).")

            st.subheader("2. Custos Variáveis (COGS)")
            st.session_state['cogs'] = st.number_input("COGS Unitário (R$)", value=st.session_state['cogs'], help="Custo direto de infraestrutura/licença POR cliente.")
            st.session_state['comissao'] = st.number_input("Comissão Vendas (%)", value=st.session_state['comissao'], format="%.2f", help="% paga a parceiros sobre o Faturamento Bruto.")
            st.session_state['taxa'] = st.number_input("Taxa Meios Pagto (%)", value=st.session_state['taxa'], format="%.2f", help="Taxa de cartão/boleto sobre o Faturamento Bruto.")
            st.session_state['imposto'] = st.number_input("Simples Nacional (%)", value=st.session_state['imposto'], format="%.2f", help="Alíquota efetiva do imposto sobre a nota fiscal.")

        with col_b:
            st.subheader("3. Despesas Fixas & Pessoal")
            st.session_state['mkt'] = st.number_input("Marketing (R$)", value=st.session_state['mkt'], help="Budget fixo mensal para aquisição de clientes (Ads, Eventos).")
            st.session_state['outros'] = st.number_input("Outros Fixos (R$)", value=st.session_state['outros'], help="Aluguel, Softwares internos, Contabilidade, etc.")
            
            with st.expander("Detalhamento da Folha (Salários)", expanded=True):
                c_sal, c_qtd = st.columns([2,1])
                with c_sal:
                    st.session_state['s_socio'] = st.number_input("Salário Sócio", st.session_state['s_socio'], help="Pró-labore individual")
                    st.session_state['s_dev'] = st.number_input("Salário Dev", st.session_state['s_dev'])
                    st.session_state['s_cs'] = st.number_input("Salário CS", st.session_state['s_cs'])
                    st.session_state['s_venda'] = st.number_input("Salário Vendas", st.session_state['s_venda'])
                with c_qtd:
                    st.session_state['q_socio'] = st.number_input("Qtd", st.session_state['q_socio'], key="k_q_socio")
                    st.session_state['q_dev'] = st.number_input("Qtd", st.session_state['q_dev'], key="k_q_dev")
                    st.session_state['q_cs'] = st.number_input("Qtd", st.session_state['q_cs'], key="k_q_cs")
                    st.session_state['q_venda'] = st.number_input("Qtd", st.session_state['q_venda'], key="k_q_venda")
            
            st.session_state['encargos'] = st.number_input("Encargos (%)", value=st.session_state['encargos'], format="%.2f", help="% sobre a folha (FGTS, Férias, 13º). Simples Nacional geralmente ~35%.")

            st.subheader("4. Contábil")
            st.session_state['deprec'] = st.number_input("Depreciação (R$)", st.session_state['deprec'], help="Perda de valor de equipamentos.")
            st.session_state['amort'] = st.number_input("Amortização (R$)", st.session_state['amort'], help="Perda de valor de intangíveis (Software).")
            st.session_state['fin'] = st.number_input("Resultado Fin. (R$)", st.session_state['fin'], help="Rendimentos (+) ou Juros Pagos (-).")

# --- ABA 4: GLOSSÁRIO ---
with tab_gloss:
    st.markdown("### 📚 Dicionário de Indicadores")
    
    with st.expander("💰 Faturamento e Receita", expanded=True):
        st.markdown("""
        * **Faturamento Bruto:** Valor total das notas fiscais emitidas no mês. (Clientes x Ticket + Upsell).
        * **MRR (Monthly Recurring Revenue):** Receita que se repete todo mês.
        * **NRR (Net Revenue Retention):** Capacidade de retenção de receita. Se > 100%, sua empresa cresce organicamente.
        """)
        
    with st.expander("📉 Custos e Despesas", expanded=True):
        st.markdown("""
        * **COGS (Cost of Goods Sold):** Custo para entregar o serviço. Se não tem cliente, esse custo é zero. (Ex: Cloud AWS).
        * **CAC (Custo Aquisição):** Soma de Marketing e Comissões dividida pelos novos clientes.
        * **Fator R:** Razão (Folha / Faturamento). Se ficar abaixo de 28%, o imposto sobe muito. Mantenha acima!
        """)
        
    with st.expander("📊 Resultado", expanded=True):
        st.markdown("""
        * **Ponto de Equilíbrio (Break-Even):** Faturamento necessário para cobrir TODOS os custos e zerar o lucro.
        * **EBITDA:** Lucro operacional (antes de depreciação e juros). Mede a saúde da operação.
        * **Payback:** Tempo em meses para recuperar o dinheiro gasto para trazer um cliente.
        """)
