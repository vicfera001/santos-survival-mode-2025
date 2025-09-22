# fetch_current_table.py
import pandas as pd

URL = "https://en.wikipedia.org/wiki/2025_Campeonato_Brasileiro_S%C3%A9rie_A"

def get_league_table(url: str) -> pd.DataFrame:
    tables = pd.read_html(url)
    # Procura uma tabela que tenha colunas de posição e pontos
    for t in tables:
        cols = [str(c).lower() for c in t.columns]
        if any("pos" in c for c in cols) and any("pts" in c or "points" in c for c in cols):
            df = t.copy()
            # normaliza nomes de colunas comuns
            colmap = {}
            for c in df.columns:
                cl = str(c).lower()
                if "team" in cl or "club" in cl:
                    colmap[c] = "Team"
                elif cl.startswith("pld") or "played" in cl:
                    colmap[c] = "Played"
                elif cl.startswith("pts") or "points" in cl:
                    colmap[c] = "Points"
            df = df.rename(columns=colmap)
            if {"Team","Points","Played"}.issubset(df.columns):
                return df[["Team","Points","Played"]]
    raise RuntimeError("Tabela de liga não encontrada.")

df = get_league_table(URL)

# Opcional: padronização de nomes (ajuste apenas se seu pipeline exigir)
name_map = {
    "RB Bragantino": "Red Bull Bragantino",
    "Atletico Mineiro": "Atlético Mineiro",
    "Gremio": "Grêmio",
    "Sao Paulo": "São Paulo",
}
df["Team"] = df["Team"].replace(name_map)

# Garantir tipos inteiros
df["Points"] = pd.to_numeric(df["Points"], errors="coerce").astype("Int64")
df["Played"] = pd.to_numeric(df["Played"], errors="coerce").astype("Int64")

# Salva para o projeto (UTF-8 com BOM -> Excel abre com acentos corretos)
df.to_csv("data/current_table.csv", index=False, encoding="utf-8-sig")
print(df.head())
