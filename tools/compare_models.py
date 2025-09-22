# tools/compare_models.py
import pandas as pd, numpy as np
from pathlib import Path

METHODS = ["baseline","elo","poisson"]
OUTDIR = Path("outputs")

def read_dist(method):
    df = pd.read_csv(OUTDIR / f"santos_positions_{method}.csv")
    df = df.set_index("Position")["Probability"].reindex(range(1,21), fill_value=0.0)
    return df

def summarize(df):
    idx = df.index.to_numpy()
    prob = df.to_numpy()
    pos_mean = float((idx * prob).sum())
    med = float(idx[np.searchsorted(prob.cumsum(), 0.5)])
    return {
        "Título (1º)":          float(prob[0]),
        "Top-4":                float(prob[:4].sum()),
        "Top-6":                float(prob[:6].sum()),
        "Top-10":               float(prob[:10].sum()),
        "Não rebaixado (1–16)": float(prob[:16].sum()),
        "Rebaixado (17–20)":    float(prob[16:].sum()),
        "Posição média":        pos_mean,
        "Mediana":              med,
    }

rows = []
for m in METHODS:
    try:
        df = read_dist(m)
        rows.append(pd.Series(summarize(df), name=m))
    except FileNotFoundError:
        pass

res = pd.DataFrame(rows)
cols_pct = ["Título (1º)","Top-4","Top-6","Top-10","Não rebaixado (1–16)","Rebaixado (17–20)"]
for c in cols_pct:
    if c in res:
        res[c] = (100*res[c]).round(2).astype(str) + "%"

print("\nComparativo — Santos (modelos)\n")
print(res.to_string(float_format=lambda x: f"{x:.2f}"))
