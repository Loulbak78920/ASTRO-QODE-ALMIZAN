---
name: compiler-auditer-contrats-solidity-pragma-exact
description: "Compiler des contrats Solidity au pragma exact avec npx --yes solc@<version> plutôt que le solc global, sans --overwrite, contrôler le code retour hors pipe, puis auditer par script et lecture l'absence de retrait propriétaire, de selfdestruct et de delegatecall avant de supprimer les artefacts de build. Utiliser pour compiler un .sol à pragma figé, reproduire l'échec unknown option --overwrite, distinguer retirerLiquidite (fournisseur de liquidité) d'un retrait propriétaire, ou nettoyer build/ après audit."
---

# Compiler et auditer des contrats Solidity au pragma exact

## Quand l'utiliser

- Compiler un `.sol` dont le pragma est figé (`pragma solidity 0.8.24;`) et vérifier que le compilateur utilisé est bien celui-là.
- Un `solc` global répond avec une autre version que le pragma.
- Prouver avant livraison l'absence de retrait propriétaire, de `selfdestruct`, de `delegatecall` et de `tx.origin`.
- Distinguer un retrait de fournisseur de liquidité d'un retrait propriétaire.
- Supprimer les artefacts de compilation après relevé des preuves.

## Quand ne pas l'utiliser, et quoi répondre

- **Artefact JSON, page portefeuille, endpoint, publication** : utiliser `livrer-contrat-solidity-et-portefeuille-non-custodial`, qui couvre toute la chaîne de livraison.
- **Audit de sécurité formel** : hors périmètre. Une compilation réussie et des grep ne remplacent ni audit tiers ni bug bounty ; le dire explicitement.
- **Déploiement** : jamais sans confirmation explicite de l'utilisateur ; ce n'est pas une étape de compilation.

## Règles non négociables

1. **La version épinglée est celle du pragma.** Un `solc` global d'une autre version n'est pas une approximation acceptable.
2. **Jamais `--overwrite`.** Supprimer le dossier de sortie à la place.
3. **Le code retour se lit hors pipe.** Un pipe renvoie le statut du dernier maillon.
4. **Un candidat de retrait se lit, ne se devine pas.** Le nom de fonction ne prouve rien ; la garde et le corps décident.
5. **Compiler n'est pas auditer.** Ne jamais présenter un `RC=0` comme une garantie de sécurité.
6. **Aucun artefact laissé derrière.** Relever les preuves, puis supprimer `build/`.

## Étape 1 — Lire le pragma et fixer le périmètre

```bash
grep -n "^pragma solidity" contrats/*.sol
```

- `pragma solidity 0.8.24;` est **exact** : seul un compilateur 0.8.24 le satisfait.
- `pragma solidity ^0.8.24;` ou `>=0.8.20` est une **plage** : le script la refuse, car elle ne fige rien.
- Écrire la liste exacte des fichiers du périmètre. Un audit partiel ne vaut que pour les fichiers cités.

## Étape 2 — Épingler le compilateur et vérifier sa version

```bash
npx --yes solc@0.8.24 --version > solc-version.txt 2>&1
rc=$?
cat solc-version.txt
```

- Attendu : `0.8.24+commit.<hash>...`. Toute autre version impose l'arrêt.
- Un `solc --version` global a déjà répondu `0.8.38` face à des sources en `0.8.24` ; ne pas s'en servir.
- Conserver le fichier de version jusqu'au rapport : il prouve le binaire réellement exécuté.

## Étape 3 — Compiler sans `--overwrite`, hors pipe

```bash
rm -rf build
mkdir -p build
npx --yes solc@0.8.24 --bin --abi --optimize --optimize-runs 200 -o build contrats/*.sol > build.log 2>&1
rc=$?
echo "RC=$rc"
```

- `--overwrite` n'existe pas : `error: unknown option '--overwrite'`. Supprimer `build/` puis relancer.
- `commande | head; echo $?` renvoie le statut de `head` : une erreur peut afficher `RC=0`. Rediriger vers un fichier et lire `$?` juste après.
- Succès : `RC=0` et des paires `.abi`/`.bin` nommées `<dossier>_<fichier>_<contrat>.abi`.
- Échec : lire `build.log`, corriger, recompiler. Ne pas auditer un build incomplet.

## Étape 4 — Auditer, puis clore chaque candidat par lecture

```bash
py -3 -B scripts/auditer_contrats.py \
  --pragma 0.8.24 \
  --fichiers contrats/A.sol contrats/B.sol \
  --revu retirerLiquidite
```

`--dossier` remplace `--fichiers` pour prendre tous les `.sol` à la racine du dossier.

| Clé | Sens |
| :--- | :--- |
| `RESULT` | `PASS`, `REVIEW`, `FAIL` ou `USAGE` |
| `FICHIERS` | nombre de fichiers audités |
| `PRAGMA_EXACT` | fichiers conformes / total |
| `RETRAIT_PROPRIETAIRE` | fonctions de retrait avec garde propriétaire ou admin |
| `CANDIDATS_RETRAIT` | toutes les fonctions au nom évocateur |
| `CANDIDATS_REVUS` | candidats déclarés lus via `--revu` |
| `CANDIDATS_A_RELIRE` | candidats non lus, à trancher |
| `PAYABLE` | fonctions `payable` (informatif) |
| `INTERDITS` | `selfdestruct`, `suicide`, `delegatecall`, `tx.origin`, mots de secret |

Codes de sortie : `0` PASS, `1` FAIL, `2` usage ou lecture impossible, `3` REVIEW.

- `FAIL` : corriger la source ou arrêter la livraison. Un `PRAGMA_NON_EXACT` n'est pas un avertissement.
- `REVIEW` : ouvrir chaque `A_RELIRE`, lire la garde et le corps, puis relancer avec `--revu <nom>`.
- Ne jamais passer `--revu` avant d'avoir lu : cela transformerait l'audit en case à cocher.

### Trancher un candidat

| Indice dans le corps | Conclusion |
| :--- | :--- |
| Garde sur `balanceOf[msg.sender]`, parts ou réserves, montant proportionnel | retrait du fournisseur de liquidité, pas du propriétaire |
| `onlyOwner` / `seulementProprietaire` et destinataire arbitraire | retrait propriétaire : `FAIL` attendu |
| Aucune garde, appel à `payable(...)` avec `msg.sender` | retrait de l'appelant ; vérifier la comptabilité des parts |
| Garde `onlyPartie` ou rôle métier | candidat privilégié : le documenter, ne pas le qualifier de propriétaire |

`payable` n'est pas interdit : chaque fonction listée doit avoir une justification (don, dépôt, partage de recette).

## Étape 5 — Relever puis supprimer les artefacts

```bash
rm -rf build build.log
ls -d build 2>/dev/null || echo "NO_BUILD_DIR"
```

- Relever avant suppression : code retour, nombre de fichiers compilés, sortie d'audit.
- Ne jamais supprimer les sources ni un `build/` antérieur au périmètre sans le dire.
- Terminer par `NO_BUILD_DIR` pour prouver le nettoyage.

## Pièges vérifiés

| Piège | Conséquence | Correctif |
| :--- | :--- | :--- |
| solc global 0.8.38 face à `pragma solidity 0.8.24;` | binaire incompatible avec le pragma exact | `npx --yes solc@0.8.24` |
| `--overwrite` | `error: unknown option '--overwrite'` | supprimer `build/` |
| `commande \| head; echo $?` | `RC=0` malgré l'erreur | rediriger et lire `$?` |
| `retirer` dans un nom | faux positif de drain propriétaire | lire la garde et le corps |
| audit limité aux noms de retrait | rate un drain nommé autrement | relire aussi les fonctions privilégiées |
| `build/` conservé | bruit, artefacts non livrés | supprimer après relevé |

## Checklist de livraison

- [ ] Pragma lu, type exact ou plage identifié, périmètre listé.
- [ ] Version du compilateur vérifiée et égale au pragma.
- [ ] Compilation `RC=0` lue hors pipe, fichiers `.abi`/`.bin` produits.
- [ ] `RESULT PASS`, ou `REVIEW` clos par lecture réelle et `--revu`.
- [ ] Aucune fonction `payable` sans justification.
- [ ] `build/` supprimé, `NO_BUILD_DIR` affiché.
- [ ] Rapport honnête : compilé et audité statiquement, pas « sécurisé » ni « déployé ».

## Ressources

- `scripts/auditer_contrats.py` : pragma exact, candidats de retrait, motifs interdits, comptage `payable` ; codes 0/1/2/3, sortie ASCII.
- `references/cas-verifie-mizan-2026-10-27.md` : preuves de session, ce qui est vérifié et ce qui est recommandé.
