import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Vaiontec | CFO Suite", layout="wide", page_icon="💎", initial_sidebar_state="collapsed")

# --- 2. CSS (HÍBRIDO: CORPORATE + GLOSSARY STYLE) ---
st.markdown("""
    <style>
        /* TEMA GERAL */
        [data-testid="stAppViewContainer"] { background-color: #f4f7f6; color: #0f2a4a; }
        [data-testid="stHeader"] { background-color: transparent; }
        
        /* KPI CARDS */
        .metric-container {
            background-color: white; padding: 18px; border-radius: 8px;
            border-left: 5px solid #1f497d; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-bottom: 10px;
        }
        .metric-label { font-size: 12px; color: #6c757d; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
        .metric-value { font-size: 24px; color: #1f497d; font-weight: 800; margin: 5px 0; }
        .metric-sub { font-size: 12px; font-weight: 500; }
        .sub-good { color: #218838; } .sub-bad { color: #c82333; } .sub-neutral { color: #6c757d; }
        
        /* TABELA DRE */
        [data-testid="stDataFrame"] { width: 100%; }
        
        /* BOTÕES */
        .stButton>button { background-color: #1f497d; color: white; border-radius: 4px; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 1px;}
        .stButton>button:hover { background-color: #163a66; color: white; border-color: #163a66; }
        
        /* ABAS */
        .stTabs [data-baseweb="tab-list"] { gap: 5px; border-bottom: 2px solid #e9ecef; }
        .stTabs [data-baseweb="tab"] { background-color: white; border-radius: 4px 4px 0 0; padding: 10px 20px; color: #495057; border: 1px solid #e9ecef; border-bottom: none; }
        .stTabs [aria-selected="true"] { background-color: #1f497d !important; color: white !important; }
        
        /* GLOSSÁRIO (VERSÃO DETALHADA RESTAURADA) */
        .glossary-card { 
            background-color: white; 
            padding: 25px; 
            border-radius: 8px; 
            border-left: 5px solid #2980b9;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 20px; 
        }
        .glossary-term { color: #1f497d; font-size: 20px; font-weight: 800; margin-bottom: 5px;}
        .glossary-cat { background-color: #eef2f7; color: #555; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
        .glossary-desc { color: #444; font-size: 16px; margin-top: 10px; line-height: 1.6; }
        .glossary-tip { background-color: #fff8e1; color: #856404; padding: 10px; border-radius: 4px; margin-top: 15px; font-size: 14px; border: 1px solid #ffeeba; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DADOS DO GLOSSÁRIO (HUMANIZADO - RESTAURADO) ---
GLOSSARIO_DB = [
    {
        "termo": "MRR (Receita Recorrente Mensal)",
        "categoria": "Receita",
        "conceito": "É a soma de todas as assinaturas ativas que você recebe todo mês. É o 'salário' da empresa.",
        "formula": r"\text{Clientes Ativos} \times \text{Valor da Assinatura}",
        "interpretacao": "Se o gráfico do MRR aponta para cima, a empresa está saudável. Se aponta para baixo, você está perdendo clientes mais rápido do que ganha."
    },
    {
        "termo": "ARR (Receita Recorrente Anual)",
        "categoria": "Receita",
        "conceito": "É uma projeção simples: se você não vendesse mais nada e ninguém cancelasse, quanto faturaria em um ano?",
        "formula": r"\text{MRR} \times 12 \text{ Meses}",
        "interpretacao": "Investidores amam esse número. Uma startup de SaaS geralmente é vendida por um múltiplo desse valor (ex: 'Valemos 5 vezes o nosso ARR')."
    },
    {
        "termo": "NRR (Retenção Líquida de Receita)",
        "categoria": "Growth",
        "conceito": "Responde à pergunta: 'Da receita que eu tinha mês passado, quanto sobrou?'. Ele desconta quem cancelou e soma quem comprou mais (upsell).",
        "formula": r"\frac{\text{Receita Inicial} + \text{Vendas Extra (Upsell)} - \text{Cancelamentos}}{\text{Receita Inicial}}",
        "interpretacao": "Acima de 100%: Fenomenal. Significa que mesmo se você parar de vender para novos clientes, a empresa cresce sozinha. Abaixo de 100%: Atenção, o balde está furado."
    },
    {
        "termo": "CAC (Custo de Aquisição)",
        "categoria": "Eficiência",
        "conceito": "Quanto dinheiro sai do seu bolso (em anúncios, comissões e salários de vendas) para convencer 1 pessoa a virar cliente.",
        "formula": r"\frac{\text{Gasto Marketing} + \text{Comissões} + \text{Salários Vendas}}{\text{Novos Clientes Conquistados}}",
        "interpretacao": "Se seu cliente paga R$ 500,00 e seu CAC é R$ 2.000,00, você tem um problema de fluxo de caixa, pois ele demora 4 meses só para pagar o custo de entrada."
    },
    {
        "termo": "LTV (Valor Vitalício)",
        "categoria": "Eficiência",
        "conceito": "É o lucro total estimado que um único cliente deixa na empresa desde o dia que entra até o dia que sai.",
        "formula": r"\frac{\text{Ticket Médio} \times \text{Margem de Contribuição \%}}{\text{Taxa de Cancelamento (Churn)}}",
        "interpretacao": "Este número deve ser sempre MUITO maior que o CAC. Se o LTV for baixo, você está pagando caro para trazer clientes que valem pouco."
    },
    {
        "termo": "Relação LTV / CAC",
        "categoria": "Eficiência",
        "conceito": "O termômetro de saúde do crescimento. Mede se vale a pena acelerar o marketing.",
        "formula": r"\frac{\text{LTV (Quanto o cliente rende)}}{\text{CAC (Quanto custa trazer ele)}}",
        "interpretacao": "O número mágico é 3. Significa que a cada R$ 1,00 que você investe em marketing, voltam R$ 3,00 de lucro ao longo do tempo."
    },
    {
        "termo": "Payback (Tempo de Retorno)",
        "categoria": "Eficiência",
        "conceito": "Quantos meses o cliente precisa pagar a mensalidade para 'cobrir' o custo que você teve para trazê-lo (CAC).",
        "formula": r"\frac{\text{Custo de Aquisição (CAC)}}{\text{Ticket Médio} \times \text{Margem de Contribuição}}",
        "interpretacao": "Quanto menor, melhor. Idealmente menos de 12 meses. Se for 18 meses, significa que você financia o cliente por 1 ano e meio antes de ter lucro real."
    },
    {
        "termo": "Churn Rate (Taxa de Cancelamento)",
        "categoria": "Growth",
        "conceito": "A porcentagem da sua base de clientes que decide ir embora todo mês.",
        "formula": r"\frac{\text{Clientes que Cancelaram}}{\text{Total de Clientes no Início do Mês}}",
        "interpretacao": "O inimigo número 1 do SaaS. Um churn de 3% ao mês parece pouco, mas destrói 30% da sua base em um ano."
    },
    {
        "termo": "COGS (Custo do Serviço)",
        "categoria": "Custos",
        "conceito": "Custo direto para o sistema funcionar. Se você tiver zero clientes, esse custo deve ser quase zero.",
        "formula": r"\text{Servidores (AWS)} + \text{Licenças por Usuário} + \text{Equipe de Suporte}",
        "interpretacao": "Não confunda com despesa fixa (aluguel). O COGS sobe junto com as vendas. Manter ele baixo garante que sobra mais dinheiro (Margem) para investir."
    },
    {
        "termo": "Margem de Contribuição",
        "categoria": "Resultados",
        "conceito": "É o dinheiro que sobra 'limpo' de cada venda depois de pagar os impostos e o custo do serviço (COGS).",
        "formula": r"\text{Receita} - (\text{Impostos} + \text{COGS} + \text{Comissões})",
        "interpretacao": "É com esse dinheiro que você paga o aluguel, a luz e o salário da diretoria. Se a margem for negativa, quanto mais você vende, mais prejuízo tem."
    },
    {
        "termo": "Ponto de Equilíbrio (Break-Even)",
        "categoria": "Resultados",
        "conceito": "A meta mínima de faturamento para não ter prejuízo. É o empate: 0x0.",
        "formula": r"\frac{\text{Custos Fixos Totais (Aluguel, Folha, etc)}}{\text{Margem de Contribuição \%}}",
        "interpretacao": "Sua primeira missão no mês é bater essa meta. Tudo que vender acima disso vira lucro líquido."
    },
    {
        "termo": "EBITDA",
        "categoria": "Resultados",
        "conceito": "É o Lucro Operacional bruto. Mostra se a operação da empresa é eficiente, ignorando juros bancários e impostos de renda.",
        "formula": r"\text{Margem de Contribuição} - \text{Despesas Operacionais (OpEx)}",
        "interpretacao": "Se o EBITDA é positivo, o negócio é viável operacionalmente. Se for negativo, a operação queima caixa estruturalmente."
    },
    {
        "termo": "Fator R",
        "categoria": "Tributário",
        "conceito": "Uma 'pegadinha' do governo para empresas de tecnologia no Simples Nacional.",
        "formula": r"\frac{\text{Folha de Pagamento (incluindo Sócios)}}{\text{Faturamento Bruto}}",
        "interpretacao": "Você DEVE manter essa divisão acima de 0,28 (28%). Se cair abaixo disso, seu imposto pula de ~6% para ~15%. Aumente o pró-labore se necessário."
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
        
        # Estrutura preparada para transposição (NOVA ABA DRE)
        dados.append({
            'Mês': m,
            '1. Clientes Ativos': fim, '1.1 Novos': novos, '1.2 Churn (Qtd)': perda,
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
    with c2: card("Lucro Líquido", f['6. Lucro Líquido'], f"Margem: {(f['6. Lucro Líquido']/f['2.1 Receita Bruta Total'])*100:.1f}%", "good" if f['6. Lucro Líquido']>0 else "bad")
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

# --- ABA 2: DRE CORPORATE (MATRIZ TRANSPOSTA) ---
with tab_dre:
    st.markdown("### 📑 Demonstrativo de Resultados (Visão Anual)")
    
    # 1. Prepara os dados para Transpor
    df_dre = df_raw.set_index('Mês').T # Inverte Linha/Coluna
    
    # 2. Definição da Ordem Lógica
    ordem_logica = [
        "1. Clientes Ativos", "1.1 Novos", "1.2 Churn (Qtd)",
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
    
    # Função de formatação linha a linha
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
    st.download_button("📥 Baixar DRE Formatado (.csv)", data=csv, file_name="DRE_Corporate_Vaiontec.csv", mime="text/csv")

# --- ABA 3: INPUTS (RESTAURADA - VERSÃO ORGANIZADA) ---
with tab_input:
    modo = st.radio("Como deseja atualizar?", ["📝 Edição Manual", "📂 Upload de Planilha Padrão"], horizontal=True)
    st.markdown("---")

    if modo == "📂 Upload de Planilha Padrão":
        c1, c2 = st.columns(2)
        with c1:
            st.info("Passo 1: Baixe o modelo atual com os metadados corretos.")
            df_tmpl = gerar_template_csv()
            st.download_button("📥 Baixar Modelo (.csv)", df_tmpl.to_csv(index=False).encode('utf-8'), "modelo.csv", "text/csv")
        with c2:
            st.info("Passo 2: Faça o upload do arquivo preenchido.")
            up = st.file_uploader("Upload .csv", type=['csv'])
            if up: processar_upload(pd.read_csv(up))
    else:
        # LAYOUT RESTAURADO COM METADADOS
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("1. Growth & Vendas")
            st.session_state['cli_ini'] = st.number_input("Clientes Iniciais", value=st.session_state['cli_ini'], help="Número total de clientes ativos.")
            st.session_state['cresc'] = st.number_input("Crescimento Mensal (%)", value=st.session_state['cresc'], format="%.2f", help="Taxa de novos clientes.")
            st.session_state['churn'] = st.number_input("Churn Rate (%)", value=st.session_state['churn'], format="%.2f", help="Taxa de cancelamento.")
            st.session_state['ticket'] = st.number_input("Ticket Médio (R$)", value=st.session_state['ticket'], help="Valor da mensalidade.")
            st.session_state['upsell'] = st.number_input("Upsell (% da Rec.)", value=st.session_state['upsell'], format="%.2f", help="Receita adicional da base.")

            st.subheader("2. Custos Variáveis (COGS)")
            st.session_state['cogs'] = st.number_input("COGS Unitário (R$)", value=st.session_state['cogs'], help="Custo direto por cliente (Cloud).")
            st.session_state['comissao'] = st.number_input("Comissão Vendas (%)", value=st.session_state['comissao'], format="%.2f")
            st.session_state['taxa'] = st.number_input("Taxa Meios Pagto (%)", value=st.session_state['taxa'], format="%.2f")
            st.session_state['imposto'] = st.number_input("Simples Nacional (%)", value=st.session_state['imposto'], format="%.2f")

        with col_b:
            st.subheader("3. Despesas Fixas & Pessoal")
            st.session_state['mkt'] = st.number_input("Marketing (R$)", value=st.session_state['mkt'], help="Budget fixo mensal.")
            st.session_state['outros'] = st.number_input("Outros Fixos (R$)", value=st.session_state['outros'], help="Aluguel, Softwares.")
            
            with st.expander("Detalhamento da Folha (Salários)", expanded=True):
                c_sal, c_qtd = st.columns([2,1])
                with c_sal:
                    st.session_state['s_socio'] = st.number_input("Salário Sócio", st.session_state['s_socio'])
                    st.session_state['s_dev'] = st.number_input("Salário Dev", st.session_state['s_dev'])
                    st.session_state['s_cs'] = st.number_input("Salário CS", st.session_state['s_cs'])
                    st.session_state['s_venda'] = st.number_input("Salário Vendas", st.session_state['s_venda'])
                with c_qtd:
                    st.session_state['q_socio'] = st.number_input("Qtd", st.session_state['q_socio'], key="kq_soc")
                    st.session_state['q_dev'] = st.number_input("Qtd", st.session_state['q_dev'], key="kq_dev")
                    st.session_state['q_cs'] = st.number_input("Qtd", st.session_state['q_cs'], key="kq_cs")
                    st.session_state['q_venda'] = st.number_input("Qtd", st.session_state['q_venda'], key="kq_vnd")
            
            st.session_state['encargos'] = st.number_input("Encargos (%)", value=st.session_state['encargos'], format="%.2f", help="FGTS, Férias, etc.")

            st.subheader("4. Contábil")
            st.session_state['deprec'] = st.number_input("Deprec. (R$)", st.session_state['deprec'])
            st.session_state['amort'] = st.number_input("Amort. (R$)", st.session_state['amort'])
            st.session_state['fin'] = st.number_input("Res. Fin (R$)", st.session_state['fin'])

# --- ABA 4: GLOSSÁRIO (RESTAURADA - HUMANIZADA E DETALHADA) ---
with tab_gloss:
    st.markdown("### 🔍 Pesquisar Conceito")
    search_term = st.text_input("Digite um termo (ex: Lucro, CAC, Churn)", "").lower()
    
    st.markdown("---")
    
    found = False
    for item in GLOSSARIO_DB:
        if search_term in item['termo'].lower() or search_term in item['conceito'].lower() or search_term == "":
            found = True
            st.markdown(f"""
            <div class="glossary-card">
                <div class="glossary-term">{item['termo']} <span class="glossary-cat">{item['categoria']}</span></div>
                <div class="glossary-desc">{item['conceito']}</div>
                <div class="formula-box">{item['formula']}</div>
                <div class="glossary-tip">💡 {item['interpretacao']}</div>
            </div>
            """, unsafe_allow_html=True)
            if 'formula' in item and '\\' in item['formula']: # Renderiza latex se tiver
                 st.latex(item['formula'])
            
    if not found:
        st.warning("Nenhum termo encontrado.")
