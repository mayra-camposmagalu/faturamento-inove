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
            # Lê o CSV bruto
            df_raw = pd.read_csv(LINK_BASE)
            
            # Limpa nomes das colunas (remove espaços extras)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            
            df = pd.DataFrame()
            
            # MAPEAMENTO FORÇADO (Baseado na sua imagem)
            # Usamos a coluna exata 'Produto' para o nome e 'Quantidade' para o valor numérico
            df['Plataforma'] = df_raw['Plataforma'].astype(str).str.strip()
            df['Produto'] = df_raw['Produto'].astype(str).str.strip()
            
            # Tratamento de Quantidade (converte 1,0 para 1)
            df['Quantidade'] = df_raw['Quantidade'].astype(str).str.replace(',', '.', regex=False)
            df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
            
            # Tratamento de Valor (VALOR TOTAL DO ITEM)
            df['Valor Item'] = df_raw['VALOR TOTAL DO ITEM'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Valor Item'] = pd.to_numeric(df['Valor Item'], errors='coerce').fillna(0)
            
            # Tratamento de Data
            df['Data'] = pd.to_datetime(df_raw['Data de Emissão'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Remove qualquer linha que tenha ficado com produto "nan" ou vazio
            df = df[df['Produto'] != 'nan']
            
            return df
        except Exception as e:
            st.error(f"Erro na estrutura da planilha: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # SIDEBAR
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
        c1.metric("Faturamento Total", f"R$ {total_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c2.metric("Qtd Total Vendida", f"{int(total_qtd):,}".replace(",", "."))
        c3.metric("Ticket Médio", f"R$ {(total_fat/total_qtd if total_qtd>0 else 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")

        # TABELAS DE AGRUPAMENTO
        col_esq, col_dir = st.columns(2)
        
        with col_esq:
            st.subheader("Ranking por Produto")
            # Agrupamento rigoroso por Produto
            ranking = df_f.groupby('Produto', as_index=False).agg({
                'Quantidade': 'sum',
                'Valor Item': 'sum'
            }).rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(ranking.sort_values('Faturamento', ascending=False), use_container_width=True)

        with col_dir:
            st.subheader("Faturamento por Plataforma")
            plat_sum = df_f.groupby('Plataforma', as_index=False)['Valor Item'].sum().rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(plat_sum.sort_values('Faturamento', ascending=False), use_container_width=True)

        st.subheader("Visão Detalhada (Plataforma + Produto)")
        detalhe = df_f.groupby(['Plataforma', 'Produto'], as_index=False).agg({
            'Quantidade': 'sum',
            'Valor Item': 'sum'
        }).rename(columns={'Valor Item': 'Faturamento'})
        st.dataframe(detalhe.sort_values(['Plataforma', 'Faturamento'], ascending=[True, False]), use_container_width=True)

    else:
        st.warning("Verifique se as colunas 'Produto' e 'VALOR TOTAL DO ITEM' estão preenchidas no Sheets.")
