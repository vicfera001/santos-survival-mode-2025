import argparse
from src.simulator import SeasonSimulator
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--method',choices=['baseline','elo','poisson'],default='baseline')
    p.add_argument('--sims',type=int,default=50000)
    p.add_argument('--santos',type=str,default='Santos')
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--outdir',type=str,default='outputs')
    a=p.parse_args()
    sim=SeasonSimulator(a.method,'data/current_table.csv','data/remaining_matches.csv','data/team_ratings.csv','data/team_strengths.csv',a.outdir,a.seed)
    s=sim.run(a.sims,a.santos)
    print(s)
if __name__=='__main__':
    main()
