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
    return st.session_state.get("password_correct", False)

if check_password():
    st.title("📊 Faturamento Inove")
    st.markdown("---")

    # Link da aba Vendas (GID 1866890896)
    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?gid=1866890896&single=true&output=csv"

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @st.cache_data(ttl=5)
    def load_data():
        try:
            # Lê os dados brutos ignorando linhas corrompidas
            df_raw = pd.read_csv(LINK_BASE, on_bad_lines='skip', low_memory=False)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            # Criando o DataFrame limpo com os NOVOS NOMES DE COLUNA
            df = pd.DataFrame()
            
            # Mapeamento Direto baseado na sua última atualização
            df['Canal'] = df_raw['ITEM_CANAL'].astype(str).str.strip()
            df['Produto'] = df_raw['ITEM_PRODUTO'].astype(str).str.strip()
            
            # Limpeza de Quantidade (Tratando 1,0 ou 1.0)
            df['Qtd'] = df_raw['ITEM_QTD'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Qtd'] = pd.to_numeric(df['Qtd'], errors='coerce').fillna(0)
            
            # Limpeza de Valor (Tratando R$ 1.000,00)
            v_raw = df_raw['ITEM_VALOR_TOTAL'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Faturamento'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            
            # Tratamento da Data (Colun: DT_EMISSÃO)
            df['Data'] = pd.to_datetime(df_raw['DT_EMISSÃO'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Filtro de segurança: remove produtos vazios ou faturamento zero
            df = df[(df['Produto'] != 'nan') & (df['Faturamento'] > 0)]
            
            return df
        except Exception as e:
            st.error(f"Erro na leitura: Verifique se as colunas no Sheets são ITEM_CANAL, ITEM_PRODUTO, ITEM_QTD, ITEM_VALOR_TOTAL e DT_EMISSÃO. Detalhe: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- SIDEBAR (FILTROS) ---
        st.sidebar.header("Filtros")
        meses = sorted(df['Mes_Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Mês:", meses, default=meses)
        
        canais = sorted(df['Canal'].unique())
        opcoes_canal = ["Todos"] + canais
        canal_sel = st.sidebar.multiselect("Canal/Plataforma:", opcoes_canal, default=["Todos"])

        # Lógica de Filtragem
        df_f = df[df['Mes_Ano'].isin(mes_sel)].copy()
        if "Todos" not in canal_sel:
            df_f = df_f[df_f['Canal'].isin(canal_sel)]

        # --- EXIBIÇÃO KPIs ---
        c1, c2, c3 = st.columns(3)
        total_f = df_f['Faturamento'].sum()
        total_q = df_f['Qtd'].sum()
        
        c1.metric("Faturamento Total", formatar_moeda(total_f))
        c2.metric("Qtd Vendida", f"{int(total_q):,}".replace(",", "."))
        c3.metric("Ticket Médio", formatar_moeda(total_f / total_q if total_q > 0 else 0))

        st.markdown("---")

        # --- TABELAS ---
        st.subheader("Vendas por Produto")
        resumo_prod = df_f.groupby('Produto', as_index=False).agg({'Qtd': 'sum', 'Faturamento': 'sum'})
        st.dataframe(resumo_prod.sort_values('Faturamento', ascending=False).style.format({
            'Faturamento': formatar_moeda, 
            'Qtd': '{:.0f}'
        }), use_container_width=True)

        st.subheader("Resumo por Canal")
        resumo_canal = df_f.groupby('Canal', as_index=False)['Faturamento'].sum()
        st.dataframe(resumo_canal.sort_values('Faturamento', ascending=False).style.format({
            'Faturamento': formatar_moeda
        }), use_container_width=True)

        # --- DOWNLOAD ---
        st.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.download_button("📥 Baixar Relatório (Excel)", data=buffer.getvalue(), file_name="Faturamento_Inove.xlsx")

    else:
        st.info("Aguardando carregamento de dados do Google Sheets...")
