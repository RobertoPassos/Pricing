import streamlit as st
import pandas as pd
from data_processing import load_reference_data, load_crawler_raw_data, adjust_df, merge_crawler_reference_bec, price_ref_maker, final_table_maker

st.set_page_config(page_title="Monitoramento de Preços", layout="wide")
st.title("📊 Monitoramento de Preço - Boticário // Hubii")

# Criando as abas no Streamlit
tab1, tab2, tab3 = st.tabs(["📌 Arquitetura de Preço Referência", "📊 Beleza em Casa iFood", "👀 Beleza em Casa (iFood) vs. Outros Canais"])

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
        elif opcao_busca == "Nome do Produto":
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
    df_crawler_ifood, df_crawler_epoca, df_crawler_bnw, df_crawler_rd, df_crawler_meli, df_crawler_bec = load_crawler_raw_data()
    df_crawler_ifood=adjust_df(df_crawler_ifood)
    df_crawler_bec=adjust_df(df_crawler_bec)
    
    df_merged = merge_crawler_reference_bec(df_ref_ind, df_crawler_bec)
    
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

    st.write("### 📄 Price Index:")
    Price_Index = df_filtered["Price Index (%)"].mean()
    st.write((f"{Price_Index:.2f}%"))
    
    st.write("### 📄 Comparação de Preços")
    st.dataframe(df_filtered.style.format({
        "Sell-in": "R$ {:.2f}",
        "Repasse Hubii": "R$ {:.2f}",
        "Sugestão de Preço DE": "R$ {:.2f}",
        "Sugestão de Preço POR": "R$ {:.2f}",
        "Desconto Sugerido": "R$ {:.2f}",
        "Markup Sugerido": "{:.2f}x",
        "original_prices": "R$ {:.2f}",
        "discount_prices": "R$ {:.2f}",
        "final_price": "R$ {:.2f}",
        "Price Index (%)": "{:.2f}%"
    }))
    st.write("O Price Index calculado na tabela acima é o comparativo do valor praticado no ifood com a tabela de referência fornecida pelo Boticário.")

# tab3: Beleza em Casa (iFood) vs. Outros Canais
with tab3:
    st.subheader("📊 Como estamos em relação aos outros canais?")

    df_crawler_epoca=adjust_df(df_crawler_epoca)
    df_crawler_bnw=adjust_df(df_crawler_bnw)
    df_crawler_rd=adjust_df(df_crawler_rd)
    df_crawler_meli=adjust_df(df_crawler_meli)

    df_crawler_bec_simp=price_ref_maker(df_crawler_bec)
    df_crawler_ifood_simp=price_ref_maker(df_crawler_ifood)
    df_crawler_epoca_simp=price_ref_maker(df_crawler_epoca)
    df_crawler_bnw_simp=price_ref_maker(df_crawler_bnw)
    df_crawler_rd_simp=price_ref_maker(df_crawler_rd)
    df_crawler_meli_simp=price_ref_maker(df_crawler_meli)
    
    df_crawler_bec_simp.rename(columns={"final_price": "final_price_bec"}, inplace=True)
    df_crawler_ifood_simp.rename(columns={"final_price": "final_price_ifood"}, inplace=True)
    df_crawler_epoca_simp.rename(columns={"final_price": "final_price_epoca"}, inplace=True)
    df_crawler_bnw_simp.rename(columns={"final_price": "final_price_bnw"}, inplace=True)
    df_crawler_rd_simp.rename(columns={"final_price": "final_price_rd"}, inplace=True)
    df_crawler_meli_simp.rename(columns={"final_price": "final_price_meli"}, inplace=True)
    
    df_list = [df_crawler_ifood_simp, df_crawler_epoca_simp, df_crawler_bnw_simp, df_crawler_rd_simp, df_crawler_meli_simp]
    df_base = final_table_maker(df_list, df_crawler_bec_simp, df_ref_ind)

    min_date = df_base["crawl_date"].min()
    max_date = df_base["crawl_date"].max()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.selectbox("📅 Data Inicial", df_base["crawl_date"].sort_values().unique(), index=0)
    with col2:
        end_date = st.selectbox("📅 Data Final", df_base["crawl_date"].sort_values().unique(), index=len(df_base["crawl_date"].unique()) - 1)
    
    df_filtered = df_base[(df_base["crawl_date"] >= start_date) & (df_base["crawl_date"] <= end_date)]
    
    # Filtro de Marca com Multiselect
    marcas_disponiveis = ["Todas as Marcas"] + sorted(df_filtered["Marca"].dropna().unique().tolist())
    marcas_selecionadas = st.multiselect("🛍️ Selecione a Marca", marcas_disponiveis, default=["Todas as Marcas"], key="multiselect_tab3")
    
    # Aplicar filtro de marca se diferente de "Todas as Marcas"
    if "Todas as Marcas" not in marcas_selecionadas:
        df_filtered = df_filtered[df_filtered["Marca"].isin(marcas_selecionadas)]

    st.write("### 📄 Price Index por Canal:")

    col3, col4, col5, col6, col7 = st.columns(5)
    with col3:
        st.write("iFood:")
        price_index_ifood = df_filtered["price_index_ifood"].mean()
        st.write((f"### {price_index_ifood:.2f}%"))
    with col4:
        st.write("Época Cosméticos:")
        price_index_epoca = df_filtered["price_index_epoca"].mean()
        st.write((f"### {price_index_epoca:.2f}%"))
    with col5:
        st.write("Beleza na Web:")
        price_index_bnw = df_filtered["price_index_bnw"].mean()
        st.write((f"### {price_index_bnw:.2f}%"))
    with col6:
        st.write("Raia-Drogasil:")
        price_index_rd = df_filtered["price_index_rd"].mean()
        st.write((f"### {price_index_rd:.2f}%"))
    with col7:
        st.write("Mercado Livre:")
        price_index_meli = df_filtered["price_index_meli"].mean()
        st.write((f"### {price_index_meli:.2f}%"))

    
    st.write("Segue o comparativos da loja Beleza em Casa com os canais mais relevantes do mercado...")
    st.dataframe(df_filtered.style.format({
        "price_index_ifood": "{:.2f}%",
        "price_index_epoca": "{:.2f}%",
        "price_index_bnw": "{:.2f}%",
        "price_index_rd": "{:.2f}%",
        "price_index_meli": "{:.2f}%",
        "final_price_bec": "R${:.2f}",
        "final_price_ifood": "R${:.2f}",
        "final_price_epoca": "R${:.2f}",
        "final_price_bnw": "R${:.2f}",
        "final_price_rd": "R${:.2f}",
        "final_price_meli": "R${:.2f}"
    }))
