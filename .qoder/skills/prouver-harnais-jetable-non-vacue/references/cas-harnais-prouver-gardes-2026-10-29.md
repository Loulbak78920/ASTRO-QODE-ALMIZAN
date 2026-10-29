# Cas vérifié — prouver un harnais sur un oracle jetable (2026-10-29)

## Source

Session `452b8145-965b-4e30-b5f2-0a050004740e`, `runtimeState: cold`, deux tours : proposition puis « 按此执行 ». Le second tour a créé `prouver-garde-statique-non-vacue` et auto-testé son harnais `scripts/prouver_gardes.py` avant le rejeu réel. Les sorties ci-dessous sont recopiées de cette session ; le rejeu du script livré a été refait le 2026-10-29 sur le harnais installé.

## 1. Premier passage : le harnais juge mal son propre oracle

Le faux vérificateur lisait son argument comme un fichier, alors que le harnais copie la source et transmet la copie : un répertoire. Résultat sur les quatre cas :

```text
CAS positif POSITIF_CASSE exit=1 garde=-
  DETAIL_ATTENDU
CAS alpha MAUVAISE_RAISON exit=1 garde=alpha
  MUTATION fichier=toy.txt occurrences=1 sha_avant=cc0c0fe53f71 sha_apres=22fbbf39923b
  DETAIL_ATTENDU ALPHA absent
CAS beta MAUVAISE_RAISON exit=1 garde=beta
CAS gamma MAUVAISE_RAISON exit=1 garde=gamma
FIXTURES ABSENTES
COUVERTURE ok gardes=3 cas_negatifs=3
RESULT: FAIL gardes=3 declenches=0 vacues=0 mauvaises=3 non_applique=0 positifs_casses=1 erreurs=0 source_drift=non
EXIT=1
```

Aucun `DETAIL_OBSERVE`, aucun `SORTIE` : le positif cassé était opaque. La couverture affichait pourtant `ok`, ce qui montre que la couverture des cas ne prouve pas l'exécution des branches.

## 2. Deux corrections

1. L'oracle résout un répertoire vers `toy.txt` (et accepte aussi un fichier).
2. Le harnais imprime les deux dernières lignes de sortie sous `SORTIE` quand le verdict est `POSITIF_CASSE` ; c'est ce que fait la version installée, lignes 416-420 de `prouver_gardes.py`.

## 3. Deuxième passage : les branches attendues apparaissent

```text
VERIFICATEUR ...\toy_verifier.py sha256=6092314c3204
CAS positif POSITIF_OK exit=0 garde=-
CAS alpha GARDE_DECLENCHE exit=1 garde=alpha
  DETAIL_ATTENDU ALPHA absent
  DETAIL_OBSERVE DETAIL ALPHA absent
  RESULT_OBSERVE RESULT: FAIL controles=3 echecs=1
CAS beta GARDE_DECLENCHE exit=1 garde=beta
CAS gamma GARDE_DECLENCHE exit=1 garde=gamma
FIXTURES ABSENTES
COUVERTURE ok gardes=3 cas_negatifs=3
RESULT: PASS gardes=3 declenches=3 positifs=1
EXIT=0
```

Les trois autres cas isolent les branches :

```text
CAS jouet GARDE_VACUE exit=0 garde=alpha
  RESULT_OBSERVE RESULT: PASS controles=3 echecs=0
RESULT: FAIL gardes=1 declenches=0 vacues=1 ... EXIT=1

CAS absent NON_APPLIQUE exit=? garde=alpha
  occurrences=0 (attendu 1)
  CAUSE occurrences=0 (attendu 1)
RESULT: FAIL ... non_applique=1 ... EXIT=1

CAS alpha_faux_detail MAUVAISE_RAISON exit=1 garde=alpha
  DETAIL_ATTENDU BETA interdit
  DETAIL_OBSERVE DETAIL ALPHA absent
RESULT: FAIL ... mauvaises=1 ... EXIT=1
```

`GARDE_VACUE` y était produit par une mutation inerte volontaire (commentaire), pas par un garde défaillant. Le script livré ne couvre pas cette branche : elle reste manuelle (SKILL.md, étape 5).

## 4. Rejeu réel après PASS de l'oracle

Harnais `prouver_gardes.py`, vérificateur `verifier_cartes_x.py` (SHA-256 `fcccfa22…`), gabarit `4d551b92…` :

```text
CAS positif POSITIF_OK exit=0 garde=-
CAS lang_absent GARDE_DECLENCHE exit=1 garde=lang_present
  DETAIL_ATTENDU attribut lang absent sur <html>
CAS lang_de GARDE_DECLENCHE exit=1 garde=lang_autorisee
CAS uppercase_brand GARDE_DECLENCHE exit=1 garde=uppercase
CAS taille_1600 GARDE_DECLENCHE exit=1 garde=taille_png
  VARIANTE fichiers_differents=1 premier=carte_fr.png
RESULT: PASS gardes=4 declenches=4 positifs=1
EXIT=0
```

## 5. Sonde inerte sur le vrai gabarit

Mutation de l'exemple `<html lang=".." dir="..">` dans le commentaire d'en-tête, que le vérificateur corrigé retire avant lecture :

```text
CAS positif POSITIF_OK exit=0 garde=-
CAS commentaire_inerte GARDE_VACUE exit=0 garde=lang_autorisee
  MUTATION fichier=carte_fr.html occurrences=1 sha_avant=4d551b924798 sha_apres=b0a2cd2d4ed1
  DETAIL_ATTENDU lang « zz » hors de fr|en|ar
  RESULT_OBSERVE RESULT: PASS cartes=1 html=1
  GARDE_OBSERVE GARDE ok carte_fr.html lang=fr dir=ltr bidi=2 ltr=2 text_ltr=4 taille=ok
RESULT: FAIL ... vacues=1 ... EXIT=1
```

Le vert est correct : la mutation est hors du texte lu. `GARDE_OBSERVE` montre l'entrée réelle (`lang=fr`). Le harnais, lui, ne sait pas distinguer ce cas d'un garde vacu et rend un FAIL global. Toute conclusion sur ce point est donc une lecture humaine, pas un verdict du code.

## 6. Rejeu du script livré

Commande :

```bash
py -3 scripts/jouer_oracle.py --harnais "C:/Users/Administrateur/.qoder/skills/prouver-garde-statique-non-vacue/scripts/prouver_gardes.py"
```

Sortie observée le 2026-10-29 :

```text
HARNAIS ...\prouver_gardes.py sha256=99c0e9dbd381
ORACLE C:\Users\Administrateur\.qoder\tmp\prouver-harnais.i171f9fx
RUN ok rc=0 verdicts=POSITIF_OK=1,GARDE_DECLENCHE=3 attendu=POSITIF_OK=1,GARDE_DECLENCHE=3 etat=CONFORME
RUN non_applique rc=1 verdicts=POSITIF_OK=1,NON_APPLIQUE=1 attendu=POSITIF_OK=1,NON_APPLIQUE=1 etat=CONFORME
RUN mauvaise rc=1 verdicts=POSITIF_OK=1,MAUVAISE_RAISON=1 attendu=POSITIF_OK=1,MAUVAISE_RAISON=1 etat=CONFORME
RUN convention rc=1 verdicts=MAUVAISE_RAISON=1,POSITIF_CASSE=1 attendu=MAUVAISE_RAISON=1,POSITIF_CASSE=1 etat=CONFORME
ORACLE_ABSENT
RESULT: PASS runs=4 verdicts=5
EXIT=0
```

## 7. Test négatif du script

Copie du harnais hors installation, remplacement de `SORTIE` par `BRUT` (occurrence unique prouvée, SHA-256 `99c0e9db…` → `1812fdb31c7b`), puis exécution du script sur la copie :

```text
RUN convention rc=1 verdicts=MAUVAISE_RAISON=1,POSITIF_CASSE=1 attendu=MAUVAISE_RAISON=1,POSITIF_CASSE=1 etat=ECART
  ECART absent='SORTIE '
RESULT: FAIL runs=4 verdicts=5 ecarts=1
WRAPPER_EXIT=1
FIXTURE_ABSENTE
```

Le harnais original est resté à `99c0e9dbd381dd0419f64bd0b8ff5adbc2bd7bc236f78b146f06833738f84c87`. Le test prouve que le script ne rend pas PASS quand une branche de diagnostic manque.

## Limites

- Le script est lié au protocole `CAS <nom> <VERDICT> exit=... garde=...` et `RESULT: PASS|FAIL` ; un autre harnais se prouve avec les étapes manuelles du SKILL.md.
- `GARDE_VACUE` et `ERREUR_EXECUTION` ne sont pas produits par le script ; un PASS ne dit rien de ces branches.
- Sous Windows, l'échec de lecture d'un répertoire rend `PermissionError` et non `IsADirectoryError` ; le script n'asserte donc pas le nom de l'exception, seulement la présence de `SORTIE`.
- Le harnais installé n'a pas de champ « verdict attendu » : une mutation volontairement inerte provoque un FAIL global. Le classement inerte/vacu reste manuel.

## Empreintes au 2026-10-29

| Fichier | SHA-256 |
|---|---|
| `prouver-garde-statique-non-vacue/scripts/prouver_gardes.py` | `99c0e9dbd381dd0419f64bd0b8ff5adbc2bd7bc236f78b146f06833738f84c87` |
| `prouver-garde-statique-non-vacue/SKILL.md` | `2e46f346b660a10bfd3ed04f299a6762e096a4fa56a91d30e245fd52994aa2fe` |
| `prouver-garde-statique-non-vacue/references/cas-verificateur-cartes-2026-10-28.md` | `82d36cbbb70c2d4af8a1b5c5ba89fa0e7d88337d5f8ff116a021d6199257c396` |
| `cartes-x-multilingues-sans-dol/scripts/verifier_cartes_x.py` | `fcccfa223e06c65c90f9d0d889124bcd068144ef1100b4cfad157476551041d5` |
| `cartes-x-multilingues-sans-dol/assets/carte_16-9.html` | `4d551b92479860934878a8d92b17ec5898cdb72984d1ffe7c1f6c4feb6e5e5cb` |
