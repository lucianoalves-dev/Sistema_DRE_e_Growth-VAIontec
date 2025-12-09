import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Vaiontec | CFO Dashboard", 
    layout="wide", 
    page_icon="💎",
    initial_sidebar_state="expanded"
)

# --- 2. DESIGN SYSTEM (CSS FORÇADO PARA TEMA LIGHT/BLUE) ---
st.markdown("""
    <style>
        /* FORÇAR TEMA CLARO */
        [data-testid="stAppViewContainer"] {
            background-color: #f4f7f6; /* Cinza muito suave */
            color: #2c3e50;
        }
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
        }
        
        /* ESTILO DOS CARDS (KPIs) */
        .metric-container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #1f497d; /* Azul Vaiontec */
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .metric-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        .metric-label {
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        .metric-value {
            font-size: 26px;
            color: #1f497d;
            font-weight: 800;
            margin-top: 5px;
        }
        .metric-sub {
            font-size: 13px;
            margin-top: 5px;
            font-weight: 500;
        }
        .sub-good { color: #27ae60; }
        .sub-bad { color: #c0392b; }
        
        /* BOTÕES PERSONALIZADOS */
        .stButton>button {
            background-color: #1f497d;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #15325b;
            color: white;
        }
        
        /* ABAS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #ffffff;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            padding: 10px 20px;
            font-weight: 600;
            color: #555;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1f497d !important;
            color: white !important;
        }
        
        /* TITULOS */
        h1, h2, h3 {
            color: #1f497d !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DE ESTADO (SESSION STATE) ---
# Isso garante que os dados não sumam ao trocar de aba
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

# --- 4. MOTOR DE CÁLCULO ---
def calcular_dre():
    s = st.session_state
    meses = list(range(1, 13))
    dados = []
    
    cli_atual = s['cli_ini']
    custo_folha_base = (s['s_socio']*s['q_socio']) + (s['s_dev']*s['q_dev']) + (s['s_cs']*s['q_cs']) + (s['s_venda']*s['q_venda'])
    
    nrr_rate = 1 + s['upsell'] - s['churn'] # Simplificação para projeção

    for m in meses:
        # Growth
        novos = int(cli_atual * s['cresc'])
        perda = int(cli_atual * s['churn'])
        cli_fim = cli_atual + novos - perda
        
        # Receita
        mrr = cli_fim * s['ticket']
        expansao = mrr * s['upsell']
        rec_bruta = mrr + expansao
        
        # Custos Variáveis
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

# Header com Logo e Título
c1, c2 = st.columns([0.8, 4])
with c1:
    # Placeholder para logo (usando emoji grande)
    st.markdown("<div style='font-size: 40px; text-align: center;'>💎</div>", unsafe_allow_html=True)
with c2:
    st.title("Vaiontec | Sistema Integrado de Gestão")
    st.markdown("Painel de Controle Financeiro & Growth (SaaS)")

# Menu de Abas
tab_dash, tab_dre, tab_input, tab_gloss = st.tabs([
    "📊 Dashboard Executivo", 
    "📑 Relatório DRE", 
    "⚙️ Atualizar Dados (Inputs)", 
    "📚 Glossário & Educação"
])

# --- ABA 1: DASHBOARD ---
df = calcular_dre()
f = df.iloc[-1] # Dados do mês 12

with tab_dash:
    # Função Helper para Cards HTML
    def card(label, value, sub, is_good=True, is_money=True):
        fmt_val = f"R$ {value:,.2f}" if is_money else f"{value}"
        color_class = "sub-good" if is_good else "sub-bad"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{fmt_val}</div>
            <div class="metric-sub {color_class}">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    # LINHA 1: GERAL
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("MRR (Recorrente Mensal)", f['MRR'], f"ARR: R$ {f['MRR']*12:,.0f}")
    with c2: card("EBITDA (Caixa Operacional)", f['EBITDA'], f"Margem: {(f['EBITDA']/f['Receita Líquida'])*100:.1f}%")
    with c3: card("Lucro Líquido", f['Lucro Líquido'], "Resultado Final do Mês", is_good=f['Lucro Líquido']>0)
    with c4: card("Caixa Mínimo (Break-Even)", f['Ponto Equilíbrio'], "Para zerar prejuízo")

    # LINHA 2: GROWTH
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("LTV (Valor Vitalício)", f['LTV'], "Lucro por cliente na vida")
    with c2: card("CAC (Custo Aquisição)", f['CAC'], "Mkt + Comissões")
    with c3: card("Payback (Retorno)", f"{f['Payback']:.1f} Meses", "Tempo para recuperar CAC", is_good=f['Payback']<12, is_money=False)
    with c4: card("NRR (Retenção Líquida)", f"{f['NRR Estimado']*100:.1f}%", "Meta > 100%", is_money=False)

    st.markdown("---")

    # GRÁFICOS
    g1, g2 = st.columns([2, 1])
    with g1:
        st.subheader("Evolução Financeira: Receita vs EBITDA vs Ponto de Equilíbrio")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Mês'], y=df['Receita Bruta'], name='Receita Bruta', marker_color='#1f497d'))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['EBITDA'], name='EBITDA', line=dict(color='#2ecc71', width=3)))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['Ponto Equilíbrio'], name='Ponto Equilíbrio', line=dict(color='#e74c3c', dash='dot')))
        fig.update_layout(template="plotly_white", height=400, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    
    with g2:
        st.subheader("Monitoramento Fator R")
        val_fr = f['Fator R']*100
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number", value = val_fr,
            title = {'text': "Meta > 28% (Anexo III)"},
            gauge = {
                'axis': {'range': [0, 50]}, 'bar': {'color': "#1f497d"},
                'steps': [{'range': [0, 28], 'color': "#ffcccc"}, {'range': [28, 50], 'color': "#ccffcc"}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 28}
            }
        ))
        fig_g.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_g, use_container_width=True)

# --- ABA 2: DRE ---
with tab_dre:
    st.markdown("### 📑 Tabela Financeira Detalhada")
    
    # Botão Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Planilha (Excel/CSV)", data=csv, file_name="Vaiontec_DRE.csv", mime="text/csv")
    
    # Formatação Visual
    df_show = df.copy()
    cols_mon = ['MRR', 'Receita Bruta', 'Receita Líquida', 'COGS', 'Margem Contrib.', 'EBITDA', 'Lucro Líquido', 'Ponto Equilíbrio', 'CAC', 'LTV']
    for c in cols_mon: df_show[c] = df_show[c].apply(lambda x: f"R$ {x:,.2f}")
    
    df_show['Fator R'] = df_show['Fator R'].apply(lambda x: f"{x*100:.1f}%")
    df_show['NRR Estimado'] = df_show['NRR Estimado'].apply(lambda x: f"{x*100:.1f}%")
    df_show['Payback'] = df_show['Payback'].apply(lambda x: f"{x:.1f} meses")
    
    st.dataframe(df_show, use_container_width=True, height=600)

# --- ABA 3: INPUTS (SETTINGS) ---
with tab_input:
    st.markdown("### ⚙️ Atualização de Premissas e Dados")
    st.info("Altere os valores abaixo. O Dashboard e o DRE serão recalculados automaticamente.")
    
    c_growth, c_custos, c_folha = st.columns(3)
    
    with c_growth:
        st.markdown("#### 🚀 Growth & Receita")
        st.session_state['cli_ini'] = st.number_input("Clientes Iniciais", value=st.session_state['cli_ini'])
        st.session_state['cresc'] = st.number_input("Crescimento Mensal (%)", value=st.session_state['cresc'], format="%.2f")
        st.session_state['churn'] = st.number_input("Churn Rate (%)", value=st.session_state['churn'], format="%.2f")
        st.session_state['ticket'] = st.number_input("Ticket Médio (R$)", value=st.session_state['ticket'])
        st.session_state['upsell'] = st.number_input("Upsell (% MRR)", value=st.session_state['upsell'], format="%.2f")

    with c_custos:
        st.markdown("#### 💸 Custos & Impostos")
        st.session_state['cogs'] = st.number_input("COGS Unitário (Infra)", value=st.session_state['cogs'])
        st.session_state['comissao'] = st.number_input("Comissão Vendas (%)", value=st.session_state['comissao'], format="%.2f")
        st.session_state['imposto'] = st.number_input("Simples Nacional (%)", value=st.session_state['imposto'], format="%.2f")
        st.session_state['mkt'] = st.number_input("Budget Marketing (R$)", value=st.session_state['mkt'])
        st.session_state['outros'] = st.number_input("Despesas Fixas Gerais (R$)", value=st.session_state['outros'])

    with c_folha:
        st.markdown("#### 👥 Folha de Pagamento")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state['s_socio'] = st.number_input("Salário Sócio", value=st.session_state['s_socio'])
            st.session_state['s_dev'] = st.number_input("Salário Dev", value=st.session_state['s_dev'])
            st.session_state['s_cs'] = st.number_input("Salário Suporte", value=st.session_state['s_cs'])
            st.session_state['s_venda'] = st.number_input("Salário Vendas", value=st.session_state['s_venda'])
        with c2:
            st.session_state['q_socio'] = st.number_input("Qtd Sócios", value=st.session_state['q_socio'])
            st.session_state['q_dev'] = st.number_input("Qtd Devs", value=st.session_state['q_dev'])
            st.session_state['q_cs'] = st.number_input("Qtd Suporte", value=st.session_state['q_cs'])
            st.session_state['q_venda'] = st.number_input("Qtd Vendas", value=st.session_state['q_venda'])
        
        st.session_state['encargos'] = st.number_input("Encargos (%)", value=st.session_state['encargos'], format="%.2f")

    st.markdown("---")
    st.markdown("#### 🏦 Contábil & Financeiro")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1: st.session_state['deprec'] = st.number_input("Depreciação", value=st.session_state['deprec'])
    with col_f2: st.session_state['amort'] = st.number_input("Amortização", value=st.session_state['amort'])
    with col_f3: st.session_state['fin'] = st.number_input("Resultado Financeiro", value=st.session_state['fin'])
    with col_f4: st.session_state['irpj'] = st.number_input("IRPJ Extra (Se não Simples)", value=st.session_state['irpj'])

# --- ABA 4: GLOSSÁRIO ---
with tab_gloss:
    st.markdown("### 📚 Glossário Financeiro Completo")
    
    with st.expander("1. Indicadores de Receita e Retenção (Top Line)", expanded=True):
        st.markdown("""
        * **MRR (Monthly Recurring Revenue):** É a sua Receita Recorrente Mensal. Basicamente `Clientes Ativos x Ticket Médio`. É o número mais importante para medir o tamanho da empresa hoje.
        * **ARR (Annual Recurring Revenue):** É o MRR anualizado (`MRR x 12`). Usado para Valuation.
        * **NRR (Net Revenue Retention):** Mede a capacidade da empresa de manter e crescer a receita da base atual.
            * *Fórmula:* `(Receita Inicial + Upsell - Churn) / Receita Inicial`.
            * *Meta:* Acima de 100% é excelente (significa que o Upsell cobre o Churn).
        * **Churn Rate:** Percentual de clientes ou receita perdida no mês.
        """)

    with st.expander("2. Indicadores de Lucratividade (Bottom Line)", expanded=True):
        st.markdown("""
        * **COGS (Cost of Goods Sold):** Custos diretos para prestar o serviço (Servidores Cloud, APIs, Licenças de Software embarcadas). Se a venda para, esse custo cai drasticamente.
        * **Margem de Contribuição:** O que sobra da Receita depois de pagar Impostos e COGS. É o dinheiro que sobra para pagar os Custos Fixos (Aluguel, Folha).
        * **EBITDA (LAJIDA):** Lucro Operacional "puro". Desconsidera juros, impostos sobre renda, depreciação e amortização. Mostra se a operação para de pé.
        * **Ponto de Equilíbrio (Break-Even):** Valor de faturamento necessário para cobrir TODOS os custos (Fixos e Variáveis). Lucro Zero. Abaixo disso é prejuízo.
        """)

    with st.expander("3. Unit Economics (Eficiência)", expanded=True):
        st.markdown("""
        * **CAC (Custo de Aquisição de Cliente):** `(Investimento em Marketing + Comissões + Salário Vendas) / Novos Clientes`. Quanto custa "comprar" um cliente.
        * **LTV (Lifetime Value):** `(Ticket Médio x Margem de Contribuição %) / Churn Rate`. Quanto lucro um cliente gera durante toda a vida dele na empresa.
        * **Payback:** `CAC / (Ticket Médio x Margem de Contribuição)`. Quantos meses o cliente precisa pagar a mensalidade para "devolver" o custo que você teve para trazê-lo. *Meta: < 12 meses.*
        """)
        
    with st.expander("4. Tributário (Fator R)", expanded=True):
        st.markdown("""
        * **Fator R:** Regra do Simples Nacional para empresas de Tech.
            * Fórmula: `Folha de Pagamento (incluindo Pró-Labore) / Faturamento Bruto (últimos 12 meses)`.
            * **Se for > 28%:** Você paga alíquota do **Anexo III** (começa em ~6%).
            * **Se for < 28%:** Você cai no **Anexo V** (começa em ~15,5%!!).
            * *Dica:* Ajuste o Pró-Labore dos sócios para garantir que essa conta bata 28%.
        """)
