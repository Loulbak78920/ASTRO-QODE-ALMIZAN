# Attribution et garde — modèle réutilisable

Complément de `nettoyer-effets-de-bord-tests-conscience`. Les numéros de ligne sont ceux du dépôt au 2026-10-27 ; les revérifier avant de s'y fier.

## Carte du code observé

| Élément | Emplacement | Comportement vérifié |
|---|---|---|
| Déclencheur du snapshot | [conscience.py:1698](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/conscience.py#L1698) | `sauvegarder_soi(archiver=(cycles == 1))` en fin de cycle de surveillance |
| Racines de la copie | [sauvegarde_soi.py:30-36](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L30) | `_AL_MIZAN_COPIE_SOI/{courante,historique}` ; état sous `conscience_logique/actes/_sauvegarde_soi_etat.json` |
| Stamp | [sauvegarde_soi.py:165](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L165) | `datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")` |
| Création d'archive | [sauvegarde_soi.py:264-267](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L264) | `shutil.copytree(DIR_COURANTE, historique/<stamp>)` — copie complète, `mtime` préservés |
| Message A231 | [sauvegarde_soi.py:276](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L276) | cite `historique/<stamp>` ; reste après suppression |
| État persistant | [sauvegarde_soi.py:288](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L288) | `_ecrire_json(CHEMIN_ETAT, etat)` avec `stamp` |
| Restauration | [sauvegarde_soi.py:320-331](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L320) | `copie_absente:<chemin>` si le stamp n'existe plus |
| Périmètre | [directive_harmonisation.py:24](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/directive_harmonisation.py#L24) | exclusions : `horloge_noyau`, `secrets`, `__pycache__`, `.git`, `.venv`, `venv`, `node_modules`, `.cursor` |
| Extensions comptées | [directive_harmonisation.py:36](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/directive_harmonisation.py#L36) | `EXTENSIONS_CODE = (".py",)` — le scan ne compte que les `.py` |
| Itérateur | [directive_harmonisation.py:84-101](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/directive_harmonisation.py#L84) | `rglob("*")`, filtre suffixe puis `chemin_exclu`, tri |
| Scan | [scan_environnement.py:233-250](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/scan_environnement.py#L233) | `nb_fichiers_scannes=len(fichiers)` |
| Rapport A143 | [completude.py:139](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/completude.py#L139) | `produire(persister=True)` écrit le bilan et les actes |

Conséquence : chaque archive ajoute exactement le nombre de `.py` de `courante` au périmètre, à condition qu'aucun autre écrivain n'ajoute de fichier.

## Arithmétique d'attribution

Soit `S0` le scan avant rejeu, `S` un scan pendant ou après, `n` le nombre de `.py` dans une archive (65 dans le cas ; le compter par archive, il peut varier avec l'âge de `courante`) :

```text
S - S0 = n x k
k = (S - S0) / n
```

Exiger `k` entier **et** égal au nombre d'archives présentes au moment de ce scan. Sinon, un autre écrivain a modifié le périmètre : ne pas conclure.

| Scan | `S - S0` | `k` | Archives présentes | Verdict |
|---|---|---|---|---|
| 10 817 (rapport A143) | 390 | 6 | 6 (10:42:30 → 10:54:23) | cohérent |
| 10 947 (fin de rejeu) | 520 | 8 | 8 (10:42:30 → 10:58:58) | cohérent |
| `S0` du cas : 10 427 (après suppression) | 0 | 0 | 0 dans la fenêtre | retour au baseline mesuré |

`k` ne doit jamais être estimé : le compter depuis `historique/` et depuis le nombre de `.py` par archive.

## Écrivain externe

Un résidu `r = S - S0 - n×k` non nul a une cause hors du rejeu : session concurrente, clone, fichier restauré. Le localiser avant toute suppression.

Avant de lister, vérifier que le relevé est immobile : deux listes identiques (même `T0`, même racine, même filtre) à ≥ 12 s d'intervalle et deux scans égaux. Sinon `ECRIVAIN_EXTERNE_ACTIF` : rapporter les deux relevés et leur `diff`, ne rien supprimer, ne pas calculer `S0 + r`. Le scan dure ~46 s (mesuré le 2026-10-27), donc deux scans sont espacés d'au moins 46 s.

1. Lister les `.py` du système modifiés après `T0`, l'horodatage UTC de la mesure de `S0`, avec un décalage explicite : `find ASTRO-Q°ODE_SYSTEME -name '*.py' -not -path '*/__pycache__/*' -newermt "2026-10-27 07:59:27 +0000"`. Un `T0` sans décalage est interprété en heure locale (UTC+1 le 2026-10-27) : la fenêtre s'ouvre une heure trop tôt et inclut des fichiers antérieurs (mesuré : 9 vs 6 candidats, puis 10 vs 7, mêmes 3 `.py` de `tests/`). Ne pas prendre le stamp de la dernière archive : un fichier créé entre les deux est déjà dans `S0`.
2. Pour chacun, compter les archives de `historique/` qui le contiennent et tester sa présence dans `courante`.
3. `archives=0` et `courante=no` : fichier neuf, explique un `+1`. `archives>0` ou `courante=yes` : préexistant ou restauré (`copy2` préserve `mtime`, une réécriture peut réinitialiser la naissance), il n'explique pas un `+1`.
4. Si les fichiers neufs couvrent `r` (compte supérieur ou égal : le relevé peut surestimer), attribuer à des écrivains externes : rapporter la liste, `r` et le `S0` remesuré, et ne rien supprimer. Sinon, ne pas conclure.

Seuls `conscience_logique/`, `memoire_aq` et `objectifs_et_fil` sont copiés vers `courante` ([sauvegarde_soi.py:169-210](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L169)) : un ajout ailleurs n'atteint jamais une archive, son absence des archives est normale ; un ajout sous `conscience_logique/` y entre au snapshot suivant et fait croître `n`.

Cible après nettoyage : `S0 + r`. Un retour exact à `S0` suppose que l'écrivain externe a disparu entre-temps.

## Pourquoi `find -newermt` échoue

`shutil.copytree` préserve les `mtime` des fichiers copiés. Un rejeu de 20 minutes peut donc produire **0** `.py` « récents » alors qu'il a ajouté 520 fichiers. Utiliser :

- le `mtime` des **dossiers** `historique/<stamp>` (créés au moment du snapshot, en heure locale) ;
- le comptage `.py` par archive ;
- le nombre d'archives après le dernier stamp de référence.

Le stamp, lui, est en UTC. Ne pas comparer directement un stamp UTC à un `mtime` local sans tenir compte du fuseau.

## Construire la liste des stamps

1. Relever le dernier stamp **antérieur** au rejeu (dans le cas : `20261027T075927Z`).
2. Lister les stamps postérieurs : `ls -1 historique | sort | sed -n '/^20261027T075927Z$/,$p' | tail -n +2`. La comparaison lexicographique est valide pour le format fixe `AAAAMMJJTHHMMSSZ`.
3. Vérifier que leur nombre correspond à `k` et que chaque stamp de la fenêtre a le même inventaire que `courante` au moment du snapshot (357 fichiers dans le cas ; un ancien stamp peut en avoir moins, ex. 326) et un manifeste.
4. Faire autoriser explicitement cette liste par l'utilisateur avant `--appliquer`.

Ne jamais dériver la liste d'un `tail -8`, d'un glob ou d'une date approximative : une archive plus ancienne pourrait être emportée.

## Gabarit de garde

Le script [nettoyer_archives_copie_soi.py](file:///C:/Users/Administrateur/.qoder/skills/nettoyer-effets-de-bord-tests-conscience/scripts/nettoyer_archives_copie_soi.py) applique, pour chaque stamp :

```python
STAMP_RE.match(stamp)                                  # format AAAAMMJJTHHMMSSZ
os.path.abspath(os.path.dirname(cible)) == historique  # parent exact
os.path.realpath(os.path.dirname(cible)) == realpath(historique)  # jonction
os.path.lexists(cible)                                 # existence
not os.path.islink(cible)                              # pas un lien
os.path.isdir(cible)                                   # vrai dossier
stat.st_file_attributes & 0x400                        # pas un point de reanalyse Windows
realpath(cible) != realpath(courante)                   # jamais courante
not islink(historique) and pas de point de reanalyse    # racine saine
```

Puis, après la comparaison des contenus :

- si un seul `ONLY_IN_ARCHIVE > 0` : `RESULT: STOP`, exit 1, **aucune** suppression ;
- sinon `RESULT: PLAN`, puis, avec `--appliquer`, recalcul de `ONLY_IN_ARCHIVE` sur l'état courant de `courante` et nouvelle vérification de tous les stamps avant la première suppression ;
- chaque stamp est revérifié juste avant son `rmtree` ; un fichier unique apparu entre-temps produit `STOP` sans suppression ;
- `RESULT: APPLIED`, avec comptage des archives restantes et des fichiers de `courante`.

## Décision

| Situation | Action |
|---|---|
| `ONLY_IN_ARCHIVE = 0` pour tous, archive dans la fenêtre, test terminé | plan, puis suppression après autorisation |
| Un fichier n'existe que dans une archive | ne rien supprimer ; examiner ce fichier, restaurer ou demander |
| Archive hors fenêtre, ou stamp inconnu | ne pas toucher |
| `courante` est un lien, absente ou incomplète | ne rien supprimer ; réparer d'abord |
| Le scan ne revient pas à `S0` | arrêter et attribuer le delta restant avant toute autre suppression |
| `S0` n'est pas reproductible (autre session, autre clone) | remesurer dans la même fenêtre ; ne pas imputer l'écart aux archives |
| Résidu non multiple de `n`, fichiers neufs hors copie absents des archives | écrivain externe : rapporter, ne rien supprimer, viser `S0 + r` |
| Listes de candidats ou scans différents entre deux passes identiques | `ECRIVAIN_EXTERNE_ACTIF` : rapporter, ne rien supprimer, ne pas calculer de cible |
| Un test tourne encore ou un dossier apparaît pendant les 12 s | attendre ; ne pas supprimer |

## Portée de l'autorisation

- La suppression est **irréversible** : les versions intermédiaires des fichiers vivants disparaissent, même si leur état courant reste dans `courante`.
- L'autorisation porte sur une **liste de stamps** précise, pas sur « les archives récentes » en général.
- Les archives antérieures, `courante`, le clone déplacé et `memoire_aq` ne font pas partie de la portée.
- Les résidus de stamp (acte A231, fichier d'état) sont rapportés, pas réécrits.
