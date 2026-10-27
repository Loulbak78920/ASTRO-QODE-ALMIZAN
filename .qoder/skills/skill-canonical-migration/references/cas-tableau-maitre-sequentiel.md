# Cas vérifié : migration vers `tableau-maitre-sequentiel`

## Provenance

- Session source : `4958a992-f36f-4d91-8ade-0826edb1ec6e`, lue le 2026-10-25.
- Migration observée : création du Skill canonique `tableau-maitre-sequentiel` et conservation de `maj-tableau-maitre-sequentiel` comme couche de compatibilité.
- Portée : migration non destructive uniquement. Aucune suppression, archivage ou renommage n'a été exécuté.

## Rôles

| Élément | Rôle |
|---|---|
| `tableau-maitre-sequentiel` | Skill canonique : procédure, référence S0–S17, validateur de référence. |
| `maj-tableau-maitre-sequentiel` | Ancien Skill conservé : entrée de compatibilité, règles de domaine encore valides, validateur historique intact. |
| Générateur | Source unique du tableau maître ; jamais édité à la main. |
| CSV et HTML | Artefacts générés à la racine du projet ; lecture seule pendant la migration. |
| `horloge_noyau/` | Zone scellée : lecture et exécution autorisées, écriture interdite. |

## Empreintes de la migration

Les valeurs ci-dessous sont l'instantané de la migration du 2026-10-25. Elles ne sont pas des invariants permanents.

| Élément | Avant | Après | Statut |
|---|---|---|---|
| Validateur historique | `5248a2db5218d4b3f61b6ea5d6c2e22259337111acb8fba27d6bb6e6a227bd78` | `5248a2db5218d4b3f61b6ea5d6c2e22259337111acb8fba27d6bb6e6a227bd78` | inchangé |
| SKILL.md historique | `bcf119503a6873622b3ba53c9bfde0e054fee878c7179e6e3562bb7ce50009ab` | `63b70d1de863f021c9aa7e46240e4cb2b0ed54fce08f7210349009978482e6b1` | correction intentionnelle |
| Référence historique | `3fd63e710ce19c77f4147b189848e6c40da8c36e6f9660dcccc3b02c6aa85da1` | `27eba358d610c9300ee50ca36f10bfb66d5f499dfa9acd92fd4cfd5dfc16745c` | correction intentionnelle |
| SKILL.md canonique | absent | `3980f017ade28c4915789f894e6b1e1507743ba325cf0c0a8d3230d9ad3d64e8` | créé |
| Référence canonique | absent | `4eafb3f3233d22886f3cc7ea4f8703ec5fe215cf582826d12f2f2ede7dfabd83` | créée |
| Validateur canonique | absent | `5eaedd2594daa72b9599ecfcdfce9e5d671dba382a08f780881ecfebdc829c41` | créé |
| Générateur | `879ded9946b856b6e4335c91cf9a76418b255222130bf0c79fd5669b9f50425d` | `879ded9946b856b6e4335c91cf9a76418b255222130bf0c79fd5669b9f50425d` | inchangé |
| `lib_physique.py` | `b52c618130ea118b83297c59da5de2fc82eeb9312cb72b8872a37dc57be842b1` | `b52c618130ea118b83297c59da5de2fc82eeb9312cb72b8872a37dc57be842b1` | inchangé |
| `VERROU.json` | `3b4257bfa4cccb9bad356accfea91dec9580065731e3e5a94d5e3ce729ea816c` | `3b4257bfa4cccb9bad356accfea91dec9580065731e3e5a94d5e3ce729ea816c` | inchangé |
| CSV | `8bac258c6b5604f67c5153a9e3e91b2a801206de5d7c6554e57e5290eca48665` | `8bac258c6b5604f67c5153a9e3e91b2a801206de5d7c6554e57e5290eca48665` | inchangé |
| HTML | `e2e211436b569a55e86d1ce3ed27df534ccc4941cb27e88aa21e5c405272dc8d` | `e2e211436b569a55e86d1ce3ed27df534ccc4941cb27e88aa21e5c405272dc8d` | inchangé |

## Preuves de validation

- Vérification structurelle de la session source : 8 PASS, 0 FAIL, 0 WARN pour chacun des deux Skills.
- Validation finale de ce Skill (2026-10-25) avec la version actuelle de `skill-file-qa` : 9 PASS, 0 FAIL, 0 WARN pour chacun des deux Skills. Le nombre a augmenté parce que le validateur a gagné un contrôle ; il faut rapporter la sortie réelle, pas un nombre mémorisé.
- Validateur historique : EXIT 0, 0 avertissement.
- Validateur canonique : EXIT 0, 0 avertissement.
- Les cinq artefacts clés du projet (générateur, `lib_physique.py`, `VERROU.json`, CSV, HTML) avaient la même empreinte avant et après la migration.

## Corrections et échecs observés

1. **Paramètre de lecture de session.** `read_chat_session` attend `sessionId`, pas `session_id`. Le premier appel avec le mauvais nom a échoué.
2. **Écriture concurrente.** L'ancien Skill a été complété par un autre processus pendant la préparation. Le canonique et certains documents ont aussi changé après la première lecture. La bonne pratique est de relire l'état vivant avant chaque écriture et de ne pas écraser les changements récents.
3. **Affirmations obsolètes de l'ancien Skill.** La date HTML était décrite comme dynamique alors qu'elle était figée ; certaines clés de couleur manquaient ; la plage de séquence du docstring était ancienne. Ces points ont été corrigés avec preuve après relecture du générateur et des artefacts.
4. **Import d'un module scellé.** Importer `lib_physique.py` via `importlib` avec un nom synthétique a produit `AttributeError: 'NoneType' object has no attribute '__dict__'` dans le traitement des dataclasses. Pour comparer un algorithme scellé, extraire le code par AST plutôt que l'importer.
5. **Console Windows cp1252.** Afficher `→` dans un `print()` a produit `UnicodeEncodeError`. Les validateurs doivent écrire en ASCII pur ; utiliser `py -3.12`, car l'alias `python` peut être celui du Microsoft Store.
6. **Capture d'écran indisponible.** Le viewport in-app a retourné `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`. La validation est restée structurelle ; aucun succès visuel n'a été déclaré.
7. **Réponses ambiguës.** Deux réponses « TOUT » ont été données à des options mutuellement exclusives. Seul le sous-ensemble non destructif a été exécuté. Une suppression, un archivage ou un renommage aurait exigé une autorisation explicite sur le chemin et l'action.

## Cas négatifs exécutés sur une copie temporaire

Les 14 cas suivants ont été exécutés hors du projet. Les codes observés correspondent aux codes attendus.

| Cas | Code attendu | Code observé | Résultat |
|---|---:|---:|---|
| Copie de base | 0 | 0 | OK |
| Saut de séquence | 1 | 1 | OK |
| Distribution S6 erronée | 1 | 1 | OK |
| Ressource externe interdite | 1 | 1 | OK |
| Ressource externe tolérée | 0 | 0 | OK, 1 avertissement |
| Contenu HTML différent du CSV | 1 | 1 | OK |
| HTML absent | 2 | 2 | OK |
| Date HTML obsolète | 0 | 0 | OK, 1 avertissement |
| Date HTML obsolète en mode strict | 1 | 1 | OK |
| Docstring obsolète | 0 | 0 | OK, 1 avertissement |
| Docstring obsolète en mode strict | 1 | 1 | OK |
| Algorithme de répartition non équivalent | 1 | 1 | OK |
| Valeurs S6 codées en dur | 0 | 0 | OK, 1 avertissement |
| Valeurs S6 codées en dur en mode strict | 1 | 1 | OK |

## État actuel et limites

Après la migration, des écritures concurrentes ont été observées sur le Skill canonique et, entre la migration et la préparation de ce Skill, sur certains artefacts du projet. Les empreintes de la section « Empreintes de la migration » décrivent donc un instantané historique, pas l'état courant : les recalculer avant toute nouvelle migration. Lors des contrôles de cette session, le validateur historique et l'ancien Skill sont restés identiques (`5248a2db5218d4b3f61b6ea5d6c2e22259337111acb8fba27d6bb6e6a227bd78`, `63b70d1de863f021c9aa7e46240e4cb2b0ed54fce08f7210349009978482e6b1`, `27eba358d610c9300ee50ca36f10bfb66d5f499dfa9acd92fd4cfd5dfc16745c`), et les deux validateurs de domaine ainsi que `skill-file-qa` passaient encore.

Ces valeurs sont un instantané, pas une garantie. Recalculer les empreintes avant toute nouvelle migration. Les contrôles de structure ne prouvent pas la qualité de la traduction, ni le rendu runtime, ni l'exactitude métier ; ils prouvent seulement que les fichiers et les invariants déclarés sont cohérents au moment de la mesure.

## Commandes de contrôle

```bash
py -3.12 "$LEGACY/scripts/<validateur-historique>.py" --root "$PROJECT"
py -3.12 "$CANONICAL/scripts/<validateur-canonique>.py" --root "$PROJECT"
py -3 "<skill-file-qa>/scripts/validate_skill.py" "$CANONICAL" --workspace "$PROJECT"
py -3 "<skill-file-qa>/scripts/validate_skill.py" "$LEGACY" --workspace "$PROJECT"
sha256sum -c "$AUDIT/legacy-before.sha256"
sha256sum -c "$AUDIT/project-before.sha256"
```
