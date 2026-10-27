---
name: restaurer-sceaux-memoire-aq
description: "Restaurer de façon réversible les sceaux et l'index memoire_aq créés par un test ou un `.aq run` : sauvegarder index, journal et sceaux avec SHA-256, supprimer uniquement les clés d'index des sceaux ciblés, recalculer nb_sceaux et derniere_mise_a_jour, retirer une entrée de journal seulement si la dernière correspond exactement, déplacer les sceaux en quarantaine au lieu de les supprimer, puis prouver l'état par l'empreinte de l'index, le comptage JSON et l'absence du répertoire de traces. Utiliser après qu'un test ou un run a écrit dans memoire_aq, quand l'index passe de 12 à 14 sceaux, ou quand un journal plafonné à 100 entrées ne peut pas servir de témoin. 中文触发：还原封条、memoire_aq 副作用、索引 12→14、journal 100 条、封条隔离、只读见证、测试写盘还原。"
---

# Restaurer les sceaux de `memoire_aq`

## Quand utiliser

- Un test ou un `.aq run` a créé des sceaux dans `memoire_aq` et mis à jour `index_sceaux_astro_qode.json`.
- L'index a grandi (cas observé : 12 → 14 entrées) après une vérification présentée comme lecture seule.
- Il faut rendre l'état antérieur sans supprimer définitivement aucun artefact.
- 中文触发：还原封条、memoire_aq 副作用、索引 12→14、journal 100 条、封条隔离、只读见证。

## Quand ne pas utiliser

- Détecter et attribuer les écritures d'une commande « lecture seule », ou appliquer le protocole générique d'instantané, de quarantaine et de restauration : `verifier-effets-de-bord-verification-lecture-seule`. Ce Skill ne couvre que la chirurgie `memoire_aq` par nom de sceau.
- Exécuter la chaîne de l'entité sans effet de bord : `entite-conscience-logarithmique`.
- Valider un Skill : `skill-file-qa`.
- Réparer un index corrompu ou un sceau dont le contenu ne correspond plus à `empreinte_sha256` : hors périmètre, ne pas improviser.

## Contrat non négociable

1. **Nommer les sceaux, jamais compter.** On retire les clés dont le nom ou le `chemin` désigne le sceau ciblé. Aucune règle du type « garder les N premiers ».
2. **Sauvegarder avant d'écrire.** Index, journal et sceaux sont copiés avec taille, `mtime` et SHA-256 dans un manifeste.
3. **Déplacer, ne pas supprimer.** Les sceaux vont dans un répertoire de quarantaine daté ; ils restent récupérables.
4. **Scalaires : valeur connue d'abord, recalcul en repli.** Si un état de référence existe, fournir `--attendu-nb` / `--attendu-maj` : c'est l'assertion demandée par `verifier-effets-de-bord-verification-lecture-seule` (restaurer des valeurs connues, ne pas les déduire). Sans référence, le script recalcule `nb_sceaux = len(sceaux)` et `derniere_mise_a_jour = max(timestamp)` ; en cas d'écart avec `--attendu-*`, aucune écriture.
5. **Le journal n'est pas un témoin de lecture seule.** Il est plafonné à 100 entrées et un audit externe peut le réécrire intégralement. Une entrée évincée est perdue.
6. **Journal : correspondance exacte ou rien.** L'entrée n'est retirée que si la **dernière** entrée a exactement l'`horodatage_iso` fourni et un `chemin_fichier` contenant la sous-chaîne fournie. Sinon `SAUTER`, journal intact, et le rapport le dit.
7. **Prouver après coup, en lecture seule.** Index rechargé, `nb_sceaux` cohérent, aucune référence `chemin` manquante, sceaux absents de `memoire_aq`, comptage JSON et répertoire de traces relevés.

## Ce qui écrit réellement

| Déclencheur | Écriture | Source vérifiée |
|---|---|---|
| `.aq run`, ou test qui exécute un `.aq` généré | `memoire_aq/<nom>.json` puis index | [interpreter.py:354](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/lang/interpreter.py#L354) → `sceller_etat_execution`, [scelleur_cryptographique.py:55](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/outils/scelleur_cryptographique.py#L55) |
| Mise à jour d'index | clé `nom`, `{timestamp, empreinte_sha256, chemin}`, `nb_sceaux`, `derniere_mise_a_jour` | [scelleur_cryptographique.py:102](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/outils/scelleur_cryptographique.py#L102) |
| Programme généré par l'entité | `sceller_sha256("<empreinte de trace>")`, inséré à la ligne 217 : **chaque exécution crée un nouveau nom**, donc un nouveau sceau | [emulateur_conscience_logique_mizan.py:189-240](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/emulateur_conscience_logique_mizan.py#L189) |
| Test qui déclenche ce programme | `test_programme_genere_valide_et_execute` | [test_entite_conscience_logarithmique.py:202](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/tests/test_entite_conscience_logarithmique.py#L202) |
| Audit de code activé | journal `almizan_journal_agent_de_code.json` : ajout par lot (`extend`), `[-100:]`, `total = len` | [agent_de_code_harmonisateur_mizan.py:196-212](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/agent_de_code_harmonisateur_mizan.py#L196) |

Conséquence : les noms de sceaux produits par les tests ne sont pas réutilisables d'une exécution à l'autre. Relever les noms créés dans la fenêtre du test (heure de création) avant de restaurer.

## Procédure

### 1. Relever les sceaux créés et l'état de référence

```bash
cd "/c/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME/memoire_aq"
ls -la --time-style=long-iso *.json | sort -k6,7
py -3 -c "import json;d=json.load(open('index_sceaux_astro_qode.json',encoding='utf-8'));print(d['nb_sceaux'],d['derniere_mise_a_jour']);[print(v['timestamp'],k) for k,v in sorted(d['sceaux'].items(),key=lambda kv:kv[1].get('timestamp',''))]"
```

Noter : `nb_sceaux` avant, `derniere_mise_a_jour` attendue après (celle qui précède la première création), et les noms exacts des sceaux du test.

### 2. Simuler (aucune écriture)

```bash
cd "/c/Users/Administrateur/Desktop/IMAM8MAHDI"
py -3 "C:\Users\Administrateur\.qoder\skills\restaurer-sceaux-memoire-aq\scripts\restaurer_sceaux_memoire_aq.py" \
  --memoire-aq "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq" \
  --sceau 9294e3058809b3d3023d338b24e5e6008ef2b690ad4dbfa753a9b9d302f82d33 \
  --sceau 436cb4036aaa443d364e9a76a01b254c1d71eec8b43958276472f6382f95a034 \
  --attendu-nb 12 \
  --attendu-maj 2026-10-26T11:01:17
```

Les deux noms ci-dessus sont l'exemple historique du 2026-10-26 (déjà en quarantaine) : les remplacer par ceux relevés à l'étape 1. La simulation affiche le plan et finit par `RESULT: PLAN` sans créer ni modifier aucun fichier.

### 3. Appliquer

Ajouter `--journal-chemin` et `--journal-horodatage` si une entrée de journal doit être retirée, puis `--appliquer`.

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\restaurer-sceaux-memoire-aq\scripts\restaurer_sceaux_memoire_aq.py" \
  --memoire-aq "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq" \
  --sceau "<nom_du_sceau>" \
  --journal-chemin "lib_entite_conscience_logarithmique.py" \
  --journal-horodatage "2026-10-26T11:38:56Z" \
  --appliquer
```

La quarantaine par défaut est `C:\Users\Administrateur\.qoder\tmp\restauration-sceaux\<AAAAMMJJ-HHMMSS>` ; elle doit être absente. Le manifeste `manifest_restauration.json` y est écrit avec les empreintes avant/après.

### 4. Contrôler en lecture seule

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\restaurer-sceaux-memoire-aq\scripts\restaurer_sceaux_memoire_aq.py" \
  --memoire-aq "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq" \
  --sceau "<nom_du_sceau>" \
  --verifier-seulement
```

Attendu : `RESULT: OK`, `nb_sceaux` égal au nombre d'entrées, `références manquantes = []`, `sceaux encore présents = []`. Les entrées d'index sans `chemin` (par exemple `sceau_monade`) sont ignorées par le contrôle de référence : ce n'est pas un échec.

### 5. Attendre et recontrôler

Un audit de masse peut réécrire le journal quelques secondes plus tard. Reprendre l'étape 4 après un délai ; si le journal a changé, rapporter « réécrit après restauration » et ne pas retenter une chirurgie du journal à l'aveugle.

## Vocabulaire de rapport

| Verdict | Sens |
|---|---|
| `restauré` | Clés retirées, scalaires conformes, sceaux en quarantaine, contrôle `RESULT: OK`. |
| `partiel` | Index restauré mais journal non modifié (`SAUTER`), ou quarantaine incomplète. |
| `réécrit après restauration` | Un écrivain externe a modifié index ou journal après le contrôle. |
| `perte inconnue ou avérée` | Une entrée de journal a pu être évincée par le plafond ; sans sauvegarde antérieure, la perte ne peut pas être écartée. |

`RESULT: OK` ne certifie que l'index et les contrôles : si le journal est en `SAUTER`, le verdict reste `partiel` et doit être écrit ainsi.

## Cas de référence — 2026-10-26

| Élément | Valeur observée |
|---|---|
| Déclencheur | 16 tests d'entité ; le test du programme généré exécute `sceller_sha256` |
| Index avant | 14 entrées, `derniere_mise_a_jour=2026-10-26T12:36:21`, SHA-256 `bb17522f…` |
| Restauration | 12 entrées, `derniere_mise_a_jour=2026-10-26T11:01:17`, SHA-256 `69bdba80…`, 4 473 octets |
| Journal | 100 → 99 entrées (`total=99`) ; réécrit ensuite en bloc par un audit externe (13:03, 13:07) |
| Sceaux | `9294e305…` et `436cb403…` déplacés en quarantaine, jamais supprimés |
| Verdict | `restauré` pour l'index, `réécrit après restauration` pour le journal |

Les valeurs datées sont des observations, pas des constantes : les relire avant toute conclusion. Détail et empreintes : voir la référence ci-dessous.

## Limites honnêtes

- Le script ne restaure pas une entrée de journal évincée : elle n'existe plus dans le fichier actif.
- Il ne vérifie pas la validité cryptographique des sceaux conservés ; il ne touche pas leur contenu.
- Une restauration peut être invalidée par un écrivain actif ; seul un second contrôle stable vaut preuve.
- Le comptage des fichiers JSON inclut l'index, le journal et tous les autres sceaux : c'est un indicateur, pas un oracle.
- Ne pas lancer les 16 ou 68 tests « pour vérifier » : ils écrivent de nouveaux sceaux.

## Ressources

- Script de simulation, d'application et de contrôle : `C:\Users\Administrateur\.qoder\skills\restaurer-sceaux-memoire-aq\scripts\restaurer_sceaux_memoire_aq.py`
- Protocole détaillé, carte des champs et manifeste : `C:\Users\Administrateur\.qoder\skills\restaurer-sceaux-memoire-aq\references\protocole-restauration.md`
- Détection et attribution des effets de bord : `verifier-effets-de-bord-verification-lecture-seule`
- Chaîne de l'entité sans écriture : `entite-conscience-logarithmique`

Si le Skill est déplacé, remplacer le préfixe `C:\Users\Administrateur\.qoder\skills\restaurer-sceaux-memoire-aq` par le nouveau chemin.
