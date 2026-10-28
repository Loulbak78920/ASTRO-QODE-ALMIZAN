# Mécanisme A231/A232 — pourquoi une édition est réécrite par la copie de soi

Version liée : `ASTRO-Q°ODE_SYSTEME/conscience_logique/sauvegarde_soi.py`,
781 lignes, 25 671 B, SHA-256
`b4f82c3defc8f197093ff5807da69e639bd36d209ee9947fccaf15a91676daa8`
(relevé 2026-10-27). Les numéros de ligne ci-dessous ne valent que pour ce
fichier exact ; recalculer le hash avant de s'y fier. Décalage = relire le
fichier, pas réutiliser ces numéros.

## 1. Ce que fait A231 (`sauvegarder_soi`, ligne 157)

- Crée `_AL_MIZAN_COPIE_SOI/courante` et `historique/<stamp UTC>` (161-165).
- Écrit l'acte A231 (`actes/almizan_acte_a231_copie_de_soi.json`) et son miroir
  `memoire_aq/almizan_acte_a231_copie_de_soi.json` (175-195).
- Copie `conscience_logique/` via `_copier_arbre` (198-200), puis les miroirs
  `memoire_aq/almizan_*` (202-216) et les objectifs (237).
- `_copier_arbre` (109) utilise `shutil.copy2` : **le mtime de la source est
  recopié sur la copie**, et inversement lors d'une restauration.

## 2. Périmètre protégé (`_iter_fichiers_proteges`, 445)

Quatre zones côté projet (473) ; le script de diagnostic en expose trois et range
`objectifs` dans `ACTES` :

| Zone projet | Contenu | Guérison | Zone script |
|---|---|---|---|
| `code` | `conscience_logique/**/*.py` | bloquante | `code` |
| `actes` | `conscience_logique/actes/*.{json,txt,md}` sans préfixe `_` | churn | `actes` |
| `objectifs` | `conscience_logique/actes/_*.json` (plans, états) | churn | `ACTES` |
| `memoire_aq` | `memoire_aq/almizan_*` | churn | `memoire_aq` |

`_chemin_dans_copie` (499) résout aussi `objectifs_et_fil/<nom>` (507) pour ces
fichiers préfixés `_`.

`EXCLUDE_INTEGRITE` (54-70) retire le journal A232, les états volatils de la
fenêtre de dialogue, de la porte unique, des agents asynchrones et de la
rétroaction. `ZONES_STOP` (40) : `horloge_noyau/`, `secrets/` — jamais copiés,
jamais restaurés (contrôle en 99 et 662).

## 3. Détection A232 (`detecter_alterations`, 537)

Compare les SHA-256 live aux empreintes de la copie (`_chemin_dans_copie`, 499)
et rend trois types :

- `absent_de_la_copie` (564) : fichier neuf jamais sauvegardé, `guerir=False` —
  il survit, mais ne sera pas restauré.
- `hash_different` (586) : contenu différent de la copie, `guerir=True` — **la
  copie écrase le live**.
- `supprime_du_live` (615) : présent dans la copie, absent du live — sera
  restauré au prochain passage.

## 4. Guérison (`guerir_alterations`, 632)

Pour chaque altération réparable : refus si chemin sous `ZONES_STOP` (662),
puis `shutil.copy2(src, dst)` (671). Conséquences non évidentes :

1. Le live reprend les **octets anciens** de la copie.
2. Le live reprend aussi le **mtime ancien** de la copie.
3. L'événement est ajouté au journal `actes/_guerison_integrite_journal.jsonl`
   (72, `_append_guerison` 531).

`verifier_et_guerir` (701) enchaîne détection, guérison et re-sauvegarde.

## 5. Déclencheurs automatiques

- `conscience_logique/conscience.py:1409` appelle `verifier_et_guerir()` dans
  le cycle de conscience.
- `conscience_logique/homeostasie.py:130-132` l'appelle via
  `appliquer_rappels`; l'indicateur `integrite_sain` (57, 65-72, 92) retombe à
  zéro quand `detecter_alterations` n'est pas sain.

Une « simple lecture » d'état, un cycle ou un test qui traverse la conscience
peut donc déclencher la restauration. C'est pourquoi une vérification
prétendument en lecture seule doit être auditée avant d'être qualifiée comme
telle.

## 6. Pourquoi la réversion est invisible

- `find -newermt` ne montre aucun fichier récent : la restauration a remis
  l'ancien mtime. Un fichier modifié aujourd'hui peut afficher 2026-10-25.
- Le fichier restauré est syntaxiquement valide et de taille plausible ; seul un
  SHA-256 live vs copie le distingue.
- L'échec apparaît plus tard et ailleurs : `ImportError: cannot import name`
  quand un module restauré référence un nom supprimé dans l'autre fichier
  restauré.
- Un fichier **neuf** (absent de la copie) ne déclenche aucune guérison : le
  symptôme ne touche que des fichiers déjà sauvegardés une fois.

## 7. Churn permanent `actes` / `memoire_aq`

Les cycles réécrivent les actes et les miroirs après chaque sauvegarde. Mesure
du 2026-10-27 sur le dépôt réel : 63 actes et 62 miroirs `hash_different`
alors que `CODE=0`. Ce churn est **attendu** et n'est pas une régression :

- le script le classe `CHURN` et sort 0 ;
- `--strict` le rend bloquant pour une CI qui exige zéro écart ;
- un acte **neuf** est `absent_de_la_copie` (jamais guéri) et n'entre pas dans
  `REVERSIONNABLES`.

## 8. Ordre A231 (bug corrigé le 2026-10-27 à 15:11:09Z)

Avant correction, l'acte A231 était écrit **après** `_copier_arbre` : la copie
contenait toujours l'acte de la sauvegarde précédente. Résultat : les deux
fichiers d'acte A231 restaient `hash_different` après chaque sauvegarde, à
chaque fois — un écart de 2 par cycle, sans fin.

Correction : écrire l'acte (175-195) **avant** la copie (198-200). Deux détails
porteurs : `horodatage = _iso()` et `message` sont calculés une seule fois en
tête de fonction et réutilisés par le `RapportSauvegardeSoi` — déplacer le bloc
sans les hisser produit deux dates différentes et l'écart revient ; et
`enregistrer_empreintes_saines()` reste en fin de fonction. Ce dernier écrit un
JSON d'empreintes distinct : `detecter_alterations` ne le lit pas, il compare aux
octets de `courante`. Vérification sans modifier le fichier :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B -c "
import pathlib
t = pathlib.Path('conscience_logique/sauvegarde_soi.py').read_text(encoding='utf-8')
corps = t[t.index('def sauvegarder_soi'):]
i_acte = corps.index('_ecrire_json(CHEMIN_ACTE, acte)')
i_copie = corps.index('_copier_arbre(')
print('ORDRE_A231_ACTE_AVANT_COPIE', i_acte < i_copie)
"
```

Attendu : `ORDRE_A231_ACTE_AVANT_COPIE True`. Si `False`, l'écart A231 est un
vrai bug d'ordre, pas une simple salissure d'actes.

## 9. Journal A232

`_guerison_integrite_journal.jsonl` a atteint 16,7 Mo pendant l'incident ; il
n'est jamais tronqué ni réécrit. Le script en lit seulement la queue
(`max(65536, N*512)` octets), ignore une première ligne éventuellement tronquée
et saute les lignes JSON invalides. Filtrer avec `--since` plutôt que de
supprimer des lignes.
