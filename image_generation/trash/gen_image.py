import pandas as pd
df = pd.read_parquet("cc12m_7m_subset_translated.parquet", columns=["caption", "url"])

mask = df["caption"].str.contains("TV ", case=False, na=False)
apple_df = df.loc[mask].copy()

apple_df.to_csv('tv_image.csv')
