import streamlit as st
import pandas as pd
import io

# 1. Configuração da Página
st.set_page_config(page_title="Faturamento Inove", layout="wide", page_icon="📊")

# --- SISTEMA DE LOGIN ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "Inove2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.title("🔐 Acesso Restrito")
        st.text_input("Senha de Acesso:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha de Acesso:", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta.")
        return False
    return True

if check_password():
    st.title("📊 Faturamento Inove")
    st.markdown("---")

    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/pub?gid=1866890896&single=true&output=csv"

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @st.cache_data(ttl=5)
    def load_data():
        try:
            df_raw = pd.read_csv(LINK_BASE, on_bad_lines='skip', low_memory=False)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            df = pd.DataFrame()
            df['Canal'] = df_raw['ITEM_CANAL'].astype(str).str.strip()
            df['Produto'] = df_raw['ITEM_PRODUTO'].astype(str).str.strip()
            q_raw = df_raw['ITEM_QTD'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Qtd'] = pd.to_numeric(q_raw, errors='coerce').fillna(0)
            v_raw = df_raw['ITEM_VALOR_TOTAL'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Faturamento'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            df['Data'] = pd.to_datetime(df_raw['DT_EMISSÃO'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Ano_Mes_Ref'] = df['Data'].dt.strftime('%Y-%m')
            df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
            df = df[(df['Produto'] != 'nan') & (df['Faturamento'] > 0)]
            return df
        except Exception as e:
            st.error(f"Erro na sincronização: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- 1. SEÇÃO FIXA (COMPARATIVO MENSAL) ---
        st.subheader("🗓️ Comparativo Mensal Geral (Fixo)")
        df_dinamico = df.groupby(['Ano_Mes_Ref', 'Mes_Ano'], as_index=False)['Faturamento'].sum().sort_values('Ano_Mes_Ref')
        tabela_comparativa = df_dinamico.pivot_table(columns='Mes_Ano', values='Faturamento', aggfunc='sum')
        ordem_meses = df_dinamico['Mes_Ano'].tolist()
        tabela_comparativa = tabela_comparativa[ordem_meses]
        st.dataframe(tabela_comparativa.style.format(formatar_moeda), use_container_width=True)
        
        st.markdown("---")

        # --- 2. SIDEBAR (FILTROS) ---
        st.sidebar.header("Filtros Analíticos")
        meses_lista = sorted(df['Mes_Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Filtrar Mês:", meses_lista, default=meses_lista)
        canais = sorted(df['Canal'].unique())
        opcoes_canal = ["Todos"] + canais
        canal_sel = st.sidebar.multiselect("Filtrar Canal:", opcoes_canal, default=["Todos"])

        df_f = df[df['Mes_Ano'].isin(mes_sel)].copy()
        if "Todos" not in canal_sel:
            df_f = df_f[df_f['Canal'].isin(canal_sel)]

        # --- 3. KPIs FILTRADOS ---
        st.subheader("🔍 Resultados Filtrados")
        c1, c2, c3 = st.columns(3)
        total_f = df_f['Faturamento'].sum()
        total_q = df_f['Qtd'].sum()
        c1.metric("Faturamento", formatar_moeda(total_f))
        c2.metric("Itens Vendidos", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio/Item", formatar_moeda(total_f / total_q if total_q > 0 else 0))

        # --- 4. TABELAS ANALÍTICAS ---
        st.markdown("---")
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.subheader("📊 Faturamento por Canal")
            resumo_canal = df_f.groupby('Canal', as_index=False)['Faturamento'].sum().sort_values('Faturamento', ascending=False)
            st.dataframe(resumo_canal.style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        with col_dir:
            st.subheader("🏆 Ranking de Produtos")
            resumo_prod = df_f.groupby('Produto', as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'}).sort_values('Faturamento', ascending=False)
            st.dataframe(resumo_prod.style.format({'Faturamento': formatar_moeda, 'Qtd': '{:.0f}'}), use_container_width=True)

        st.markdown("---")
        st.subheader("📑 Detalhado (Canal + Produto)")
        detalhe = df_f.groupby(['Canal', 'Produto'], as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'}).sort_values(['Canal', 'Faturamento'], ascending=[True, False])
        st.dataframe(detalhe.style.format({'Faturamento': formatar_moeda, 'Qtd': '{:.0f}'}), use_container_width=True)

        # --- 5. EXTRAÇÃO DE DADOS (EXCEL) ---
        st.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.download_button(
            label="📥 Extrair Dados Analíticos (Excel)",
            data=buffer.getvalue(),
            file_name=f"Analitico_Inove_{pd.Timestamp.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("Aguardando carregamento de dados do Google Planilhas...")
