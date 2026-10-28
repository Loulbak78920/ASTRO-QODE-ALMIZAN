# Cas vérifié : vérifier un script réseau avec 9 requêtes de quota restantes

## Source de l'observation

- Session Qoder `e1486500-02a6-4784-a12a-4d30a46215bf` (2026-10-28), qui audite le Skill `ancrer-anteriorite-depot-github-public`.
- Journal : `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\e1486500-02a6-4784-a12a-4d30a46215bf.jsonl`.
- Relevé : 321 lignes, 793 652 octets, SHA-256 `4645fede6c00107603c2263adb4ea4e48b17ff6af3c807cfb429705b0ea33e2e`, mtime `2026-10-28T12:07:19Z` (UTC). Lignes citées valables pour ce relevé seulement.
- `read_chat_session` a renvoyé une synthèse assistant tronquée, non les sorties brutes. Toutes les preuves ci-dessous viennent des couples `tool_use` / `tool_result` du journal.
- Environnement : Windows, `py -3` (3.14, d'où `cpython-314`), `GITHUB_TOKEN` absent (`token_env_present=no`) → limite non authentifiée de 60 req/h.

## Quota relevé

| Instant | Commande | Résultat | Ligne |
|---|---|---|---|
| `12:03:43Z` | `curl -D - https://api.github.com/repos/...` | `HTTP/1.1 200`, `Limit: 60`, `Remaining: 9` | L181 |
| `12:03:51Z` | `curl -D - https://api.github.com/rate_limit` | `Remaining: 9`, `Reset: 1793190665` | L188 |
| `12:03:59Z` | conversion epoch | `reset_in_seconds 1626`, `reset_utc 2026-10-28T12:31:05Z` | L193 |

Le premier relevé provient d'une sonde `/repos/...`, qui consomme une requête ; `/rate_limit` est l'endpoint dédié, non décompté par l'API. Le jeton GCM n'a pas été extrait malgré l'option envisagée : sans accord explicite, la limite de 60 req/h est restée la contrainte.

## Coût chiffré avant exécution

Modèle déduit des points d'appel du script : 1 métadonnées de dépôt + pages de commits + 1 par chemin.

| Scénario | Calcul | Requêtes |
|---|---|---|
| Run 1 fichier (`CITATION.cff`) | 1 + ceil(213/100) + 1 | 5 |
| Run 2 fichiers | 1 + ceil(213/100) + 2 | 6 |
| Test négatif 404 | échec au premier appel | 1 |

Budget : `9 − 5 − 1 = 3` requêtes après un run et un test négatif — d'où le renoncement à un second run CLI (6 requêtes).

## Parcours exécuté de bout en bout (rc=0)

Commande : script installé, un seul `--fichier`, sortie sous `~/.qoder/tmp/anteriorite-check/run1`. Sortie verbatim (L205) :

```
DEPOT=Loulbak78920/ASTRO-QODE-ALMIZAN
VISIBILITE=public
COMMITS_TOTAL=213
COMMIT_PLUS_ANCIEN=e6bc5fd0cbf8290b4eb2481c9f388096d97b528d
FICHIER=CITATION.cff
PUBLIE=True
IDENTIQUE_OCTETS=True
IDENTIQUE_HORS_CRLF=True
SHA256_PUBLIE=73e6e3353e2dc8fac423b18f2c20022c17cf3eae8e15632ce4e748da31122689
SHA256_LOCAL=73e6e3353e2dc8fac423b18f2c20022c17cf3eae8e15632ce4e748da31122689
VERDICT=ANCRAGE_PUBLIE_ETABLI
RC=0
```

## Test négatif (rc=2, 1 requête)

Dépôt `Loulbak78920/definitely-not-a-repo-xyz` (L212) :

```
ERREUR=HTTP_404_SUR_https://api.github.com/repos/Loulbak78920/definitely-not-a-repo-xyz
RC=2
```

L'échec survient sur l'appel de métadonnées : aucun coût de pagination.

## Branches couvertes hors quota

Téléchargement brut à SHA épinglé via `raw.githubusercontent.com` (L214) : `CITATION_public.cff` → `73e6e335…` (identique au local), `contrat_public.sol` → `3f8864a9c8733b4b593cb07da71b181859eaf0abf8224b05c83cee773fc4ff67`.

Import par chemin puis appel des fonctions pures (L219) :

```
CRLF_COPY_SIZE 3217 SHA a85f1f58
CRLF_IDENTIQUE_OCTETS False
CRLF_IDENTIQUE_HORS_CRLF True
SOL_IDENTIQUE_OCTETS False SOL_IDENTIQUE_HORS_CRLF False
SOL_SHA_LOCAL 23a5fa76d611 SOL_SHA_PUBLIE 3f8864a9c873
VERDICT_PARTIEL ('ANCRAGE_PUBLIE_PARTIEL', 'DIVERGENCE_OU_FICHIER_MANQUANT')
VERDICT_NON_PUBLIE ('NON_ETABLI', 'AUCUN_FICHIER_PUBLIE')
VERDICT_NON_PUBLIC ('NON_ETABLI', 'DEPOT_NON_PUBLIC')
```

Les SHA de cette sortie sont des préfixes (8 et 12 caractères), non les empreintes complètes.

## Résidu d'import à retirer

`importlib.util.spec_from_file_location` puis `exec_module` a créé, à l'intérieur du Skill installé :

```
18808 1793189075.8484794000 .../scripts/__pycache__/verifier_anteriorite_depot.cpython-314.pyc
```

(L251 ; mtime epoch `1793189075` = `12:04:35Z`, pendant l'import.) Un résidu plus ancien, 18 569 o à `12:58:55Z`, était déjà présent avant le contrôle de syntaxe (`compile()` + `--help`, L107 → L109 : `SYNTAX_OK 278 lines`). Supprimé par `rm -rf` (L276) ; la sortie du même appel (L284) ne liste plus que `SKILL.md`, `references/cas-…md` et `scripts/…py`, et l'inventaire final (L312) que `SKILL.md`, `references`, `scripts`.

## Ce qui n'a pas été exécuté de bout en bout

| Parcours | Statut | Raison |
|---|---|---|
| Verdict partiel (rc=1) via CLI | prouvé par fonction seulement | second run = 6 requêtes > 3 restantes |
| Fichier absent du dépôt (`PUBLIE=False`) | non exécuté | même coût, aucune requête disponible |
| Dépôt non public via CLI | prouvé par `verdict()` seulement | nécessiterait un dépôt privé |

Ces limitations ont été déclarées ; elles ne doivent jamais être présentées comme des passages d'acceptation.

## Enseignements réutilisables

1. Chiffrer le coût **avant** le premier appel : 213 commits imposent 3 pages, ce qui fait passer un run de 3 à 5 requêtes.
2. Le test négatif 404 est le meilleur rapport preuve/coût (1 requête).
3. Le contenu brut et l'import de module couvrent les branches CRLF et divergence à coût nul, à condition de supprimer le `__pycache__` produit par l'import.
4. Le reset était à 27 minutes : fractionner et déclarer a été préféré à l'attente et au silence.
