# tools/make_fixtures_from_teams.py
import pandas as pd
from pathlib import Path

TABLE = "data/current_table.csv"
OUT   = "data/fixtures_38r.csv"

NAME_FIX = {
    "Atlético": "Atlético Mineiro",
    "Bragantino": "Red Bull Bragantino",
    "Sao Paulo": "São Paulo",
    "Gremio": "Grêmio",
    "Atletico Mineiro": "Atlético Mineiro",
    "RB Bragantino": "Red Bull Bragantino",
}

def load_teams(path):
    df = pd.read_csv(path)
    assert "Team" in df.columns, "Falta a coluna 'Team' em data/current_table.csv"
    teams = [NAME_FIX.get(str(t).strip(), str(t).strip()) for t in df["Team"].tolist()]
    assert len(teams)==20 and len(set(teams))==20, "Devem ser 20 times distintos."
    return teams

def berger_schedule(teams):
    teams = list(teams)
    n = len(teams)
    if n % 2 != 0:
        teams.append("BYE")
        n += 1
    rounds = n - 1
    half = n // 2
    arr = teams[:]
    ida = []
    for r in range(rounds):
        pares = []
        for i in range(half):
            t1, t2 = arr[i], arr[n-1-i]
            if "BYE" in (t1, t2):
                continue
            # alterna mando por rodada
            home, away = (t1, t2) if r % 2 == 0 else (t2, t1)
            pares.append((r+1, home, away))
        ida.extend(pares)
        # rotação mantendo o primeiro fixo
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    volta = [(r+rounds, a, h) for (r, h, a) in ida]
    return ida + volta

def main():
    teams = load_teams(TABLE)
    fixtures = berger_schedule(teams)
    df = pd.DataFrame(fixtures, columns=["round","home","away"]).sort_values(["round","home","away"])
    Path("data").mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"Gerado: {OUT}  (linhas: {len(df)})")

if __name__ == "__main__":
    main()

