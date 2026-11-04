"""Matrice IMAM8MAHDI : centres High/Low, cinq couples, preuves trivalentes."""
from decimal import Decimal as D
from enum import Enum
HORIZONS=("12M","1M","1W","1D","1H","5m")
class Etat(str,Enum):
    VRAI="VRAI"; FAUX="FAUX"; INCONNU="INCONNU"
def et(etats):
    if Etat.FAUX in etats:return Etat.FAUX
    if all(x==Etat.VRAI for x in etats):return Etat.VRAI
    return Etat.INCONNU
def calcul(bougies):
    """bougies[h]={'high':..., 'low':..., 'closed':bool}; six horizons requis."""
    if set(bougies)!=set(HORIZONS):raise ValueError("Six horizons requis")
    centres={}
    for h in HORIZONS:
        b=bougies[h]; hi,lo=D(str(b["high"])),D(str(b["low"]))
        if hi<lo:raise ValueError("high < low")
        centres[h]=(hi+lo)/2
    f=[centres[HORIZONS[i]]-centres[HORIZONS[i+1]] for i in range(5)]
    assert sum(f,D(0))==centres["12M"]-centres["5m"]
    return {"centres":{h:str(v) for h,v in centres.items()},
            "forces":{f"F{i}":str(v) for i,v in enumerate(f)},
            "synchronisme":all(x==0 for x in f),
            "somme":str(sum(f,D(0))),
            "closes":all(b["closed"] for b in bougies.values()),
            "live":all(not b["closed"] for b in bougies.values()),
            "mixte":len({b["closed"] for b in bougies.values()})>1}
def rapprochement():
    c,g,b=D("25000"),D("18958505.54"),D("18983505.54")
    return {"residu":str(b-c-g),"identite":b==c+g,
            "creance_prouvee":False}
def preuve_creance(contrat,version,eligibilite,echeance,recompense=None,versements=None):
    p=et((contrat,version,eligibilite,echeance))
    montant=None if p!=Etat.VRAI or recompense is None or versements is None else str(max(D(0),D(str(recompense))-D(str(versements))))
    return {"preuve":p.value,"montant":montant}
def preuve_etat(faute,prejudice,causalite,dommage=None):
    p=et((faute,prejudice,causalite))
    return {"preuve":p.value,"montant":str(D(str(dommage))) if p==Etat.VRAI and dommage is not None else None}
if __name__=="__main__":
    print(rapprochement())
