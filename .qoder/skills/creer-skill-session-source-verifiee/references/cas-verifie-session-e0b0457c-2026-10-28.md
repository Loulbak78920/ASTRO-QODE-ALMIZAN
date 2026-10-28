# Cas vérifié — créer un Skill depuis la session e0b0457c (2026-10-28)

## Source

- Session : `e0b0457c-795b-41fc-890c-7f5dcaf5be79`, titre « 创建Solidity审计Skill ».
- JSONL : `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\e0b0457c-795b-41fc-890c-7f5dcaf5be79.jsonl`.
- État au 2026-10-28 : `runtimeState=cold`, `revision=0`, `hasMoreBefore=false`, 1 message humain, 58 tool_uses et 58 tool_results appariés.
- Mesures du JSONL : 294 lignes, 1 127 821 octets, mtime `2026-10-28T00:12:35`, SHA-256 `5133f56e280823bacaa24bd6adf0a4bb03a719637d551b03677544eb60fb96e9`.

La session amont lue par ce tour est `de5bacf6-50d0-42ce-b890-f3149acbbd91`, titre « Équations et résolution de l'ignorance ». Au moment de la lecture : `revision=167`, `runtimeState=running`, `hasMoreBefore=true`.

## Faits et corrections

| # | Fait observé | Preuve (lignes JSONL) | Correction appliquée |
| :--- | :--- | :--- | :--- |
| 1 | La lecture de la session amont a été tronquée | L25–L28 : `[OUTPUT TRUNCATED - MCP tool 'read_chat_session' ... produced ~94992 tokens (284 976 characters), exceeding the 25000 token limit]`, puis un fichier `tool-results/builtin_read_chat_session_0888c2d9aec8.txt` | Lire le fichier complet par tranches ou extraire le JSONL ; ne pas compléter le manque par déduction |
| 2 | Un filtre par `messageStream` a masqué des messages humains | L50–L52 : filtre `messageStream in (None,"final","response")` ; L60–L62 : `[0] role=user stream=thinking` et `[2] role=user stream=thinking` | Filtrer par `role`, inclure `thinking` ; un résultat vide n'est pas une absence de message |
| 3 | Les métadonnées d'outils ne contiennent pas les commandes | Le snapshot de `read_chat_session` ne rend que `name` et `status` ; le cas produit l'écrit aussi : `read_chat_session renvoie les sorties d'outils, pas les lignes de commande` | Citer les sorties et classer chaque commande « vérifiée » ou « recommandée » |
| 4 | Un Skill existant couvrait déjà l'essentiel | `livrer-contrat-solidity-et-portefeuille-non-custodial` couvrait `npx --yes solc@0.8.24`, le refus de `--overwrite`, le piège du pipe, `rm -rf build` et l'absence de `selfdestruct` ; manquaient le pragma exact face au solc global, la distinction retrait LP/retrait propriétaire et le nettoyage après audit | Produire la matrice de couverture, puis faire trancher le périmètre par l'utilisateur (fait 5) |
| 5 | Le périmètre et le paquet ont été choisis par l'utilisateur | L114–L116 : AskUserQuestion « Le contenu incrémental est faible face au Skill Solidity existant. Quel périmètre retenir ? » et « Quel paquet de fichiers pour ce Skill ? ». Réponses : « Créer le Skill étroit (Recommandé) » et « SKILL.md + script + référence (Recommandé) » | Ne pas décider seul quand la couverture est proche ; enregistrer les deux réponses |
| 6 | Le compteur de candidats revus était faux | L153–L155 : 13 fichiers, `CANDIDATS_RETRAIT=8`, `CANDIDATS_REVUS=6` alors qu'un seul `--revu` était fourni ; L169–L171 : sans `--revu`, `CANDIDATS_REVUS=1` et `CANDIDAT_NON_REVU=...retirerLiquidite` avec `EXIT=3` | L161–L167 et L176–L182 : compter `CANDIDATS_RETRAIT` depuis `candidates_total`, `CANDIDATS_REVUS` depuis `reviewed_total`, ajouter `CANDIDATS_A_RELIRE` ; rejouer le cas sans `--revu` |
| 7 | Le nombre de fichiers hors périmètre était faux | L275–L277 : ancien texte « 6 autres sont hors périmètre » ; nouveau texte « 13 .sol au total : 7 exacts et 6 en plage. Sur les 8 fichiers hors périmètre, 2 sont exacts ... et 6 sont en plage » | Recompter sur disque : total moins périmètre, puis séparer exacts et plages |
| 8 | La QA de livraison a passé | L280–L282 : `PASS skill references: 1 checked`, `Fingerprint (final): 7555 bytes`, `PASS fingerprint: unchanged during validation`, `Summary: 9 pass, 0 fail, 0 warn`, `RESULT PASS` | Relever `Files (N)`, les empreintes et les hashes ; ne pas extrapoler au-delà de la structure |

## Tests du script dans la session source

- Fixtures hors installation, L200–L202 : cas PASS, pragma différent + `onlyOwner` + `selfdestruct`, pragma en plage, `--revu` inconnu, fichier absent, arguments manquants.
- Codes attendus et obtenus : `0` PASS, `1` FAIL, `2` USAGE, `3` REVIEW.
- Le cas sans `--revu` est le contrôle qui a révélé le faux compteur ; il doit rester dans toute régression.

## Empreintes du paquet produit par la session source

| Fichier | Octets | SHA-256 |
| :--- | ---: | :--- |
| `SKILL.md` | 7555 | `4a8f9e63a60ca4cb1a0a544551046761797ecdf7fb3ceed2a4dbbae8905de2f4` |
| `scripts/auditer_contrats.py` | 7149 | `6cc3130f43a0f13398366f0ce9e47260aa4a0f56dd7b746479517c4b5adc0855` |
| `references/cas-verifie-mizan-2026-10-27.md` | — | `31f0b12e4387a6a441fc0df82353285de9b46355dad6b72f3230067cadd77b30` |

## Limites

- Les numéros de ligne ne sont valides que pour le SHA-256 du JSONL enregistré ci-dessus. Toute réécriture du fichier impose une nouvelle extraction.
- La session source est une session de création de Skill, pas un déploiement ni un audit de sécurité.
- Les tests du script prouvent son comportement, pas la sécurité des contrats audités.
- Le `RESULT PASS` de `skill-file-qa` couvre la structure et les références, pas la sémantique des phrases.
- Ce paquet ne contient aucun script : les scripts restent dans les Skills spécialisés cités par la chaîne.
