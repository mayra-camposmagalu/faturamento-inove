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
        st.title("🔐 Acesso Inove")
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if check_password():
    st.title("📊 Faturamento Inove")
    st.markdown("---")

    # LINK DA ABA VENDAS (GID 1866890896)
    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?gid=1866890896&single=true&output=csv"

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @st.cache_data(ttl=5)
    def load_data():
        try:
            # Lendo o CSV ignorando erros de linhas com colunas a mais
            df_raw = pd.read_csv(LINK_BASE, on_bad_lines='skip', low_memory=False)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            # Criando o DataFrame final com as colunas EXATAS da sua imagem
            df = pd.DataFrame()
            
            # Pegamos apenas as colunas que importam, limpando espaços vazios
            df['Plataforma'] = df_raw['Plataforma'].astype(str).str.strip()
            df['Produto_Nome'] = df_raw['Produto'].astype(str).str.strip()
            
            # Limpeza Numérica - Quantidade
            # Convertemos para string, limpamos e forçamos o formato numérico
            q_raw = df_raw['Quantidade'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Quantidade'] = pd.to_numeric(q_raw, errors='coerce').fillna(0)
            
            # Limpeza Numérica - Valor Item
            v_raw = df_raw['VALOR TOTAL DO ITEM'].astype(str).str.replace('R$', '', regex=False)
            v_raw = v_raw.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Valor_Item'] = pd.to_numeric(v_raw, errors='coerce').fillna(0)
            
            # Tratamento de Data
            df['Data'] = pd.to_datetime(df_raw['Data de Emissão'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Filtro de segurança: remove produtos sem nome ou com erro de leitura
            df = df[df['Produto_Nome'] != 'nan']
            df = df[df['Valor_Item'] > 0]
            
            return df
        except Exception as e:
            st.error(f"Erro na sincronização: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- FILTROS ---
        st.sidebar.header("Filtros")
        meses = sorted(df['Mês/Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Mês:", meses, default=meses)
        
        plats = sorted(df['Plataforma'].unique())
        opcoes_plat = ["Todos"] + plats
        plat_sel = st.sidebar.multiselect("Plataforma:", opcoes_plat, default=["Todos"])

        # Aplicação dos Filtros
        df_f = df[df['Mês/Ano'].isin(mes_sel)].copy()
        if "Todos" not in plat_sel:
            df_f = df_f[df_f['Plataforma'].isin(plat_sel)]

        # --- KPIs ---
        c1, c2, c3 = st.columns(3)
        total_fat = df_f['Valor_Item'].sum()
        total_qtd = df_f['Quantidade'].sum()
        
        c1.metric("Faturamento Total", formatar_moeda(total_fat))
        c2.metric("Quantidade Total", f"{int(total_qtd):,}".replace(",", "."))
        c3.metric("Ticket Médio", formatar_moeda(total_fat / total_qtd if total_qtd > 0 else 0))

        st.markdown("---")

        # --- TABELAS ---
        # 1. Ranking por Produto (Sem misturar colunas)
        st.subheader("1. Ranking por Produto")
        ranking = df_f.groupby('Produto_Nome', as_index=False).agg({
            'Quantidade': 'sum',
            'Valor_Item': 'sum'
        }).rename(columns={'Produto_Nome': 'Produto', 'Valor_Item': 'Faturamento'})
        
        st.dataframe(ranking.sort_values('Faturamento', ascending=False).style.format({
            'Faturamento': formatar_moeda, 
            'Quantidade': '{:.0f}'
        }), use_container_width=True)

        col_esq, col_dir = st.columns(2)
        
        with col_esq:
            st.subheader("2. Faturamento por Plataforma")
            plat_sum = df_f.groupby('Plataforma', as_index=False)['Valor_Item'].sum().rename(columns={'Valor_Item': 'Faturamento'})
            st.dataframe(plat_sum.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        with col_dir:
            st.subheader("3. Detalhado (Plataforma + Produto)")
            detalhe = df_f.groupby(['Plataforma', 'Produto_Nome'], as_index=False).agg({
                'Quantidade': 'sum', 
                'Valor_Item': 'sum'
            }).rename(columns={'Produto_Nome': 'Produto', 'Valor_Item': 'Faturamento'})
            st.dataframe(detalhe.sort_values(['Plataforma', 'Faturamento'], ascending=[True, False]).style.format({
                'Faturamento': formatar_moeda, 
                'Quantidade': '{:.0f}'
            }), use_container_width=True)

    else:
        st.warning("Verificando conexão com o Sheets... Verifique as colunas de Data e Valor.")
