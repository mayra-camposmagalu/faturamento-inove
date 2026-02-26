import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Faturamento Inove", layout="wide")

# --- LOGIN ---
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

    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?gid=1866890896&single=true&output=csv"

    @st.cache_data(ttl=5)
    def load_data():
        try:
            # Carrega os dados brutos
            raw_data = pd.read_csv(LINK_BASE, on_bad_lines='warn', low_memory=False)
            raw_data.columns = [str(c).strip() for c in raw_data.columns]

            # Criamos um DataFrame novo e limpo para evitar contaminação de colunas
            df = pd.DataFrame()

            # Mapeamento Direto (Usando os novos nomes do Passo 1)
            df['Canal'] = raw_data['ITEM_CANAL'].astype(str).str.strip()
            df['Produto'] = raw_data['ITEM_PRODUTO'].astype(str).str.strip()
            
            # Limpeza de Quantidade (Tratando 1,0 ou 1.0)
            df['Qtd'] = raw_data['ITEM_QTD'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Qtd'] = pd.to_numeric(df['Qtd'], errors='coerce').fillna(0)
            
            # Limpeza de Valor (Tratando R$ 1.000,00)
            v_raw = raw_data['ITEM_VALOR_TOTAL'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Faturamento'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            
            # Data
            df['Data'] = pd.to_datetime(raw_data['Data de Emissão'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Remove linhas "sujas" (sem produto ou sem valor)
            df = df[(df['Produto'] != 'nan') & (df['Faturamento'] > 0)]
            
            return df
        except Exception as e:
            st.error(f"Erro na leitura das colunas: {e}. Verifique se alterou os nomes no Sheets!")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- FILTROS ---
        st.sidebar.header("Filtros")
        meses = sorted(df['Mes_Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Mês:", meses, default=meses)
        
        plats = sorted(df['Canal'].unique())
        opcoes_plat = ["Todos"] + plats
        plat_sel = st.sidebar.multiselect("Plataforma:", opcoes_plat, default=["Todos"])

        df_f = df[df['Mes_Ano'].isin(mes_sel)].copy()
        if "Todos" not in plat_sel:
            df_f = df_f[df_f['Canal'].isin(plat_sel)]

        # --- EXIBIÇÃO ---
        c1, c2, c3 = st.columns(3)
        total_f = df_f['Faturamento'].sum()
        total_q = df_f['Qtd'].sum()
        
        c1.metric("Faturamento", f"R$ {total_f:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c2.metric("Qtd Vendida", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio", f"R$ {(total_f/total_q if total_q > 0 else 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")

        # Tabelas de Agrupamento
        st.subheader("Vendas por Produto")
        # Agrupamento rigoroso pelo nome do produto
        resumo_prod = df_f.groupby('Produto', as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'})
        st.dataframe(resumo_prod.sort_values('Faturamento', ascending=False), use_container_width=True)

        st.subheader("Vendas por Canal")
        resumo_canal = df_f.groupby('Canal', as_index=False)['Faturamento'].sum()
        st.dataframe(resumo_canal.sort_values('Faturamento', ascending=False), use_container_width=True)

    else:
        st.info("Aguardando alteração dos nomes das colunas no Google Sheets...")
