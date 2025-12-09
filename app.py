import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Vaiontec | CFO", layout="wide", page_icon="💎", initial_sidebar_state="collapsed")

# --- 2. CSS (AZUL/LIGHT) ---
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #f4f7f6; color: #2c3e50; }
        [data-testid="stHeader"] { background-color: transparent; }
        .metric-container {
            background-color: white; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1f497d; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px;
        }
        .metric-label { font-size: 13px; color: #7f8c8d; text-transform: uppercase; font-weight: 700; }
        .metric-value { font-size: 28px; color: #1f497d; font-weight: 800; margin: 8px 0; }
        .metric-sub { font-size: 13px; font-weight: 500; }
        .sub-good { color: #27ae60; } .sub-bad { color: #c0392b; } .sub-neutral { color: #7f8c8d; }
        .stButton>button { background-color: #1f497d; color: white; border-radius: 6px; border: none; font-weight: 600; }
        .stButton>button:hover { background-color: #15325b; color: white; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: white; border-radius: 6px; padding: 10px 20px; color: #555; border: 1px solid #ddd;}
        .stTabs [aria-selected="true"] { background-color: #1f497d !important; color: white !important; border: none;}
        
        /* Estilo do Glossário */
        .glossary-card { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 10px; }
        .glossary-term { color: #1f497d; font-size: 18px; font-weight: bold; }
        .glossary-desc { color: #555; margin-top: 5px; margin-bottom: 10px; line-height: 1.5; }
        .formula-box { background-color: #f8f9fa; padding: 10px; border-radius: 4px; border-left: 3px solid #e67e22; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DADOS DO GLOSSÁRIO (BASE DE CONHECIMENTO) ---
GLOSSARIO_DB = [
    {
        "termo": "MRR (Monthly Recurring Revenue)",
        "categoria": "Receita",
        "conceito": "A soma de todas as receitas de assinatura que se repetem mensalmente. É o principal indicador de tamanho de uma empresa SaaS.",
        "formula": r"MRR = \sum (\text{Clientes Ativos} \times \text{Valor da Assinatura})",
        "interpretacao": "Se o MRR cresce, a empresa está saudável. Quedas indicam Churn alto ou falta de vendas."
    },
    {
        "termo": "ARR (Annual Recurring Revenue)",
        "categoria": "Receita",
        "conceito": "A projeção anualizada do seu faturamento recorrente. Usado para Valuation (avaliação de valor de venda da empresa).",
        "formula": r"ARR = MRR \times 12",
        "interpretacao": "Investidores usam múltiplos de ARR para definir quanto vale sua startup (Ex: 5x ARR)."
    },
    {
        "termo": "NRR (Net Revenue Retention)",
        "categoria": "Growth",
        "conceito": "Mede a capacidade da empresa de reter e expandir a receita da base de clientes existente, descontando cancelamentos.",
        "formula": r"NRR = \frac{(\text{Receita Inicial} + \text{Upsell} - \text{Churn})}{\text{Receita Inicial}} \times 100",
        "interpretacao": "Acima de 100%: A empresa cresce mesmo sem vender para novos clientes (Upsell > Churn). Abaixo de 100%: A empresa está 'vazando' dinheiro."
    },
    {
        "termo": "CAC (Custo de Aquisição de Cliente)",
        "categoria": "Eficiência",
        "conceito": "Quanto dinheiro você gasta em Marketing e Vendas para conquistar 1 novo cliente pagante.",
        "formula": r"CAC = \frac{\text{Investimento em Mkt} + \text{Salários Vendas} + \text{Comissões}}{\text{Número de Novos Clientes}}",
        "interpretacao": "Quanto menor, melhor. Se o CAC for maior que o LTV, o modelo de negócio é inviável."
    },
    {
        "termo": "LTV (Lifetime Value)",
        "categoria": "Eficiência",
        "conceito": "O lucro bruto total que um cliente gera para a empresa durante todo o tempo que permanece assinante.",
        "formula": r"LTV = \frac{\text{Ticket Médio} \times \text{Margem de Contribuição \%}}{\text{Churn Rate \%}}",
        "interpretacao": "Indica o teto do quanto você pode gastar para adquirir um cliente."
    },
    {
        "termo": "Relação LTV / CAC",
        "categoria": "Eficiência",
        "conceito": "O 'Santo Graal' do SaaS. Mede o retorno sobre o investimento de aquisição.",
        "formula": r"Ratio = \frac{LTV}{CAC}",
        "interpretacao": "Ideal: > 3x (A cada R$1 gasto, voltam R$3). Se < 1x, você perde dinheiro vendendo."
    },
    {
        "termo": "Payback Period",
        "categoria": "Eficiência",
        "conceito": "O tempo (em meses) que leva para recuperar o dinheiro gasto (CAC) para trazer o cliente.",
        "formula": r"Payback = \frac{CAC}{\text{Ticket Médio} \times \text{Margem Contribuição \%}}",
        "interpretacao": "Ideal: Menor que 12 meses. Se for muito longo, a empresa precisa de muito caixa para crescer."
    },
    {
        "termo": "Churn Rate",
        "categoria": "Growth",
        "conceito": "A taxa de cancelamento. Pode ser medida em número de clientes (Logo Churn) ou em dinheiro (Revenue Churn).",
        "formula": r"Churn \% = \frac{\text{Clientes Cancelados no Mês}}{\text{Clientes no Início do Mês}}",
        "interpretacao": "O 'furo no balde'. Churn alto mata o crescimento composto. Ideal em SaaS B2B: < 1% ao mês."
    },
    {
        "termo": "COGS (Cost of Goods Sold)",
        "categoria": "Custos",
        "conceito": "Custo das Mercadorias/Serviços Vendidos. Em software, refere-se aos custos de infraestrutura (servidores), licenças embarcadas e suporte direto.",
        "formula": r"COGS = \text{Servidores Cloud} + \text{APIs de Terceiros} + \text{Equipe Suporte N1}",
        "interpretacao": "Quanto menor o COGS, maior a Margem Bruta. SaaS de excelência tem Margem Bruta > 80%."
    },
    {
        "termo": "Margem de Contribuição",
        "categoria": "Resultados",
        "conceito": "O valor que sobra da receita de vendas após pagar os custos variáveis (Impostos + COGS + Comissões).",
        "formula": r"MC = \text{Receita Líquida} - (\text{COGS} + \text{Comissões} + \text{Impostos Variáveis})",
        "interpretacao": "É o dinheiro que sobra para pagar as contas fixas (aluguel, salários) e gerar lucro."
    },
    {
        "termo": "Ponto de Equilíbrio (Break-Even)",
        "categoria": "Resultados",
        "conceito": "O momento ou valor de faturamento onde a empresa não tem nem lucro nem prejuízo.",
        "formula": r"PE (R\$) = \frac{\text{Custos Fixos Totais}}{\text{Margem de Contribuição \%}}",
        "interpretacao": "Abaixo desse valor, a empresa queima caixa. Acima, gera lucro."
    },
    {
        "termo": "EBITDA (LAJIDA)",
        "categoria": "Resultados",
        "conceito": "Lucro Antes de Juros, Impostos, Depreciação e Amortização. Mede a geração de caixa operacional pura.",
        "formula": r"EBITDA = \text{Margem Contribuição} - \text{Despesas Operacionais (OpEx)}",
        "interpretacao": "Melhor indicador para comparar a eficiência operacional de empresas diferentes, ignorando dívidas e impostos."
    },
    {
        "termo": "Fator R",
        "categoria": "Tributário",
        "conceito": "Regra do Simples Nacional que define a alíquota de imposto baseada na folha de pagamento.",
        "formula": r"Fator R = \frac{\text{Folha de Pagamento (12 meses)}}{\text{Faturamento Bruto (12 meses)}}",
        "interpretacao": "Se > 28%: Anexo III (Imposto ~6%). Se < 28%: Anexo V (Imposto ~15.5%). Fundamental monitorar mensalmente."
    }
]

# --- 4. ESTADO E DEFAULTS ---
defaults = {
    'cli_ini': 50, 'cresc': 0.10, 'churn': 0.03, 'ticket': 500.0, 'upsell': 0.05,
    'cogs': 30.0, 'comissao': 0.05, 'imposto': 0.06, 'taxa': 0.02,
    'mkt': 5000.0, 'outros': 3000.0, 'encargos': 0.35,
    'deprec': 400.0, 'amort': 600.0, 'fin': 0.0, 'irpj': 0.0,
    's_socio': 8000.0, 'q_socio': 2, 's_dev': 5000.0, 'q_dev': 2,
    's_cs': 2500.0, 'q_cs': 1, 's_venda': 3000.0, 'q_venda': 1
}

# Mapping para CSV
key_map = {
    'cli_ini': 'Clientes Iniciais', 'cresc': 'Crescimento Mensal (%)', 'churn': 'Churn Rate (%)',
    'ticket': 'Ticket Médio (R$)', 'upsell': 'Upsell (% MRR)', 'cogs': 'COGS Unitário (R$)',
    'comissao': 'Comissão (%)', 'imposto': 'Simples (%)', 'taxa': 'Taxa Pagto (%)',
    'mkt': 'Budget Mkt (R$)', 'outros': 'Fixos Gerais (R$)', 'encargos': 'Encargos (%)',
    'deprec': 'Depreciação', 'amort': 'Amortização', 'fin': 'Res. Financeiro', 'irpj': 'IRPJ Extra',
    's_socio': 'Sal. Sócio', 'q_socio': 'Qtd Sócio', 's_dev': 'Sal. Dev', 'q_dev': 'Qtd Dev',
    's_cs': 'Sal. CS', 'q_cs': 'Qtd CS', 's_venda': 'Sal. Venda', 'q_venda': 'Qtd Venda'
}

for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 5. FUNÇÕES ---
def gerar_template_csv():
    data = []
    for k, v in defaults.items():
        data.append({'Parametro': key_map.get(k, k), 'Valor': st.session_state[k], 'Codigo_Interno': k})
    return pd.DataFrame(data)

def processar_upload(df_up):
    try:
        for index, row in df_up.iterrows():
            codigo = row.get('Codigo_Interno')
            if codigo and codigo in defaults: st.session_state[codigo] = float(row['Valor'])
        st.toast("✅ Dados atualizados!", icon="🚀")
    except Exception as e: st.error(f"Erro: {e}")

def calcular_dre():
    s = st.session_state
    meses = list(range(1, 13))
    dados = []
    
    cli = s['cli_ini']
    folha_base = (s['s_socio']*s['q_socio']) + (s['s_dev']*s['q_dev']) + (s['s_cs']*s['q_cs']) + (s['s_venda']*s['q_venda'])
    nrr = 1 + s['upsell'] - s['churn']

    for m in meses:
        novos = int(cli * s['cresc'])
        perda = int(cli * s['churn'])
        fim = cli + novos - perda
        
        mrr = fim * s['ticket']
        rec_bruta = mrr * (1 + s['upsell'])
        rec_liq = rec_bruta * (1 - s['imposto'])
        
        var_total = (fim * s['cogs']) + (rec_bruta * s['comissao']) + (rec_bruta * s['taxa'])
        margem = rec_liq - var_total
        
        folha_tot = folha_base * (1 + s['encargos'])
        fixos = folha_tot + s['mkt'] + s['outros']
        
        ebitda = margem - fixos
        ebit = ebitda - (s['deprec'] + s['amort'])
        lair = ebit + s['fin']
        lucro = lair * (1 - s['irpj']) if lair > 0 else lair
        
        fator_r = folha_tot / rec_bruta if rec_bruta > 0 else 0
        pe_val = (fixos + s['deprec'] + s['amort'] - s['fin']) / (margem/rec_bruta) if rec_bruta > 0 else 0
        cac = (s['mkt'] + (rec_bruta * s['comissao'])) / novos if novos > 0 else 0
        ltv = (s['ticket'] * (margem/rec_liq)) / s['churn'] if s['churn'] > 0 else 0
        payback = cac / (s['ticket'] * (margem/rec_liq)) if (s['ticket'] * (margem/rec_liq)) > 0 else 0
        
        dados.append({
            'Mês': m, 'Clientes': fim, 'Novos': novos, 'Receita Bruta': rec_bruta,
            'Receita Líquida': rec_liq, 'COGS': fim*s['cogs'], 'Margem Contrib.': margem,
            'EBITDA': ebitda, 'Lucro Líquido': lucro, 'Ponto Equilíbrio': pe_val,
            'Fator R': fator_r, 'CAC': cac, 'LTV': ltv, 'Payback': payback,
            'NRR': nrr, 'MRR': mrr
        })
        cli = fim
    return pd.DataFrame(dados)

# --- 6. INTERFACE ---
c1, c2 = st.columns([0.5, 5])
with c1: st.markdown("# 💎")
with c2: 
    st.markdown("## Vaiontec | Sistema de Gestão Financeira")
    st.caption("Environment: Production | Mode: Executive View")

tab_dash, tab_dre, tab_input, tab_gloss = st.tabs(["📊 Dashboard", "📑 Relatório DRE", "⚙️ Atualizar Dados", "📚 Glossário Inteligente"])

df = calcular_dre()
f = df.iloc[-1]

with tab_dash:
    def card(label, val, sub, color="neutral", money=True):
        v_str = f"R$ {val:,.2f}" if money else f"{val}"
        st.markdown(f"""<div class="metric-container"><div class="metric-label">{label}</div>
        <div class="metric-value">{v_str}</div><div class="metric-sub sub-{color}">{sub}</div></div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Faturamento Mensal", f['Receita Bruta'], "Projeção Mês 12", "neutral")
    with c2: card("Clientes Ativos", int(f['Clientes']), f"+{int(f['Novos'])} novos", "neutral", False)
    with c3: card("Lucro Líquido", f['Lucro Líquido'], f"Margem: {(f['Lucro Líquido']/f['Receita Bruta'])*100:.1f}%", "good" if f['Lucro Líquido']>0 else "bad")
    with c4: card("Ponto de Equilíbrio", f['Ponto Equilíbrio'], "Necessário para zerar", "neutral")

    c1, c2, c3, c4 = st.columns(4)
    with c1: card("LTV", f['LTV'], "Lucro Vitalício")
    with c2: card("CAC", f['CAC'], "Custo Aquisição")
    with c3: card("Payback", f"{f['Payback']:.1f} Meses", "Meta < 12", "good" if f['Payback']<12 else "bad", False)
    with c4: card("Fator R", f"{f['Fator R']*100:.1f}%", "Anexo III (>28%)" if f['Fator R']>=0.28 else "Anexo V", "good" if f['Fator R']>=0.28 else "bad", False)

    st.markdown("---")
    g1, g2 = st.columns([2, 1])
    with g1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Mês'], y=df['Receita Bruta'], name='Fat.', marker_color='#1f497d'))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['Ponto Equilíbrio'], name='Break-Even', line=dict(color='#e74c3c', dash='dot')))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['Lucro Líquido'], name='Lucro', line=dict(color='#2ecc71')))
        fig.update_layout(height=400, margin=dict(t=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig_u = go.Figure()
        fig_u.add_trace(go.Bar(name='CAC', x=df['Mês'], y=df['CAC'], marker_color='#e67e22'))
        fig_u.add_trace(go.Bar(name='LTV', x=df['Mês'], y=df['LTV'], marker_color='#2980b9'))
        fig_u.update_layout(barmode='group', height=400, margin=dict(t=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_u, use_container_width=True)

with tab_dre:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar DRE (.csv)", data=csv, file_name="DRE.csv", mime="text/csv")
    df_show = df.copy()
    for c in ['Receita Bruta','Receita Líquida','COGS','Margem Contrib.','EBITDA','Lucro Líquido','Ponto Equilíbrio','CAC','LTV']:
        df_show[c] = df_show[c].apply(lambda x: f"R$ {x:,.2f}")
    df_show['Fator R'] = df_show['Fator R'].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(df_show, use_container_width=True, height=600)

with tab_input:
    modo = st.radio("Método:", ["📝 Manual", "📂 Upload Padrão"], horizontal=True)
    st.markdown("---")
    if modo == "📂 Upload Padrão":
        c1, c2 = st.columns(2)
        with c1:
            df_tmpl = gerar_template_csv()
            st.download_button("📥 Baixar Modelo (.csv)", df_tmpl.to_csv(index=False).encode('utf-8'), "modelo.csv", "text/csv")
        with c2:
            up = st.file_uploader("Upload .csv", type=['csv'])
            if up: processar_upload(pd.read_csv(up))
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Growth & Vendas")
            st.session_state['cli_ini'] = st.number_input("Clientes Iniciais", value=st.session_state['cli_ini'])
            st.session_state['cresc'] = st.number_input("Crescimento (%)", value=st.session_state['cresc'])
            st.session_state['churn'] = st.number_input("Churn Rate (%)", value=st.session_state['churn'])
            st.session_state['ticket'] = st.number_input("Ticket (R$)", value=st.session_state['ticket'])
            st.session_state['upsell'] = st.number_input("Upsell (%)", value=st.session_state['upsell'])
            st.subheader("2. Custos Variáveis")
            st.session_state['cogs'] = st.number_input("COGS Unit. (R$)", value=st.session_state['cogs'])
            st.session_state['comissao'] = st.number_input("Comissão (%)", value=st.session_state['comissao'])
            st.session_state['imposto'] = st.number_input("Simples (%)", value=st.session_state['imposto'])
            st.session_state['taxa'] = st.number_input("Taxa Pagto (%)", value=st.session_state['taxa'])
        with c2:
            st.subheader("3. Fixos & Pessoal")
            st.session_state['mkt'] = st.number_input("Mkt (R$)", value=st.session_state['mkt'])
            st.session_state['outros'] = st.number_input("Outros Fixos (R$)", value=st.session_state['outros'])
            with st.expander("Folha Detalhada"):
                c_s, c_q = st.columns([2,1])
                with c_s:
                    st.session_state['s_socio'] = st.number_input("Sal. Sócio", st.session_state['s_socio'])
                    st.session_state['s_dev'] = st.number_input("Sal. Dev", st.session_state['s_dev'])
                    st.session_state['s_cs'] = st.number_input("Sal. CS", st.session_state['s_cs'])
                    st.session_state['s_venda'] = st.number_input("Sal. Venda", st.session_state['s_venda'])
                with c_q:
                    st.session_state['q_socio'] = st.number_input("Qtd", st.session_state['q_socio'], key="kq_soc")
                    st.session_state['q_dev'] = st.number_input("Qtd", st.session_state['q_dev'], key="kq_dev")
                    st.session_state['q_cs'] = st.number_input("Qtd", st.session_state['q_cs'], key="kq_cs")
                    st.session_state['q_venda'] = st.number_input("Qtd", st.session_state['q_venda'], key="kq_vnd")
            st.session_state['encargos'] = st.number_input("Encargos (%)", value=st.session_state['encargos'])
            st.subheader("4. Contábil")
            st.session_state['deprec'] = st.number_input("Deprec. (R$)", st.session_state['deprec'])
            st.session_state['amort'] = st.number_input("Amort. (R$)", st.session_state['amort'])
            st.session_state['fin'] = st.number_input("Res. Fin (R$)", st.session_state['fin'])

with tab_gloss:
    st.markdown("### 🔍 Pesquisar Conceito")
    search_term = st.text_input("Digite um termo (ex: Lucro, CAC, Churn)", "").lower()
    
    st.markdown("---")
    
    found = False
    for item in GLOSSARIO_DB:
        if search_term in item['termo'].lower() or search_term in item['conceito'].lower():
            found = True
            st.markdown(f"""
            <div class="glossary-card">
                <div class="glossary-term">{item['termo']} <span style="font-size:12px; color:#999">({item['categoria']})</span></div>
                <div class="glossary-desc">{item['conceito']}</div>
                <div class="formula-box">{item['formula']}</div>
                <div class="glossary-desc" style="margin-top:10px"><i>💡 {item['interpretacao']}</i></div>
            </div>
            """, unsafe_allow_html=True)
            
    if not found and search_term:
        st.warning("Nenhum termo encontrado.")
    if not search_term:
        st.caption("Mostrando todos os termos disponíveis.")
