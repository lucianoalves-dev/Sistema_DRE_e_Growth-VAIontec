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
    initial_sidebar_state="collapsed"
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
    's_dev': 'Salário Dev', 'q_dev
