import streamlit as st
import pandas as pd
import io

# 1. Configurações e Login
st.set_page_config(page_title="Faturamento Inove", layout="wide")

def check_password():
    def password_entered():
        if st.session_state["password"] == "Inove2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.title("🔐 Acesso Inove")
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if check_password():
    st.title("📊 Faturamento Inove")
    st.markdown("---")

    # Link com GID da aba Vendas
    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?gid=1866890896&single=true&output=csv"

    @st.cache_data(ttl=5)
    def load_data():
        try:
            # Lê o CSV garantindo que não misture colunas (on_bad_lines)
            df_raw = pd.read_csv(LINK_BASE, on_bad_lines='skip', low_memory=False)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            # Criando DataFrame limpo com os novos cabeçalhos
            df = pd.DataFrame()
            
            # Buscando as colunas específicas para evitar o erro de inversão
            df['Plataforma'] = df_raw['Plataforma'].astype(str).str.strip()
            df['Produto'] = df_raw['ITEM_NOME'].astype(str).str.strip()
            
            # Limpeza rigorosa da Quantidade
            q_raw = df_raw['Quantidade'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Quantidade'] = pd.to_numeric(q_raw, errors='coerce').fillna(0)
            
            # Limpeza rigorosa do Valor (ITEM_VALOR)
            v_raw = df_raw['ITEM_VALOR'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Valor_Total'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            
            # Tratamento da Data de Emissão
            df['Data'] = pd.to_datetime(df_raw['Data de Emissão'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Filtro para remover linhas vazias ou erradas
            df = df[(df['Produto'] != 'nan') & (df['Valor_Total'] > 0)]
            
            return df
        except Exception as e:
            st.error(f"Erro: Certifique-se de que mudou as colunas para ITEM_NOME e ITEM_VALOR. Erro: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- FILTROS ---
        st.sidebar.header("Filtros")
        meses = sorted(df['Mês/Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Mês:", meses, default=meses)
        
        plats = sorted(df['Plataforma'].unique())
        opcoes_plat = ["Todos"] + plats
        plat_sel = st.sidebar.multiselect("Plataforma:", opcoes_plat, default=["Todos"])

        df_f = df[df['Mês/Ano'].isin(mes_sel)].copy()
        if "Todos" not in plat_sel:
            df_f = df_f[df_f['Plataforma'].isin(plat_sel)]

        # --- KPIs ---
        total_f = df_f['Valor_Total'].sum()
        total_q = df_f['Quantidade'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Faturamento Total", f"R$ {total_f:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c2.metric("Itens Vendidos", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio", f"R$ {(total_f/total_q if total_q>0 else 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")

        # --- TABELAS ---
        st.subheader("Vendas por Produto")
        # Agrupamento explícito para o Caderno e Adesivo não trocarem de lugar
        ranking = df_f.groupby('Produto', as_index=False).agg({
            'Quantidade': 'sum',
            'Valor_Total': 'sum'
        }).rename(columns={'Valor_Total': 'Faturamento'})
        
        st.dataframe(ranking.sort_values('Faturamento', ascending=False), use_container_width=True)

        st.subheader("Resumo por Plataforma")
        plat_sum = df_f.groupby('Plataforma', as_index=False)['Valor_Total'].sum().rename(columns={'Valor_Total': 'Faturamento'})
        st.dataframe(plat_sum.sort_values('Faturamento', ascending=False), use_container_width=True)

    else:
        st.warning("Verifique se as colunas no Sheets são ITEM_NOME e ITEM_VALOR.")
