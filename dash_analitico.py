import streamlit as st
import pandas as pd
import io

# 1. Configuração da Página
st.set_page_config(
    page_title="Inove - Faturamento",
    layout="wide",
    page_icon="📊"
)

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
    return st.session_state.get("password_correct", False)

if check_password():
    # --- CABEÇALHO ---
    st.markdown(
        """
        <div style="background-color: #2F3E4D; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h1 style="color: #E0E0E0; margin: 0; font-family: sans-serif; font-size: 28px;">
                Dash de Faturamento Analítico <span style="color: #A2D149;">• Inove</span>
            </h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Links de Dados
    LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/pub?gid=1866890896&single=true&output=csv"
    LINK_EDIT = "https://docs.google.com/spreadsheets/d/1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/edit#gid=1866890896"

    # FUNÇÃO DE FORMATAÇÃO BRASILEIRA (1.234,56)
    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @st.cache_data(ttl=5)
    def load_data():
        try:
            df_raw = pd.read_csv(LINK_CSV, on_bad_lines='skip', low_memory=False)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            df = pd.DataFrame()
            df['Canal'] = df_raw['ITEM_CANAL'].astype(str).str.strip()
            df['Produto'] = df_raw['ITEM_PRODUTO'].astype(str).str.strip()
            
            # Tratamento numérico
            q_raw = df_raw['ITEM_QTD'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Qtd'] = pd.to_numeric(q_raw, errors='coerce').fillna(0)
            
            v_raw = df_raw['ITEM_VALOR_TOTAL'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Faturamento'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            
            # Tratamento de Data
            df['Data'] = pd.to_datetime(df_raw['DT_EMISSÃO'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Ano_Mes'] = df['Data'].dt.strftime('%Y-%m')
            df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- 1. COMPARATIVO MENSAL (FIXO) ---
        st.subheader("🗓️ Comparativo Mensal Geral (Fixo)")
        df_m = df.groupby(['Ano_Mes', 'Mes_Ano'], as_index=False)['Faturamento'].sum().sort_values('Ano_Mes')
        tabela_fixa = df_m.pivot_table(columns='Mes_Ano', values='Faturamento', aggfunc='sum')
        # Aplica a formatação brasileira na tabela
        st.dataframe(tabela_fixa.style.format(formatar_moeda), use_container_width=True)

        # --- 2. FILTROS (SIDEBAR) ---
        st.sidebar.header("Filtros Analíticos")
        mes_sel = st.sidebar.multiselect("Filtrar Mês:", sorted(df['Mes_Ano'].unique(), reverse=True), default=df['Mes_Ano'].unique())
        canal_list = sorted(df['Canal'].unique())
        canal_sel = st.sidebar.multiselect("Filtrar Canal:", ["Todos"] + canal_list, default=["Todos"])

        df_f = df[df['Mes_Ano'].isin(mes_sel)].copy()
        if "Todos" not in canal_sel:
            df_f = df_f[df_f['Canal'].isin(canal_sel)]

        # --- 3. KPIs ---
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        total_f = df_f['Faturamento'].sum()
        total_q = df_f['Qtd'].sum()
        c1.metric("Faturamento Filtrado", formatar_moeda(total_f))
        c2.metric("Itens Vendidos", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio", formatar_moeda(total_f / total_q if total_q > 0 else 0))

        # --- 4. TABELAS ANALÍTICAS ---
        st.markdown("---")
        col_esq, col_dir = st.columns(2)
        
        with col_esq:
            st.subheader("📊 Faturamento por Canal")
            resumo_canal = df_f.groupby('Canal', as_index=False)['Faturamento'].sum().sort_values('Faturamento', ascending=False)
            st.dataframe(resumo_canal.style.format({"Faturamento": formatar_moeda}), use_container_width=True)

        with col_dir:
            st.subheader("🏆 Ranking de Produtos")
            resumo_prod = df_f.groupby('Produto', as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'}).sort_values('Faturamento', ascending=False)
            st.dataframe(resumo_prod.style.format({"Faturamento": formatar_moeda, "Qtd": "{:.0f}"}), use_container_width=True)

        st.markdown("---")
        st.subheader("📑 Detalhado (Canal + Produto)")
        detalhe = df_f.groupby(['Canal', 'Produto'], as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'}).sort_values(['Canal', 'Faturamento'], ascending=[True, False])
        st.dataframe(detalhe.style.format({"Faturamento": formatar_moeda, "Qtd": "{:.0f}"}), use_container_width=True)

        # --- 5. EXPORTAÇÃO E ACESSO ---
        st.markdown("---")
        st.subheader("📂 Extração de Dados")
        ce1, ce2 = st.columns(2)
        
        with ce1:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_f.to_excel(writer, index=False)
            st.download_button(
                label="📥 Baixar Relatório Analítico (Excel)",
                data=buffer.getvalue(),
                file_name=f"Analitico_Inove_{pd.Timestamp.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        with ce2:
            st.link_button("🌐 Abrir no Google Planilhas", LINK_EDIT, use_container_width=True)

    else:
        st.info("Aguardando dados do Google Planilhas...")
