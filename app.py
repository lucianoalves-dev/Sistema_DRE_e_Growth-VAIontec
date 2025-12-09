import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Vaiontec | Growth Intelligence", layout="wide", page_icon="🚀", initial_sidebar_state="collapsed")

# --- 2. CSS (CORPORATE BLUE + INPUTS PRO) ---
st.markdown("""
    <style>
        /* TEMA GERAL */
        [data-testid="stAppViewContainer"] { background-color: #f4f7f6; color: #0f2a4a; }
        [data-testid="stHeader"] { background-color: transparent; }
        
        /* CARDS KPI */
        .metric-container {
            background-color: white; padding: 18px; border-radius: 8px;
            border-left: 5px solid #1f497d; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-bottom: 10px;
        }
        .metric-label { font-size: 12px; color: #6c757d; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
        .metric-value { font-size: 24px; color: #1f497d; font-weight: 800; margin: 5px 0; }
        .metric-sub { font-size: 12px; font-weight: 500; }
        .sub-good { color: #218838; } .sub-bad { color: #c82333; } .sub-neutral { color: #6c757d; }
        
        /* TABELA */
        [data-testid="stDataFrame"] { width: 100%; }
        
        /* BOTÕES */
        .stButton>button { background-color: #1f497d; color: white; border-radius: 4px; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 1px;}
        .stButton>button:hover { background-color: #163a66; color: white; border-color: #163a66; }
        
        /* INPUT CARD */
        .input-group-title { color: #1f497d; font-size: 16px; font-weight: 700; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
        .input-card { background-color: white; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; margin-bottom: 10px; }
        .input-title { font-weight: 700; color: #1f497d; font-size: 14px; margin-bottom: 4px; }
        .input-desc { font-size: 12px; color: #666; margin-bottom: 8px; font-style: italic; min-height: 30px; line-height: 1.2; }
        
        /* ABAS */
        .stTabs [data-baseweb="tab-list"] { gap: 5px; border-bottom: 2px solid #e9ecef; }
        .stTabs [data-baseweb="tab"] { background-color: white; border-radius: 4px 4px 0 0; padding: 10px 20px; color: #495057; border: 1px solid #e9ecef; border-bottom: none; }
        .stTabs [aria-selected="true"] { background-color: #1f497d !important; color: white !important; }
        
        /* GLOSSÁRIO (ESTILO RESTAURADO) */
        .glossary-card { background-color: white; padding: 20px; border-radius: 8px; border-left: 5px solid #2980b9; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .glossary-term { color: #1f497d; font-size: 18px; font-weight: 800; margin-bottom: 5px; }
        .glossary-cat { background-color: #eef2f7; color: #555; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-left: 10px; }
        .glossary-desc { color: #444; font-size: 15px; margin-top: 10px; line-height: 1.5; }
        .glossary-tip { background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 13px; border: 1px solid #ffeeba; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DADOS DO GLOSSÁRIO (ESTRUTURA COMPLETA) ---
GLOSSARIO_DB = [
    {
        "termo": "MRR (Monthly Recurring Revenue)",
        "categoria": "Receita",
        "conceito": "Receita Recorrente Mensal. É a soma de todas as assinaturas ativas. O principal indicador de saúde de um SaaS.",
        "formula": r"MRR = \text{Clientes Ativos} \times \text{Ticket Médio}",
        "interpretacao": "Se o MRR sobe, a empresa cresce. Quedas indicam Churn alto."
    },
    {
        "termo": "NRR (Net Revenue Retention)",
        "categoria": "Growth",
        "conceito": "Retenção Líquida de Receita. Mede quanto da receita do mês anterior permaneceu, somando expansões (upsell) e descontando cancelamentos.",
        "formula": r"NRR = \frac{(\text{Receita Inicial} + \text{Upsell} - \text{Churn})}{\text{Receita Inicial}}",
        "interpretacao": "Acima de 100% (ou 1.0) significa crescimento orgânico sem novas vendas."
    },
    {
        "termo": "CAC (Custo de Aquisição)",
        "categoria": "Eficiência",
        "conceito": "Valor gasto em Marketing e Vendas para conquistar 1 novo cliente.",
        "formula": r"CAC = \frac{\text{Mkt} + \text{Comissões} + \text{Salários Vendas}}{\text{Novos Clientes}}",
        "interpretacao": "Quanto menor, melhor a eficiência da máquina de vendas."
    },
    {
        "termo": "LTV (Lifetime Value)",
        "categoria": "Eficiência",
        "conceito": "Lucro bruto total que um cliente deixa na empresa durante toda sua vida útil.",
        "formula": r"LTV = \frac{\text{Ticket Médio} \times \text{Margem Contribuição \%}}{\text{Churn Rate}}",
        "interpretacao": "O LTV deve ser pelo menos 3x maior que o CAC (LTV/CAC > 3)."
    },
    {
        "termo": "Payback Period",
        "categoria": "Eficiência",
        "conceito": "Tempo (em meses) para recuperar o investimento feito para adquirir o cliente (CAC).",
        "formula": r"Payback = \frac{CAC}{\text{Ticket Médio} \times \text{Margem Contribuição}}",
        "interpretacao": "Ideal: Menos de 12 meses para fluxo de caixa saudável."
    },
    {
        "termo": "Ponto de Equilíbrio",
        "categoria": "Financeiro",
        "conceito": "Faturamento necessário para cobrir todos os custos e despesas (Lucro Zero).",
        "formula": r"PE = \frac{\text{Custos Fixos Totais}}{\text{Margem Contribuição \%}}",
        "interpretacao": "Abaixo disso é prejuízo (Burn Rate). Acima é lucro."
    },
    {
        "termo": "EBITDA",
        "categoria": "Financeiro",
        "conceito": "Lucro antes de Juros, Impostos, Depreciação e Amortização. Mede a geração de caixa operacional.",
        "formula": r"EBITDA = \text{Margem Contribuição} - \text{Despesas Operacionais}",
        "interpretacao": "Indica se a operação da empresa para de pé sozinha."
    },
    {
        "termo": "Fator R",
        "categoria": "Tributário",
        "conceito": "Razão entre Folha de Pagamento e Faturamento para definir anexo do Simples Nacional.",
        "formula": r"Fator R = \frac{\text{Folha Total}}{\text{Faturamento Bruto}}",
        "interpretacao": "Mantenha > 28% para pagar imposto reduzido (Anexo III ~6%)."
    }
]

# --- 4. INICIALIZAÇÃO DE ESTADO ---
defaults = {
    # 1. Receita Drivers
    'cli_ini': 50, 'cresc': 0.10, 'churn': 0.03, 'ticket': 500.0, 'upsell': 0.05,
    # 2. Variáveis
    'cogs': 30.0, 'comissao': 0.05, 'imposto': 0.06, 'taxa': 0.02,
    # 3. Fixos
    'mkt': 5000.0, 'outros': 3000.0, 
    # 4. Folha
    's_socio': 8000.0, 'q_socio': 2, 
    's_dev': 5000.0, 'q_dev': 2,
    's_cs': 2500.0, 'q_cs': 1,
    's_venda': 3000.0, 'q_venda': 1,
    'encargos': 0.35,
    # 5. Contábil
    'deprec': 400.0, 'amort': 600.0, 'fin': 0.0, 'irpj': 0.0
}

key_map = {
    'cli_ini': 'Clientes Iniciais', 'cresc': 'Tx Crescimento Mensal', 'churn': 'Tx Churn Mensal',
    'ticket': 'Ticket Médio (R$)', 'upsell': 'Tx Upsell (% Rec)',
    'cogs': 'COGS Unitário (R$)', 'comissao': 'Tx Comissão (%)', 'imposto': 'Tx Imposto Simples (%)', 'taxa': 'Tx Meios Pagto (%)',
    'mkt': 'Budget Marketing (R$)', 'outros': 'Outras Desp. Fixas (R$)',
    's_socio': 'Salário Sócio', 'q_socio': 'Qtd Sócio',
    's_dev': 'Salário Dev', 'q_dev': 'Qtd Dev',
    's_cs': 'Salário Suporte', 'q_cs': 'Qtd Suporte',
    's_venda': 'Salário Vendas', 'q_venda': 'Qtd Vendas',
    'encargos': 'Tx Encargos Folha (%)',
    'deprec': 'Depreciação (R$)', 'amort': 'Amortização (R$)', 'fin': 'Resultado Fin. (R$)', 'irpj': 'Tx IRPJ Extra (%)'
}

for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# --- 5. FUNÇÕES ---
def gerar_template_csv():
    data = []
    for k in defaults.keys():
        data.append({'Parametro': key_map.get(k, k), 'Valor': st.session_state[k], 'Codigo_Interno': k})
    return pd.DataFrame(data)

def processar_upload(df_up):
    try:
        count = 0
        for index, row in df_up.iterrows():
            codigo = row.get('Codigo_Interno')
            if codigo and codigo in defaults: 
                st.session_state[codigo] = float(row['Valor'])
                count += 1
        if count > 0:
            st.toast(f"✅ {count} campos atualizados com sucesso!", icon="🚀")
        else:
            st.error("Nenhum código válido encontrado no CSV.")
    except Exception as e: st.error(f"Erro ao processar: {e}")

def calcular_dre():
    s = st.session_state
    meses = [f"Mês {i}" for i in range(1, 13)]
    dados = []
    
    cli = s['cli_ini']
    folha_base = (s['s_socio']*s['q_socio']) + (s['s_dev']*s['q_dev']) + (s['s_cs']*s['q_cs']) + (s['s_venda']*s['q_venda'])
    nrr = 1 + s['upsell'] - s['churn']

    for m in meses:
        # Lógica de Growth
        novos = int(cli * s['cresc'])
        perda = int(cli * s['churn'])
        fim = cli + novos - perda
        
        # Receita
        mrr = fim * s['ticket']
        rec_bruta = mrr * (1 + s['upsell'])
        
        # Variáveis
        imp_val = rec_bruta * s['imposto']
        rec_liq = rec_bruta - imp_val
        cogs_val = fim * s['cogs']
        comissao_val = rec_bruta * s['comissao']
        taxa_val = rec_bruta * s['taxa']
        
        custos_var_total = cogs_val + comissao_val + taxa_val
        margem = rec_liq - custos_var_total
        
        # Fixos
        folha_tot = folha_base * (1 + s['encargos'])
        fixos_op = folha_tot + s['mkt'] + s['outros']
        
        # Resultados
        ebitda = margem - fixos_op
        deprec_amort = s['deprec'] + s['amort']
        ebit = ebitda - deprec_amort
        lair = ebit + s['fin']
        lucro = lair * (1 - s['irpj']) if lair > 0 else lair
        
        # KPIs (Protegidos contra div/0)
        mc_pct = margem / rec_liq if rec_liq > 0 else 0
        mb_pct = margem / rec_bruta if rec_bruta > 0 else 0
        
        fixos_totais_pe = fixos_op + deprec_amort - s['fin']
        pe_val = fixos_totais_pe / mb_pct if mb_pct > 0 else 0
        
        fator_r = folha_tot / rec_bruta if rec_bruta > 0 else 0
        
        cac = (s['mkt'] + comissao_val) / novos if novos > 0 else 0
        
        ltv_num = s['ticket'] * mc_pct
        ltv = ltv_num / s['churn'] if s['churn'] > 0 else 0
        
        payback = cac / ltv_num if ltv_num > 0 else 0
        
        dados.append({
            'Mês': m,
            '1. Clientes Ativos': fim, '1.1 Novos': novos, '1.2 Churn (Qtd)': perda, '1.3 Ticket Médio': s['ticket'],
            '2. MRR (Recorrente)': mrr, '2.1 Receita Bruta': rec_bruta,
            '(-) Impostos': imp_val,
            '3. Receita Líquida': rec_liq,
            '(-) COGS (Entrega)': cogs_val, '(-) Comissões/Taxas': comissao_val + taxa_val,
            '4. Margem Contribuição': margem,
            '(-) Folha + Encargos': folha_tot, '(-) Mkt + Fixos': s['mkt'] + s['outros'],
            '5. EBITDA': ebitda,
            '(-) Deprec/Amort': deprec_amort, '(+/-) Res. Financeiro': s['fin'],
            '6. Lucro Líquido': lucro,
            '7. Ponto Equilíbrio (R$)': pe_val, 'Fator R (%)': fator_r,
            'CAC (R$)': cac, 'LTV (R$)': ltv, 'Payback (Meses)': payback, 'NRR (Estimado)': nrr
        })
        cli = fim
    return pd.DataFrame(dados)

# --- INTERFACE ---
c1, c2 = st.columns([0.5, 6])
with c1: st.markdown("### 🚀")
with c2: 
    st.markdown("### Vaiontec | Growth & Financial Intelligence")
    st.caption("Strategic Dashboard for CRO/CFO")

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
    with c1: card("Faturamento Mensal", f['2.1 Receita Bruta'], "Projeção Mês 12", "neutral")
    with c2: card("Lucro Líquido", f['6. Lucro Líquido'], f"Margem: {(f['6. Lucro Líquido']/f['2.1 Receita Bruta'])*100:.1f}%" if f['2.1 Receita Bruta']>0 else "0%", "good" if f['6. Lucro Líquido']>0 else "bad")
    with c3: card("Caixa Mínimo (Break-Even)", f['7. Ponto Equilíbrio (R$)'], "Meta para 0x0", "neutral")
    with c4: card("Base de Clientes", int(f['1. Clientes Ativos']), f"Novos: +{int(f['1.1 Novos'])}", "neutral", False)

    c1, c2, c3, c4 = st.columns(4)
    with c1: card("LTV", f['LTV (R$)'], "Lucro Vitalício")
    with c2: card("CAC", f['CAC (R$)'], "Custo Aquisição")
    with c3: card("Payback", f"{f['Payback (Meses)']:.1f} Meses", "Meta < 12", "good" if f['Payback (Meses)']<12 else "bad", False)
    with c4: card("NRR (Retenção)", f"{f['NRR (Estimado)']*100:.1f}%", "Meta > 100%", "good" if f['NRR (Estimado)']>=1 else "bad", False)

    st.markdown("---")
    g1, g2 = st.columns([2, 1])
    with g1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_raw['Mês'], y=df_raw['2.1 Receita Bruta'], name='Fat. Bruto', marker_color='#1f497d'))
        fig.add_trace(go.Scatter(x=df_raw['Mês'], y=df_raw['7. Ponto Equilíbrio (R$)'], name='Break-Even', line=dict(color='#e74c3c', dash='dot')))
        fig.add_trace(go.Scatter(x=df_raw['Mês'], y=df_raw['6. Lucro Líquido'], name='Lucro Líquido', line=dict(color='#2ecc71', width=3)))
        fig.update_layout(template="plotly_white", height=400, margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig_u = go.Figure()
        fig_u.add_trace(go.Bar(name='CAC', x=df_raw['Mês'], y=df_raw['CAC (R$)'], marker_color='#e67e22'))
        fig_u.add_trace(go.Bar(name='LTV', x=df_raw['Mês'], y=df_raw['LTV (R$)'], marker_color='#2980b9'))
        fig_u.update_layout(barmode='group', height=400, margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_u, use_container_width=True)

# --- ABA 2: DRE ---
with tab_dre:
    st.markdown("### 📑 Demonstrativo de Resultados")
    df_dre = df_raw.set_index('Mês').T
    
    ordem = [
        "1. Clientes Ativos", "1.1 Novos", "1.2 Churn (Qtd)", "1.3 Ticket Médio",
        "2. MRR (Recorrente)", "2.1 Receita Bruta",
        "(-) Impostos", "3. Receita Líquida",
        "(-) COGS (Entrega)", "(-) Comissões/Taxas",
        "4. Margem Contribuição",
        "(-) Folha + Encargos", "(-) Mkt + Fixos",
        "5. EBITDA",
        "(-) Deprec/Amort", "(+/-) Res. Financeiro",
        "6. Lucro Líquido",
        "7. Ponto Equilíbrio (R$)", "Fator R (%)",
        "CAC (R$)", "LTV (R$)", "Payback (Meses)", "NRR (Estimado)"
    ]
    df_dre = df_dre.reindex(ordem)
    
    def fmt(val, idx):
        if pd.isna(val): return "-"
        if any(x in idx for x in ['%', 'NRR', 'Fator']): return f"{val*100:.1f}%"
        if any(x in idx for x in ['Clientes', 'Novos', 'Churn']): return f"{int(val)}"
        if 'Meses' in idx: return f"{val:.1f}"
        return f"R$ {val:,.2f}"

    df_disp = df_dre.copy()
    for col in df_disp.columns:
        df_disp[col] = [fmt(v, i) for i, v in zip(df_disp.index, df_disp[col])]

    st.dataframe(df_disp, use_container_width=True, height=800)
    st.download_button("📥 Baixar DRE (.csv)", df_disp.to_csv().encode('utf-8'), "DRE_Vaiontec.csv", "text/csv")

# --- ABA 3: INPUTS ---
with tab_input:
    # HELPER DE INPUT VISUAL
    def input_box(key, label, desc, fmt="%.2f", step=0.01, min_val=0.0):
        st.markdown(f"""
        <div class='input-card'>
            <div class='input-title'>{label}</div>
            <div class='input-desc'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        # min_val=0.0 para aceitar zero. key=key para binding.
        st.number_input(label, key=key, format=fmt, step=step, min_value=min_val, label_visibility="collapsed")

    modo = st.radio("Método:", ["📝 Edição Manual", "📂 Upload Padrão"], horizontal=True)
    st.markdown("---")

    if modo == "📂 Upload Padrão":
        c1, c2 = st.columns(2)
        with c1:
            st.info("Baixe a planilha com seus dados atuais, edite no Excel e suba novamente.")
            df_tmpl = gerar_template_csv()
            st.download_button("📥 Baixar Modelo (.csv)", df_tmpl.to_csv(index=False).encode('utf-8'), "modelo_inputs.csv", "text/csv")
        with c2:
            up = st.file_uploader("Upload .csv", type=['csv'])
            if up: processar_upload(pd.read_csv(up))
    else:
        # COLUNA 1: RECEITA & VARIÁVEIS
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown("<div class='input-group-title'>1. Receita (Top Line)</div>", unsafe_allow_html=True)
            input_box('cli_ini', "Clientes Iniciais", "Base ativa no início.", "%.0f", 1.0)
            input_box('cresc', "Crescimento (%)", "Taxa mensal de novos.", "%.2f", 0.01)
            input_box('churn', "Churn (%)", "Taxa mensal de perda.", "%.2f", 0.01)
            input_box('ticket', "Ticket Médio (R$)", "Valor da mensalidade.", "%.2f", 1.0)
            input_box('upsell', "Upsell (%)", "Venda extra na base.", "%.2f", 0.01)

        with c2:
            st.markdown("<div class='input-group-title'>2. Variáveis</div>", unsafe_allow_html=True)
            input_box('imposto', "Imposto Simples (%)", "Alíquota sobre NFs.")
            input_box('cogs', "COGS Unit. (R$)", "Custo Cloud/Licença por cliente.")
            input_box('comissao', "Comissão (%)", "Sobre vendas brutas.")
            input_box('taxa', "Taxa Pagto (%)", "Taxa do Gateway/Boleto.")

        with c3:
            st.markdown("<div class='input-group-title'>3. Fixos & Mkt</div>", unsafe_allow_html=True)
            input_box('mkt', "Budget Mkt (R$)", "Verba fixa de Ads/Mkt.")
            input_box('outros', "Outros Fixos (R$)", "Aluguel, Softwares, etc.")
            input_box('encargos', "Encargos Folha (%)", "FGTS, Férias (Simples ~35%).")

        with c4:
            st.markdown("<div class='input-group-title'>4. Pessoal & Contábil</div>", unsafe_allow_html=True)
            # Folha Detalhada
            with st.expander("Detalhar Salários", expanded=True):
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
            
            input_box('deprec', "Depreciação (R$)", "Perda valor equip.")
            input_box('amort', "Amortização (R$)", "Perda valor software.")
            input_box('fin', "Res. Financ. (R$)", "Juros (-) ou Rend (+).", min_val=None)

# --- ABA 4: GLOSSÁRIO ---
with tab_gloss:
    st.markdown("### 🔍 Knowledge Base")
    search = st.text_input("Pesquisar indicador...", "").lower()
    st.markdown("---")
    
    for item in GLOSSARIO_DB:
        if search in item['termo'].lower() or search in item['conceito'].lower() or search == "":
            st.markdown(f"""
            <div class="glossary-card">
                <div class="glossary-term">{item['termo']} <span class="glossary-cat">{item['categoria']}</span></div>
                <div class="glossary-desc">{item['conceito']}</div>
                <div class="glossary-tip">💡 {item['interpretacao']}</div>
            </div>
            """, unsafe_allow_html=True)
            # FÓRMULA COM ST.LATEX (AQUI ESTAVA O ERRO ANTERIOR)
            st.latex(item['formula'])
