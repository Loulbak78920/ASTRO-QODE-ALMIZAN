# Cas de référence — audit d'un paquet Skill concurrent (2026-10-28)

Cas reconstruit depuis la session source `12be287c-b14d-4363-bb1a-2d26a6ceabba` (JSONL de 1 845 985 octets, 470 lignes, titre « 创建 Sudo VPS 密码轮换 Skill »). Ce paquet n'a pas servi à produire le cas : les commandes citées sont celles observées dans la session, revérifiées localement quand c'était possible.

Statut des éléments : **VERIFIE** = relu dans le JSONL source ou remesuré sur disque ; **INFERE** = déduit de l'ordre des messages, sans observation directe ; **NON VERIFIE** = non rejoué.

## Contexte et décision

| Élément | Valeur | Statut |
| --- | --- | --- |
| Session source | `12be287c-b14d-4363-bb1a-2d26a6ceabba` | VERIFIE |
| Paquet concurrent apparu | `rotation-mot-de-passe-vps-sans-fuite` (messages 164, 175, 184) | VERIFIE |
| Rapport de doublon | messages 197–200 | VERIFIE |
| Choix utilisateur | garder le concurrent (« Garder le concurrent (recommandé) ») | VERIFIE |
| Décision (message 203) | ne pas créer la cible ; audit en lecture seule + rapport couverture/limites | VERIFIE |
| Cible finalement créée | aucune (`rotation-mot-de-passe-sudo-vps` : `CIBLE ABSENTE`, message 300) | VERIFIE |

Conclusion : la session de création s'est transformée en audit d'un paquet écrit par elle-même, sans modification du paquet concurrent après la décision.

## QA statique

| Mesure | Valeur | Statut |
| --- | --- | --- |
| Résultat | `PASS`, 10 pass / 0 fail / 0 warn (messages 181, 294) | VERIFIE |
| Fichiers | `Files (3)` | VERIFIE |
| Description | 830 caractères | VERIFIE |
| Corps | 132 lignes | VERIFIE |

Le PASS ne couvrait que `SKILL.md` ; référence et script ont donc été mesurés séparément (voir ci-dessous).

## Dérive détectée pendant l'audit

Script de production du paquet concurrent, deux mesures successives :

| Heure locale (+0100) | Taille | SHA-256 |
| --- | --- | --- |
| 01:34:11.974 | 6 386 | `d81e7918e166c23c933f2f7bcd831838885428317e05cf11d4cee086c7d0541f` |
| 01:36:28.974 | 6 555 | `128f1695961670110dc98d016ecc35bf311b2c884ebfe1eb0aa652caff1584a9` |

Statut VERIFIE (messages 187, 241, 250). Le changement a été attribué à l'écrivain du paquet ; les constats antérieurs sont devenus `HISTORIQUE` et l'audit a été poursuivi sur la version 6 555 octets.

## Provenance des affirmations

| Affirmation auditée | Preuve brute | Classement | Statut |
| --- | --- | --- | --- |
| Contenu de la ligne 68 de la documentation | `sed -n '66,70p'` | SUPPORTED | VERIFIE |
| Script de production = 8 908 octets, SHA-256 `0aa8b05a25d79878fac7b28487c00e25ee3a50841c93c5046bf777d34863c4be`, mtime 01:23:07.453 +0100 | `sha256sum`, `stat` | SUPPORTED | VERIFIE |
| Incident `bash: line 1: <secret>: command not found` | 4 occurrences dans le JSONL source : ligne 1165 (×2), 1167, 1329 | SUPPORTED | VERIFIE |
| Jetons des lignes d'incident | longueurs 20 et 10, valeurs jamais affichées | SUPPORTED | VERIFIE |

Le SHA-256 complet a été recalculé et comparé aux valeurs citées ; la recherche JSONL a été faite avec un motif construit en mémoire, chaque ligne étant imprimée avec `<secret>` à la place de la valeur.

## Fixture du contrat fonctionnel

| Élément | Valeur | Statut |
| --- | --- | --- |
| Emplacement | `%TEMP%\audit_secrets_fixture_12be287c.py` (hors racines de Skills) | VERIFIE |
| Faux secret | `FAKE_SECRET_ABC123XYZ` | VERIFIE |
| Cas | 15 | VERIFIE |
| Premier échec | attendu `FUITE projet\app.py:2`, obtenu `FUITE app.py:2` | VERIFIE |
| Diagnostic | `repr(stdout)` a montré que la racine par défaut est `secrets.parent.parent` (répertoire projet) | VERIFIE |
| Correctif | attente du harnais corrigée (message 273), script audité inchangé | VERIFIE |
| Résultat final | 15/15 PASS | VERIFIE |
| Écritures / caches / fuite | aucune écriture, aucun `__pycache__`/`.pyc`/`.tmp`, secret absent des sorties | VERIFIE |

Ce point est la raison d'être de la règle « corriger le harnais, pas le script » : l'échec venait d'une attente fausse, pas du comportement observé.

## Expiration après écritures légitimes

Après la conclusion de l'audit, le paquet a été modifié légitimement (messages 415, 419, 447) :

| Fichier | Taille | mtime local | SHA-256 | Statut |
| --- | --- | --- | --- | --- |
| Référence | 8 916 | 01:47:24.717 | `6829468f1a48cd468d0092b0f0635910d97c8a6b37605a8e44cfedb286cb338b` | VERIFIE |
| Script de production | 10 463 | non relevé | `a9d133d7db58b07afbafd4e17c7c4fbb156ce9628436c2b8eb829c052b4b8d37` | VERIFIE |
| `SKILL.md` | 11 545 | inchangé | `3785da9bed72d1ed9dc58ca40dc315a56440f57764577ea4376197af307e4174` | VERIFIE |

L'audit porte donc la mention `EXPIRÉ` : les constats sur la référence et le script ne valent que pour les empreintes ci-dessus, avant ces écritures. Aucun rejeu de l'audit sur la version 10 463 octets n'a été effectué (NON VERIFIE).

## Couverture et limites

Couvert :

- vérification d'absence de la cible aux deux racines ;
- deux scans d'empreintes et rattachement des constats à la version courante ;
- QA statique et mesure séparée de chaque fichier ;
- provenance des affirmations (hash complet, ligne de documentation, lignes d'incident caviardées) ;
- fixture jetable hors racines, faux secret, 15 cas, preuve d'absence d'écriture et de cache ;
- triage harnais/script et expiration après écritures postérieures.

Non couvert :

- l'audit n'a pas été rejoué sur la dernière version (script 10 463 octets) ;
- la fixture exerce le comportement observable du script, pas une garantie de sécurité absolue ;
- les horodatages proviennent du JSONL et de `stat` local ; l'ordre des messages est la seule preuve d'antériorité ;
- le JSONL source a été lu via une extraction directe après troncature de `read_chat_session` ; les comptes ci-dessus viennent du fichier brut, pas du résumé de l'outil.
