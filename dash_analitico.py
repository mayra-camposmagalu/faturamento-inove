import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Faturamento Inove", layout="wide", page_icon="📊")

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

    LINK_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7RsXNDvNTLHTpbvDjjN9yUWq2EzTiCLDmXIFc3b_1g7G00hFCiuWcD-qWuJOD9w/pub?gid=1866890896&single=true&output=csv"

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @st.cache_data(ttl=5)
    def load_data():
        try:
            df = pd.read_csv(LINK_BASE)
            df.columns = [str(c).strip() for c in df.columns]

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
            
            # Limpeza Crítica de Texto (Remove espaços e padroniza)
            df['Produto'] = df['Produto'].astype(str).str.strip()
            df['Plataforma'] = df['Plataforma'].astype(str).str.strip()
            
            # Tratamento de Valores
            df['Valor Item'] = df['Valor Item'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df['Valor Item'] = pd.to_numeric(df['Valor Item'], errors='coerce').fillna(0)
            
            # Tratamento de Quantidade (Garante que seja número limpo)
            df['Quantidade'] = df['Quantidade'].astype(str).str.replace(',', '.', regex=False).str.strip()
            df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
            
            # Tratamento de Datas
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
            
            return df
        except Exception as e:
            st.error(f"Erro: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        st.sidebar.header("Filtros")
        meses = sorted(df['Mês/Ano'].unique(), reverse=True)
        mes_sel = st.sidebar.multiselect("Mês:", meses, default=meses)
        
        plats = sorted(df['Plataforma'].unique())
        opcoes_plat = ["Todos"] + plats
        plat_sel = st.sidebar.multiselect("Plataforma:", opcoes_plat, default=["Todos"])

        df_f = df[df['Mês/Ano'].isin(mes_sel)].copy()
        if "Todos" not in plat_sel:
            df_f = df_f[df_f['Plataforma'].isin(plat_sel)]

        # KPIs
        c1, c2, c3 = st.columns(3)
        total = df_f['Valor Item'].sum()
        c1.metric("Faturamento Total", formatar_moeda(total))
        c2.metric("Quantidade Total", f"{int(df_f['Quantidade'].sum()):,}".replace(",", "."))
        c3.metric("Ticket Médio", formatar_moeda(total / len(df_f) if len(df_f) > 0 else 0))

        st.markdown("---")

        # 1. Plataforma
        t1 = df_f.groupby('Plataforma', as_index=False)['Valor Item'].sum().rename(columns={'Valor Item': 'Faturamento'})
        st.subheader("1. Faturamento por Plataforma")
        st.dataframe(t1.style.format({'Faturamento': formatar_moeda}), use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("2. Ranking de Produtos")
            t2 = df_f.groupby('Produto', as_index=False).agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(t2.sort_values('Faturamento', ascending=False).style.format({'Faturamento': formatar_moeda, 'Quantidade': '{:.0f}'}), use_container_width=True)
        
        with col_b:
            st.subheader("3. Detalhado (Plataforma + Produto)")
            t3 = df_f.groupby(['Plataforma', 'Produto'], as_index=False).agg({'Quantidade': 'sum', 'Valor Item': 'sum'}).rename(columns={'Valor Item': 'Faturamento'})
            st.dataframe(t3.sort_values(['Plataforma', 'Faturamento'], ascending=[True, False]).style.format({'Faturamento': formatar_moeda, 'Quantidade': '{:.0f}'}), use_container_width=True)

        st.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.download_button("📥 Baixar Excel", data=buffer.getvalue(), file_name="Inove.xlsx")
