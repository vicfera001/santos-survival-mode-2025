# tools/quick_summary.py
import argparse, pandas as pd, numpy as np
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, choices=["baseline","elo","poisson"])
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()

    path = Path(args.outdir) / f"santos_positions_{args.method}.csv"
    df = pd.read_csv(path)  # colunas: Position, Count, Probability

    # reconstrói amostra virtual para métricas simples
    positions = np.repeat(df["Position"].to_numpy(), df["Count"].to_numpy())
    N = positions.size

    metrics = {
        "Título (1º)":          (positions == 1).mean(),
        "Top-4":                (positions <= 4).mean(),
        "Top-6":                (positions <= 6).mean(),
        "Top-10":               (positions <= 10).mean(),
        "Não rebaixado (1–16)": (positions <= 16).mean(),
        "Rebaixado (17–20)":    (positions >= 17).mean(),
        "Posição média":        positions.mean(),
        "Mediana":              float(np.median(positions)),
    }
    print(f"Método: {args.method} | Simulações: {N}")
    for k,v in metrics.items():
        print(f"{k}: {v:.4f}" if "posição" in k.lower() else f"{k}: {100*v:.2f}%")

if __name__ == "__main__":
    main()
