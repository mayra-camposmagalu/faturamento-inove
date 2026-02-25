import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Faturamento Inove", layout="wide", page_icon="📊")

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

    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?gid=1866890896&single=true&output=csv"

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @st.cache_data(ttl=5)
    def load_data():
        try:
            # Lendo o CSV ignorando erros de delimitadores
            df_raw = pd.read_csv(LINK_BASE, on_bad_lines='skip', low_memory=False)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            # Criando DataFrame limpo com os NOVOS NOMES que você vai colocar no Sheets
            df = pd.DataFrame()
            
            # Mapeamento Direto e Exclusivo
            df['Plataforma'] = df_raw['Plataforma'].astype(str).str.strip()
            df['Produto'] = df_raw['NOME_PRODUTO'].astype(str).str.strip()
            
            # Limpeza de Quantidade
            q_raw = df_raw['Quantidade'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Quantidade'] = pd.to_numeric(q_raw, errors='coerce').fillna(0)
            
            # Limpeza de Valor usando o novo nome VALOR_TOTAL_ITEM
            v_raw = df_raw['VALOR_TOTAL_ITEM'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Valor_Item'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            
            # Data
            df['Data'] = pd.to_datetime(df_raw['Data de Emissão'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Filtro de segurança contra linhas "lixo"
            df = df[(df['Produto'] != 'nan') & (df['Valor_Item'] > 0)]
            
            return df
        except Exception as e:
            st.error(f"Erro ao ler as colunas. Verifique se mudou os nomes no Sheets para NOME_PRODUTO e VALOR_TOTAL_ITEM. Detalhe: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
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
        c1, c2, c3 = st.columns(3)
        total_fat = df_f['Valor_Item'].sum()
        total_qtd = df_f['Quantidade'].sum()
        
        c1.metric("Faturamento Total", formatar_moeda(total_fat))
        c2.metric("Quantidade Total", f"{int(total_qtd):,}".replace(",", "."))
        c3.metric("Ticket Médio", formatar_moeda(total_fat / total_qtd if total_qtd > 0 else 0))

        st.markdown("---")

        # TABELAS
        st.subheader("Análise de Vendas por Produto")
        ranking = df_f.groupby('Produto', as_index=False).agg({
            'Quantidade': 'sum',
            'Valor_Item': 'sum'
        }).rename(columns={'Valor_Item': 'Faturamento'})
        
        st.dataframe(ranking.sort_values('Faturamento', ascending=False).style.format({
            'Faturamento': formatar_moeda, 
            'Quantidade': '{:.0f}'
        }), use_container_width=True)

        st.subheader("Resumo por Plataforma")
        plat_sum = df_f.groupby('Plataforma', as_index=False)['Valor_Item'].sum().rename(columns={'Valor_Item': 'Faturamento'})
        st.dataframe(plat_sum.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

    else:
        st.warning("Verifique se os nomes das colunas no Google Sheets foram alterados para NOME_PRODUTO e VALOR_TOTAL_ITEM.")
