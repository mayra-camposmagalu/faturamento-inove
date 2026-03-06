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
            
            # Colunas de tempo para ordenação e exibição
            df['Ano_Mes_Ref'] = df['Data'].dt.strftime('%Y-%m')
            df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            df = df[(df['Produto'] != 'nan') & (df['Faturamento'] > 0)]
            return df
        except Exception as e:
            st.error(f"Erro na sincronização: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- SEÇÃO FIXA: TABELA DINÂMICA MENSAL (IGNORA FILTROS) ---
        st.subheader("🗓️ Comparativo Mensal Fixo (Total Geral)")
        
        # Criamos a tabela dinâmica: Meses nas colunas, Faturamento como valor
        df_dinamico = df.groupby(['Ano_Mes_Ref', 'Mes_Ano'], as_index=False)['Faturamento'].sum()
        df_dinamico = df_dinamico.sort_values('Ano_Mes_Ref')
        
        # Transpondo para ficar em formato de linha única com meses nas colunas
        tabela_comparativa = df_dinamico.pivot_table(columns='Mes_Ano', values='Faturamento', aggfunc='sum')
        
        # Reordenando as colunas para seguir a ordem cronológica correta
        ordem_meses = df_dinamico['Mes_Ano'].tolist()
        tabela_comparativa = tabela_comparativa[ordem_meses]

        # Exibindo a tabela com formatação de moeda
        st.dataframe(tabela_comparativa.style.format(formatar_moeda), use_container_width=True)
        
        st.markdown("---")

        # --- SIDEBAR (FILTROS) ---
        st.sidebar.header("Filtros de Análise Detalhada")
        meses_lista = sorted(df['Mes_Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Filtrar Mês:", meses_lista, default=meses_lista)
        canais = sorted(df['Canal'].unique())
        opcoes_canal = ["Todos"] + canais
        canal_sel = st.sidebar.multiselect("Filtrar Canal:", opcoes_canal, default=["Todos"])

        # Aplicando filtros apenas para os blocos abaixo
        df_f = df[df['Mes_Ano'].isin(mes_sel)].copy()
        if "Todos" not in canal_sel:
            df_f = df_f[df_f['Canal'].isin(canal_sel)]

        # --- INDICADORES FILTRADOS ---
        st.subheader("🔍 Detalhamento Analítico (Com Filtros)")
        c1, c2, c3 = st.columns(3)
        total_f = df_f['Faturamento'].sum()
        total_q = df_f['Qtd'].sum()
        
        c1.metric("Faturamento Filtrado", formatar_moeda(total_f))
        c2.metric("Itens Filtrados", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio/Item", formatar_moeda(total_f / total_q if total_q > 0 else 0))

        # --- TABELA DE PRODUTOS FILTRADA ---
        resumo_prod = df_f.groupby('Produto', as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'})
        st.dataframe(resumo_prod.sort_values('Faturamento', ascending=False).style.format({
            'Faturamento': formatar_moeda, 
            'Qtd': '{:.0f}'
        }), use_container_width=True)

    else:
        st.info("Aguardando carregamento de dados...")
