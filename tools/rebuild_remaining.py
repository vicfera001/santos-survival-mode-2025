# tools/rebuild_remaining.py
import pandas as pd

TABLE = "data/current_table.csv"
FIXTURES_ALL = "data/fixtures_38r.csv"      # calendário completo com 38 rodadas
OUT = "data/remaining_matches_atualizado.csv"

NAME_FIX = {
    "Atlético": "Atlético Mineiro",
    "Bragantino": "Red Bull Bragantino",
    "Sao Paulo": "São Paulo",
    "Gremio": "Grêmio",
    "Atletico Mineiro": "Atlético Mineiro",
    "RB Bragantino": "Red Bull Bragantino",
}

def load_table(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    assert {"Team","Points","Played"}.issubset(df.columns), f"Colunas esperadas: Team, Points, Played. Obtido: {df.columns.tolist()}"
    df["Team"] = df["Team"].map(lambda x: NAME_FIX.get(str(x).strip(), str(x).strip()))
    df["Points"] = pd.to_numeric(df["Points"], errors="raise").astype(int)
    df["Played"] = pd.to_numeric(df["Played"], errors="raise").astype(int)
    return df.set_index("Team")[["Played"]]

def load_fixtures(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    assert {"round","home","away"}.issubset(df.columns), "Esperado: round, home, away"
    for col in ["home","away"]:
        df[col] = df[col].map(lambda x: NAME_FIX.get(str(x).strip(), str(x).strip()))
    df["round"] = pd.to_numeric(df["round"], errors="raise").astype(int)
    return df[["round","home","away"]]

table = load_table(TABLE)
fix = load_fixtures(FIXTURES_ALL)

# Um jogo da rodada r foi disputado se (Played_home >= r) e (Played_away >= r)
fix = fix.merge(table, left_on="home", right_index=True).rename(columns={"Played":"played_home"})
fix = fix.merge(table, left_on="away", right_index=True).rename(columns={"Played":"played_away"})

played_mask = (fix["played_home"] >= fix["round"]) & (fix["played_away"] >= fix["round"])
remaining = fix.loc[~played_mask, ["round","home","away"]].sort_values(["round","home","away"]).reset_index(drop=True)

remaining.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"Arquivo gerado: {OUT}  (linhas: {len(remaining)})")

# Diagnóstico resumido por time
cnt = {}
for t in table.index:
    cnt[t] = ((remaining["home"]==t) | (remaining["away"]==t)).sum()
rep = pd.DataFrame({"Team": list(cnt.keys()), "RemainingFromFile": list(cnt.values())})
rep["Expected(38-Played)"] = 38 - table.loc[rep["Team"], "Played"].values
rep["Diff"] = rep["RemainingFromFile"] - rep["Expected(38-Played)"]
print("\nResumo por time (RemainingFromFile vs Expected):")
print(rep.sort_values('Team').to_string(index=False))
