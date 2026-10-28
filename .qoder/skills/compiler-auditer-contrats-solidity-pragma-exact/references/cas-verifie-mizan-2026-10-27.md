# Cas vérifié — compiler et auditer 5 contrats Al-Mizan (2026-10-27)

## Source

- Session : `de5bacf6-50d0-42ce-b890-f3149acbbd91`, titre « Équations et résolution de l'ignorance ».
- Tour utile : `1cc9a23c-2a83-48b0-8f45-7c0d06c96849`, message utilisateur du `2026-10-27T22:23:39.185Z`.
- Lecture le 2026-10-28 : `revision=167`, `runtimeState=running`, `activeTurnId=74e0c611-c04e-4fe4-b3db-f5636d7e7626`, `hasMoreBefore=true`.
- `read_chat_session` renvoie les sorties d'outils, pas les lignes de commande. Les faits ci-dessous sont donc des sorties citées, et les commandes sont classées « vérifiée » ou « recommandée ».

## Faits vérifiés

| Fait | Preuve citée | Statut |
| :--- | :--- | :--- |
| Le solc global répond 0.8.38 | `0.8.38+commit.1835d247.Emscripten.clang` | REPRODUIT |
| La version épinglée répond 0.8.24 | `0.8.24+commit.e11b9ed9.Emscripten.clang` | REPRODUIT |
| `--overwrite` est refusé | `error: unknown option '--overwrite'` | REPRODUIT |
| Le code retour affiché est trompeur | la même sortie contient `RC=0` | REPRODUIT |
| Compilation des 5 contrats | `RC=0` puis 16 fichiers `.abi`/`.bin` | REPRODUIT |
| Un seul nom de retrait | `AlMizanPoolsMultiactifs.sol:134: function retirerLiquidite(uint256 parts)` | REPRODUIT |
| Aucune destruction | `== selfdestruct ==` puis `AUCUNE` | REPRODUIT |
| Aucune clé privée | `== adresses privées / clés ==` puis `AUCUNE` | REPRODUIT |
| Artefacts supprimés | `== artefacts de build supprimés ==` | REPRODUIT |

Les cinq sources portaient `pragma solidity 0.8.24;` en ligne 2. Le comptage `payable` de la session est un comptage d'**occurrences** par fichier (3, 2, 7, 1, 0 ; total 13), pas un comptage de fonctions : le script compte 3 fonctions `payable`. Les deux mesures ne sont pas interchangeables.

## Commandes

### Vérifiée : résolution des versions

```bash
npx --yes solc@0.8.24 --version
# attendu : 0.8.24+commit.<hash>...
```

La session a observé successivement `0.8.38+...` puis `0.8.24+...` : le premier résultat venait d'un binaire global, le second du binaire épinglé.

### Recommandée : compilation

```bash
rm -rf build
mkdir -p build
npx --yes solc@0.8.24 --bin --abi --optimize --optimize-runs 200 -o build contrats/*.sol > build.log 2>&1
rc=$?
echo "RC=$rc"
```

Cette forme complète n'a pas été observée caractère par caractère ; seuls la version résolue, le refus de `--overwrite`, le `RC=0` et les noms d'artefacts sont prouvés.

### Vérifiée : audit des 5 contrats (2026-10-28)

```bash
py -3 -B scripts/auditer_contrats.py --pragma 0.8.24 \
  --fichiers contrats/AlMizanAccordLegal5050.sol contrats/AlMizanPoolsMultiactifs.sol \
             contrats/AlMizanZakatSadaqa.sol contrats/AlMizanRegistrePortefeuilles.sol \
             contrats/MizanMultimodalRegistry.sol \
  --revu retirerLiquidite
```

Sortie réelle, code 0 :

```text
RESULT PASS
FICHIERS=5
PRAGMA=0.8.24
PRAGMA_EXACT=5/5
RETRAIT_PROPRIETAIRE=0
CANDIDATS_RETRAIT=1
CANDIDATS_REVUS=1
CANDIDATS_A_RELIRE=0
PAYABLE=3
INTERDITS=0
- AlMizanAccordLegal5050.sol:95 deposerEtRepartir PAYABLE
- AlMizanAccordLegal5050.sol:139 deposerPourLitige PAYABLE
- AlMizanZakatSadaqa.sol:144 donner PAYABLE
- AlMizanPoolsMultiactifs.sol:134 retirerLiquidite CANDIDAT_REVU
```

Sans `--revu retirerLiquidite`, la même commande rend `RESULT REVIEW` et le code 3, avec `CANDIDAT_NON_REVU=AlMizanPoolsMultiactifs.sol:134:retirerLiquidite`.

### Vérifiée : cas négatifs en fixture jetable

| Fixture | Contenu | Attendu | Obtenu |
| :--- | :--- | :--- | :--- |
| `FixtureOk.sol` | pragma 0.8.24, retrait sur parts | `PASS`, code 0 | conforme |
| `FixtureFail.sol` | pragma 0.8.25, `onlyOwner` + `selfdestruct` | `FAIL`, code 1 | `PRAGMA_DIFFERENT`, `INTERDIT=SELFDESTRUCT`, `RETRAIT_PROPRIETAIRE` |
| `FixtureRange.sol` | `^0.8.24` | `FAIL`, code 1 | `PRAGMA_NON_EXACT` |
| argument `--revu inexistante` | nom absent | `USAGE`, code 2 | `ERREUR=revu_inconnu:inexistante` |
| fichier absent | lecture impossible | `USAGE`, code 2 | `ERREUR=fichier introuvable` |

Les fixtures ont été supprimées après relevé.

## Pourquoi `retirerLiquidite` n'est pas un retrait propriétaire

Corps réel du contrat livré :

```solidity
function retirerLiquidite(uint256 parts)
    external
    nonReentrant
    returns (uint256 montant0, uint256 montant1)
{
    require(parts > 0 && balanceOf[msg.sender] >= parts, "AL-MIZAN: parts insuffisantes");
```

La garde porte sur les parts détenues par l'appelant, et le montant est calculé au prorata des réserves. Un retrait propriétaire, à l'inverse, est réservé par `onlyOwner` ou `seulementProprietaire` et envoie vers un destinataire arbitraire. Le nom seul ne permet pas de trancher : la garde et le corps, oui.

Sur le même dossier, `AlMizanV2Souverain.sol` contient `recupererETH` et `recupererERC20` avec `seulementProprietaire` : le script les classe `RETRAIT_PROPRIETAIRE` et sort en code 1. C'est le comportement voulu.

## État disque au 2026-10-28

- Les 5 contrats sont dans `ASTRO-Q°ODE_SYSTEME/contracts/` avec `pragma solidity 0.8.24;` en ligne 2.
- Aucun `build/` ni `build_v2/` dans `ASTRO-Q°ODE_SYSTEME/`.
- Le dossier contient 13 `.sol` au total : 7 portent le pragma exact 0.8.24 et 6 une plage (`^0.8.20`, `^0.8.24`). Sur les 8 fichiers hors périmètre, 2 sont exacts (`AlMizanV2Souverain.sol`, `AlMizanEncherePersonnalisee.sol`) et 6 sont en plage. Un audit par `--dossier` signale ces 6 en `PRAGMA_NON_EXACT`, ce qui est correct mais ne doit pas être présenté comme un défaut des 5 contrats livrés.

## Limites

- Compilation et audit statique seulement : ni déploiement, ni audit de sécurité formel, ni vérification on-chain.
- La commande de compilation exacte n'est pas observable dans la session ; seule sa forme recommandée est reproduite ici.
- Le script reconnaît des **noms** de fonction ; un drain nommé autrement échappe à la détection automatique. La relecture des fonctions privilégiées reste obligatoire.
- Les fixtures négatives prouvent le comportement du script, pas la sécurité des contrats.

## Empreintes au 2026-10-28

| Fichier | Octets | SHA-256 |
| :--- | ---: | :--- |
| `SKILL.md` | 7555 | `4a8f9e63a60ca4cb1a0a544551046761797ecdf7fb3ceed2a4dbbae8905de2f4` |
| `scripts/auditer_contrats.py` | 7149 | `6cc3130f43a0f13398366f0ce9e47260aa4a0f56dd7b746479517c4b5adc0855` |

Cette référence n'est pas auto-référencée : son empreinte est relevée dans le rapport de session.

