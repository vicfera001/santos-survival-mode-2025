import numpy as np, pandas as pd
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt
from .elo import elo_probabilities
from .poisson import poisson_match_probs

NAME_FIX = {
    "Atlético": "Atlético Mineiro",
    "Atletico Mineiro": "Atlético Mineiro",
    "RB Bragantino": "Red Bull Bragantino",
    "Bragantino": "Red Bull Bragantino",
    "Sao Paulo": "São Paulo",
    "Gremio": "Grêmio",
}

def normalize_name(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\xa0", " ").strip()
    while "  " in s:
        s = s.replace("  ", " ")
    return NAME_FIX.get(s, s)

@dataclass
class SeasonSimulator:
    method:str='baseline'
    current_table_path:str='data/current_table.csv'
    remaining_matches_path:str='data/remaining_matches.csv'
    ratings_path:str='data/team_ratings.csv'
    strengths_path:str='data/team_strengths.csv'
    outdir:str='outputs'
    random_seed:int=42

    def _load(self):
        t = pd.read_csv(self.current_table_path)
        m = pd.read_csv(self.remaining_matches_path)

        # Padroniza nomes em current_table e remaining_matches
        m.columns = [c.strip().lower() for c in m.columns]
        t["Team"] = t["Team"].map(normalize_name)
        for c in ("home", "away"):
            if c in m.columns:
                m[c] = m[c].map(normalize_name)

        # (opcional) converte numéricos
        if "Points" in t.columns:
            t["Points"] = pd.to_numeric(t["Points"], errors="raise")
        if "Played" in t.columns:
            t["Played"] = pd.to_numeric(t["Played"], errors="raise")

        self.r_elo = None
        # Carrega ratings e strengths (se existirem), já com strip aplicado
        try:
            r = pd.read_csv(self.ratings_path)
            if "Team" in r.columns:
                r["Team"] = r["Team"].map(normalize_name)
            if "Elo" in r.columns:
                r["Elo"] = pd.to_numeric(r["Elo"], errors="coerce")
                self.r_elo = {row["Team"]: float(row["Elo"]) for _, row in r.dropna(subset=["Elo"]).iterrows()}
            else:
                r = None
        except Exception:
            r = None
        # ---- Forças (Poisson) → dict {Team: (a, d)}
        self.str_lookup = None
        try:
            s = pd.read_csv(self.strengths_path)
            if "Team" in s.columns:
                s["Team"] = s["Team"].map(normalize_name)
            # monta o lookup apenas uma vez; a função _as_lookup aceita DF ou dict
            from .poisson import as_lookup
            self.str_lookup = as_lookup(s)
        except Exception:
            s = None
            self.str_lookup = None

        # Checagem preventiva: todo time citado em m deve existir em t
        missing = (set(m["home"]) | set(m["away"])) - set(t["Team"])
        if missing:
            raise KeyError(f"Times em remaining_matches sem correspondência em current_table: {sorted(missing)}")

        return t, m, r, s

    def _baseline(self,diff,base_draw=0.28):
        pE=float(np.clip(base_draw+0.10*np.exp(-abs(diff)/100.0),0.18,0.36))
        dec=1-pE; pH_no=1/(1+np.exp(-diff/150.0)); pH=dec*pH_no; pA=dec*(1-pH_no)
        return float(pH),float(pE),float(pA)
    
    def _probs(self,home,away,r,stren):
        # Elo: use o lookup (dict) se existir; senão, o DataFrame r
        if self.method=='elo' and (self.r_elo is not None or r is not None):
            src = self.r_elo if isinstance(self.r_elo, dict) and self.r_elo else r
            return elo_probabilities(home,away,src)
        
        # Poisson: use o lookup (dict) se existir; senão, o DataFrame s (stren)
        if self.method=='poisson' and (self.str_lookup is not None or stren is not None):
            src = self.str_lookup if isinstance(self.str_lookup, dict) and self.str_lookup else stren
            return poisson_match_probs(home,away,src)
        
        #Baseline com ajuste por Elo se tivermos o dict (fallback)
        diff=50.0
        if isinstance(self.r_elo, dict) and self.r_elo:
            Rh=float(self.r_elo.get(home,1500.0))
            Ra=float(self.r_elo.get(away,1500.0))
            diff=(Rh+50.0)-Ra
        return self._baseline(diff)
    
    def _once(self,t,m,r,s,rng):
        # pontos em dict -> acesso 0(1)
        pts=dict(zip(t['Team'],t['Points'].astype(float)))
        #itertuples é mais rápido que iterrows
        for home,away in m[["home","away"]].itertuples(index=False, name=None):
            pH,pE,pA=self._probs(home,away,r,s)
            o = rng.choice(("H", "E", "A"), p=[pH, pE, pA])
            if o=="H":
                pts[home]=pts.get(home,0.0)+3.0
            elif o=="E":
                pts[home]=pts.get(home,0.0)+1.0
                pts[away]=pts.get(away,0.0)+1.0
            else: pts[away]=pts.get(away,0.0)+3.0

        # volta para DataFrame com desempate aleatório
        fin = pd.DataFrame({"Team": list(pts.keys()), "Points": list(pts.values())})
        fin["r"] = rng.random(len(fin))
        fin = fin.sort_values(["Points", "r"], ascending=[False, False]).drop(columns=["r"]).reset_index(drop=True)
        fin["Pos"] = np.arange(1, len(fin) + 1)
        return fin

    def run(self,n_sims,santos_name='Santos'):
        #Executa n_sims temporadas a partir da tabela corrente 
        # e dos jogos restantes.
        #Salva:
        #outputs/santos_positions_{method}.png (histograma das posições simuladas)
        #outputs/santos_positions_{method}.csv (distribuição de posições)
        #Retorna:
            #{'santos_not_relegated_prob': <probabilidade de ficar entre 1..16>}
        #garante pasta de saída       
        Path(self.outdir).mkdir(parents=True,exist_ok=True)

        t,m,r,s=self._load(); 
        santos_name_norm= normalize_name(santos_name)
        
        rng=np.random.default_rng(self.random_seed)
        pos=[]
        not_relegated=0
        for _ in range(n_sims):
            fin=self._once(t,m,r,s,rng)
            mask=(fin["Team"]==santos_name_norm)
            if not mask.any():
                disponiveis="', '".join(sorted(fin['Team'].tolist()))
                raise KeyError(
                    f"Time '{santos_name}' não encontrado no resultado final da simulação."
                    f"Verifique a normalização dos nomes. Disponíveis: '{disponiveis}'"
                )
            p=int(fin.loc[mask, "Pos"].iloc[0]); 
            pos.append(p); 
            not_relegated+=(p<=16)
        pos=np.array(pos, dtype=int)
        pr=not_relegated/n_sims

        # --- Figura (histograma) ---
        fig = plt.figure()
        plt.hist(pos, bins=np.arange(0.5, 20.6, 1.0))
        plt.title(f'{santos_name_norm} — {self.method}')
        fig.savefig(f'{self.outdir}/santos_positions_{self.method}.png', dpi=140)
        plt.close(fig)
        
        #CSV (distribuição de posições)
        dist=(pd.Series(pos).value_counts().sort_index()
                .reindex(range(1,21),fill_value=0)
                .rename_axis('Position').reset_index(name='Count'))
        dist["Probability"]=dist['Count']/n_sims
        dist.to_csv(f'{self.outdir}/santos_positions_{self.method}.csv',index=False)    

        return {'santos_not_relegated_prob': float(pr)}
        
