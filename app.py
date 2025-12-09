import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Vaiontec | CFO Suite", layout="wide", page_icon="💎", initial_sidebar_state="collapsed")

# --- 2. CSS (CORPORATE BLUE + INPUTS) ---
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #f4f7f6; color: #0f2a4a; }
        [data-testid="stHeader"] { background-color: transparent; }
        .metric-container {
            background-color: white; padding: 18px; border-radius: 8px;
            border-left: 5px solid #1f497d; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-bottom: 10px;
        }
        .metric-label { font-size: 12px; color: #6c757d; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
        .metric-value { font-size: 24px; color: #1f497d; font-weight: 800; margin: 5px 0; }
        .metric-sub { font-size: 12px; font-weight: 500; }
        .sub-good { color: #218838; } .sub-bad { color: #c82333; } .sub-neutral { color: #6c757d; }
        [data-testid="stDataFrame"] { width: 100%; }
        .stButton>button { background-color: #1f497d; color: white; border-radius: 4px; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 1px;}
        .stButton>button:hover { background-color: #163a66; color: white; border-color: #163a66; }
        .stTabs [data-baseweb="tab-list"] { gap: 5px; border-bottom: 2px solid #e9ecef; }
        .stTabs [data-baseweb="tab"] { background-color: white; border-radius: 4px 4px 0 0; padding: 10px 20px; color: #495057; border: 1px solid #e9ecef; border-bottom: none; }
        .stTabs [aria-selected="true"] { background-color: #1f497d !important; color: white !important; }
        .glossary-card { background-color: white; padding: 25px; border-radius: 8px; border-left: 5px solid #2980b9; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .glossary-term { color: #1f497d; font-size: 20px; font-weight: 800; margin-bottom: 5px;}
        .glossary-desc { color: #444; font-size: 16px; margin-top: 10px; line-height: 1.6; }
        .glossary-tip { background-color: #fff8e1; color: #856404; padding: 10px; border-radius: 4px; margin-top: 15px; font-size: 14px; border: 1px solid #ffeeba; }
        .input-card { background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 10px; }
        .input-title { font-weight: 700; color: #1f497d; font-size: 14px; margin-bottom: 4px; }
        .input-desc { font-size: 12px; color: #666; margin-bottom: 8px; font-style: italic; min-height: 30px; line-height: 1.2; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DADOS GLOSSÁRIO ---
GLOSSARIO_DB = [
    {"termo": "MRR (Receita Recorrente)", "categoria": "Receita", "conceito": "Soma das assinaturas ativas no mês.", "formula": r"\text{Clientes} \times \text{Ticket}", "interpretacao": "O pulso do SaaS."},
    {"termo": "NRR (Retenção Líquida)", "categoria": "Growth", "conceito": "Receita retida + expansão - churn.", "formula": r"\frac{\text{Rec Inicial} + \text{Upsell} - \text{Churn}}{\text{Rec Inicial}}", "interpretacao": "> 100%: Crescimento orgânico."},
    {"termo": "CAC", "categoria": "Eficiência", "conceito": "Custo total p/ trazer 1 cliente.", "formula": r"\frac{\text{Mkt} + \text{Vendas}}{\text{Novos Clientes}}", "interpretacao": "Quanto menor, melhor."},
    {"termo": "LTV", "categoria": "Eficiência", "conceito": "Lucro total de um cliente na vida.", "formula": r"\frac{\text{Ticket} \times \text{Margem \%}}{\text{Churn Rate}}", "interpretacao": "Deve ser 3x maior que o CAC."},
    {"termo": "Payback", "categoria": "Eficiência", "conceito": "Meses p/ recuperar o CAC.", "formula": r"\frac{\text{CAC}}{\text{Ticket} \times \text{Margem}}", "interpretacao": "Ideal < 12 meses."},
    {"termo": "Ponto de Equilíbrio", "categoria": "Resultado", "conceito": "Faturamento para zerar custos.", "formula": r"\frac{\text{Custos Fixos}}{\text{Margem \%}}", "interpretacao": "Meta mínima mensal."},
    {"termo": "Fator R", "categoria": "Tributário", "conceito": "Razão Folha/Fat para Simples Nacional.", "formula": r"\frac{\text{Folha}}{\text{Faturamento}}", "interpretacao": "Manter > 28% (Anexo III)."}
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
key_map = {
    'cli_ini': 'Clientes Iniciais', 'cresc': 'Crescimento Mensal (%)', 'churn': 'Churn Rate (%)',
    'ticket': 'Ticket Médio (R$)', 'upsell': 'Upsell (% MRR)', 'cogs': 'COGS Unitário (R$)',
    'comissao': 'Comissão (%)', 'imposto': 'Simples (%)', 'taxa': 'Taxa Pagto (%)',
    'mkt': 'Budget Mkt (R$)', 'outros': 'Fixos Gerais (R$)', 'encargos': 'Encargos (%)',
    'deprec': 'Depreciação', 'amort': 'Amortização', 'fin': 'Res. Financeiro', 'irpj': 'IRPJ Extra',
    's_socio': 'Sal. Sócio', 'q_socio': 'Qtd Sócio', 's_dev': 'Sal. Dev', 'q_dev': 'Qtd Dev',
    's_cs': 'Sal. CS', 'q_cs': 'Qtd CS', 's_venda': 'Sal. Venda', 'q_venda': 'Qtd Venda'
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

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
    meses = [f"Mês {i}" for i in range(1, 13)]
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
        
        # Proteção contra Divisão por Zero
        mc_pct = margem / rec_liq if rec_liq > 0 else 0
        
        folha_tot = folha_base * (1 + s['encargos'])
        fixos = folha_tot + s['mkt'] + s['outros']
        
        ebitda = margem - fixos
        ebit = ebitda - (s['deprec'] + s['amort'])
        lair = ebit + s['fin']
        lucro = lair * (1 - s['irpj']) if lair > 0 else lair
        
        # KPIs com Proteção Matemática
        fator_r = folha_tot / rec_bruta if rec_bruta > 0 else 0
        
        fixos_totais_pe = fixos + s['deprec'] + s['amort'] - s['fin']
        mb_pct = margem / rec_bruta if rec_bruta > 0 else 0 # Margem Bruta
        pe_val = fixos_totais_pe / mb_pct if mb_pct > 0 else 0
        
        cac = (s['mkt'] + (rec_bruta * s['comissao'])) / novos if novos > 0 else 0
        
        # Proteção LTV: Ticket x Margem / Churn (Se churn > 0)
        ltv_num = s['ticket'] * mc_pct
        ltv = ltv_num / s['churn'] if s['churn'] > 0 else 0
        
        # Proteção Payback: CAC / (Ticket x Margem) (Se margem > 0)
        payback = cac / ltv_num if ltv_num > 0 else 0
        
        dados.append({
            'Mês': m,
            '1. Clientes Ativos': fim, '1.1 Novos': novos, '1.2 Churn (Qtd)': perda,
            '1.3 Ticket Médio (R$)': s['ticket'],
            '2. MRR (Recorrente)': mrr, '2.1 Receita Bruta Total': rec_bruta,
            '(-) Impostos': rec_bruta * s['imposto'],
            '3. Receita Líquida': rec_liq,
            '(-) COGS (Entrega)': fim * s['cogs'], '(-) Comissões/Taxas': (rec_bruta * s['comissao']) + (rec_bruta * s['taxa']),
            '4. Margem Contribuição': margem,
            '(-) Folha + Encargos': folha_tot, '(-) Mkt + Fixos': s['mkt'] + s['outros'],
            '5. EBITDA': ebitda,
            '(-) Deprec/Amort': s['deprec'] + s['amort'], '(+/-) Resultado Fin.': s['fin'],
            '6. Lucro Líquido': lucro,
            '7. Ponto Equilíbrio (R$)': pe_val, 'Fator R (%)': fator_r,
            'CAC (R$)': cac, 'LTV (R$)': ltv, 'Payback (Meses)': payback, 'NRR (Estimado)': nrr
        })
        cli = fim
    return pd.DataFrame(dados)

# --- INTERFACE ---
c1, c2 = st.columns([0.5, 6])
with c1: st.markdown("### 💎")
with c2: 
    st.markdown("### Vaiontec | CFO Suite")
    st.caption("Strategic Financial Planning & Analysis (FP&A)")

tab_dash, tab_dre, tab_input, tab_gloss = st.tabs(["📊 Executive Dashboard", "📑 Relatório DRE (Corporate)", "⚙️ Inputs & Update", "📚 Knowledge Base"])

df_raw = calcular_dre()
f = df_raw.iloc[-1]

# --- ABA 1: DASHBOARD ---
with tab_dash:
    def card(label, val, sub, color="neutral", money=True):
        v_str = f"R$ {val:,.2f}" if money else f"{val}"
        st.markdown(f"""<div class="metric-container"><div class="metric-label">{label}</div>
        <div class="metric-value">{v_str}</div><div class="metric-sub sub-{color}">{sub}</div></div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Faturamento Mensal", f['2.1 Receita Bruta Total'], "Projeção Mês 12", "neutral")
    with c2: card("Lucro Líquido", f['6. Lucro Líquido'], f"Margem: {(f['6. Lucro Líquido']/f['2.1 Receita Bruta Total'])*100:.1f}%" if f['2.1 Receita Bruta Total'] > 0 else "0%", "good" if f['6. Lucro Líquido']>0 else "bad")
    with c3: card("Caixa Mínimo (Break-Even)", f['7. Ponto Equilíbrio (R$)'], "Necessário para 0x0", "neutral")
    with c4: card("Base de Clientes", int(f['1. Clientes Ativos']), f"Novos: +{int(f['1.1 Novos'])}", "neutral", False)

    c1, c2, c3, c4 = st.columns(4)
    with c1: card("LTV", f['LTV (R$)'], "Lucro Vitalício")
    with c2: card("CAC", f['CAC (R$)'], "Custo Aquisição")
    with c3: card("Payback", f"{f['Payback (Meses)']:.1f} Meses", "Meta < 12", "good" if f['Payback (Meses)']<12 else "bad", False)
    with c4: card("Fator R", f"{f['Fator R (%)']*100:.1f}%", "Anexo III (>28%)" if f['Fator R (%)']>=0.28 else "Anexo V", "good" if f['Fator R (%)']>=0.28 else "bad", False)

    st.markdown("---")
    g1, g2 = st.columns([2, 1])
    with g1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_raw['Mês'], y=df_raw['2.1 Receita Bruta Total'], name='Fat. Bruto', marker_color='#1f497d'))
        fig.add_trace(go.Scatter(x=df_raw['Mês'], y=df_raw['7. Ponto Equilíbrio (R$)'], name='Ponto Equilíbrio', line=dict(color='#e74c3c', dash='dot')))
        fig.add_trace(go.Scatter(x=df_raw['Mês'], y=df_raw['6. Lucro Líquido'], name='Lucro Líquido', line=dict(color='#2ecc71', width=3)))
        fig.update_layout(template="plotly_white", height=400, margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig_u = go.Figure()
        fig_u.add_trace(go.Bar(name='CAC', x=df_raw['Mês'], y=df_raw['CAC (R$)'], marker_color='#e67e22'))
        fig_u.add_trace(go.Bar(name='LTV', x=df_raw['Mês'], y=df_raw['LTV (R$)'], marker_color='#2980b9'))
        fig_u.update_layout(barmode='group', height=400, margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_u, use_container_width=True)

# --- ABA 2: DRE CORPORATE ---
with tab_dre:
    st.markdown("### 📑 Demonstrativo de Resultados")
    df_dre = df_raw.set_index('Mês').T
    
    ordem_logica = [
        "1. Clientes Ativos", "1.1 Novos", "1.2 Churn (Qtd)", "1.3 Ticket Médio (R$)",
        "2. MRR (Recorrente)", "2.1 Receita Bruta Total",
        "(-) Impostos", "3. Receita Líquida",
        "(-) COGS (Entrega)", "(-) Comissões/Taxas",
        "4. Margem Contribuição",
        "(-) Folha + Encargos", "(-) Mkt + Fixos",
        "5. EBITDA",
        "(-) Deprec/Amort", "(+/-) Resultado Fin.",
        "6. Lucro Líquido",
        "7. Ponto Equilíbrio (R$)", "Fator R (%)",
        "CAC (R$)", "LTV (R$)", "Payback (Meses)", "NRR (Estimado)"
    ]
    
    df_dre = df_dre.reindex(ordem_logica)
    
    def formatar_valores(val, idx_name):
        if pd.isna(val): return "-"
        if any(x in idx_name for x in ['%', 'NRR', 'Fator']): return f"{val*100:.1f}%"
        if any(x in idx_name for x in ['Clientes', 'Novos', 'Churn']): return f"{int(val)}"
        if 'Meses' in idx_name: return f"{val:.1f}"
        return f"R$ {val:,.2f}"

    df_display = df_dre.copy()
    for col in df_display.columns:
        df_display[col] = [formatar_valores(v, i) for i, v in zip(df_display.index, df_display[col])]

    st.dataframe(df_display, use_container_width=True, height=800)
    csv = df_display.to_csv().encode('utf-8')
    st.download_button("📥 Baixar DRE Formatado (.csv)", data=csv, file_name="DRE_Vaiontec.csv", mime="text/csv")

# --- ABA 3: INPUTS (CORRIGIDA E SEGURA) ---
with tab_input:
    modo = st.radio("Modo:", ["📝 Edição Manual", "📂 Upload Padrão"], horizontal=True)
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
        # HELPER DE INPUT SEGURO
        def input_box(key, label, desc, fmt="%.2f", step=0.01, min_val=0.0):
            st.markdown(f"""
            <div class='input-card'>
                <div class='input-title'>{label}</div>
                <div class='input-desc'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            # min_val=0.0 permite zero. step define precisão.
            st.number_input(label, key=key, format=fmt, step=step, min_value=min_val, label_visibility="collapsed")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("1. Growth")
            input_box('cli_ini', "Clientes Iniciais", "Base inicial de clientes ativos (Mês 0).", "%.0f", 1.0)
            input_box('cresc', "Crescimento Mensal (%)", "Taxa esperada de novos clientes.", "%.2f", 0.01)
            input_box('churn', "Churn Rate (%)", "Percentual de cancelamento mensal.", "%.2f", 0.01)
            input_box('ticket', "Ticket Médio (R$)", "Valor médio da assinatura mensal.", "%.2f", 1.0)
            input_box('upsell', "Upsell (% da Rec.)", "Vendas adicionais na base atual.", "%.2f", 0.01)
        
        with c2:
            st.subheader("2. Custos Variáveis")
            input_box('cogs', "COGS Unitário (R$)", "Custo direto (Cloud/Licença) por cliente.")
            input_box('comissao', "Comissão (%)", "% sobre Vendas paga a terceiros.")
            input_box('imposto', "Simples Nacional (%)", "Alíquota sobre nota fiscal.")
            input_box('taxa', "Taxa Meios Pagto (%)", "Taxa do gateway (Stripe/Boleto).")
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("3. Fixos Gerais")
            input_box('mkt', "Budget Mkt (R$)", "Verba fixa mensal para Marketing.")
            input_box('outros', "Outros Fixos (R$)", "Aluguel, Softwares, Contabilidade.")

        with c3:
            st.subheader("4. Folha & Contábil")
            with st.expander("Detalhamento Salários", expanded=True):
                c_s, c_q = st.columns([2,1])
                with c_s:
                    st.number_input("Sal. Sócio", key='s_socio', step=100.0)
                    st.number_input("Sal. Dev", key='s_dev', step=100.0)
                    st.number_input("Sal. CS", key='s_cs', step=100.0)
                    st.number_input("Sal. Venda", key='s_venda', step=100.0)
                with c_q:
                    st.number_input("Qtd", key='q_socio', min_value=0, step=1)
                    st.number_input("Qtd", key='q_dev', min_value=0, step=1)
                    st.number_input("Qtd", key='q_cs', min_value=0, step=1)
                    st.number_input("Qtd", key='q_venda', min_value=0, step=1)
            
            input_box('encargos', "Encargos Folha (%)", "FGTS, Férias, 13º (Simples ~35%).")
            input_box('deprec', "Depreciação (R$)", "Perda valor equip. (Notebooks).")
            input_box('amort', "Amortização (R$)", "Perda valor intangível (Software).")
            # Res Financeiro pode ser negativo (min_val=None)
            input_box('fin', "Res. Financeiro (R$)", "Rendimentos (+) ou Juros Pagos (-).", "%.2f", 0.01, None)

# --- ABA 4: GLOSSÁRIO ---
with tab_gloss:
    st.markdown("### 🔍 Knowledge Base")
    search = st.text_input("Pesquisar indicador...", "").lower()
    for item in GLOSSARIO_DB:
        if search in item['termo'].lower() or search in item['conceito'].lower() or search == "":
            st.markdown(f"""
            <div class="glossary-card">
                <div class="glossary-term">{item['termo']} <span style="font-size:12px; color:#17a2b8; border:1px solid #17a2b8; padding:2px 6px; border-radius:4px">{item['categoria']}</span></div>
                <div style="color:#555; margin-bottom:10px">{item['conceito']}</div>
                <div class="formula-box">🧮 Fórmula: {item['formula']}</div>
                <div style="font-style:italic; font-size:13px; color:#666; margin-top:8px">💡 {item['interpretacao']}</div>
            </div>
            """, unsafe_allow_html=True)
            if 'formula' in item and '\\' in item['formula']: st.latex(item['formula'])
