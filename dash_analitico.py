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
            # Lê o CSV sem transformar nada primeiro
            df_raw = pd.read_csv(LINK_BASE)
            
            # Remove espaços dos nomes das colunas
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            
            # CRIANDO UM NOVO DATAFRAME LIMPO PARA NÃO MISTURAR COLUNAS
            df = pd.DataFrame()
            
            # Identificação manual e forçada das colunas baseada no seu relato
            df['Plataforma'] = df_raw['Plataforma'].astype(str).str.strip()
            df['Produto'] = df_raw['Produto'].astype(str).str.strip()
            df['Quantidade'] = df_raw['Quantidade']
            df['Valor Item'] = df_raw['VALOR TOTAL DO ITEM']
            df['Data'] = df_raw['Data de Emissão']

            # --- TRATAMENTO NUMÉRICO RIGOROSO ---
            # Trata Valor Item
            df['Valor Item'] = df['Valor Item'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Valor Item'] = pd.to_numeric(df['Valor Item'], errors='coerce').fillna(0)
            
            # Trata Quantidade
            df['Quantidade'] = df['Quantidade'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
            
            # Trata Data
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            return df
        except Exception as e:
            st.error(f"Erro na leitura das colunas: {e}. Verifique se os nomes das colunas no Sheets não mudaram.")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # FILTROS
        st.sidebar.header("Filtros")
        meses = sorted(df['Mês/Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Mês:", meses, default=meses)
        
        plats = sorted(df['Plataforma'].unique())
        opcoes_plat = ["Todos"] + plats
        plat_sel = st.sidebar.multiselect("Plataforma:", opcoes_plat, default=["Todos"])

        df_f = df[df['Mês/Ano'].isin(mes_sel)].copy()
        if "Todos" not in plat_sel:
            df_f = df_f[df_f['Plataforma'].isin(plat_sel)]

        # KPIs
        total_fat = df_f['Valor Item'].sum()
        total_qtd = df_f['Quantidade'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Faturamento", f"R$ {total_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c2.metric("Quantidade", f"{int(total_qtd):,}".replace(",", "."))
        c3.metric("Ticket Médio", f"R$ {(total_fat/len(df_f) if len(df_f)>0 else 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")

        # TABELA PRINCIPAL - Onde estava o erro
        st.subheader("Análise Detalhada por Produto")
        
        # Agrupamento explícito
        tabela_final = df_f.groupby(['Produto'], as_index=False).agg({
            'Quantidade': 'sum',
            'Valor Item': 'sum'
        }).rename(columns={'Valor Item': 'Faturamento Total'})
        
        # Ordenar para ver os principais
        tabela_final = tabela_final.sort_values('Faturamento Total', ascending=False)
        
        st.dataframe(tabela_final, use_container_width=True)

        # Botão de conferência
        st.write("Dica: Se os nomes ainda estiverem trocados, verifique se a coluna 'Produto' no Sheets não está deslocada.")
