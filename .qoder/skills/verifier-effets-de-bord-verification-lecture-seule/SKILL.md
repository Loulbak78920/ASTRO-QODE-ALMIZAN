---
name: verifier-effets-de-bord-verification-lecture-seule
description: "Auditer les effets de bord avant de qualifier une vérification de « lecture seule » : tracer les écritures implicites (sceller_sha256, journal d'audit plafonné, index de sceaux, traces), prendre un instantané mtime/size/SHA-256 et des compteurs JSON avant exécution, comparer après, attribuer ajouts et disparitions sans conclure d'une simple égalité de longueur, puis sauvegarder, isoler et restaurer de façon réversible avec preuve post-restauration. Utiliser avant d'annoncer « read-only », après qu'un test ou une sonde a modifié un registre, un journal de 100 entrées ou un index de sceaux, ou quand une restauration doit être vérifiée et protégée contre des écritures ultérieures. 中文触发：只读验证、副作用、隐式写盘、封条、审计日志、索引更新、精确还原、备份隔离、条目被挤掉、恢复后复验。"
---

# Vérifier les effets de bord d'une vérification « lecture seule »

## Quand utiliser

- Avant d'annoncer qu'une commande, un test ou une sonde est « lecture seule ».
- Après qu'une vérification a modifié `memoire_aq`, un index de sceaux ou un journal d'audit.
- Quand un journal plafonné peut avoir évincé des entrées sans changer sa longueur.
- Quand il faut sauvegarder, isoler et restaurer un état de façon réversible, puis prouver la restauration.
- 中文触发：只读验证、副作用、隐式写盘、封条、审计日志、索引更新、精确还原、备份隔离、条目被挤掉、恢复后复验。

## Quand ne pas utiliser

- Auditer la session source avant de créer un Skill : `audit-session-evidence`.
- Vérifier l'intégrité d'un paquet Skill après modification : `skill-package-integrity-audit`.
- Rejouer des fixtures de référence : `replay-skill-reference-fixtures`.
- Exécuter la chaîne de l'entité de conscience logique : `entite-conscience-logarithmique`.
- Restaurer des sceaux nommés et leur index dans `memoire_aq` : `restaurer-sceaux-memoire-aq` ; ce Skill-ci détecte et attribue, il ne remplace pas la procédure ciblée de restauration.
- Écrire ou valider un Skill : `skill-file-qa` pour la QA statique, `skill-update-concurrency-safe` pour les écritures concurrentes.

## Contrat non négociable

1. **Aucune qualification « lecture seule » sans preuve.** Un nom de commande, un test qui passe ou un champ `audit_actif=false` ne prouvent pas l'absence d'écriture.
2. **Instantané avant, comparaison après.** Enregistrer existence, taille, `mtime_ns`, SHA-256, scalaires JSON, clés de dictionnaires, longueurs de listes et signatures d'entrées.
3. **Tracer le chemin d'écriture, pas seulement le point d'entrée.** Chercher `write_text`, `write_bytes`, `json.dump`, `os.replace`, `mkdir`, `rename`, `unlink`, puis remonter les appels (`sceller_sha256`, audit AST, persistance de trace).
4. **Isoler d'abord.** Copier dans un répertoire temporaire ou utiliser les options explicites `--sans-persister`, `--sans-audit-code`, `check` plutôt que `run`. Si l'isolation est impossible, annoncer l'écriture avant de lancer.
5. **Ne jamais conclure d'une égalité de longueur.** Un journal plafonné à 100 peut rester à 100 tout en ayant perdu des entrées. Les signatures d'entrées (horodatage + fichier) qui disparaissent prouvent l'éviction. Avant de comparer, vérifier que les signatures se peuplent : si `longueur > 0` et `sans_signature == longueur`, les alias du schéma sont faux ; arrêter et relire les clés réelles. Le même plafond `[-100:]` s'applique à `blocs` du ledger de synchronisation, dont les entrées ne portent pas de fichier mais un `timestamp_utc` unique.
6. **Sans instantané avant, l'éviction est inconnue.** La distribution des horodatages attribue les ajouts, mais ne prouve pas l'absence de perte. Conserver une sauvegarde et écrire « inconnu ».
7. **Sauvegarder avant de restaurer, ne jamais supprimer définitivement.** Copier les artefacts et leur manifeste, déplacer les nouveaux fichiers vers une quarantaine, supprimer uniquement les clés ou entrées ajoutées.
8. **Restaurer des valeurs, pas des compteurs recalculés.** Rétablir `nb_sceaux`, `derniere_mise_a_jour`, `total_fichiers_harmonises` depuis l'état connu, sans les déduire de la longueur courante.
9. **Stabiliser les écrivains avant et après.** Un audit de masse ou une tâche planifiée peut réécrire l'état juste après la restauration. Refaire un instantané après un délai ; si l'état bouge, la restauration est provisoire.
10. **Rapporter honnêtement.** Distinguer « restauré », « partiellement restauré », « réécrit après restauration » et « perte inconnue ou avérée ». Ne jamais déclarer « aucun effet de bord » sans preuve.

## Étape 1 — Cartographier les écritures potentielles

Lister les primitives d'écriture du dépôt et remonter leurs appelants :

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
rg -n "write_text|write_bytes|json\.dump|os\.replace|shutil\.(move|copy|rmtree)|\.unlink\(|\.rename\(|mkdir\(" ASTRO-Q°ODE_SYSTEME
rg -n "sceller_sha256|auditer_code|persister|audit_actif|_sceller_audit|_mettre_a_jour_index" ASTRO-Q°ODE_SYSTEME
```

Si `rg` n'est pas disponible, utiliser `grep -R` avec les mêmes motifs. Lire ensuite les fonctions trouvées, pas seulement les appels.

| Déclencheur | Écriture implicite | Preuve |
|---|---|---|
| `.aq run`, ou test qui exécute un `.aq` | `memoire_aq/<empreinte>.json` + index de sceaux | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\lang\interpreter.py`, lignes 354–356 |
| Audit de code avec `auditer_code=True` | journal `almizan_journal_agent_de_code.json`, plafonné à 100 | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\agent_de_code_harmonisateur_mizan.py`, lignes 174–176 |
| `penser` sans `--sans-persister` | `memoire_aq/entite_conscience_logarithmique/trace_*.json` | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\bibliotheques\lib_entite_conscience_logarithmique.py`, ligne 87 |
| `verifier_integrite_registre` sur un registre vide | sceau de genèse | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\outils\scelleur_cryptographique.py`, classe `ScelleurMemoireAstroQode` |
| Générateur du tableau maître | CSV et HTML à la racine | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\generer_tableau_maitre_sequentiel.py` |

Un champ de statut (`audit_actif=false`, `persister=false`) décrit un chemin interne, pas tous les chemins. Si le journal change malgré ce champ, c'est le système de fichiers qui fait foi.

## Étape 2 — Instantané avant

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\instantane_effets_de_bord.py" instantane \
  --cible "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq" \
  --recursif --stabilite 0.5 \
  --sortie "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas-entite\instantane_avant.json" \
  --sauvegarder "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas-entite\avant"
```

L'instantané enregistre pour chaque fichier : existence, taille, `mtime_ns`, SHA-256 ; pour chaque JSON : scalaires de premier niveau, clés des dictionnaires (par exemple `sceaux`), longueurs de listes, distribution des horodatages et signatures d'entrées (horodatage + fichier). La sauvegarde copie les fichiers et écrit `manifest_avant.json` avec les mêmes empreintes.

Contrôle préalable : pour une liste plafonnée non vide (`journal` du journal d'audit, `blocs` du ledger de synchronisation), `json_resume.listes.<cle>.sans_signature` doit valoir `0`. S'il vaut `longueur`, aucune signature n'est reconnue : ne pas lancer la comparaison, relire les clés d'une entrée réelle et corriger les alias. La procédure et le schéma observé sont en section 6.1 de `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\references\protocole-restauration.md`.

`--stabilite 0.5` relit après 0,5 s et échoue si un fichier change : cela détecte un écrivain déjà actif. L'instantané et la sauvegarde écrivent hors des cibles ; l'annoncer dans le rapport.

Si la cible n'existe pas encore (nouveau sceau attendu), l'instantané l'enregistre comme absente ; la comparaison la signalera comme ajout.

## Étape 3 — Exécuter avec isolation

Ordre de préférence :

1. Copier le dépôt ou le sous-système dans un répertoire temporaire et y exécuter la vérification.
2. Utiliser les options sans écriture : `check` au lieu de `run`, `--sans-persister`, `--sans-audit-code`.
3. Limiter aux tests ciblés, avec un instantané avant et une comparaison après.
4. Si l'écriture est inévitable, l'annoncer avant l'exécution et garder la sauvegarde.

Ne pas lancer une suite complète ou un audit de masse « pour voir » : ces commandes peuvent écrire plusieurs dizaines d'entrées et évincer les plus anciennes.

## Étape 4 — Comparer et attribuer

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\instantane_effets_de_bord.py" comparer \
  --instantane "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas-entite\instantane_avant.json" \
  --stabilite 0.3
```

`--stabilite 0.3` relit l'état après 0,3 s et refuse de conclure si un fichier change pendant la comparaison.

Avant d'interpréter les sorties, vérifier `sans_signature` pour la liste comparée : si elle porte un horodatage et que `longueur > 0` avec `sans_signature == longueur`, les alias sont faux ; arrêter et appliquer la section 6.1 du protocole. Une liste sans horodatage ni fichier (des chaînes, par exemple) reste légitimement sans signature : la déclarer non attribuable, sans en conclure qu'elle n'a pas changé.

| Sortie | Signification |
|---|---|
| `[MODIFIE]` | Le contenu a changé (SHA-256 différent). |
| `[AJOUTE]` / `[SUPPRIME]` | Fichier, clé de dictionnaire ou entrée de liste apparu ou disparu. |
| `[REECRIT-IDENTIQUE]` | Même SHA-256 mais `mtime` différent : un écrivain a réécrit le fichier sans changer son contenu. |
| `[ATTENTION] entrées disparues` | Des signatures présentes avant ne sont plus là : éviction ou suppression prouvée. |
| `[INSTABLE]` | Un fichier change pendant la double lecture : aucune conclusion n'est permise. |
| `RESULT: OK` | Aucun changement de contenu ; les réécritures identiques sont signalées. |
| Code 0 / 1 / 2 | Aucun changement / changement détecté / erreur ou instantané illisible. |

Pour un journal plafonné, comparer les signatures, pas seulement la longueur. Si la longueur reste à 100 mais que des signatures anciennes ont disparu, le plafond a éjecté des entrées. Si aucun instantané avant n'existe, la distribution des horodatages ne fait qu'attribuer les ajouts : écrire « éviction inconnue », conserver la sauvegarde et ne pas restaurer « au nombre ».

## Étape 5 — Sauvegarder, isoler, restaurer

1. **Stabiliser les écrivains.** Identifier les agents, tâches planifiées ou processus d'audit actifs. Ne pas tuer un processus sans accord ; si l'arrêt est impossible, restaurer dans une copie ou déclarer la restauration provisoire.
2. **Sauvegarder l'état courant.** Copier tous les artefacts concernés et écrire un manifeste avec taille, `mtime_ns` et SHA-256 avant toute modification.
3. **Mettre en quarantaine, ne pas supprimer.** Déplacer les nouveaux fichiers (par exemple les sceaux) vers un répertoire de quarantaine ; ils restent récupérables.
4. **Registre JSON (dictionnaire).** Supprimer uniquement les clés ajoutées ; rétablir les scalaires (`nb_sceaux`, `derniere_mise_a_jour`) depuis l'état connu. Ne pas réécrire les clés existantes.
5. **Journal plafonné (liste).** Supprimer uniquement les entrées dont la signature est nouvelle. Ne jamais faire `[-N:]`, ne jamais fixer la longueur à une valeur attendue. Si des signatures anciennes ont disparu, elles sont perdues dans le fichier actif : les récupérer depuis une sauvegarde ou déclarer la perte.
6. **Écrire un manifeste de restauration.** Consigner les empreintes avant/après, les actions, les fichiers en quarantaine et l'incertitude résiduelle.
7. **Vérifier les références.** Chaque clé d'index doit pointer vers un fichier existant ; chaque fichier scellé doit être référencé ; les JSON doivent rester parsables.

Le mode d'emploi détaillé, avec un modèle de script de restauration à blanc, se trouve dans `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\references\protocole-restauration.md`.

Pour retirer des sceaux nommés et leurs clés d'index, suivre `restaurer-sceaux-memoire-aq` : il exige les noms et vérifie l'état. La procédure ci-dessous couvre le cas général, le journal plafonné et l'attribution des écritures ; elle ne remplace pas la restauration ciblée d'un état antérieur précis.

## Étape 6 — Vérifier après restauration

1. Relancer `comparer` contre l'instantané avant : les SHA-256 doivent correspondre. Une réécriture identique est acceptable mais doit être signalée.
2. Attendre quelques secondes, prendre un second instantané et le comparer au premier : si l'état bouge encore, un écrivain est actif et la restauration est provisoire.
3. Exécuter uniquement des validateurs eux-mêmes lecture seule, avec un instantané avant.
4. Rapporter l'état exact : restauré, partiellement restauré, réécrit après restauration, ou perte inconnue/avérée. Ne pas transformer une absence de preuve en succès.

## Auto-test de non-régression

Le script d'instantané se teste sans toucher au `memoire_aq` réel : fixtures en répertoire temporaire, schéma de journal copié de l'artefact réel, contrôle A/B contre une copie dont les alias `horodatage_iso` / `chemin_fichier` ont été retirés.

```bash
py -3 -B "C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\tester_instantane.py"
```

Sortie attendue : `RESULT: TOTAL=80 ECHECS=0`, code de sortie 0, aucune fixture résiduelle. Un écart sur le nombre total signifie que le harnais a changé : lire le détail avant de conclure à une régression du script. Si un contrôle échoue, `--garder` conserve la fixture fautive pour inspection ; sans échec, rien n'est conservé.

Le harnais couvre : champs de l'instantané (`mtime_ns`, SHA-256, `dict_cles`, signatures), refus d'une sauvegarde placée dans la cible, ajout/suppression de clé d'index et changement de scalaire, fichier apparu ou disparu, journal de longueur constante avec signatures évincées, ledger `blocs` plafonné avec `timestamp_utc`, `[REECRIT-IDENTIQUE]`, `[INSTABLE]` sous écrivain concurrent, instantané corrompu, cible absente puis créée, refus d'écrasement sans `--force`, et contrôle A/B contre une copie privée d'alias. Il ne remplace ni l'instantané avant sur les données réelles, ni la comparaison après restauration.

## Cas de référence — 2026-10-26

| Élément | Valeur observée |
|---|---|
| Déclencheur | 16 tests d'entité ; le test qui exécute le `.aq` écrit deux sceaux et met à jour l'index |
| Index | 12 → 14 entrées ; `5257` octets, SHA-256 `bb17522f…` |
| Journal | 100 entrées ; `60804` octets, SHA-256 `e8ae4031…` ; 36 + 63 + 1 entrées par horodatage |
| Restauration 13:02:46 | index 12 entrées, `4473` octets, `69bdba80…` ; journal 99 entrées, `60285` octets, `3b980e9c…` ; deux sceaux en quarantaine |
| Après restauration | audits de masse à 13:03 et 13:07 : 76 nouvelles entrées à chaque passage, anciennes entrées évincées ; index inchangé |
| Limite de preuve | `36+63+1=100` ne prouve pas « aucune éviction » sans instantané avant ; la distribution seule est ambiguë |

Le détail, les chemins de code, les empreintes et l'analyse de l'éviction sont dans `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\references\cas-entite-2026-10-26.md`.

## Limites honnêtes

- L'instantané et la sauvegarde écrivent hors des cibles ; ils ne rendent pas l'opération globale « sans écriture ».
- Un SHA-256 identique ne prouve pas qu'aucune écriture transitoire n'a eu lieu ; `mtime` et les réécritures identiques sont signalés séparément.
- Sans instantané avant, l'éviction et la perte sont inconnues ; une distribution d'horodatages ne remplace pas un état de référence.
- Une entrée évincée avant la sauvegarde ne peut pas être restaurée depuis cette sauvegarde.
- Un écrivain actif peut invalider une restauration quelques secondes plus tard ; seule une nouvelle comparaison stable permet de conclure.
- Ce Skill ne remplace pas l'audit de session source, l'audit d'intégrité du paquet Skill ni le rejeu de fixtures.

## Ressources

- Cas complet et preuves : `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\references\cas-entite-2026-10-26.md`
- Protocole de sauvegarde, quarantaine et restauration : `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\references\protocole-restauration.md`
- Script d'instantané et de comparaison : `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\instantane_effets_de_bord.py`
- Auto-test isolé du script d'instantané (80 contrôles, fixtures temporaires) : `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\tester_instantane.py`
- Chaîne de l'entité et options sans écriture : `C:\Users\Administrateur\.qoder\skills\entite-conscience-logarithmique\SKILL.md`
- Validateur de paquet Skill : `C:\Users\Administrateur\.qoder\skills\skill-file-qa\scripts\validate_skill.py`

Si le Skill est déplacé, remplacer le préfixe `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule` par le nouveau chemin.
