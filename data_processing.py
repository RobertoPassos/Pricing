import pandas as pd

# URL do Google Sheets no formato CSV
sheet_url_ref = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=0"
sheet_url_bic = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=169147023"

def load_reference_data(discount_percentage):
    df_ref_ind = pd.read_csv(sheet_url_ref)

    # Ajustar colunas numéricas (substituir vírgulas por pontos e converter para float)
    colunas_precos = ["Sell-in", "Repasse Hubii", "Sugestão de Preço DE"]
    for col in colunas_precos:
        df_ref_ind[col] = df_ref_ind[col].astype(str).str.replace(",", ".").astype(float)

    # Criando a coluna "Sugestão de Preço POR" com o desconto sugerido
    df_ref_ind["Desconto Sugerido"] = df_ref_ind["Sugestão de Preço DE"] * (discount_percentage / 100)
    df_ref_ind["Sugestão de Preço POR"] = df_ref_ind["Sugestão de Preço DE"] - df_ref_ind["Desconto Sugerido"]
    df_ref_ind["Markup Sugerido"] = df_ref_ind["Repasse Hubii"] / df_ref_ind["Sell-in"]

    return df_ref_ind

def load_crawler_data():
    df_crawler_bic = pd.read_csv(sheet_url_bic)
    
    # Ajustar colunas numéricas (substituir vírgulas por pontos e converter para float)
    df_crawler_bic["original_prices"] = df_crawler_bic["original_prices"].astype(str).str.replace(",", ".").astype(float)
    df_crawler_bic["discount_prices"] = df_crawler_bic["discount_prices"].astype(str).str.replace(",", ".").astype(float)
    
    # Converter data para datetime
    df_crawler_bic["crawl_date"] = pd.to_datetime(df_crawler_bic["crawl_date"])
    
    return df_crawler_bic

def merge_crawler_reference(df_ref_ind, df_crawler_bic):
    df_merged = df_crawler_bic.merge(df_ref_ind, left_on="eans", right_on="EAN", how="left")
    
    # Filtrar apenas produtos que têm preço no dia
    df_merged = df_merged.dropna(subset=["discount_prices"])
    
    # Calcular o Price Index (%)
    df_merged["Price Index (%)"] = (df_merged["discount_prices"] / df_merged["Sugestão de Preço POR"]) * 100
    
    # Arredondar todas as colunas numéricas para duas casas decimais
    colunas_numericas = ["Sell-in", "Repasse Hubii", "Sugestão de Preço DE", "Sugestão de Preço POR", "Desconto Sugerido", "Markup Sugerido", "original_prices", "discount_prices", "Price Index (%)"]
    df_merged[colunas_numericas] = df_merged[colunas_numericas].round(2)
    
    # Reorganizar as colunas conforme solicitado
    colunas_ordenadas = [
        "EAN", "Nome do Produto", "Marca", "Sell-in", "Repasse Hubii", "Sugestão de Preço DE", "Sugestão de Preço POR", 
        "Desconto Sugerido", "Markup Sugerido", "original_prices", "discount_prices", "Price Index (%)", "crawl_date"
    ]
    df_merged = df_merged[colunas_ordenadas]
    
    # Formatar valores monetários como R$
    colunas_reais = ["Sell-in", "Repasse Hubii", "Sugestão de Preço DE", "Sugestão de Preço POR", "Desconto Sugerido", "original_prices", "discount_prices"]
    df_merged[colunas_reais] = df_merged[colunas_reais].applymap(lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "")
    
    return df_merged
