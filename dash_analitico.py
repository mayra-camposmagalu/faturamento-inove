import streamlit as st
import pandas as pd
import io

# 1. Configuração da Página
st.set_page_config(page_title="Faturamento Inove", layout="wide")

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
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta.")
        return False
    return True

if check_password():
    st.title("📊 Faturamento Inove")
    st.markdown("---")

    # LINK ATUALIZADO COM O GID ESPECÍFICO DA ABA 'Vendas'
    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?gid=1866890896&single=true&output=csv"

    def formatar_moeda(valor):
        try:
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"

    @st.cache_data(ttl=10)
    def load_data():
        try:
            # Lendo o CSV da aba específica
            df = pd.read_csv(LINK_BASE)
            df.columns = [str(c).strip() for c in df.columns]

            # Mapeamento de colunas conforme os nomes no seu Google Sheets
            mapa = {
                'Plataforma': ['Plataforma', 'PLATAFORMA'],
                'Produto': ['Produto', 'PRODUTO', 'Descrição do Produto'],
                'Quantidade': ['Quantidade', 'QUANTIDADE', 'Qtd'],
                'Valor Item': ['VALOR TOTAL DO ITEM', 'Valor Item'],
                'Data': ['Data de Emissão', 'DATA DE EMISSÃO', 'Data']
            }

            for padrao, variacoes in mapa.items():
                for var in variacoes:
                    if var in df.columns:
                        df = df.rename(columns={var: padrao})
                        break
            
            # TRATAMENTO DE NÚMEROS (Converte padrão brasileiro 27,90 para 27.90)
            if 'Valor Item' in df.columns:
                df['Valor Item'] = df['Valor Item'].astype(str).str.replace('R$', '', regex=False).str.strip()
                # Remove ponto de milhar e troca vírgula decimal por ponto
                df['Valor Item'] = df['Valor Item'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df['Valor Item'] = pd.to_numeric(df['Valor Item'], errors='coerce').fillna(0)
            
            if 'Quantidade' in df.columns:
                # Trata quantidades (ex: "1,0" vira "1.0")
                df['Quantidade'] = df['Quantidade'].astype(str).str.replace(',', '.', regex=False)
                df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)

            # Tratamento de Datas
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['Data'])
                df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            # Limpeza final de nomes de plataforma
            df['Plataforma'] = df['Plataforma'].fillna('Outros').astype(str).str.strip()
            
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados da aba selecionada: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # --- SIDEBAR FILTROS ---
        st.sidebar.header("Filtros")
        
        # Filtro de Mês
        periodos = sorted(df['Mês/Ano'].unique())
        mes_sel = st.sidebar.multiselect("Mês:", periodos, default=periodos)
        
        # Filtro de Plataforma com a opção "Todos"
        plats_list = sorted(df['Plataforma'].unique())
        opcoes_plat = ["Todos"] + plats_list
        plat_sel = st.sidebar.multiselect("Plataforma:", opcoes_plat, default=["Todos"])

        # Lógica de Filtragem
        df_f = df[df['Mês/Ano'].isin(mes_sel)].copy()
        
        # Se "Todos" não estiver selecionado, filtra as plataformas marcadas
        if "Todos" not in plat_sel:
            df_f = df_f[df_f['Plataforma'].isin(plat_sel)]

        # --- EXIBIÇÃO ---
        c1, c2, c3 = st.columns(3)
        fat_total = df_f['Valor Item'].sum()
        qtd_total = df_f['Quantidade'].sum()
        
        c1.metric("Faturamento Total", formatar_moeda(fat_total))
        c2.metric("Quantidade Total", f"{int(qtd_total):,}".replace(",", "."))
        c3.metric("Ticket Médio", formatar_moeda(fat_total / qtd_total if qtd_total > 0 else 0))

        st.markdown("---")

        # 1. Tabela por Plataforma
        st.subheader("1. Faturamento por Plataforma")
        t1 = df_f.groupby('Plataforma')['Valor Item'].sum().reset_index().rename(columns={'Valor Item': 'Faturamento'})
        st.dataframe(t1.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            # 2. Tabela por Produto
            st.subheader("2. Resumo por Produto")
            t2 = df_f.groupby('Produto').agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).reset_index().rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(t2.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)
            
        with col_b:
            # 3. Tabela Cruzada
            st.subheader("3. Detalhado (Plataforma + Produto)")
            t3 = df_f.groupby(['Plataforma', 'Produto']).agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).reset_index().rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(t3.sort_values(['Plataforma', 'Faturamento'], ascending=[True, False]).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        st.markdown("---")
        # Botão para baixar os dados filtrados em Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.download_button("📥 Baixar Relatório Analítico (Excel)", data=buffer.getvalue(), file_name="Faturamento_Inove_Vendas.xlsx")

    else:
        st.info("Aguardando carregamento de dados do Google Sheets...")
