# Protocole de restauration des sceaux de `memoire_aq`

## Périmètre et source

- Projet : `C:\Users\Administrateur\Desktop\IMAM8MAHDI`, sous-système `ASTRO-Q°ODE_SYSTEME`.
- Session source : `efa8bcbd-363a-47c3-892f-93612a9db730`, lue en `revision 16` (`runtimeState: running`, `hasMoreBefore: false`). Les textes d'assistant de `read_chat_session` étaient tronqués : les commandes et sorties citées ici viennent du JSONL brut `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\efa8bcbd-363a-47c3-892f-93612a9db730.jsonl`.
- Correction utilisateur retenue : « 先还原副作用，再按默认只读模式创建 » (`2026-10-26T12:02:08.293Z`).
- Les empreintes de ce document ont été re-mesurées sur les fichiers de quarantaine au moment de la création du Skill. Ce sont des observations datées, pas des constantes.

## Carte des écritures

| Chemin | Rôle | Extrait vérifié |
|---|---|---|
| `ASTRO-Q°ODE_SYSTEME\lang\interpreter.py:354-359` | `.aq` : `sceller_sha256(nom)` appelle le scelleur avec l'état complet de la VM. | `ScelleurMemoireAstroQode.sceller_etat_execution(nom_sceau=str(arg_val), rapport_vm=self.vm.rapport_etat_complet())` |
| `ASTRO-Q°ODE_SYSTEME\outils\scelleur_cryptographique.py:55-100` | Écrit `memoire_aq/<nom_propre>.json`, puis met à jour l'index. Le nom est normalisé (`isalnum`, `_`, `-`). | `chemin_sceau.write_text(json.dumps(sceau, ...))` |
| `ASTRO-Q°ODE_SYSTEME\outils\scelleur_cryptographique.py:102-127` | `_mettre_a_jour_index` : ajoute la clé `nom`, pose `derniere_mise_a_jour = ts`, `nb_sceaux = len(sceaux)`. | `sceaux_map[nom] = {"timestamp": ts, "empreinte_sha256": sha256, "chemin": chemin}` |
| `ASTRO-Q°ODE_SYSTEME\emulateur_conscience_logique_mizan.py:189-240` | Le programme généré contient `sceller_sha256("<empreinte de trace>")`. **Chaque exécution produit un nom différent.** | `alpha_empreinte = sceller_sha256("...");` |
| `ASTRO-Q°ODE_SYSTEME\tests\test_entite_conscience_logarithmique.py:202` | `test_programme_genere_valide_et_execute` génère puis exécute ce programme : c'est le test qui scelle. | `InterpreteurAstroQode().executer_source(source)` |
| `ASTRO-Q°ODE_SYSTEME\agent_de_code_harmonisateur_mizan.py:196-212` | Journal : ajout par lot (`_sceller_audits`, `extend`), plafond `[-100:]`, `total_fichiers_harmonises = len(journal)`. Écrit sans `ensure_ascii=False` ; ce lot explique les réécritures de 76 entrées. | `data["journal"] = data["journal"][-100:]` |

## Schémas utiles

Index `memoire_aq\index_sceaux_astro_qode.json` :

```json
{
  "sceaux": {
    "<nom>": {
      "timestamp": "2026-10-26T12:36:21",
      "empreinte_sha256": "<empreinte canonique du sceau>",
      "chemin": "C:\\Users\\Administrateur\\Desktop\\IMAM8MAHDI\\ASTRO-Q°ODE_SYSTEME\\memoire_aq\\<nom>.json"
    }
  },
  "derniere_mise_a_jour": "2026-10-26T12:36:21",
  "nb_sceaux": 14,
  "qubit_physique_local": false,
  "completude_pourcent": 100.0
}
```

Points de vigilance :

- La clé est le nom du sceau, pas nécessairement le SHA-256 du fichier. Pour un sceau produit par le programme généré, le nom est l'empreinte de la trace.
- `empreinte_sha256` est l'empreinte canonique du dictionnaire du sceau. Elle diffère du SHA-256 des octets du fichier : pour `9294e305…json`, fichier = `2e0a111e…`, 5 430 octets.
- Certaines entrées ont un `chemin` vide (cas observé : `sceau_monade`). Le contrôle de référence les ignore ; ce n'est pas une corruption.
- Ne pas réécrire les clés existantes : supprimer uniquement les clés ciblées, puis recalculer `nb_sceaux` et `derniere_mise_a_jour`.

Sceau `memoire_aq\<nom>.json` : `nom_sceau`, `timestamp`, `statut`, `doi`, `invariants`, `garde_fous`, `etat_vm_biomecanique`, `metadata_supplementaire`, `empreinte_sha256`.

Journal `memoire_aq\almizan_journal_agent_de_code.json` : `agent`, `date_creation_iso`, `total_fichiers_harmonises`, `journal` (liste d'objets avec `horodatage_iso`, `chemin_fichier`, `score_harmonie_100`, …).

## Règle du journal

1. Le plafond `[-100:]` signifie qu'un ajout peut évincer la plus ancienne entrée sans changer la longueur (100 → 100). Une égalité de longueur ne prouve rien.
2. Un audit externe peut réécrire le fichier entier. Deux réécritures de 76 entrées ont été observées à 13:03 et 13:07 locales après une restauration réussie : l'entrée retirée n'est pas revenue, mais le reste du fichier a été remplacé.
3. Règle appliquée : retirer **uniquement** la dernière entrée, et **uniquement** si `horodatage_iso` est exactement celui fourni et si `chemin_fichier` contient la sous-chaîne fournie. Sinon `SAUTER`, journal intact.
4. Ne jamais écrire `total_fichiers_harmonises` à une valeur arbitraire : le recalculer avec `len(journal)` après retrait.
5. Une entrée évincée avant la sauvegarde est perdue. Le rapport doit alors dire « perte inconnue ou avérée ».
6. `RESULT: OK` ne dit rien du journal : si l'état est `SAUTER`, la restauration est `partielle` et le rapport doit le nommer.

Articulation avec `verifier-effets-de-bord-verification-lecture-seule` : ce dernier fournit l'instantané, la comparaison et le protocole générique (restaurer des valeurs connues) ; ce Skill n'ajoute que la suppression des clés par nom de sceau, la garde de la dernière entrée du journal et les assertions `--attendu-*`. Fournir ces assertions dès qu'un état de référence existe.

## Manifeste

`manifest_restauration.json` est écrit dans le répertoire de quarantaine :

| Champ | Contenu |
|---|---|
| `horodatage` | Date locale de l'application. |
| `memoire_aq` | Répertoire traité. |
| `sceaux_demandes` | Noms normalisés fournis. |
| `cles_supprimees` | Clé d'index → nom de sceau. |
| `nb_sceaux_avant`, `nb_sceaux_apres` | Compteurs avant et après. |
| `derniere_mise_a_jour_apres` | `max(timestamp)` des entrées restantes. |
| `journal` | `etat` (`RETIRER`/`SAUTER`/`ABSENT`), `detail`, `ecrit`. |
| `fichiers_avant`, `fichiers_apres` | `sha256`, `octets`, `mtime` par fichier. |
| `quarantaine` | Sceaux déplacés : chemin et SHA-256. |
| `sauvegarde` | Copie des fichiers d'origine. |

## Cas de référence 2026-10-26

| Élément | Valeur mesurée |
|---|---|
| Index avant restauration | 14 entrées, `derniere_mise_a_jour=2026-10-26T12:36:21`, 5 257 octets, SHA-256 `bb17522f3ec18c8d9889d965afb8335e2a41956a663fe8170a1a720607ba169c` |
| Index après restauration | 12 entrées, `derniere_mise_a_jour=2026-10-26T11:01:17`, 4 473 octets, SHA-256 `69bdba8050f38b68d9d9b1f31c4591d287ff1198e78a449c49890f5111c1b3f5` |
| Journal avant | 100 entrées, 60 804 octets, SHA-256 `e8ae40317e687c21f97a4e81cbe9e52a84d56880f238472b9b12d2e4e7eda4d6` |
| Journal après retrait | 99 entrées, `total=99`, 60 285 octets, SHA-256 `3b980e9c13353085fd7f08b04396e758b684a3ac353cb8172efd3721c148e0aa` |
| Sceau `9294e305…json` | 5 430 octets, SHA-256 `2e0a111e16fcb21b20304d3435a1da19e3159e3a112fd8d9b6bb4c03ad09014b`, en quarantaine |
| Sceau `436cb403…json` | 5 430 octets, SHA-256 `7f239d44e45bf4fee7c6d2f25c29e722b658b6fcb201759ea58a60126c0bc2f3`, en quarantaine |
| Manifeste | 1 444 octets, SHA-256 `e627b0d476cf6328fda0be64af6a8e508d0b7118e3368a1630f1bc3dd4fd4666` |
| Entrée de journal retirée | `2026-10-26T11:38:56Z` / `lib_entite_conscience_logarithmique.py` |

Les fichiers de quarantaine sont dans `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\`. Ils contiennent aussi les sceaux d'exécutions ultérieures (`8c4d11bd…`, `3e9c4502…`) et une copie d'index postérieure.

## Sorties du script

| Sortie | Sens | Code |
|---|---|---|
| `RESULT: PLAN` | Simulation terminée, aucune écriture. | 0 |
| `RESULT: OK` | Application et contrôle réussis pour l'index ; le journal peut être intact (`SAUTER`), auquel cas le verdict global est `partiel`. | 0 |
| `RESULT: FAIL` | Application faite mais contrôle en échec (index incohérent, référence manquante, sceau encore présent). | 1 |
| `RESULT: REFUS` | Précondition non remplie (sceau introuvable, clé absente, `--attendu-*` non conforme, quarantaine existante) : aucune écriture. | 1 |
| `RESULT: ERREUR` | Argument ou environnement invalide (index/journal illisible, `--journal-chemin` sans `--journal-horodatage`). | 2 |
| `[ATTENTION] journal non modifié` | La dernière entrée ne correspond pas à la condition : journal intact. | — |

## Limites

- Aucune reconstruction d'une entrée de journal évincée.
- Aucun contrôle cryptographique des sceaux conservés ni réparation d'un index corrompu.
- Une restauration peut être invalidée par un écrivain actif ; un second contrôle stable est nécessaire pour conclure.
- Le script écrit hors de `memoire_aq` (quarantaine, sauvegarde, manifeste) : l'annoncer dans le rapport.

## Fichiers de preuve

- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\manifest_restauration.json`
- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\index_sceaux_astro_qode.json`
- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\almizan_journal_agent_de_code.json`
- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\9294e3058809b3d3023d338b24e5e6008ef2b690ad4dbfa753a9b9d302f82d33.json`
- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\436cb4036aaa443d364e9a76a01b254c1d71eec8b43958276472f6382f95a034.json`
