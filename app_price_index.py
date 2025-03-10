import streamlit as st
import pandas as pd
from data_processing import load_reference_data, load_crawler_data, merge_crawler_reference

st.set_page_config(page_title="Monitoramento de Preços", layout="wide")
st.title("📊 Monitoramento de Preço - Hubii")

# Criando as abas no Streamlit
tab1, tab2 = st.tabs(["📌 Arquitetura de Preço Referência", "📊 Beleza em Casa iFood"])

# Tab 1: Arquitetura de Preço Referência**
with tab1:
    st.subheader("📌 Arquitetura de Preço - Referência da Indústria")
    
    col1, col2 = st.columns([0.25, 0.75])
    
    with col1:
        opcao_busca = st.radio("🔍 Buscar por:", ["EAN", "Marca", "Nome do Produto"], horizontal=True)
        desconto_sugerido = st.number_input("🔻 Desconto Sugerido (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        df_ref_ind = load_reference_data(desconto_sugerido)
        
        filtro_selecionado = None
        if opcao_busca == "EAN":
            filtro_selecionado = st.selectbox("Selecione o EAN", [""] + list(df_ref_ind["EAN"].unique()))
        elif opcao_busca == "Marca":
            filtro_selecionado = st.selectbox("Selecione a Marca", [""] + list(df_ref_ind["Marca"].unique()))
        elif opcao_busca == "Nome do SKU":
            filtro_selecionado = st.selectbox("Selecione o SKU", [""] + list(df_ref_ind["Nome do Produto"].unique()))
    
    df_filtrado = df_ref_ind.copy()
    if filtro_selecionado:
        df_filtrado = df_filtrado[df_filtrado[opcao_busca] == filtro_selecionado]
    
    st.write("### 📄 Dados de Referência")
    st.dataframe(df_filtrado.style.format({
        "Sell-in": "R$ {:.2f}",
        "Repasse Hubii": "R$ {:.2f}",
        "Sugestão de Preço DE": "R$ {:.2f}",
        "Sugestão de Preço POR": "R$ {:.2f}",
        "Desconto Sugerido": "R$ {:.2f}",
        "Markup Sugerido": "{:.2f}x"
    }))

# tab2: Beleza em Casa iFood**
with tab2:
    st.subheader("📊 Beleza em Casa iFood - Monitoramento de Preços")
    
    # Carregar dados do crawler e referência
    df_crawler_bic = load_crawler_data()
    df_merged = merge_crawler_reference(df_ref_ind, df_crawler_bic)
    
    # Criar seleção de data inicial e final com base nos dados disponíveis
    min_date = df_merged["crawl_date"].min()
    max_date = df_merged["crawl_date"].max()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.selectbox("📅 Data Inicial", df_merged["crawl_date"].sort_values().unique(), index=0)
    with col2:
        end_date = st.selectbox("📅 Data Final", df_merged["crawl_date"].sort_values().unique(), index=len(df_merged["crawl_date"].unique()) - 1)
    
    df_filtered = df_merged[(df_merged["crawl_date"] >= start_date) & (df_merged["crawl_date"] <= end_date)]
    
    # Filtro de Marca com Multiselect
    marcas_disponiveis = ["Todas as Marcas"] + sorted(df_filtered["Marca"].dropna().unique().tolist())
    marcas_selecionadas = st.multiselect("🛍️ Selecione a Marca", marcas_disponiveis, default=["Todas as Marcas"])
    
    # Aplicar filtro de marca se diferente de "Todas as Marcas"
    if "Todas as Marcas" not in marcas_selecionadas:
        df_filtered = df_filtered[df_filtered["Marca"].isin(marcas_selecionadas)]
    
    st.write("### 📄 Comparação de Preços")
    st.dataframe(df_filtered)
    st.write("O Price Index calculado na tabela acima é o comparativo do valor praticano no ifood com a tabela de referência fornecida pelo Boticário.")
