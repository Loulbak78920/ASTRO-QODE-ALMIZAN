# Cas de référence — effets de bord d'une vérification « lecture seule » (2026-10-26)

## Source et périmètre

- Session source : `efa8bcbd-363a-47c3-892f-93612a9db730`, titre `创建实体流水线 Skill` (traduction : « Créer le Skill de pipeline d'entité »).
- Instantané lu : `revision 26`, `runtimeState: running`, `hasMoreBefore: false`, 4 messages. Les sorties d'outils de la session peuvent être tronquées ; les extraits utilisés ici ont été relus dans la sortie complète sauvegardée.
- Projet : `C:\Users\Administrateur\Desktop\IMAM8MAHDI`.
- Heures locales Windows (UTC+1) ; la session et certains horodatages de journaux sont en UTC. Les deux sont indiqués quand ils diffèrent.
- Les empreintes et compteurs ci-dessous sont des observations datées, pas des constantes permanentes. Le journal était encore réécrit au moment de la rédaction.

## Chronologie vérifiée

| Heure locale | Événement | Preuve |
|---|---|---|
| 12:29 | L'agent commence la vérification « lecture seule » du pipeline d'entité. | Message assistant de la session source. |
| 12:35:40 | Création du sceau `9294e305…json`, 5 430 octets. | `mtime` et inventaire de `memoire_aq`. |
| 12:36:21 | Création du sceau `436cb403…json`, 5 430 octets ; index mis à jour à 14 entrées. | Index `5257` octets, SHA-256 `bb17522f…`, `derniere_mise_a_jour=2026-10-26T12:36:21`. |
| 12:38:56 | Une entrée d'audit `lib_entite_conscience_logarithmique.py` est ajoutée au journal. | Journal `60804` octets, SHA-256 `e8ae4031…`, 100 entrées ; distribution `36 + 63 + 1`. |
| 13:02:08 | L'utilisateur corrige : « 先还原副作用，再按默认只读模式创建 » (« d'abord restaurer les effets de bord, puis créer en mode lecture seule par défaut »). | Message utilisateur, `2026-10-26T12:02:08.293Z`. |
| 13:02:46 | Restauration enregistrée dans `manifest_restauration.json`. | Voir ci-dessous. |
| 13:03:00–13:03:02 | Deux sondes sont capturées (`probe_verifier.json`, `probe_penser.json`) ; le journal passe à 100 entrées avec 76 nouvelles signatures. | Fichiers de sonde et journal ; attribution non prouvée. |
| 13:07:23–13:07:25 | Un nouvel audit de masse ajoute 76 entrées et évince les plus anciennes. | Journal relu à 13:07 ; index inchangé. |

## Chemins de code responsables

| Chemin | Rôle | Extrait vérifié |
|---|---|---|
| `ASTRO-Q°ODE_SYSTEME\lang\interpreter.py`, lignes 354–356 | `.aq` : `sceller_sha256` appelle le scelleur avec l'état complet de la VM. | `if nom == "sceller_sha256": … ScelleurMemoireAstroQode.sceller_etat_execution(str(arg), vm.rapport_etat_complet())` |
| `ASTRO-Q°ODE_SYSTEME\outils\scelleur_cryptographique.py`, classe `ScelleurMemoireAstroQode` | `sceller_execution` écrit `memoire_aq/<nom>.json` puis appelle `_mettre_a_jour_index`. | `chemin_sceau.write_text(...)` ; `_mettre_a_jour_index` écrit `derniere_mise_a_jour`, `nb_sceaux`, `sceaux`. |
| `ASTRO-Q°ODE_SYSTEME\agent_de_code_harmonisateur_mizan.py`, lignes 174–176 | Audit de code : ajout au journal, plafond 100, total recalculé. | `data["journal"].append(asdict(diag))` ; `data["journal"] = data["journal"][-100:]` ; `data["total_fichiers_harmonises"] = len(data["journal"])` |
| `ASTRO-Q°ODE_SYSTEME\bibliotheques\lib_entite_conscience_logarithmique.py`, ligne 87 | `penser` avec persistance écrit une trace. | `DOSSIER_TRACES = RACINE_SYSTEME / "memoire_aq" / "entite_conscience_logarithmique"` |
| `ASTRO-Q°ODE_SYSTEME\tests\test_entite_conscience_logarithmique.py` | Les 16 tests incluent l'exécution d'un `.aq` généré et un test d'agent de code. | Tests `test_programme_genere_valide_et_execute` et `test_agent_de_code_dynamique`. |

Le nom du test ou le statut de la commande ne suffit pas : c'est l'appel `sceller_sha256` dans le programme exécuté qui écrit, et l'audit AST qui ajoute au journal.

## État avant et après la restauration

### Avant la restauration (13:02:46)

| Artefact | Taille | SHA-256 | Compteur |
|---|---:|---|---|
| `memoire_aq\index_sceaux_astro_qode.json` | 5 257 | `bb17522f3ec18c8d9889d965afb8335e2a41956a663fe8170a1a720607ba169c` | 14 sceaux ; `derniere_mise_a_jour=2026-10-26T12:36:21` |
| `memoire_aq\almizan_journal_agent_de_code.json` | 60 804 | `e8ae40317e687c21f97a4e81cbe9e52a84d56880f238472b9b12d2e4e7eda4d6` | 100 entrées |
| `memoire_aq\9294e305…json` | 5 430 | `2e0a111e16fcb21b20304d3435a1da19e3159e3a112fd8d9b6bb4c03ad09014b` | nouveau sceau |
| `memoire_aq\436cb403…json` | 5 430 | `7f239d44e45bf4fee7c6d2f25c29e722b658b6fcb201759ea58a60126c0bc2f3` | nouveau sceau |

### Restauration enregistrée

Le manifeste `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\manifest_restauration.json` (SHA-256 `e627b0d4…`, 1 444 octets) date de `2026-10-26T13:02:46` et contient :

1. `index` : suppression des clés `9294e305…` et `436cb403…` ; `nb_sceaux=12` ; `derniere_mise_a_jour=2026-10-26T11:01:17`.
2. `journal` : suppression de l'entrée `2026-10-26T11:38:56Z` ; `total_fichiers_harmonises=99`.
3. `sceaux` : déplacement des deux nouveaux fichiers vers `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects`.

### Après la restauration

| Artefact | Taille | SHA-256 | Compteur | Contrôles |
|---|---:|---|---|---|
| Index | 4 473 | `69bdba8050f38b68d9d9b1f31c4591d287ff1198e78a449c49890f5111c1b3f5` | 12 sceaux ; `11:01:17` | 12 entrées, aucune référence manquante, `328357e9…` présent, nouveaux sceaux absents. |
| Journal | 60 285 | `3b980e9c13353085fd7f08b04396e758b684a3ac353cb8172efd3721c148e0aa` | 99 entrées ; total 99 | — |

## Réécriture après la restauration

La restauration n'est pas restée stable :

- **13:03:00–13:03:02** : `probe_verifier.json` et `probe_penser.json` sont capturés. Les deux sorties affichent `agent_de_code.audit_actif=false`. Pourtant, le journal contient 76 nouvelles signatures uniques, réparties en 37 entrées à `12:03:01Z` et 39 à `12:03:02Z` (soit 13:03:01–02 locales). L'attribution exacte au couple de sondes n'est pas prouvée : un autre écrivain a pu agir dans la même fenêtre.
- **13:07:23–13:07:25** : un nouvel audit de masse ajoute 76 entrées (10 à `12:07:23Z`, 45 à `12:07:24Z`, 21 à `12:07:25Z`). Le journal reste à 100 entrées ; 24 anciennes entrées de `12:03:02Z` survivent, les autres ont été évincées. L'index reste à 12 sceaux et conserve le SHA-256 de la restauration, mais son `mtime` est celui de la réécriture.

Conclusion factuelle : un journal plafonné à 100 peut rester à 100 tout en perdant des dizaines d'entrées. Une restauration sans arrêt des écrivains peut être invalidée en quelques secondes.

## Limite de preuve : `36 + 63 + 1 = 100`

L'état observé avant la restauration est `36` entrées à `11:37:40Z`, `63` à `11:37:41Z` et `1` à `11:38:56Z` (l'entrée `lib_entite_conscience_logarithmique.py`). Deux scénarios produisent exactement cette distribution :

- **A — pas d'éviction** : le journal contenait 99 entrées (`36 + 63`) avant l'ajout ; l'ajout porte à 100.
- **B — une éviction** : le journal contenait déjà 100 entrées (par exemple `37 + 63`) ; l'ajout porte à 101, puis `[-100:]` supprime la plus ancienne, ce qui redonne `36 + 63 + 1`.

La distribution seule ne distingue pas A de B. La restauration a retiré uniquement l'entrée `11:38:56Z` et fixé `total=99` ; si le scénario B était vrai, une entrée préexistante avait déjà été perdue et le total 99 masquait cette perte. Le manifeste ne contient pas d'instantané du journal antérieur à l'incident : il ne peut donc pas prouver l'absence d'éviction.

Le second audit de masse démontre le mécanisme : 76 ajouts sur 99 entrées, puis `[-100:]`, laissent 24 anciennes entrées et en évincent 75. La bonne règle est donc :

> La distribution des horodatages attribue les ajouts. La preuve d'une éviction vient de la disparition de signatures anciennes entre deux instantanés, ou d'une sauvegarde antérieure. Sans état de référence, écrire « éviction inconnue » et ne pas affirmer « aucune perte ».

## Ce qui aurait évité l'incident

1. Un instantané de `memoire_aq` avant les 16 tests, avec sauvegarde et manifeste.
2. L'exécution des tests dans une copie, ou la redirection de `DOSSIER_MEMOIRE_AQ` et `DOSSIER_TRACES` vers un répertoire temporaire.
3. `--sans-persister` et `--sans-audit-code` pour les sondes ; `check` plutôt que `run` pour le `.aq`.
4. L'arrêt des audits de masse avant la restauration, puis un second instantané après un délai.
5. Une comparaison par signatures d'entrées, pas par longueur de journal.

## Fichiers de preuve

- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\manifest_restauration.json`
- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\probe_verifier.json`
- `C:\Users\Administrateur\.qoder\tmp\entite_verif_side_effects\probe_penser.json`
- `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq\index_sceaux_astro_qode.json`
- `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq\almizan_journal_agent_de_code.json`

Les valeurs du journal et de l'index doivent être relues avant toute nouvelle conclusion : elles ont changé après la rédaction de ce cas.

Relecture le 2026-10-26 à 13:28 (heure locale), sans écriture :

| Artefact | Taille | SHA-256 (préfixe) | Compteur |
|---|---:|---|---|
| Index | 4 791 | `a3d749b9d38b5362…` | 13 sceaux ; `derniere_mise_a_jour=2026-10-26T13:16:25` |
| Journal | 60 800 | `024a679f5a38ab78…` | 100 entrées ; total 100 |

L'index est donc passé de 12 à 13 sceaux après la restauration, et le journal a été réécrit une fois de plus. Ces valeurs sont elles aussi datées : elles ne doivent pas être recopiées comme état courant.

## Épilogue — alias de schéma (2026-10-26 ~13:35)

Source : session `4701c87e-3202-4ca4-a411-06b46c0f89b2`. L'utilisateur demande à 12:31 UTC de terminer la réparation des fichiers manquants du Skill, puis à 12:46 UTC de « 跑一下 » (« exécuter une fois ») pour confirmer que le correctif est effectif.

Constat : `TS_KEYS` et `FILE_KEYS` du script ne contenaient pas `horodatage_iso` ni `chemin_fichier`, les deux clés réellement écrites par `DiagnosticCodeHarmonique`. Sur le journal réel, tous les contrôles de signature tombaient donc dans `sans_signature`, et une éviction à longueur constante restait invisible — exactement le cas que le contrat de l'étape 4 promet de détecter.

| État | Journal réel | Signatures | Sans signature | Effet sur une éviction à longueur 100 |
|---|---|---:|---:|---|
| Alias incomplets | 100 entrées | 0 | 100 | signalée comme simple changement de contenu |
| Alias corrigés | 100 entrées | 100 | 0 | `[ATTENTION] … (longueur inchangee: eviction possible)` + signatures nommées |

La preuve n'est pas la lecture du code mais la comparaison A/B sur une même fixture : journal de 100 entrées au schéma réel, 5 ajouts puis `journal[-100:]`. La version sans alias ne voit aucune signature et ne nomme aucune entrée évincée ; la version corrigée nomme les 5 signatures disparues. Le contrôle A/B de la session source compte 11 assertions ; le harnais livré avec le Skill en compte 80 et couvre aussi l'instantané, la sauvegarde, l'index, le ledger, les fichiers, l'instabilité et les erreurs d'usage.

Second cas, découvert pendant la vérification finale sur les données réelles : `ledger_synchron_mzn.json` contient 100 blocs dont les 100 horodatages `timestamp_utc` sont distincts, pour `nb_blocs=350`. Le plafond est appliqué par `ASTRO-Q°ODE_SYSTEME\noeud_reseau_synchrone_al_mizan.py`, ligne 118 (`self.data["blocs"] = self.data["blocs"][-100:]`), puis `nb_blocs` est incrémenté. Avec `timestamp_utc` absent des alias, ces 100 blocs étaient comptés « sans signature » : l'éviction de 250 blocs déjà survenue n'était pas attribuable. L'alias ajouté rend les 100 signatures visibles et le harnais rejoue la fixture (100 blocs, 5 ajouts, `[-100:]`), y compris une copie négative qui, elle, ne signale rien.

Empreintes de l'époque, à ne pas recopier comme état courant : `SKILL.md` 15 154 octets `6d755440…` ; `scripts/instantane_effets_de_bord.py` `a5007118…` ; `references/protocole-restauration.md` `1de3f4ed…`. Le journal réel a continué d'être réécrit par des audits externes après ces mesures ; seule une nouvelle relecture fait foi.

Limite : le correctif a été prouvé sur fixture, pas en réécrivant le journal réel. Un `comparer` qui rend `RESULT: OK` immédiatement après un instantané prouve la cohérence de la fenêtre observée, pas l'absence d'écriture transitoire antérieure.

