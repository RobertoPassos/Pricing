import pandas as pd
import numpy as np

# URL do Google Sheets no formato CSV
sheet_url_ref   = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=0"
sheet_url_ifood = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=2128778105"
sheet_url_epoca = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=1140492275"
sheet_url_bnw   = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=169147023"
sheet_url_rd    = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=1708084953"
sheet_url_meli  = "https://docs.google.com/spreadsheets/d/1gi_DzxjKoYQcKrwp7HJgmGYR-DRpK0kX71mwgl9EEJE/export?format=csv&gid=1787364151"

def load_reference_data(discount_percentage):
    df_ref_ind = pd.read_csv(sheet_url_ref)
    colunas_precos = ["Sell-in", "Repasse Hubii", "Sugestão de Preço DE"]
    for col in colunas_precos:
        df_ref_ind[col] = df_ref_ind[col].astype(str).str.replace(",", ".").astype(float)

    df_ref_ind["Desconto Sugerido"] = df_ref_ind["Sugestão de Preço DE"] * (discount_percentage / 100)
    df_ref_ind["Sugestão de Preço POR"] = df_ref_ind["Sugestão de Preço DE"] - df_ref_ind["Desconto Sugerido"]
    df_ref_ind["Markup Sugerido"] = df_ref_ind["Repasse Hubii"] / df_ref_ind["Sell-in"]

    return df_ref_ind

def load_crawler_raw_data():
    df_crawler_ifood = pd.read_csv(sheet_url_ifood)
    df_crawler_epoca = pd.read_csv(sheet_url_epoca)
    df_crawler_bnw = pd.read_csv(sheet_url_bnw)
    df_crawler_rd = pd.read_csv(sheet_url_rd)
    df_crawler_meli = pd.read_csv(sheet_url_meli)
    df_crawler_bec = df_crawler_ifood[df_crawler_ifood["stores"] == "Beleza em Casa"][["names","stores","eans", "original_prices", "discount_prices", "crawl_date"]]

    return df_crawler_ifood, df_crawler_epoca, df_crawler_bnw, df_crawler_rd, df_crawler_meli, df_crawler_bec

def add_final_price(df):
    df["final_price"] = np.where(
    (df["discount_prices"].notna()) & (df["discount_prices"] < df["original_prices"]),
    df["discount_prices"],
    df["original_prices"]
    )
    return df

def adjust_df(df):
    df["original_prices"] = df["original_prices"].astype(str).str.replace(",", ".").astype(float)
    df["discount_prices"] = df["discount_prices"].astype(str).str.replace(",", ".").astype(float)
    df["crawl_date"] = pd.to_datetime(df["crawl_date"])
    df=add_final_price(df)
    seq_df=['names','stores','eans','original_prices','discount_prices','final_price','crawl_date']
    df=df[seq_df]
    return df

def merge_crawler_reference_bec(df_ref_ind, df_crawler_bec):
    df_merged = df_ref_ind.merge(df_crawler_bec, left_on="EAN", right_on="eans", how="left")
    df_merged = df_merged.dropna(subset=["original_prices"]) # Filtrar apenas produtos que têm preço no dia
    df_merged["Price Index (%)"] = (df_merged["final_price"] / df_merged["Sugestão de Preço POR"]) * 100 # Calcular o Price Index (%)
    
    # Reorganizar as colunas conforme solicitado
    colunas_ordenadas = [
        "EAN", "Nome do Produto", "Marca", "Sell-in", "Repasse Hubii", "Sugestão de Preço DE", "Sugestão de Preço POR", 
        "Desconto Sugerido", "Markup Sugerido", "original_prices", "discount_prices","final_price", "Price Index (%)", "crawl_date"
    ]
    df_merged = df_merged[colunas_ordenadas]
    
    return df_merged

def price_ref_maker(df):
    df_counts = df.groupby(["eans", "crawl_date"]).size().reset_index(name="count")
    df = df.merge(df_counts, on=["eans", "crawl_date"], how="left")
    df_min_price = df.groupby(["eans", "crawl_date"])["final_price"].min().reset_index()
    df_filtered = df.merge(df_min_price, on=["eans", "crawl_date", "final_price"], how="left", indicator=True)
    df_filtered = df_filtered[~((df_filtered["count"] > 4) & (df_filtered["_merge"] == "both"))]
    df_final = df_filtered.groupby(["eans", "crawl_date"])["final_price"].min().reset_index()

    return df_final

def final_table_maker(df_list, reference_df, df_ref_ind):
    for df in df_list:
        df["eans"] = df["eans"].astype(str)
    
    all_dfs = [reference_df] + df_list
    df_base = pd.concat([df[["eans", "crawl_date"]] for df in all_dfs]).drop_duplicates()
    
    df_base = df_base.merge(df_ref_ind[["EAN", "Marca", "Nome do Produto"]], left_on="eans", right_on="EAN", how="inner")
    df_base.drop(columns=["EAN"], inplace=True)
    
    # Identificar a coluna de preço de referência
    ref_price_col = [col for col in reference_df.columns if "final_price" in col][0]
    
    # Adicionar final_price do reference_df
    df_base = df_base.merge(reference_df[["eans", "crawl_date", ref_price_col]], on=["eans", "crawl_date"], how="left")
    
    # Adicionar os preços finais de cada DataFrame da lista e calcular o price index
    for df in df_list:
        final_price_cols = [col for col in df.columns if "final_price" in col]
        
        for price_col in final_price_cols:
            df_base = df_base.merge(df[["eans", "crawl_date", price_col]], on=["eans", "crawl_date"], how="left")
            
            # Criar nome da coluna de price index
            price_index_col = price_col.replace("final_price_", "price_index_")
            
            # Calcular a razão entre final_price da referência e do canal
            df_base[price_index_col] = df_base[ref_price_col]*100 / df_base[price_col]
    
    return df_base
