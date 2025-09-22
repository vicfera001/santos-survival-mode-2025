# tools/audit_ratings.py
import pandas as pd
from pathlib import Path

def normalize(s: str) -> str:
    s = str(s).replace("\xa0"," ").strip()
    while "  " in s: s = s.replace("  "," ")
    MAP = {"Atlético":"Atlético Mineiro", "Atletico Mineiro":"Atlético Mineiro",
           "RB Bragantino":"Red Bull Bragantino", "Bragantino":"Red Bull Bragantino",
           "Sao Paulo":"São Paulo", "Gremio":"Grêmio"}
    return MAP.get(s, s)

t = pd.read_csv("data/current_table.csv")
t["Team"] = t["Team"].map(normalize)

try:
    r = pd.read_csv("data/team_ratings.csv")
    r["Team"] = r["Team"].map(normalize)
    r["Elo"] = pd.to_numeric(r["Elo"], errors="coerce")
except Exception as e:
    print("Não foi possível abrir data/team_ratings.csv:", e)
    raise SystemExit

present = set(r.dropna(subset=["Elo"])["Team"])
needed  = set(t["Team"])
missing = sorted(needed - present)

print("Cobertura de ratings:", f"{len(present)}/{len(needed)} times com Elo válido.")
if missing:
    print("Ausentes:", ", ".join(missing))

elos = r["Elo"].dropna()
if not elos.empty:
    print("\nEstatísticas dos Elo válidos:")
    print(f"Média: {elos.mean():.1f} | Desvio-padrão: {elos.std():.1f} | Mín: {elos.min():.1f} | Máx: {elos.max():.1f}")
