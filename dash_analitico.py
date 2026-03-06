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

    # NOVO LINK DA PLANILHA GOOGLE (Aba Vendas)
    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0d0ocvTeVlsTsefpEWaiefrs24ZLT6J_ZeqbmXyztSMBd1iCYtxvMKWONdhRy-kmA14uHwTiufFg2/pub?gid=1866890896&single=true&output=csv"

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @st.cache_data(ttl=5)
    def load_data():
        try:
            # Lê o CSV ignorando linhas problemáticas
            df_raw = pd.read_csv(LINK_BASE, on_bad_lines='skip', low_memory=False)
            
            # Limpa espaços nos nomes das colunas
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            # Cria um DataFrame limpo com mapeamento fixo
            df = pd.DataFrame()
            
            # Mapeamento baseado nos novos nomes da Sheet
            df['Canal'] = df_raw['ITEM_CANAL'].astype(str).str.strip()
            df['Produto'] = df_raw['ITEM_PRODUTO'].astype(str).str.strip()
            
            # Limpeza de Quantidade (Trata 1,0 ou 1.0)
            q_raw = df_raw['ITEM_QTD'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Qtd'] = pd.to_numeric(q_raw, errors='coerce').fillna(0)
            
            # Limpeza de Valor Total
            v_raw = df_raw['ITEM_VALOR_TOTAL'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Faturamento'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            
            # Tratamento de Data
            df['Data'] = pd.to_datetime(df_raw['DT_EMISSÃO'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Remove linhas com erros ou valores zerados
            df = df[(df['Produto'] != 'nan') & (df['Faturamento'] > 0)]
            
            return df
        except Exception as e:
            st.error(f"Erro na sincronização: Verifique se as colunas estão como ITEM_CANAL, ITEM_PRODUTO, ITEM_QTD, ITEM_VALOR_TOTAL e DT_EMISSÃO. Detalhe: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- FILTROS (SIDEBAR) ---
        st.sidebar.header("Filtros de Análise")
        
        meses = sorted(df['Mes_Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Selecione o Mês:", meses, default=meses)
        
        canais = sorted(df['Canal'].unique())
        opcoes_canal = ["Todos"] + canais
        canal_sel = st.sidebar.multiselect("Selecione o Canal:", opcoes_canal, default=["Todos"])

        # Filtragem
        df_f = df[df['Mes_Ano'].isin(mes_sel)].copy()
        if "Todos" not in canal_sel:
            df_f = df_f[df_f['Canal'].isin(canal_sel)]

        # --- INDICADORES (KPIs) ---
        total_f = df_f['Faturamento'].sum()
        total_q = df_f['Qtd'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Faturamento Total", formatar_moeda(total_f))
        c2.metric("Itens Vendidos", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio/Item", formatar_moeda(total_f / total_q if total_q > 0 else 0))

        st.markdown("---")

        # --- VISUALIZAÇÕES ---
        st.subheader("Análise por Produto")
        resumo_prod = df_f.groupby('Produto', as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'})
        st.dataframe(resumo_prod.sort_values('Faturamento', ascending=False).style.format({
            'Faturamento': formatar_moeda, 
            'Qtd': '{:.0f}'
        }), use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Faturamento por Canal")
            resumo_canal = df_f.groupby('Canal', as_index=False)['Faturamento'].sum()
            st.dataframe(resumo_canal.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)
        
        with col_b:
            st.subheader("Top Produtos (Qtd)")
            st.dataframe(resumo_prod.sort_values('Qtd', ascending=False)[['Produto', 'Qtd']], use_container_width=True)

        # --- EXPORTAÇÃO ---
        st.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.download_button("📥 Baixar Relatório em Excel", data=buffer.getvalue(), file_name="Relatorio_Inove_Vendas.xlsx")

    else:
        st.info("Aguardando carregamento de dados do Google Planilhas...")
