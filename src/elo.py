# src/elo.py
import numpy as np

# Parâmetros padrão do modelo Elo
DEFAULT_ELO = 1500.0
HOME_ADV    = 50.0       # vantagem de mando adicionada ao Elo do mandante
GAMMA       = 400.0      # escala logística base-10 (clássica do Elo)

# Empate: simples (fixo) ou dinâmico (opcional)
BASE_DRAW   = 0.28
USE_DYNAMIC_DRAW = False  # mude para True se quiser empates dinâmicos
BETA        = 0.10
TAU         = 100.0
P_MIN, P_MAX = 0.18, 0.36

def _as_lookup(ratings):
    """Converte ratings em dict {Team: Elo}, aceitando DataFrame ou dict."""
    if isinstance(ratings, dict):
        return ratings
    try:
        # espera colunas 'Team' e 'Elo'
        teams = ratings["Team"].tolist()
        elos  = ratings["Elo"].tolist()
        return {t: float(e) for t, e in zip(teams, elos) if e == e}  # filtra NaN
    except Exception:
        return {}

def elo_probabilities(home: str, away: str, ratings):
    lut = _as_lookup(ratings)
    Rh = float(lut.get(home, DEFAULT_ELO))
    Ra = float(lut.get(away, DEFAULT_ELO))
    d  = (Rh + HOME_ADV) - Ra

    if USE_DYNAMIC_DRAW:
        pE = float(np.clip(BASE_DRAW + BETA*np.exp(-abs(d)/TAU), P_MIN, P_MAX))
    else:
        pE = BASE_DRAW

    dec   = 1.0 - pE
    pH_no = 1.0 / (1.0 + 10.0**(-d / GAMMA))  # logística base-10
    pH    = dec * pH_no
    pA    = dec * (1.0 - pH_no)
    return float(pH), float(pE), float(pA)
