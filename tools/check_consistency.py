# tools/check_consistency.py
import pandas as pd
from collections import Counter

TABLE = "data/current_table.csv"
REMAINING = "data/remaining_matches.csv"  # colunas: round,home,away

TEAMS_2025 = {
 "Flamengo","Cruzeiro","Palmeiras","Mirassol","Botafogo","Bahia","São Paulo",
 "Red Bull Bragantino","Corinthians","Fluminense","Ceará","Internacional",
 "Atlético Mineiro","Grêmio","Vasco da Gama","Santos","Vitória","Juventude",
 "Fortaleza","Sport"
}
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
    assert len(df)==20, f"Devem ser 20 times; encontrei {len(df)}"
    assert df["Team"].is_unique, "Times repetidos em current_table.csv"
    df["Points"] = pd.to_numeric(df["Points"], errors="raise").astype(int)
    df["Played"] = pd.to_numeric(df["Played"], errors="raise").astype(int)
    return df[["Team","Points","Played"]]

def load_remaining(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    assert {"round","home","away"}.issubset(df.columns), f"Colunas esperadas: round, home, away. Obtido: {df.columns.tolist()}"
    for col in ["home","away"]:
        df[col] = df[col].map(lambda x: NAME_FIX.get(str(x).strip(), str(x).strip()))
    df["round"] = pd.to_numeric(df["round"], errors="raise").astype(int)
    return df[["round","home","away"]]

def main():
    table = load_table(TABLE)
    remaining = load_remaining(REMAINING)

    rounds_fully_completed = int(table["Played"].min())
    round_in_progress = rounds_fully_completed + 1 if table["Played"].max() > rounds_fully_completed else None
    print(f"Rodadas completamente concluídas: {rounds_fully_completed}")
    print(f"Rodada em andamento: {round_in_progress if round_in_progress else 'nenhuma'}")

    names = set(table["Team"])
    faltam = TEAMS_2025 - names
    extras = names - TEAMS_2025
    if faltam: print("⚠️ Faltando na tabela:", sorted(faltam))
    if extras: print("⚠️ Nomes fora do padrão na tabela:", sorted(extras))
    if not faltam and not extras:
        print("✅ Participantes batem com a Série A 2025.")

    expected_remaining = {t: 38 - int(p) for t,p in table.set_index("Team")["Played"].items()}
    c = Counter()
    for _, row in remaining.iterrows():
        c[row["home"]] += 1
        c[row["away"]] += 1
    remaining_count = dict(c)

    diffs = []
    for t in sorted(names):
        exp = expected_remaining.get(t, None)
        got = remaining_count.get(t, 0)
        if exp != got:
            diffs.append((t, exp, got))
    if diffs:
        print("\n⚠️ Diferenças entre '38 - Played' e jogos em remaining_matches.csv:")
        for t, exp, got in diffs:
            print(f" - {t}: esperado {exp}, arquivo tem {got}")
    else:
        print("\n✅ remaining_matches.csv consistente com current_table.csv para todos os times.")

    if not remaining.empty:
        rounds_list = sorted(remaining["round"].unique())
        print(f"\nRodadas ainda listadas em remaining_matches: {rounds_list}")
        round_sizes = remaining.groupby("round").size()
        bad = round_sizes[round_sizes != 10]
        if not bad.empty:
            print("⚠️ Rodadas com quantidade ≠ 10 jogos (pode haver adiamentos):")
            print(bad.to_string())

if __name__ == "__main__":
    main()
