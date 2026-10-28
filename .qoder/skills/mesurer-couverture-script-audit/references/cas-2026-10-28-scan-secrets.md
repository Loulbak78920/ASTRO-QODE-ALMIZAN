# Couverture réelle d'un scan de secrets : cas `auditer_secrets_locaux.py` (2026-10-28)

Objet : montrer, mesure à l'appui, comment un verdict vert coexiste avec des secrets présents sur disque, et fixer la méthode de mesure réutilisée par ce Skill.

Version auditée : 6 555 octets, SHA-256 `128f1695961670110dc98d016ecc35bf311b2c884ebfe1eb0aa652caff1584a9`, fichier `auditer_secrets_locaux.py` du dossier `scripts/` du Skill `rotation-mot-de-passe-vps-sans-fuite`. Les numéros de ligne cités ne valent que pour ces octets.

Exécution : Git Bash sous Windows, `py -3 -B`, `PYTHONIOENCODING=utf-8`, secret factice `FAKE-MDP-COUVERTURE-2026` (chaîne ASCII, jamais un vrai secret), fixtures sous `%LOCALAPPDATA%\Temp\cov-audit-20261028` et sous `~/.qoder/tmp/cov-g-20261028`. Chaque cas a sa propre racine. Les deux fixtures ont été supprimées après les exécutions ; l'existence est passée de `true` à `false` pour les deux.

Convention de lecture des blocs : la ligne `SECRETS …` (chemin absolu de la fixture) est omise partout. Les en-têtes `FICHIER`, `CLES`, `TEMPORAIRE`, `PERMANENT` et `RESIDU` sont reproduits au cas A et omis des cas B à E et G lorsqu'ils sont identiques ; le cas D ne montre que `RESIDU`, qui diffère. Les deux dernières lignes (`rc=…`, `secret_in_output=…`) sont produites par le harnais, pas par le script. Toute autre omission est signalée dans le texte.

## 1. Cas A — contrôle positif

`notes.md` contient le secret (liste blanche, petit fichier) :

```text
FICHIER json=ok
CLES manquantes=aucune
TEMPORAIRE non_vide=non
PERMANENT coherent=oui
RESIDU tmp=aucun
SCAN racine=ok fichiers=1
FUITE total=1
  FUITE notes.md:2
ANTIPATTERN total=0
FAIL secret hors du fichier de secrets: 1 occurrence(s)
RESULT FAIL
rc=1
secret_in_output=False
```

Le contrôle positif passe : le harnais voit bien une fuite quand elle est dans le périmètre. Sans ce cas, un vert ailleurs ne prouverait rien.

## 2. Cas B — trois copies, aucune vue

`journal.log` (extension non listée), `gros.py` (2 099 999 octets, au-dessus du plafond) et `node_modules\mod.py` (dossier ignoré) contiennent tous les trois le secret :

```text
FICHIER json=ok
CLES manquantes=aucune
TEMPORAIRE non_vide=non
PERMANENT coherent=oui
RESIDU tmp=aucun
SCAN racine=ok fichiers=0
FUITE total=0
ANTIPATTERN total=0
RESULT OK
rc=0
secret_in_output=False
```

`fichiers=0` et `RESULT OK` avec trois copies du secret sur disque : c'est la démonstration centrale. Un seul cas B couvre trois limites d'un coup ; c'est pour cela qu'il ne faut pas le découper.

## 3. Cas C, D, E

C — témoin, `petit.py` en liste blanche, rc=1 :

```text
SCAN racine=ok fichiers=1
FUITE total=1
  FUITE petit.py:2
FAIL secret hors du fichier de secrets: 1 occurrence(s)
RESULT FAIL
```

D — résidu, `secrets\ovh.json.tmp` présent, rc=1 :

```text
RESIDU tmp=ovh.json.tmp
SCAN racine=ok fichiers=1
FUITE total=1
  FUITE petit.py:2
FAIL residu .tmp: ovh.json.tmp
FAIL secret hors du fichier de secrets: 1 occurrence(s)
RESULT FAIL
```

E — encodage, `enc.py` écrit en UTF-16 avec le secret, rc=0 :

```text
SCAN racine=ok fichiers=1
FUITE total=0
ANTIPATTERN total=0
RESULT OK
rc=0
```

Le fichier est bien compté (`fichiers=1`) et pourtant illisible pour le décodeur : la limite d'encodage ne se voit pas dans le compteur de périmètre.

## 4. Cas F — plafond d'affichage

`vingtcinq.py` contient le secret sur 25 lignes, `--max-findings` laissé à sa valeur par défaut (20). Le script affiche 20 lignes, de `vingtcinq.py:1` à `vingtcinq.py:20` ; seules la première, la dernière affichée et la ligne de troncature sont reproduites, les 18 intermédiaires sont identiques et omises.

```text
SCAN racine=ok fichiers=1
FUITE total=25
  FUITE vingtcinq.py:1
  FUITE vingtcinq.py:20
  FUITE ... tronque (5 de plus)
ANTIPATTERN total=0
FAIL secret hors du fichier de secrets: 25 occurrence(s)
RESULT FAIL
rc=1
secret_in_output=False
```

Le total est exact, la liste ne l'est pas : 5 occurrences sont comptées sans être montrées. Écrire « 25 lignes de fuite » est vrai ; décrire leur contenu ne l'est pas.

## 5. Cas G — racine sous un composant ignoré

Racine `~/.qoder/tmp/cov-g-20261028`, `notes.md` contient le secret, rc=1 :

```text
SCAN racine=ok fichiers=1
FUITE total=1
  FUITE notes.md:2
FAIL secret hors du fichier de secrets: 1 occurrence(s)
RESULT FAIL
rc=1
secret_in_output=False
```

Ici le vert serait le symptôme : `.qoder` figure dans `DOSSIERS_IGNORES`, et une comparaison sur composants **absolus** viderait tout le scan. Le rouge prouve que le filtre porte sur les composants relatifs à `--racine`.

## 6. Table des limites (lignes de code)

| Limite | Code (fichier, ligne) | Conséquence observée |
|---|---|---|
| Liste blanche d'extensions, plus les noms `.env*` | `EXTENSIONS`, l. 23-27 ; test l. 37 | `.log` jamais lu (cas B) |
| Sept dossiers ignorés | `DOSSIERS_IGNORES`, l. 22 ; test l. 52 | `node_modules` jamais lu (cas B) |
| Taille au plus 2 000 000 octets | `TAILLE_MAX_FICHIER`, l. 21 ; l. 39 | 2 099 999 octets sauté, sans compteur (cas B) |
| Une seule valeur recherchée | l. 89 et l. 128 | une fuite de `mot_de_passe_permanent` n'est pas signalée (INFERRED) |
| Décodage `utf-8` avec `errors="ignore"` | l. 125 | UTF-16 illisible, `FUITE total=0` (cas E) |
| Un seul nom de temporaire | l. 105 | `.swp`, `.bak` du JSON non contrôlés (INFERRED) |
| Anti-modèles limités à `sudo -S` et `bash -s` | l. 28-31 ; l. 151-155 | autres formes non signalées (INFERRED) |
| Plafond d'affichage par catégorie | défaut l. 173 ; affichage l. 144 et l. 152 | total exact, liste partielle (cas F) |
| Table rc | `fails` l. 160-164 ; avertissements l. 157-158 ; usage l. 177-179 | avertissements sans effet sur le rc ; `--max-findings 0` donne rc 2 |

## 7. Premier run réel (source session, non rejoué ici)

Racine `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME`, mêmes octets, sortie verbatim relevée dans la session `f63cc483-5ef1-46b7-b646-dcb517ae8b3b` :

```text
SCAN racine=ok fichiers=698
FUITE total=0
ANTIPATTERN total=46
  ANTIPATTERN deploiement_vps\deploiement_automatique_ovh.py:106 sudo -S
  ANTIPATTERN ... tronque (26 de plus)
RESULT OK
```

Ce run n'a pas été refait ici (698 fichiers, hors du périmètre de la mesure). Lecture correcte : 698 fichiers éligibles lus, aucune occurrence exacte du secret, 46 lignes d'anti-modèles dont 20 seulement sont affichées — un passif de scripts de déploiement, pas une fuite. Les 46 ne changent pas le rc.

## 8. Bug historique et correctif (source session)

La première version de `_fichiers` comparait les composants **absolus** du chemin à `DOSSIERS_IGNORES`. Un fixture créé sous `…\.qoder\tmp\…` contenait donc `.qoder` : tous les fichiers étaient ignorés, le harnais affichait 6 échecs, et chaque cas fautif montrait `SCAN racine=ok fichiers=0` suivi de `RESULT OK`.

Correctif : comparaison sur `chemin.relative_to(racine).parts[:-1]` (l. 49-51), puis harnais à 0 échec. `.bak`, `.old`, `.orig`, `.save` ont aussi été ajoutés aux extensions (l. 26). Le cas G de ce document est la garde qui empêche la régression : il doit rester rouge.

## 9. Classement

| Affirmation | Niveau | Preuve |
|---|---|---|
| Cas A à G, rc et absence du secret dans stdout/stderr | REPRODUCED | exécutions du 2026-10-28 sur les octets `128f1695…` |
| Trois fuites invisibles avec `fichiers=0` et `RESULT OK` | REPRODUCED | cas B |
| UTF-16 non détecté malgré `fichiers=1` | REPRODUCED | cas E |
| Total affiché exact mais liste tronquée | REPRODUCED | cas F |
| Comparaison relative, non absolue | REPRODUCED | cas G |
| Run réel 698 / 0 fuite / 46 anti-modèles / 20 affichées | REPRODUCED en session source, non rejoué ici | §7 |
| Bug des composants absolus et sa correction | REPRODUCED en session source (JSONL + harnais) | §8 |
| Seul `mot_de_passe_ssh` est cherché ; un seul nom de `.tmp` ; ACL et `gitignore` non contrôlés | INFERRED | lecture du code, non exercé isolément |

## 10. Ce que cette mesure ne prouve pas

- Elle ne prouve pas qu'un fichier hors périmètre en production contient le secret ; elle prouve seulement que le script ne le verrait pas.
- Elle ne prouve pas la même chose pour une autre version du script : toute citation est liée au SHA-256 de l'en-tête.
- Elle ne mesure pas les contrôles distants (connexion, authentification) : ce sont d'autres critères de sortie.
- Elle ne dit rien des permissions, ACL, `.gitignore` ni des secrets transformés (base64, URL-encodé, tronqué).

## 11. Rejeu indépendant du 2026-10-28 (adoption du paquet)

Rejeu des cas A à G par `scripts/rejouer_matrice.py` (SHA-256 `43c9d2a0…`, 8 204 octets) contre les mêmes octets du script (`128f1695…`), racines sous `%TEMP%` et, pour le cas G, sous `~/.qoder/tmp`. Les sept cas rendent le rc et les lignes attendus ; aucune sortie ne contient le secret.

Contrôles négatifs du harnais, exécutés avant de conclure :

| Cas | Attendu | Observé |
|---|---|---|
| Scanner factice imprimant le secret sur stdout | échec bloquant | `FAIL … SECRET_DANS_LA_SORTIE`, sortie non affichée, rc 1 |
| `attendu_rc=0` sur le cas A (qui rend 1) | échec | `FAIL … rc=1 attendu=0`, rc 1 |

Les deux bases de fixtures affichent `existe=False` après suppression. Ce rejeu ne crée aucune mesure nouvelle : il confirme §1 à §5 et ne remplace pas §7, non rejoué.
