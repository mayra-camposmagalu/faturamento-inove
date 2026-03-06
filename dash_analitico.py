import streamlit as st
import pandas as pd
import io
import base64

# 1. Configuração da Página
st.set_page_config(
    page_title="Inove - Faturamento",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Funções de Estética
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
    # --- CSS CUSTOMIZADO ---
    st.markdown(
        """
        <style>
            /* Cor cinza claro para textos do cabeçalho */
            .header-text {
                color: #E0E0E0 !important;
                font-weight: 600;
                font-size: 32px;
                margin: 0;
            }
            /* Cartões de métricas */
            div[data-metric-label] > label {
                color: #A2D149 !important;
            }
            /* Botões e destaques */
            .stButton>button {
                background-color: #A2D149;
                color: white;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- CABEÇALHO COM LOGO ---
    try:
        # Tenta carregar a logo do GitHub (certifique-se de subir o arquivo logo_inove.png)
        logo_img = get_base64("logo_inove.png")
        st.markdown(
            f"""
            <div style="background-color: #2F3E4D; padding: 20px; border-radius: 10px; margin-bottom: 25px; display: flex; align-items: center; gap: 20px;">
                <img src="data:image/png;base64,{logo_img}" style="height: 80px;">
                <p class="header-text">Dash de Faturamento Analítico • Inove</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        # Caso a imagem ainda não esteja no GitHub, mostra apenas o texto estilizado
        st.markdown(
            """
            <div style="background-color: #2F3E4D; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                <p class="header-text">Dash de Faturamento Analítico • Inove</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Links de Dados
    LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/pub?gid=1866890896&single=true&output=csv"
    LINK_EDIT = "https://docs.google.com/spreadsheets/d/1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/edit#gid=1866890896"

    @st.cache_data(ttl=5)
    def load_data():
        df_raw = pd.read_csv(LINK_CSV, on_bad_lines='skip', low_memory=False)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        df = pd.DataFrame()
        df['Canal'] = df_raw['ITEM_CANAL'].astype(str).str.strip()
        df['Produto'] = df_raw['ITEM_PRODUTO'].astype(str).str.strip()
        q_raw = df_raw['ITEM_QTD'].astype(str).str.replace(',', '.', regex=False).str.strip()
        df['Qtd'] = pd.to_numeric(q_raw, errors='coerce').fillna(0)
        v_raw = df_raw['ITEM_VALOR_TOTAL'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
        df['Faturamento'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df_raw['DT_EMISSÃO'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])
        df['Ano_Mes'] = df['Data'].dt.strftime('%Y-%m')
        df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
        return df

    df = load_data()

    if not df.empty:
        # 1. TABELA FIXA
        st.subheader("🗓️ Comparativo Mensal Geral (Fixo)")
        df_m = df.groupby(['Ano_Mes', 'Mes_Ano'], as_index=False)['Faturamento'].sum().sort_values('Ano_Mes')
        tabela = df_m.pivot_table(columns='Mes_Ano', values='Faturamento', aggfunc='sum')
        st.dataframe(tabela.style.format("R$ {:,.2f}"), use_container_width=True)

        # 2. FILTROS
        st.sidebar.header("Filtros")
        mes_sel = st.sidebar.multiselect("Mês:", sorted(df['Mes_Ano'].unique(), reverse=True), default=df['Mes_Ano'].unique())
        df_f = df[df['Mes_Ano'].isin(mes_sel)]

        # 3. KPIs
        c1, c2, c3 = st.columns(3)
        fat = df_f['Faturamento'].sum()
        c1.metric("Faturamento Filtrado", f"R$ {fat:,.2f}")
        c2.metric("Itens Vendidos", f"{int(df_f['Qtd'].sum()):,}")
        c3.metric("Ticket Médio", f"R$ {(fat/df_f['Qtd'].sum() if df_f['Qtd'].sum()>0 else 0):,.2f}")

        # 4. TABELAS ANALÍTICAS
        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📊 Por Canal")
            st.dataframe(df_f.groupby('Canal')['Faturamento'].sum().sort_values(ascending=False), use_container_width=True)
        with col_b:
            st.subheader("🏆 Top Produtos")
            st.dataframe(df_f.groupby('Produto')['Faturamento'].sum().sort_values(ascending=False), use_container_width=True)

        # 5. EXPORTAÇÃO
        st.markdown("---")
        c_ex1, c_ex2 = st.columns(2)
        with c_ex1:
            buffer = io.BytesIO()
            df_f.to_excel(buffer, index=False)
            st.download_button("📥 Baixar Excel", data=buffer.getvalue(), file_name="faturamento_inove.xlsx", use_container_width=True)
        with c_ex2:
            st.link_button("🌐 Abrir Google Planilhas", LINK_EDIT, use_container_width=True)
