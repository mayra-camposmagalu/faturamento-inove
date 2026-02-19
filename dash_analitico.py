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
        st.text_input("Digite a senha para acessar o Faturamento Inove:", 
                     type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Acesso Restrito")
        st.text_input("Digite a senha para acessar o Faturamento Inove:", 
                     type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta. Tente novamente.")
        return False
    else:
        return True

if check_password():

    st.title("📊 Faturamento Inove")
    st.markdown("---")

    LINK_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?output=csv"

    def formatar_moeda(valor):
        try:
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"

    @st.cache_data(ttl=10)
    def load_data():
        try:
            # Lê o CSV do Google Sheets
            df = pd.read_csv(LINK_GOOGLE_SHEETS)
            
            # Limpa espaços nos nomes das colunas
            df.columns = [str(c).strip() for c in df.columns]

            # MAPEAMENTO EXATO COM SEUS NOVOS CAMPOS
            mapa = {
                'Plataforma': ['Plataforma', 'PLATAFORMA'],
                'Produto': ['Produto', 'PRODUTO', 'Descrição do Produto'],
                'Quantidade': ['Quantidade', 'QUANTIDADE', 'Qtd'],
                'Valor Item': ['VALOR TOTAL DO ITEM', 'VALOR TOTAL DO ITEM ', 'Valor Item'],
                'Data': ['Data de Emissão', 'DATA DE EMISSÃO', 'Data']
            }

            for padrao, variacoes in mapa.items():
                for var in variacoes:
                    if var in df.columns:
                        df = df.rename(columns={var: padrao})
                        break
            
            # LIMPEZA DOS VALORES (Trata R$, pontos e vírgulas)
            if 'Valor Item' in df.columns:
                # Converte para string e limpa caracteres não numéricos, exceto vírgula/ponto
                df['Valor Item'] = df['Valor Item'].astype(str).str.replace('R$', '', regex=False).str.replace(' ', '', regex=False)
                
                # Lógica para converter padrão brasileiro (1.000,00) para padrão Python (1000.00)
                # Se houver ponto e vírgula, remove o ponto e troca vírgula por ponto
                df['Valor Item'] = df['Valor Item'].apply(lambda x: x.replace('.', '').replace(',', '.') if ',' in x else x)
                
                df['Valor Item'] = pd.to_numeric(df['Valor Item'], errors='coerce').fillna(0)
            
            if 'Quantidade' in df.columns:
                df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)

            # Limpa a coluna de Plataforma contra espaços vazios
            if 'Plataforma' in df.columns:
                df['Plataforma'] = df['Plataforma'].astype(str).str.strip()
            
            # Tratamento da Data de Emissão
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['Data'])
                df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            else:
                df['Mês/Ano'] = 'Sem Data'
                
            # Filtra apenas linhas que possuem valor maior que zero
            df = df[df['Valor Item'] > 0]
            
            return df
        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        st.sidebar.header("Filtros")
        
        # Filtro de Mês
        periodos = sorted([p for p in df['Mês/Ano'].unique() if p and str(p) != 'nan'])
        mes_sel = st.sidebar.multiselect("Mês:", options=periodos, default=periodos)
        
        # Filtro de Plataforma
        plats_disponiveis = sorted([p for p in df['Plataforma'].unique() if p and str(p) != 'nan' and p != 'None'])
        opcoes_plataforma = ["Todos"] + plats_disponiveis
        plat_sel = st.sidebar.multiselect("Plataforma:", options=opcoes_plataforma, default=["Todos"])

        # --- Lógica de Filtragem ---
        df_f = df[df['Mês/Ano'].isin(mes_sel)].copy()

        if "Todos" not in plat_sel:
            df_f = df_f[df_f['Plataforma'].isin(plat_sel)]

        # --- Dashboard ---
        c1, c2, c3 = st.columns(3)
        total_faturado = df_f['Valor Item'].sum()
        total_qtd = df_f['Quantidade'].sum()
        
        c1.metric("Faturamento Total", formatar_moeda(total_faturado))
        c2.metric("Qtd de Itens", f"{int(total_qtd):,}".replace(",", "."))
        c3.metric("Ticket Médio/Item", formatar_moeda(total_faturado / total_qtd if total_qtd > 0 else 0))

        st.markdown("---")

        # Tabelas Dinâmicas
        st.subheader("1. Faturamento por Plataforma")
        t1 = df_f.groupby('Plataforma')['Valor Item'].sum().reset_index().rename(columns={'Valor Item': 'Faturamento'})
        st.dataframe(t1.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("2. Resumo por Produto")
            t2 = df_f.groupby('Produto').agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).reset_index().rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(t2.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)
        
        with col_b:
            st.subheader("3. Detalhado (Plataforma + Produto)")
            t3 = df_f.groupby(['Plataforma', 'Produto']).agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).reset_index().rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(t3.sort_values(['Plataforma', 'Faturamento'], ascending=[True, False]).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        st.markdown("---")
        # Botão de Download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.download_button("📥 Baixar Relatório (Excel)", data=buffer.getvalue(), file_name="Faturamento_Inove.xlsx")

    else:
        st.info("Nenhum dado encontrado. Verifique se o Google Sheets possui as colunas 'VALOR TOTAL DO ITEM' e 'Data de Emissão' preenchidas corretamente.")
