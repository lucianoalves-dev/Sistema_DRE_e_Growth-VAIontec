import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Financeiro Vaiontec", layout="wide", page_icon="📈")

# --- CSS PARA ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1f497d; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #e6f3ff; border-bottom: 2px solid #1f497d; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE CÁLCULO ---
def calcular_dre(premissas, staff):
    meses = list(range(1, 13))
    dados = []
    
    clientes_atual = premissas['clientes_iniciais']
    
    # Custo Base da Folha (Salário x Quantidade)
    custo_folha_base = sum([c['salario'] * c['qtd'] for c in staff])

    for m in meses:
        # 1. Growth
        novos = int(clientes_atual * premissas['crescimento'])
        churn = int(clientes_atual * premissas['churn_rate'])
        clientes_fim = clientes_atual + novos - churn
        
        # 2. Receita
        rec_base = clientes_fim * premissas['ticket']
        upsell = rec_base * premissas['upsell']
        rec_bruta = rec_base + upsell
        
        # 3. Deduções
        impostos = rec_bruta * premissas['imposto_simples']
        rec_liq = rec_bruta - impostos
        
        # 4. COGS (Custo de Entrega)
        # Antiga "Infraestrutura". Agora reflete custo direto por cliente.
        cogs_total = clientes_fim * premissas['cogs_unitario'] 
        
        # 5. Custos Variáveis de Venda
        comissoes = rec_bruta * premissas['comissao']
        taxas_pagto = rec_bruta * premissas['taxa_pgto']
        
        # 6. Margem de Contribuição
        custos_var_total = cogs_total + comissoes + taxas_pagto
        margem_cont = rec_liq - custos_var_total
        
        # 7. Despesas Fixas (OpEx)
        encargos = custo_folha_base * premissas['encargos_pct']
        total_folha_encargos = custo_folha_base + encargos
        despesas_fixas = total_folha_encargos + premissas['mkt'] + premissas['outras_fixas']
        
        # 8. Resultados Operacionais
        ebitda = margem_cont - despesas_fixas
        deprec_amort = premissas['depreciacao'] + premissas['amortizacao']
        res_fin = premissas['res_financeiro']
        
        # 9. Resultado Final
        lair = ebitda - deprec_amort + res_fin
        irpj_extra = lair * premissas['irpj_extra'] if lair > 0 else 0
        lucro_liq = lair - irpj_extra
        
        # 10. KPIs Avançados
        
        # Ponto de Equilíbrio (R$)
        # Soma de todos os custos que não variam diretamente com a venda unitária imediata
        custos_estrutura_total = despesas_fixas + deprec_amort - res_fin
        margem_pct = (margem_cont / rec_bruta) if rec_bruta > 0 else 0
        pe_receita = custos_estrutura_total / margem_pct if margem_pct > 0 else 0
        
        # Fator R
        fator_r = (custo_folha_base + encargos) / rec_bruta if rec_bruta > 0 else 0

        # CAC e LTV
        cac = (premissas['mkt'] + comissoes) / novos if novos > 0 else 0
        ltv = (premissas['ticket'] * (margem_cont/rec_liq)) / premissas['churn_rate'] if premissas['churn_rate'] > 0 else 0
        payback = cac / (premissas['ticket'] * (margem_cont/rec_liq)) if (premissas['ticket'] * (margem_cont/rec_liq)) > 0 else 0

        registro = {
            'Mês': f'Mês {m}',
            'Clientes Ativos': clientes_fim,
            'Novos': novos,
            'Receita Bruta': rec_bruta,
            'Receita Líquida': rec_liq,
            'COGS (Entrega)': cogs_total,
            'Margem Contrib.': margem_cont,
            'EBITDA': ebitda,
            'Lucro Líquido': lucro_liq,
            'Ponto Equilíbrio (R$)': pe_receita,
            'Fator R': fator_r,
            'CAC': cac,
            'LTV': ltv,
            'Payback (Meses)': payback
        }
        dados.append(registro)
        clientes_atual = clientes_fim # Atualiza loop
        
    return pd.DataFrame(dados)

# --- BARRA LATERAL (INPUTS) ---
with st.sidebar:
    st.title("⚙️ Configurações")
    modo_input = st.radio("Fonte de Dados:", ["Simulação Manual", "Upload CSV"], horizontal=True)
    
    premissas = {}
    staff = []
    
    if modo_input == "Simulação Manual":
        with st.expander("1. Vendas & Growth", expanded=True):
            premissas['clientes_iniciais'] = st.number_input("Clientes Iniciais", value=50)
            premissas['crescimento'] = st.number_input("Cresc. Mensal (%)", 0.0, 1.0, 0.10, format="%.2f")
            premissas['churn_rate'] = st.number_input("Churn Rate (%)", 0.0, 1.0, 0.03, format="%.2f")
            premissas['ticket'] = st.number_input("Ticket Médio (R$)", value=500.0)
            premissas['upsell'] = st.number_input("Upsell (% da Rec.)", 0.0, 1.0, 0.05)
        
        with st.expander("2. Custos Variáveis (COGS/Impostos)", expanded=False):
            st.info("💡 **COGS:** Custo direto para entregar o serviço (Cloud, API, Licenças).")
            premissas['cogs_unitario'] = st.number_input("COGS Unitário (por Cliente)", value=30.0)
            premissas['comissao'] = st.number_input("Comissão Vendas (%)", 0.0, 1.0, 0.05)
            premissas['taxa_pgto'] = st.number_input("Taxa Meios Pagto (%)", 0.0, 1.0, 0.02)
            premissas['imposto_simples'] = st.number_input("Simples Nacional (%)", 0.0, 1.0, 0.06)
        
        with st.expander("3. Despesas Fixas & Mkt", expanded=False):
            premissas['mkt'] = st.number_input("Marketing/Ads (R$)", value=5000.0)
            premissas['outras_fixas'] = st.number_input("Outros Fixos (Aluguel, etc)", value=3000.0)
            premissas['encargos_pct'] = st.number_input("Encargos Folha (%)", 0.0, 1.0, 0.35)
            
        with st.expander("4. Contábil & Financeiro", expanded=False):
            premissas['depreciacao'] = st.number_input("Depreciação Mensal", value=400.0)
            premissas['amortizacao'] = st.number_input("Amortização Mensal", value=600.0)
            premissas['res_financeiro'] = st.number_input("Resultado Financeiro (+/-)", value=0.0)
            premissas['irpj_extra'] = st.number_input("IRPJ Extra (Se não for Simples)", 0.0, 1.0, 0.0)
            
        with st.expander("5. Quadro de Funcionários (Folha)", expanded=False):
            st.caption("Insira salários unitários e quantidade")
            c1, c2 = st.columns(2)
            with c1:
                sal_socio = st.number_input("Pró-Labore Sócio", value=8000.0)
                sal_dev = st.number_input("Salário Dev", value=5000.0)
                sal_cs = st.number_input("Salário Suporte", value=2500.0)
                sal_vendas = st.number_input("Salário Vendas", value=3000.0)
            with c2:
                qtd_socio = st.number_input("Qtd Sócios", value=2, step=1)
                qtd_dev = st.number_input("Qtd Devs", value=2, step=1)
                qtd_cs = st.number_input("Qtd Suporte", value=1, step=1)
                qtd_vendas = st.number_input("Qtd Vendas", value=1, step=1)
            
            staff = [
                {'salario': sal_socio, 'qtd': qtd_socio},
                {'salario': sal_dev, 'qtd': qtd_dev},
                {'salario': sal_cs, 'qtd': qtd_cs},
                {'salario': sal_vendas, 'qtd': qtd_vendas},
            ]
    else:
        st.info("Para usar upload, envie um arquivo CSV com as colunas: 'parametro' e 'valor'.")
        uploaded_file = st.file_uploader("Arquivo de Premissas", type="csv")
        if uploaded_file is None:
            st.warning("Aguardando arquivo. Usando dados padrão para visualização.")
            # Mock de dados para não quebrar a tela sem arquivo
            # (Em um app real, aqui entraria o parser do CSV)
            # Replicando defaults apenas para rodar
            premissas = {'clientes_iniciais':50, 'crescimento':0.1, 'churn_rate':0.03, 'ticket':500, 'upsell':0.05,
                         'cogs_unitario':30, 'comissao':0.05, 'taxa_pgto':0.02, 'imposto_simples':0.06,
                         'mkt':5000, 'outras_fixas':3000, 'encargos_pct':0.35, 'depreciacao':400,
                         'amortizacao':600, 'res_financeiro':0, 'irpj_extra':0}
            staff = [{'salario':26500, 'qtd':1}] # Soma simplificada

# --- PROCESSAMENTO ---
df = calcular_dre(premissas, staff)
mes_final = df.iloc[-1]

# --- DASHBOARD PRINCIPAL ---
st.title("🚀 Sistema de Gestão Financeira - VAIONTEC")

# TAB SYSTEM
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & KPIs", "📋 DRE Detalhado", "🎓 Glossário & Fórmulas"])

with tab1:
    # CARTÕES DE TOPO
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Mensal (Mês 12)", f"R$ {mes_final['Receita Bruta']:,.2f}", f"{premissas['crescimento']*100:.0f}% Growth")
    
    cor_lucro = "normal" if mes_final['Lucro Líquido'] > 0 else "inverse"
    col2.metric("Lucro Líquido (Mês 12)", f"R$ {mes_final['Lucro Líquido']:,.2f}", delta_color=cor_lucro)
    
    col3.metric("Clientes Ativos", int(mes_final['Clientes Ativos']), f"-{premissas['churn_rate']*100:.1f}% Churn")
    
    status_fator_r = "✅ Anexo III" if mes_final['Fator R'] >= 0.28 else "⚠️ Anexo V (Caro)"
    col4.metric("Fator R (Imposto)", f"{mes_final['Fator R']*100:.1f}%", status_fator_r)

    st.markdown("---")
    
    # GRÁFICO 1: PONTO DE EQUILÍBRIO
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🏁 Corrida para o Ponto de Equilíbrio")
        fig_be = go.Figure()
        fig_be.add_trace(go.Scatter(x=df['Mês'], y=df['Receita Bruta'], name='Receita Bruta', 
                                    line=dict(color='#00CC96', width=4)))
        fig_be.add_trace(go.Scatter(x=df['Mês'], y=df['Ponto Equilíbrio (R$)'], name='Ponto de Equilíbrio', 
                                    line=dict(color='#EF553B', dash='dot', width=2)))
        fig_be.update_layout(height=400, template="plotly_white", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_be, use_container_width=True)
    
    with c2:
        st.subheader("💰 Distribuição (Mês 12)")
        labels = ['COGS (Entrega)', 'Impostos', 'Despesas Op.', 'Lucro Líquido']
        values = [mes_final['COGS (Entrega)'], 
                  mes_final['Receita Bruta']*premissas['imposto_simples'],
                  (mes_final['Receita Líquida'] - mes_final['Lucro Líquido'] - mes_final['COGS (Entrega)']),
                  max(0, mes_final['Lucro Líquido'])]
        fig_pie = px.pie(values=values, names=labels, hole=0.4)
        fig_pie.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # GRÁFICO 2: GROWTH
    st.subheader("📈 Eficiência de Growth (CAC vs LTV)")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Bar(x=df['Mês'], y=df['LTV'], name='LTV (Valor Vitalício)', marker_color='#636EFA'))
        fig_growth.add_trace(go.Bar(x=df['Mês'], y=df['CAC'], name='CAC (Custo Aquisição)', marker_color='#FFA15A'))
        fig_growth.update_layout(barmode='group', height=350, template="plotly_white")
        st.plotly_chart(fig_growth, use_container_width=True)
    
    with col_g2:
        st.info(f"**Análise Mês 12:**\n\nPara cada R$ 1,00 investido em adquirir um cliente (CAC), ele retorna **R$ {mes_final['LTV']/mes_final['CAC']:.2f}** ao longo da vida (LTV).\n\nO cliente demora **{mes_final['Payback (Meses)']:.1f} meses** para 'se pagar' (Payback).")

with tab2:
    st.subheader("Demonstrativo de Resultados do Exercício (DRE)")
    
    # Formatando para exibição em Tabela
    df_display = df.copy()
    format_money = lambda x: f"R$ {x:,.2f}"
    format_pct = lambda x: f"{x*100:.1f}%"
    
    cols_money = ['Receita Bruta', 'Receita Líquida', 'COGS (Entrega)', 'Margem Contrib.', 'EBITDA', 'Lucro Líquido', 'Ponto Equilíbrio (R$)', 'CAC', 'LTV']
    for col in cols_money:
        df_display[col] = df_display[col].apply(format_money)
    
    df_display['Fator R'] = df_display['Fator R'].apply(format_pct)
    
    st.dataframe(df_display, use_container_width=True, height=600)
    
    # Botão de Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar DRE em Excel/CSV", data=csv, file_name="DRE_Vaiontec_Sistema.csv", mime="text/csv")

with tab3:
    st.header("🎓 Glossário e Metodologia de Cálculo")
    
    st.markdown("""
    ### 1. COGS (Cost of Goods Sold / Custo dos Serviços Prestados)
    **Antiga nomenclatura:** *Infraestrutura / Custos Variáveis*
    
    **O que é:** Representa o custo direto para "entregar" o software ao cliente. Se você não vendesse nada, esse custo seria zero.
    
    **Composição na Vaiontec:**
    * 📡 **Infraestrutura Cloud:** AWS/Azure/Google Cloud (Servidores que escalam com uso).
    * 🔑 **Licenças Embarcadas:** APIs pagas por chamada, Banco de Dados, Ferramentas de terceiro por usuário.
    * 👷 **Hora Técnica Variável:** Se houvesse setup manual por cliente.
    
    **Fórmula no Sistema:**
    $$
    \\text{COGS Total} = \\text{Clientes Ativos} \\times \\text{Custo Unitário (Input)}
    $$
    
    ---
    
    ### 2. Ponto de Equilíbrio (Break-Even Point)
    **O que é:** O valor exato de faturamento necessário para cobrir todos os custos e despesas. É o momento onde o Lucro = 0.
    
    **Por que é vital?** Abaixo deste valor, a Vaiontec "queima caixa". Acima dele, gera riqueza.
    
    **Fórmula:**
    $$
    PE (R\$) = \\frac{\\text{Despesas Fixas} + \\text{Folha} + \\text{Depreciação} - \\text{Res. Financeiro}}{\\text{Margem de Contribuição (\%)}}
    $$
    
    ---
    
    ### 3. Fator R (Simples Nacional)
    **O que é:** Uma regra da Receita Federal para empresas de tecnologia no Simples.
    
    **A Regra de Ouro:**
    * Se a Folha de Pagamento for **menor que 28%** do Faturamento -> Você paga **Anexo V (começa em ~15.5%)**. 💸
    * Se a Folha for **maior que 28%** do Faturamento -> Você paga **Anexo III (começa em ~6%)**. 💰
    
    **Estratégia:** Aumentamos o Pró-labore dos sócios na simulação para garantir que você fique no Anexo III.
    
    ---
    
    ### 4. LTV vs CAC (A "Máquina de Vendas")
    **CAC (Custo de Aquisição):** Quanto gasto de Marketing + Comissão para trazer 1 cliente.
    **LTV (Valor Vitalício):** Quanto lucro esse cliente deixa antes de cancelar (Churn).
    
    **Fórmula LTV:**
    $$
    LTV = \\frac{\\text{Ticket Médio} \\times \\text{Margem Contribuição \%}}{\\text{Churn Rate \%}}
    $$
    
    **Meta de Mercado:** O LTV deve ser pelo menos **3x maior** que o CAC.
    """)
