---
name: verifier-espace-disque-windows
description: "Mesurer et qualifier l'espace disque réellement libéré sous Windows en Git Bash : octets apparents sommés (du -sb), allocation (du -s), relevé df -B1, fsutil volume diskfree élevé via Start-Process -Verb RunAs, calibration par fichier témoin de taille exacte, puis conclusion bornée qui n'attribue au nettoyage que ce qui est prouvé. Utiliser quand on demande combien une suppression a libéré, si le disque a réellement diminué après un nettoyage de caches ou de tmp, pour relever l'espace libre exact de C:, ou quand fsutil rend l'erreur 5 ou un « fichier introuvable » causé par $env:TEMP dans une commande PowerShell."
---

# Vérifier l'espace disque réellement libéré (Windows)

## Aperçu

Mesurer sur trois couches distinctes — octets apparents des chemins supprimés, blocs alloués, espace libre du volume — puis calibrer la résolution de la mesure avant de conclure. Un nettoyage de quelques Mo sur un volume de plusieurs centaines de Go est noyé par le bruit d'écriture ambiant : sans relevé antérieur, un delta de volume ne prouve rien et ne doit pas être présenté comme une preuve.

## Quand utiliser / ne pas utiliser

| Demande | Action |
|---|---|
| « Combien la suppression a-t-elle libéré ? » | Ce Skill, étapes 1 → 6 |
| « L'espace libre exact de `C:` ? » | Ce Skill, étapes 2 → 4 |
| « Le disque a-t-il vraiment diminué ? » | Ce Skill, étapes 5 → 6 (conclusion bornée) |
| Inventorier, sélectionner ou supprimer des dossiers tmp | `auditer-nettoyer-temp-qoder` |
| Reconstituer la preuve d'une session (messages, outils) | `extraire-preuves-session-qoder` |
| Auditer les structures et références d'un paquet Skill | `skill-file-qa` |

Ce Skill mesure et qualifie. Il ne décide pas quoi supprimer et n'exécute aucune suppression en masse.

## Règle d'attribution

- **Tableau apparent** (`du -sb`) : somme des tailles de fichiers supprimés. Exacte, sommable, indépendante de l'état du disque.
- **Allocation** (`du -s`, blocs de 1 Kio) : octets réellement occupés, arrondis au cluster, avec le surcoût des petits fichiers.
- **Volume** (`df -B1`, `fsutil`) : état global à un instant donné. Ne s'attribue **pas** rétroactivement sans relevé pris avant la suppression.

N'annoncer un chiffre « libéré » qu'à partir des deux premières couches. La troisième ne sert que de contrôle de cohérence et de contexte.

## Étape 1 — Inventaire apparent et alloué

```bash
USER_TMP="$HOME/.qoder/tmp"
PROJECT_TMP="C:/Users/Administrateur/Desktop/IMAM8MAHDI/.qoder/tmp"   # adapter au projet courant
du -sb "$USER_TMP" "$PROJECT_TMP"   # octets apparents
du -s  "$USER_TMP" "$PROJECT_TMP"   # blocs de 1 Kio
du -sb "$USER_TMP"/* 2>/dev/null | sort -n   # détail par entrée
```

Dériver le total libéré de deux mesures indépendantes : la somme des entrées réellement supprimées et l'écart des totaux avant/après. Elles doivent coïncider à l'octet. Vérifier aussi que chaque entrée conservée a exactement la même taille qu'avant, sinon une écriture concurrente fausse le bilan.

Cas de référence (2026-10-27, 43 chemins supprimés) : `~/.qoder/tmp` 49 030 387 → 43 049 913 o, projet 838 710 → 124 612 o, total libéré **6 694 572 o** (6,38 Mio), égal à la somme directe des entrées supprimées. Allocation après suppression (`du -s`, blocs de 1 Kio) : 45 330 Kio pour `~/.qoder/tmp`, 160 Kio pour le projet ; la baisse ≈ 7,8 Mio est estimée sur les `du -sh` arrondis d'avant suppression (52 M → 45 M, 952 K → 160 K), pas sur un relevé en blocs.

## Étape 2 — Espace libre du volume, sans élévation

```bash
free() { df -B1 /c | awk 'NR==2{print $4}'; }
free
df -B1 /c
df -h /c
```

- La colonne 4 (`Available`) donne l'octet exact. `df -h` ne sert qu'au contexte lisible.
- `df` fonctionne sans élévation dans Git Bash et concorde avec `fsutil` sur total/utilisé/libre.
- Un volume de plusieurs centaines de Go rend les pourcentages inutiles : 6,7 Mo sur 52,4 Go libres = 0,013 %. Toujours citer l'octet et l'unité lisible.
- Prendre ce relevé **avant** toute suppression. C'est la seule façon d'attribuer un delta au nettoyage.

## Étape 3 — fsutil élevé

Sans élévation, `fsutil volume diskfree C:` rend `Erreur 5 : Accès refusé.`. Écrire un wrapper qui redirige la sortie vers un fichier, puis le lancer élevé.

```bat
@echo off
"C:\Windows\System32\fsutil.exe" volume diskfree C: > "%TEMP%\fsutil-free.txt" 2>&1
```

```bash
rm -f "$HOME/AppData/Local/Temp/fsutil-free.txt"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'C:\Users\Administrateur\AppData\Local\Temp\fsutil-probe.cmd' -Verb RunAs -Wait -WindowStyle Hidden" 2>&1
echo "PS_RC=$?"
cat "$HOME/AppData/Local/Temp/fsutil-free.txt" 2>&1 || echo "NO_OUTPUT"
```

- Le chemin du `.cmd` doit être **absolu et littéral**, entre apostrophes. Remplacer le nom d'utilisateur par le chemin réel (`cygpath -w "$HOME/AppData/Local/Temp/fsutil-probe.cmd"`).
- Ne jamais placer `$env:TEMP` dans la commande PowerShell entre guillemets doubles : bash l'expanse en chaîne vide et PowerShell reçoit `:TEMP\fsutil-probe.cmd`, puis échoue avec `Le fichier spécifié est introuvable` et `PS_RC=1`.
- Une fenêtre UAC s'ouvre : l'utilisateur doit l'accepter. `-Wait` est nécessaire avant de lire le fichier.
- `PS_RC=0` prouve seulement que le `.cmd` élevé s'est exécuté, pas que `fsutil` a réussi. Valider par le contenu (étape 4).

## Étape 4 — Décoder la sortie et contrôler l'identité

```bash
PYTHONIOENCODING=utf-8 py -3 - <<'PY'
p = r"C:\Users\Administrateur\AppData\Local\Temp\fsutil-free.txt"
raw = open(p, "rb").read()
print("SIZE", len(raw), "| non_ascii", sum(1 for b in raw if b > 127))
for i, line in enumerate(raw.decode("cp850").splitlines(), 1):
    print("%2d | %s" % (i, line.replace("\u00a0", " ").replace("\u202f", " ")))
PY
```

- La sortie native est en **cp850** (page OEM), ni UTF-8 ni cp1252 : `0xFF` sépare les milliers, `0x82` code `é`. Décodée en cp1252 elle affiche `ÿ`/`‚`, en UTF-8 `�`. Décoder cp850 avant de citer un chiffre, et nommer l'encodage constaté.
- Contrôle d'identité obligatoire : `total − utilisés − réservés = libres`, à l'octet.
- Le marqueur `EXIT=` d'un wrapper qui écrit `echo EXIT=%ERRORLEVEL%>> fichier` n'apparaît pas dans le fichier : `0>>` est lu par cmd comme une redirection du descripteur 0. Ne pas attendre ce marqueur ; valider par `PS_RC=0`, taille non nulle et identité. Le correctif `echo EXIT=... >>` (espace avant `>>`) n'a pas été testé.
- Sous Windows, `Read` ou une console en cp1252 affichent `�` à la place des espaces insécables : lire le fichier via Python en `PYTHONIOENCODING=utf-8` pour citer proprement.

Cas de référence : 722 o, 10 lignes, 22 octets non ASCII ; libres 52 335 308 800, total 252 841 029 632, utilisés 200 160 362 496, réservés 345 358 336 — identité vérifiée à l'octet.

## Étape 5 — Calibrer la résolution avec un fichier témoin

Quand aucun relevé n'existe avant suppression, prouver que `df` résout une variation de la taille annoncée : créer un fichier de **exactement** ce nombre d'octets, relever avant/création/suppression.

```bash
SIZE=6694572
PROBE="$HOME/AppData/Local/Temp/fsprobe-$SIZE.bin"
free() { df -B1 /c | awk 'NR==2{print $4}'; }
A=$(free); echo "FREE_BEFORE=$A"
py -3 - "$PROBE" "$SIZE" <<'PY'
import sys
p, size = sys.argv[1], int(sys.argv[2])
with open(p, "wb") as fh:
    left = size
    chunk = b"\0" * 1048576
    while left:
        n = min(left, len(chunk)); fh.write(chunk[:n]); left -= n
print("WROTE", p)
PY
B=$(free); echo "FREE_AFTER_CREATE=$B"
rm -f -- "$PROBE"
C=$(free); echo "FREE_AFTER_DELETE=$C"
py -3 -c "a,b,c=$A,$B,$C; print('create_delta=%d'%(b-a)); print('delete_delta=%d'%(c-b)); print('net=%d'%(c-a))"
```

Lecture attendue pour un témoin de l'ordre du Mo : `create_delta` ≈ −SIZE arrondi au cluster, `delete_delta` ≈ +SIZE, `net` = 0 ou −1 cluster.

- Cas de référence : −6 701 056 / +6 696 960 / net −4 096 pour un témoin de 6 694 572 o (un cluster retenu).
- Taille du témoin : dimensionner SIZE au même ordre que la quantité revendiquée. Rejoué le 2026-10-27 avec SIZE = 1 Mio sous charge ambiante : −905 216 / +1 048 576 / net +143 360 — le bruit dépasse alors le cluster. Interpréter `net` par rapport au bruit ambiant observé, pas seulement à l'arrondi de cluster.
- Vérifier la disparition du témoin : `ls "$PROBE"` doit rendre `No such file or directory`.
- Ne pas créer de fichier sparse : l'allocation ne bougerait pas et la calibration serait fausse.
- Si `|create_delta|` s'écarte de SIZE de plus d'un cluster (ou de plus que le bruit observé), suspecter un autre écrivain ou un `df` pointant sur un autre volume, pas une erreur de `df`.
- Le témoin prouve la **sensibilité** de l'outil, pas que le nettoyage a produit ce delta au niveau volume.

## Étape 6 — Conclure de façon bornée

Gabarit :

> Suppression de N chemins = X octets apparents (Y Mio), allocation `du -s` −Z. `df -B1` / `fsutil` à HH:MM : libre = L (identité vérifiée). Témoin de X résolu par `df` : −a à la création, +b à la suppression, net −c (arrondi cluster). Attribution au nettoyage au niveau volume : **non mesurable** — le volume a perdu d octets en ~m min sous l'activité ambiante, soit d/X ≈ k×, sans relevé antérieur.

- Ne jamais écrire « le disque a libéré X » sans relevé pris avant la suppression.
- Séparer explicitement ce qui est établi (chemins absents, somme apparente exacte, baisse d'allocation, calibration) de ce qui ne l'est pas (delta de volume attribuable).
- Quantifier le bruit entre deux horodatages et exprimer la fraction du libre occupée par le nettoyage : c'est ce qui justifie la prudence.
- Cas de référence : 52 375 986 176 → 52 335 308 800 o, soit 40 677 376 o perdus en ~6 min, 6,08× les 6 694 572 o nettoyés. Conclusion retenue : libération réelle ≈ 6,4 Mio établie au niveau fichiers/allocation ; `fsutil` donne l'état exact du volume mais ne peut pas l'attribuer.

## Frontières

- **Références Git** : supprimer des branches ne libère localement **aucun** octet. Les objets restent (`git count-objects -vH` : vrac + packs). Les récupérer exige `reflog expire` + `git gc --prune=now` — irréversible, donc à demander explicitement à l'utilisateur.
- **Fichiers système, points de restauration, VSS** : non mesurables par cette séquence.
- **Résidus de travail** : listes, logs et `.cmd` laissés dans `%TEMP%` se comptent séparément et se déclarent comme preuves conservées. Ces fichiers ne sont pas durables : constaté le 2026-10-27, `fsutil-free.txt`, `fsutil-probe.cmd` et la liste de suppression présents à 15:11 (local) et absents à 15:16, sans action de cette session. Recopier les chiffres dans la réponse dès la mesure.
- **Autres écrivains** : arrêter les sessions ou processus qui écrivent sur le volume avant de mesurer, sinon le bruit dépasse la quantité mesurée.

## Pièges

| Symptôme | Cause | Correctif |
|---|---|---|
| `Erreur 5 : Accès refusé` | `fsutil` non élevé | wrapper `.cmd` + `Start-Process -Verb RunAs` |
| `Le fichier spécifié est introuvable` et `FilePath ":TEMP\..."` | `$env:TEMP` expansé par bash | chemin absolu littéral entre apostrophes |
| Chiffres illisibles (`ÿ`, `‚`, `�`) | cp850 lu en UTF-8 ou cp1252 | décoder cp850 |
| `EXIT=0` absent du fichier produit | `%ERRORLEVEL%>>` = redirection du descripteur 0 | valider par `PS_RC`, taille, identité |
| Delta `df` négatif après une suppression | écritures ambiantes sur le volume | témoin + conclusion bornée |
| Net du témoin = −4 096 o | arrondi cluster | tolérer un cluster |
| `du -sb` > `du -s` | apparent vs alloué | ne pas les comparer, les nommer |
| 0 octet libéré après suppression de branches | objets Git non purgés | `gc` explicite, avec accord |
| `PS_RC=0` mais fichier vide | UAC refusée ou `fsutil` en échec | vérifier `NO_OUTPUT`, relancer en expliquant l'UAC |

## Liste de contrôle

- [ ] `du -sb` et `du -s` avant/après ; entrées conservées inchangées à l'octet
- [ ] Total libéré recoupé par deux mesures indépendantes
- [ ] `df -B1` relevé et horodaté (ou absence de relevé antérieur déclarée)
- [ ] `fsutil` élevé : `PS_RC=0`, fichier non vide, sortie décodée en cp850
- [ ] Identité `total − utilisés − réservés = libres` vérifiée
- [ ] Témoin à l'échelle de la quantité revendiquée ; `net` comparé au bruit ; fichier confirmé absent
- [ ] Bruit ambiant quantifié entre deux horodatages
- [ ] Conclusion séparant l'établi de l'attribution impossible au niveau volume

## Ressources

- Ce Skill ne contient que `SKILL.md`, aucun script ni référence.
- Source vérifiée : session `c106ed2c` du 2026-10-27 (43 chemins, 6 694 572 o, `fsutil` 52 335 308 800 o libres, bruit 40 677 376 o en ~6 min). Les valeurs datent de ce relevé ; les recalculer avant de les citer comme actuelles.
- Rejeu local du 2026-10-27 après écriture : `df -B1`, `du -sb`/`du -s` et valeurs d'octets cp850 (`0xFF` = espace insécable, `0x82` = `é`) confirmées ; témoin de 1 Mio exécuté, deltas bruités (cf. étape 5). Branche élevée `fsutil` non rejouée : elle exige l'acceptation UAC par l'utilisateur, et la sortie de référence a été supprimée de `%TEMP%` entre-temps.
- Inventaire et suppression des dossiers tmp : `auditer-nettoyer-temp-qoder`.
