import pandas as pd

def filter_df_with_object(df: pd.DataFrame, object_name: str) -> pd.DataFrame:
    mask = df["caption"].astype(str).str.contains(object_name, case=False, na=False)
    df = df.loc[mask].copy()
    token_len = (df["caption"].fillna("").astype(str).str.split().str.len())
    df = df[token_len < 20]
    
    df["caption"] = (df["caption"].fillna("")
                      .astype(str)
                      .str.replace(r"\s+", " ", regex=True)
                      .str.strip())

    df = df[df["caption"] != ""]
    return df.reset_index(drop=True)