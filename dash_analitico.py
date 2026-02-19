import streamlit as st
import pandas as pd
import io

# Configuração da página
st.set_page_config(page_title="Faturamento Inove", layout="wide")
st.title("📊 Faturamento Inove")

# Link do seu Google Sheets
LINK_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?output=csv"

def formatar_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_csv(LINK_GOOGLE_SHEETS)
        # Limpa linhas e colunas fantasmadas do Sheets
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        df.columns = [str(c).strip() for c in df.columns]

        mapa = {
            'Plataforma': ['PLATAFORMA', 'CANAL', 'MARKETPLACE', 'Plataforma'],
            'Produto': ['PRODUTO', 'DESC. NOTA', 'DESCRICAO', 'Desc. Nota', 'Produto'],
            'Quantidade': ['QUANTIDADE', 'QTD', 'Soma de Quantidade', 'Quantidade'],
            'Valor Item': ['VALOR ITEM', 'VALOR TOTAL DO ITEM', 'VALOR_TOTAL', 'Soma de Valor Item', 'Valor Item'],
            'Data': ['DATA', 'DATA DE EMISSÃO', 'DATA EMISSAO', 'Data de Emissão', 'Data']
        }

        for padrao, variacoes in mapa.items():
            for var in variacoes:
                if var in df.columns:
                    df = df.rename(columns={var: padrao})
                    break
        
        if 'Valor Item' in df.columns:
            df['Valor Item'] = df['Valor Item'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Valor Item'] = pd.to_numeric(df['Valor Item'], errors='coerce').fillna(0)
        
        if 'Quantidade' in df.columns:
            df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)

        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
        else:
            df['Mês/Ano'] = 'Sem Data'
            
        df['Plataforma'] = df['Plataforma'].fillna('Outros').astype(str)
        df = df[df['Valor Item'] > 0]
        
        return df
    except Exception as e:
        st.error(f"Erro na sincronização: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- SIDEBAR: FILTROS ---
    st.sidebar.header("Filtros")
    
    # Filtro de Mês
    periodos = sorted([p for p in df['Mês/Ano'].unique() if p and str(p) != 'nan'])
    mes_sel = st.sidebar.multiselect("Mês:", options=periodos, default=periodos)
    
    # Filtro de Plataforma com a opção "Todos"
    plats_originais = sorted([p for p in df['Plataforma'].unique() if p and str(p) != 'nan'])
    opcoes_plataforma = ["Todos"] + plats_originais
    
    # Define "Todos" como padrão inicial
    plat_sel = st.sidebar.multiselect("Plataforma:", options=opcoes_plataforma, default=["Todos"])

    # --- LÓGICA DE FILTRAGEM ---
    if "Todos" in plat_sel:
        df_f = df[df['Mês/Ano'].isin(mes_sel)]
    else:
        df_f = df[(df['Mês/Ano'].isin(mes_sel)) & (df['Plataforma'].isin(plat_sel))]

    # --- MÉTRICAS ---
    c1, c2, c3 = st.columns(3)
    faturamento = df_f['Valor Item'].sum()
    c1.metric("Faturamento Total", formatar_moeda(faturamento))
    c2.metric("Quantidade Total", f"{int(df_f['Quantidade'].sum()):,}".replace(",", "."))
    c3.metric("Ticket Médio", formatar_moeda(faturamento / len(df_f) if len(df_f) > 0 else 0))

    st.markdown("---")

    # --- TABELAS DINÂMICAS ---
    
    # 1. Plataforma e Faturamento
    st.subheader("1. Faturamento por Plataforma")
    t1 = df_f.groupby('Plataforma')['Valor Item'].sum().reset_index().rename(columns={'Valor Item': 'Faturamento'})
    st.dataframe(t1.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

    st.markdown("---")
    
    # Correção do SyntaxError aqui (fechando o parêntese corretamente)
    col_a, col_b = st.columns(2)

    with col_a:
        # 2. Produto, Quantidade e Faturamento
        st.subheader("2. Resumo por Produto")
        t2 = df_f.groupby('Produto').agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).reset_index().rename(columns={'Valor Item': 'Faturamento'})
        st.dataframe(t2.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda}), use_container_width=True)
    
    with col_b:
        # 3. Detalhado (Plataforma + Produto)
        st.subheader("3. Detalhado (Plataforma + Produto)")
        t3 = df_f.groupby(['Plataforma', 'Produto']).agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).reset_index().rename(columns={'Valor Item': 'Faturamento'})
        st.dataframe(t3.sort_values(['Plataforma', 'Faturamento'], ascending=[True, False]).style.format({'Faturamento': formatar_moeda}), use_container_width=True)

    # --- DOWNLOAD ---
    st.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_f.to_excel(writer, index=False)
    st.download_button("📥 Baixar Base Filtrada (Excel)", data=buffer.getvalue(), file_name="Faturamento_Inove.xlsx")

else:
    st.warning("Aguardando dados do Google Sheets...")