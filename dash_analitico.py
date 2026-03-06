import streamlit as st
import pandas as pd
import io

# 1. Configuração da Página e Tematização Base
st.set_page_config(
    page_title="Inove - Faturamento",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed" # Começa recolhido para focar no conteúdo
)

# Paleta de Cores Definida (com base na logo)
# Verde Lima Vibrante da Logo: #A2D149
# Cinza Escuro para Fundo Sidebar/Header: #2F3E4D
# Branco para Área de Conteúdo: #FFFFFF
# Preto para Títulos em Fundo Branco: #000000
# Cinza Médio para Texto Secundário: #555555

# --- SISTEMA DE LOGIN ---
def check_password():
    """Verifica a senha e exibe a interface de login com estilo."""
    def password_entered():
        if st.session_state["password"] == "Inove2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Estilo Centralizado e Moderno para Login
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background-color: #F8F9FA;">
                <div style="background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; width: 400px;">
                    <h1 style="color: #A2D149; font-size: 36px; margin-bottom: 5px;">🔐</h1>
                    <h2 style="color: #000000; font-size: 24px; margin-bottom: 20px; font-weight: 500;">Acesso Restrito - Inove</h2>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.text_input("Senha de Acesso:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Reexibe o card de login com mensagem de erro embutida
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background-color: #F8F9FA;">
                <div style="background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; width: 400px;">
                    <h1 style="color: #A2D149; font-size: 36px; margin-bottom: 5px;">🔐</h1>
                    <h2 style="color: #000000; font-size: 24px; margin-bottom: 20px; font-weight: 500;">Acesso Restrito - Inove</h2>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.text_input("Senha de Acesso:", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta. Tente novamente.")
        return False
    return True

if check_password():
    # --- CSS CUSTOMIZADO PARA DESIGN ---
    # Aplica o estilo de cartões e paleta de cores
    st.markdown(
        """
        <style>
            /* Cor vibrante da marca para destaques e títulos */
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMetric, .st-b5, .stDownloadButton button {
                color: #A2D149 !important;
            }

            /* Estilo dos cartões principais (KPIs, tabelas, downloads) */
            .css-1r6slb0, .css-1y4p8pa, .css-k0g4e6 {
                background-color: #FFFFFF !important;
                border-radius: 10px !important;
                padding: 25px !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
                border: 1px solid #EEEEEE !important;
                margin-bottom: 20px;
            }

            /* Ajuste de cor do texto em fundos claros */
            .stMarkdown p, .stMarkdown span, .css-1dp5a5w, .css-10trblm {
                color: #333333 !important;
            }
            
            /* Título do Sidebar */
            .css-1y4p8pa h1, .css-1y4p8pa h2 {
                color: #A2D149 !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- CABEÇALHO E FILTROS ---
    # Estilo do cabeçalho com logo e nome da empresa em destaque
    st.markdown(
        """
        <div style="background-color: #2F3E4D; padding: 20px; border-radius: 10px; margin-bottom: 25px; display: flex; align-items: center; gap: 20px;">
            <img src="URL_DA_SUA_LOGO" alt="Logo Inove" style="height: 60px;">
            <h1 style="margin: 0; color: #FFFFFF !important; font-weight: 600;">Dash de Faturamento Analítico</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- SIDEBAR (FILTROS) ---
    # Fundo cinza escuro para o sidebar, harmonizando com o cabeçalho
    with st.sidebar:
        st.markdown(
            """
            <div style="background-color: #2F3E4D; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #FFFFFF;">Filtros de Análise</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Link para leitura (CSV)
    LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/pub?gid=1866890896&single=true&output=csv"
    
    # Link para edição (Google Planilhas)
    LINK_EDIT = "https://docs.google.com/spreadsheets/d/1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/edit#gid=1866890896"

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
        # Tabela dinâmica em um card branco com bordas arredondadas e sombra
        st.markdown(
            """
            <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 25px;">
                <h3 style="color: #000000 !important; font-weight: 500;">🗓️ Evolução Mensal Geral</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        df_dinamico = df.groupby(['Ano_Mes_Ref', 'Mes_Ano'], as_index=False)['Faturamento'].sum().sort_values('Ano_Mes_Ref')
        tabela_comparativa = df_dinamico.pivot_table(columns='Mes_Ano', values='Faturamento', aggfunc='sum')
        ordem_meses = df_dinamico['Mes_Ano'].tolist()
        tabela_comparativa = tabela_comparativa[ordem_meses]
        st.dataframe(tabela_comparativa.style.format(formatar_moeda), use_container_width=True)

        # --- FIM CABEÇALHO E FILTROS NO SIDEBAR ---
        with st.sidebar:
            meses_lista = sorted(df['Mes_Ano'].unique(), reverse=True)
            mes_sel = st.sidebar.multiselect("Filtrar Mês:", meses_lista, default=meses_lista)
            canais = sorted(df['Canal'].unique())
            opcoes_canal = ["Todos"] + canais
            canal_sel = st.sidebar.multiselect("Filtrar Canal:", opcoes_canal, default=["Todos"])

        df_f = df[df['Mes_Ano'].isin(mes_sel)].copy()
        if "Todos" not in canal_sel:
            df_f = df_f[df_f['Canal'].isin(canal_sel)]

        # --- 3. INDICADORES FILTRADOS (KPIs) ---
        # Título da seção detalhada
        st.markdown(
            """
            <div style="margin-top: 30px; margin-bottom: 15px;">
                <h3 style="color: #A2D149 !important; font-weight: 500;">🔍 Detalhamento Analítico</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        c1, c2, c3 = st.columns(3)
        total_f = df_f['Faturamento'].sum()
        total_q = df_f['Qtd'].sum()
        
        # Estilo dos Cartões de KPI com a cor da marca
        st.markdown(
            """
            <style>
                .stMetric {
                    border-bottom: 3px solid #A2D149;
                    background-color: white !important;
                    border-radius: 10px !important;
                    padding: 20px !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        c1.metric("Faturamento", formatar_moeda(total_f))
        c2.metric("Itens Vendidos", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio/Item", formatar_moeda(total_f / total_q if total_q > 0 else 0))

        # --- 4. TABELAS ANALÍTICAS (Produto e Canal) ---
        # Títulos das subseções
        st.markdown(
            """
            <div style="margin-top: 20px; margin-bottom: 10px;">
                <h4 style="color: #000000 !important; font-weight: 500;">📈 Ranking de Desempenho</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        col_esq, col_dir = st.columns(2)

        with col_esq:
            # Card para Faturamento por Canal
            st.markdown(
                """
                <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px;">
                    <h5 style="color: #A2D149 !important; margin: 0; font-weight: 500;">📊 Faturamento por Canal</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            resumo_canal = df_f.groupby('Canal', as_index=False)['Faturamento'].sum().sort_values('Faturamento', ascending=False)
            st.dataframe(resumo_canal.style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        with col_dir:
            # Card para Ranking de Produtos
            st.markdown(
                """
                <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px;">
                    <h5 style="color: #A2D149 !important; margin: 0; font-weight: 500;">🏆 Ranking de Produtos</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            resumo_prod = df_f.groupby('Produto', as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'}).sort_values('Faturamento', ascending=False)
            st.dataframe(resumo_prod.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda, 'Qtd': '{:.0f}'}), use_container_width=True)

        # Seção Detalhada em um Card
        st.markdown(
            """
            <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 25px; margin-bottom: 25px;">
                <h4 style="color: #A2D149 !important; font-weight: 500;">📑 Visão Cruzada (Canal + Produto)</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        detalhe = df_f.groupby(['Canal', 'Produto'], as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'}).sort_values(['Canal', 'Faturamento'], ascending=[True, False])
        st.dataframe(detalhe.style.format({'Faturamento': formatar_moeda, 'Qtd': '{:.0f}'}), use_container_width=True)

        # --- 5. EXTRAÇÃO E ACESSO AOS DADOS ---
        # Cartão exclusivo para opções de exportação, facilitando o download
        st.markdown(
            """
            <div style="background-color: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 30px;">
                <h3 style="color: #A2D149 !important; margin: 0; font-weight: 500;">📂 Área de Download e Base</h3>
                <p style="color: #666666; margin-top: 5px;">Acesse a base completa no Google Planilhas ou extraia o relatório analítico.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col_ex1, col_ex2 = st.columns(2)

        with col_ex1:
            # Botão de download estilizado para se destacar
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_f.to_excel(writer, index=False)
            st.download_button(
                label="📥 Extrair Dados Analíticos (Excel)",
                data=buffer.getvalue(),
                file_name=f"Analitico_Inove_{pd.Timestamp.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_ex2:
            # Link direto para a planilha mãe
            st.link_button("🌐 Abrir no Google Planilhas", LINK_EDIT, use_container_width=True)

    else:
        st.info("Aguardando carregamento de dados do Google Planilhas...")
