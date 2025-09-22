# src/poisson.py
import numpy as np

# Parâmetros médios (podem ser calibrados a partir dos dados históricos)
MU_HOME = 1.40
MU_AWAY = 1.10

def _pick_col(df, candidates):
    cols = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in cols:
            return cols[c]
    raise KeyError(f"Coluna não encontrada. Candidatei: {candidates} — existentes: {list(df.columns)}")

def _as_lookup(strengths):
    """
    Converte 'strengths' em um dict {Team: (attack, defense)}.
    Aceita DataFrame (com colunas de ataque/defesa) OU dict já pronto.
    """
    if isinstance(strengths, dict):
        return strengths

    if strengths is None:
        return {}
    
    # Importa pandas somente quando necessário
    import pandas as pd
    import numpy as np

    df = strengths.copy()
    # normaliza nomes de times
    df["Team"] = df["Team"].astype(str).str.replace("\xa0", " ").str.strip()

    # Localiza colunas de ataque/defesa por nomes comuns
    def _pick_col(df, candidates):
        cols = {c.lower(): c for c in df.columns}
        for c in candidates:
            if c in cols:
                return cols[c]
        raise KeyError(f"Coluna não encontrada. Candidatei: {candidates} — existentes: {list(df.columns)}")
    
    # tenta achar colunas de ataque/defesa com nomes comuns
    a_col = _pick_col(df, ["a", "attack", "atk"])
    d_col = _pick_col(df, ["d", "defense", "def"])

    # Conversão numérica vetorizada
    a = pd.to_numeric(df[a_col], errors="coerce").to_numpy()
    d = pd.to_numeric(df[d_col], errors="coerce").to_numpy()
    teams = df["Team"].to_numpy()

    mask = ~(np.isnan(a) | np.isnan(d))
    return {t: (float(aa), float(dd)) for t, aa, dd in zip(teams[mask], a[mask], d[mask])}

def _poisson_pmf(lam, kmax):
    """PMF de Poisson até kmax (inclusivo), sem fatorial explícito."""
    pmf = np.empty(kmax + 1, dtype=float)
    pmf[0] = np.exp(-lam)
    for k in range(1, kmax + 1):
        pmf[k] = pmf[k-1] * lam / k
    # pequena normalização numérica (caso kmax seja baixo)
    s = pmf.sum()
    if s > 0:
        pmf /= s
    return pmf

def poisson_match_probs(home: str, away: str, strengths, mu_home=MU_HOME, mu_away=MU_AWAY, gmax=10):
    """
    Calcula (pH, pE, pA) com taxas λ_H = mu_home * a_H * d_A e λ_A = mu_away * a_A * d_H.
    'strengths' pode ser DataFrame (com Team + a/attack/atk, d/defense/def) ou dict {Team: (a,d)}.
    """
    lut = _as_lookup(strengths)  # dict {Team: (a, d)}

    aH, dH = lut.get(home, (1.0, 1.0))
    aA, dA = lut.get(away, (1.0, 1.0))

    lamH = float(mu_home) * float(aH) * float(dA)
    lamA = float(mu_away) * float(aA) * float(dH)

    # PMFs truncadas até gmax (rápido e suficiente para futebol)
    pmfH = _poisson_pmf(lamH, gmax)
    pmfA = _poisson_pmf(lamA, gmax)
    cdfA = np.cumsum(pmfA)

    # Empate: sum_k P_H(k) * P_A(k)
    pE = float(np.dot(pmfH, pmfA))

    # Mandante vence: sum_i P_H(i) * P_A(<= i-1)
    cdfA_prev = np.concatenate(([0.0], cdfA[:-1]))
    pH = float(np.dot(pmfH, cdfA_prev))

    # Visitante vence: complemento
    pA = 1.0 - pH - pE

    # Saneamento numérico
    pH = max(0.0, min(1.0, pH))
    pE = max(0.0, min(1.0, pE))
    pA = max(0.0, min(1.0, pA))

    # Normaliza se houver drift numérico
    s = pH + pE + pA
    if s > 0:
        pH, pE, pA = pH/s, pE/s, pA/s

    return pH, pE, pA
