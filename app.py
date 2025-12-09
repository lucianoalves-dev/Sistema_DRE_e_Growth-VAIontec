import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Vaiontec Financial Suite", layout="wide", page_icon="💎")

# --- ESTILIZAÇÃO CSS (DESIGN SYSTEM BLUE) ---
st.markdown("""
    <style>
    /* Fundo e Fontes */
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1f497d; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Cartões de Métricas (KPI Cards) */
    div.css-1r6slb0 { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    
    /* Estilo Personalizado para Métricas */
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #1f497d; /* Azul Vaiontec */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .kpi-title { font-size: 14px; color: #666; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; }
    .kpi-value { font-size: 28px; color: #1f497d; font-weight: 700; margin: 5px 0; }
    .kpi-delta { font-size: 12px; color: #28a745; font-weight: 600; }
    .kpi-delta.neg { color: #dc3545; }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 4px; color: #1f497d; border: 1px solid #e1e4e8; }
    .stTabs [aria-selected="true"] { background-color: #1f497d; color: white; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #f0f4f8; border-right: 1px solid #d1d9e6; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE CÁLCULO ---
def calcular_dre_completo(p, staff):
    meses = list(range(1, 13))
    dados = []
    
    clientes_atual = p['clientes_iniciais']
    custo_folha_base = sum([c['salario'] * c['qtd'] for c in staff])
    
    # NRR Estimado (Projeção): 1 + Upsell - Churn
    nrr_projetado = (1 + p['upsell'] - p['churn_rate'])

    for m in meses:
        # 1. Base de Clientes
        novos = int(clientes_atual * p['crescimento'])
        perda = int(clientes_atual * p['churn_rate'])
        clientes_fim = clientes_atual + novos - perda
        
        # 2. Receita (Top Line)
        mrr_base = clientes_fim * p['ticket'] # Receita Recorrente Mensal
        expansao = mrr_base * p['upsell']
        receita_bruta = mrr_base + expansao
        arr = receita_bruta * 12 # Annual Recurring Revenue (Run Rate)
        
        # 3. Deduções
        impostos = receita_bruta * p['imposto_simples']
        receita_liq = receita_bruta - impostos
        
        # 4. Custos Variáveis (COGS + Vendas)
        cogs = clientes_fim * p['cogs_unitario'] # Custo do Serviço (Infra/Licenças)
        comissoes = receita_bruta * p['comissao']
        taxas_pg = receita_bruta * p['taxa_pgto']
        custos_var_total = cogs + comissoes + taxas_pg
        
        # 5. Margem de Contribuição
        margem_cont = receita_liq - custos_var_total
        margem_cont_pct = (margem_cont / receita_liq) if receita_liq > 0 else 0
        
        # 6. Despesas Fixas (OpEx)
        encargos = custo_folha_base * p['encargos_pct']
        folha_total = custo_folha_base + encargos
        despesas_operacionais = folha_total + p['mkt'] + p['outras_fixas']
        
        # 7. EBITDA (Lucro Operacional de Caixa)
        ebitda = margem_cont - despesas_operacionais
        ebitda_margem = (ebitda / receita_liq) if receita_liq > 0 else 0
        
        # 8. Abaixo do EBITDA
        deprec_amort = p['depreciacao'] + p['amortizacao']
        ebit = ebitda - deprec_amort
        
        # Financeiro e Imposto s/ Lucro
        res_fin = p['res_financeiro']
        lair = ebit + res_fin
        irpj_csll = lair * p['irpj_extra'] if lair > 0 else 0 # 0 no Simples
        
        lucro_liq = lair - irpj_csll
        margem_liq = (lucro_liq / receita_liq) if receita_liq > 0 else 0
        
        # 9. KPIs Específicos
        
        # Fator R
        fator_r = folha_total / receita_bruta if receita_bruta > 0 else 0
        
        # Ponto de Equilíbrio (Break-Even)
        custos_fixos_totais = despesas_operacionais + deprec_amort - res_fin
        margem_bruta_pct = (margem_cont / receita_bruta) if receita_bruta > 0 else 0
        pe_receita = custos_fixos_totais / margem_bruta_pct if margem_bruta_pct > 0 else 0
        
        # Unit Economics
        cac = (p['mkt'] + comissoes) / novos if novos > 0 else 0
        ltv = (p['ticket'] * margem_cont_pct) / p['churn_rate'] if p['churn_rate'] > 0 else 0
        payback = cac / (p['ticket'] * margem_cont_pct) if (p['ticket'] * margem_cont_pct) > 0 else 0

        dados.append({
            'Mês': f'Mês {m}',
            'Clientes': clientes_fim,
            'Novos': novos,
            'Churn': perda,
            'MRR (Recorrente)': mrr_base,
            'Receita Bruta': receita_bruta,
            'Receita Líquida': receita_liq,
            'COGS': cogs,
            'Margem Contribuição ($)': margem_cont,
            'Margem Contribuição (%)': margem_cont_pct,
            'EBITDA': ebitda,
            'EBITDA (%)': ebitda_margem,
            'Lucro Líquido': lucro_liq,
            'Margem Líquida (%)': margem_liq,
            'Fator R': fator_r,
            'Ponto Equilíbrio (R$)': pe_receita,
            'CAC': cac,
            'LTV': ltv,
            'NRR Estimado': nrr_projetado,
            'Folha Total': folha_total
        })
        
        clientes_atual = clientes_fim
        
    return pd.DataFrame(dados)

# --- COMPONENTE DE CARTÃO KPI (HTML PURO) ---
def kpi_card(title, value, subtitle="", is_money=True, color="blue"):
    val_str = f"R$ {value:,.2f}" if is_money else f"{value}"
    
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{val_str}</div>
        <div class="kpi-delta">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR (CONFIGURAÇÕES) ---
with st.sidebar:
    st.title("🔧 Configurações")
    st.markdown("---")
    
    with st.expander("1. Growth & Receita (CRO)", expanded=True):
        p_clientes = st.number_input("Clientes Iniciais", value=50)
        p_crescimento = st.number_input("Cresc. Mensal (%)", value=0.10, step=0.01)
        p_churn = st.number_input("Churn Rate (%)", value=0.03, step=0.01)
        p_ticket = st.number_input("Ticket Médio (R$)", value=500.0)
        p_upsell = st.number_input("Upsell (% MRR)", value=0.05, step=0.01)

    with st.expander("2. Custos & Tributos (CFO)", expanded=False):
        p_cogs = st.number_input("COGS Unitário (Infra/Lic)", value=30.0, help="Custo direto de entrega por cliente")
        p_comissao = st.number_input("Comissão Vendas (%)", value=0.05, step=0.01)
        p_imposto = st.number_input("Simples Nacional (%)", value=0.06, step=0.01)
        p_taxa = st.number_input("Taxa Meios Pagto (%)", value=0.02, step=0.01)
        p_mkt = st.number_input("Verba Marketing (CAC)", value=5000.0)
        p_outros = st.number_input("Outros Fixos (Aluguel)", value=3000.0)
        
    with st.expander("3. Pessoal (Folha)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            s_socio = st.number_input("Pró-Labore Sócio", 8000.0)
            s_dev = st.number_input("Sal. Dev", 5000.0)
            s_cs = st.number_input("Sal. Suporte", 2500.0)
            s_venda = st.number_input("Sal. Vendas", 3000.0)
        with col2:
            # CORREÇÃO AQUI: Adicionado key unique para evitar DuplicateElementId
            q_socio = st.number_input("Qtd", 2, key="q_socio")
            q_dev = st.number_input("Qtd", 2, key="q_dev")
            q_cs = st.number_input("Qtd", 1, key="q_cs")
            q_venda = st.number_input("Qtd", 1, key="q_venda")
            
        p_encargos = st.number_input("Encargos (%)", value=0.35, step=0.01)
        
    with st.expander("4. Contábil", expanded=False):
        p_deprec = st.number_input("Depreciação", 400.0)
        p_amort = st.number_input("Amortização", 600.0)
        p_fin = st.number_input("Res. Financeiro", 0.0)
        p_irpj = st.number_input("IRPJ Extra", 0.0)

    # Monta Dicionário e Staff
    premissas = {
        'clientes_iniciais': p_clientes, 'crescimento': p_crescimento, 'churn_rate': p_churn,
        'ticket': p_ticket, 'upsell': p_upsell, 'cogs_unitario': p_cogs, 'comissao': p_comissao,
        'imposto_simples': p_imposto, 'taxa_pgto': p_taxa, 'mkt': p_mkt, 'outras_fixas': p_outros,
        'encargos_pct': p_encargos, 'depreciacao': p_deprec, 'amortizacao': p_amort,
        'res_financeiro': p_fin, 'irpj_extra': p_irpj
    }
    staff_list = [
        {'salario': s_socio, 'qtd': q_socio}, {'salario': s_dev, 'qtd': q_dev},
        {'salario': s_cs, 'qtd': q_cs}, {'salario': s_venda, 'qtd': q_venda}
    ]

# --- CÁLCULO ---
df = calcular_dre_completo(premissas, staff_list)
final = df.iloc[-1] # Mês 12

# --- DASHBOARD (MAIN) ---
st.title("Vaiontec | Executive Dashboard")
st.markdown(f"**Visão Projetada (Mês 12)** • Clientes Ativos: **{int(final['Clientes'])}**")

tab1, tab2, tab3 = st.tabs(["📊 Visão Estratégica (CRO/CFO)", "📑 DRE Detalhado", "📚 Glossário Financeiro"])

with tab1:
    # LINHA 1: TOP LINE & BOTTOM LINE
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("MRR (Receita Mensal)", final['Receita Bruta'], f"ARR: R$ {final['Receita Bruta']*12:,.0f}")
    with col2:
        kpi_card("EBITDA", final['EBITDA'], f"Margem: {final['EBITDA (%)']*100:.1f}%")
    with col3:
        cor_status = "✅ Lucro" if final['Lucro Líquido'] > 0 else "🔻 Prejuízo"
        kpi_card("Lucro Líquido", final['Lucro Líquido'], cor_status)
    with col4:
        # Cash Runway ou Ponto de Equilibrio
        kpi_card("Ponto de Equilíbrio", final['Ponto Equilíbrio (R$)'], "Necessário para 0x0")

    st.markdown("---")

    # LINHA 2: UNIT ECONOMICS & GROWTH
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        kpi_card("LTV (Valor Cliente)", final['LTV'])
    with col_b:
        kpi_card("CAC (Custo Aquisição)", final['CAC'])
    with col_c:
        razao = final['LTV']/final['CAC'] if final['CAC'] > 0 else 0
        kpi_card("LTV / CAC", razao, "Meta > 3.0x", is_money=False)
    with col_d:
        kpi_card("NRR (Retenção)", f"{final['NRR Estimado']*100:.1f}%", "Meta > 100%", is_money=False)

    st.markdown("---")

    # LINHA 3: GRÁFICOS
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Análise de Resultado (Waterfall)")
        # Gráfico de Barras Empilhadas ou Linhas
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['Receita Bruta'], name='Receita Bruta', line=dict(color='#1f497d', width=3)))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['EBITDA'], name='EBITDA', line=dict(color='#28a745', width=3)))
        fig.add_trace(go.Scatter(x=df['Mês'], y=df['Ponto Equilíbrio (R$)'], name='Ponto de Equilíbrio', line=dict(color='#dc3545', dash='dot')))
        fig.update_layout(template="plotly_white", height=400, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("Folha vs Receita")
        # Indicador de Fator R
        fator_r_pct = final['Fator R']*100
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fator_r_pct,
            title = {'text': "Fator R (Meta > 28%)"},
            gauge = {
                'axis': {'range': [0, 50]},
                'bar': {'color': "#1f497d"},
                'steps': [
                    {'range': [0, 28], 'color': "#ffc7ce"},
                    {'range': [28, 50], 'color': "#c6efce"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 28}}))
        fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

with tab2:
    st.markdown("### 📑 Demonstrativo de Resultados do Exercício (DRE)")
    
    # Preparar DataFrame para visualização bonita
    df_vis = df.copy()
    
    # Formatar colunas monetárias
    cols_money = ['MRR (Recorrente)', 'Receita Bruta', 'Receita Líquida', 'COGS', 'Margem Contribuição ($)', 'EBITDA', 'Lucro Líquido', 'Ponto Equilíbrio (R$)', 'Folha Total']
    for c in cols_money:
        df_vis[c] = df_vis[c].apply(lambda x: f"R$ {x:,.2f}")
        
    # Formatar percentuais
    cols_pct = ['Margem Contribuição (%)', 'EBITDA (%)', 'Margem Líquida (%)', 'NRR Estimado', 'Fator R']
    for c in cols_pct:
        df_vis[c] = df_vis[c].apply(lambda x: f"{x*100:.1f}%")
        
    # Exibir tabela interativa
    st.dataframe(df_vis, use_container_width=True, height=600)
    
    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Planilha Completa (Excel/CSV)", data=csv, file_name="DRE_Vaiontec_Executive.csv", mime="text/csv")

with tab3:
    st.markdown("""
    ### 📘 Glossário Avançado (SaaS & Finanças)
    
    #### 1. Métricas de Receita (Top Line)
    * **MRR (Monthly Recurring Revenue):** Receita recorrente mensal. É o "coração" do SaaS. 
    * **ARR (Annual Recurring Revenue):** MRR x 12. Mostra o tamanho anualizado da empresa.
    * **NRR (Net Revenue Retention):** A métrica mais importante para Valuation. 
        * *Fórmula:* `(Receita Base + Expansão - Churn) / Receita Base`. 
        * *Meta:* > 100% (significa que a empresa cresce mesmo sem vender para novos clientes).
    
    #### 2. Margens e Lucratividade
    * **COGS (Cost of Goods Sold):** Custos diretos de entrega (Servidor, Licença, Suporte N1).
    * **Margem de Contribuição:** `Receita Líquida - (COGS + Impostos Variáveis + Comissões)`. É quanto sobra para pagar a estrutura fixa.
    * **EBITDA (LAJIDA):** Lucro Operacional antes de Juros, Impostos, Depreciação e Amortização. É o melhor indicador de geração de caixa operacional.
    * **EBIT (LAJIR):** EBITDA descontando a Depreciação (computadores) e Amortização (software desenvolvido).
    
    #### 3. Eficiência (Unit Economics)
    * **CAC:** Custo para adquirir 1 cliente (Marketing + Vendas).
    * **LTV:** Lucro bruto que 1 cliente deixa na vida toda.
    * **LTV/CAC:** O "Santo Graal". Se for < 1, você perde dinheiro vendendo. O ideal é > 3.
    * **Ponto de Equilíbrio (Break-Even):** Faturamento necessário para Lucro Líquido = 0.
    
    #### 4. Tributário
    * **Fator R:** Razão entre Folha de Pagamento e Faturamento.
        * Se Folha > 28% da Receita -> Anexo III (Imposto Reduzido).
        * Se Folha < 28% da Receita -> Anexo V (Imposto Alto).
        * *O sistema monitora isso automaticamente no gráfico de "velocímetro".*
    """)
