---
name: verifier-abi-locale-contrat-deploye
description: "Vérifier en lecture seule qu'un artefact ABI local correspond au contrat déployé : sélecteur keccak4 de la fonction cible, présence dans eth_getCode, chaîne et bloc consignés. Utiliser après toute réparation ou déplacement d'un chemin d'ABI, avant d'envoyer une transaction mainnet, quand le dry-run d'un script sceller_* passe mais que l'ABI pourrait venir d'un autre build, ou pour contrôler la complétude d'un artefact par son nombre d'entrées ABI. Si plusieurs scripts doivent être rebranchés sur une résolution partagée, utiliser `centraliser-resolution-artefact-python`."
---

# Vérifier une ABI locale contre le contrat déployé

## Quand l'utiliser

- Un script Python charge une ABI depuis un fichier local et s'apprête à appeler un contrat déployé.
- Le dry-run passe (lecture `nextActeId`, simulation) et il faut prouver que l'ABI lue est celle du contrat ciblé, pas d'un autre build.
- Après réparation ou déplacement d'un chemin d'artefact, ou avant tout envoi de transaction.
- Un doute sur la complétude du fichier : le nombre d'entrées ABI est consigné et comparable à une valeur attendue.

## Quand ne pas l'utiliser

- **Réparer un chemin absolu mort** : c'est le flux de `reparer-chemin-artefact-absolu-script-python`. Ce Skill intervient après, pour la preuve.
- **Audit de sécurité formel** : hors périmètre. Un sélecteur présent ne dit rien de la logique, des droits ou des invariants.
- **Prouver l'identité de la source compilée** : `eth_getCode` ne recompile rien. Pour cela, vérifier la source sur l'explorateur ou comparer le bytecode de build au bytecode déployé.
- **Contrat derrière un proxy** : `eth_getCode` renvoie le proxy, dont le bytecode ne contient pas les sélecteurs de l'implémentation. Vérifier l'adresse d'implémentation.
- **Fonction à tuple ou tableau** : le script refuse la signature (`rc=2`) ; comparer manuellement, en hashant le type canonique (`(address,bytes)[]`) puis en cherchant les 4 octets dans `eth_getCode`.

## Procédure

Depuis le dossier du Skill. Remplacer `<artefact.json>` par le chemin absolu de l'artefact lu et `<0x + 40 hex>` par l'adresse du contrat ; `--signature` reprend la signature exacte de l'appel du script :

```bash
py -3 -B scripts/verifier_abi_deploye.py \
  --artifact <artefact.json> \
  --address <0x + 40 hex> \
  --signature "scellerActe(address,string,bytes32,string)" \
  --rpc https://mainnet.base.org \
  --expect-chain 8453 \
  --expect-entries 70
```

La commande est en lecture seule : `eth_getCode`, `eth_chainId`, `eth_blockNumber`. Aucune clé, aucune transaction. Autre réseau : changer `--rpc` et `--expect-chain` ensemble.

Lire `RESULT PASS` et le code 0 **avant** le mode réel. `RESULT FAIL` n'est pas un avertissement : ne pas envoyer de transaction.

## Lecture de la sortie

| Clé | Sens |
| :--- | :--- |
| `ABI` | chemin absolu de l'artefact réellement lu |
| `ABI_ENTRIES` / `ABI_VALID` | nombre d'entrées, validité du tableau `abi` |
| `FUNCTION` | signature canonique (espaces retirés) |
| `IN_ABI` | signature présente avec les types d'entrée exacts |
| `SELECTOR` | 4 premiers octets du keccak-256 de la signature canonique |
| `CODE_BYTES` | taille du bytecode d'exécution ; `0` = compte sans code |
| `SELECTOR_IN_BYTECODE` | `PRESENT` / `ABSENT` |
| `CHAIN` / `BLOCK` | chaîne et bloc de la lecture, à consigner |
| `RESULT` | `PASS` ou `FAIL (n)` |

Codes de sortie : `0` PASS, `1` contrôle échoué, `2` usage, lecture ou RPC impossible. Un RPC injoignable sort en `2` : ce n'est pas un verdict sur l'ABI.

Consigner dans la preuve : sélecteur, verdict, `CHAIN`, `BLOCK`, nombre d'entrées. Le bloc **au moment de la requête** ; ne jamais recopier un bloc d'une session antérieure.

## Limites de la preuve

- Présence du sélecteur ≠ identité de source : collision possible sur 4 octets, et le sélecteur peut apparaître dans une constante `PUSH4`.
- La preuve ne couvre que la fonction demandée, pas les 70 entrées de l'ABI.
- Un proxy, un contrat auto-détruit ou une mise à jour d'implémentation invalident la preuve après coup : d'où le bloc consigné.
- Sur une adresse de proxy, le verdict est `RESULT FAIL (1)` même avec une ABI correcte : ce n'est pas un défaut de l'artefact mais un mauvais point d'interrogation. Le slot d'implémentation dépend du proxy (EIP-1967 `0x3608…`, ou slot spécifique : Circle FiatTokenProxy).
- Les types tuple et tableau ne sont pas pris en charge : refus `rc=2` avant tout appel RPC, à traiter manuellement.
- `IN_ABI=NO` avec des surcharges présentes est un vrai échec : la signature demandée n'existe pas avec ces types.

## Pièges vérifiés (28/10/2026)

| Piège | Conséquence constatée |
|---|---|
| Hasher la signature brute avec des espaces | sélecteur faux ; le script canonise `f( address, uint256 )` en `f(address,uint256)` |
| Conclure sur un dry-run vert | le dry-run lit un champ, il ne prouve pas que l'ABI est celle du build déployé |
| Recopier le bloc d'une session | `53199416` cité en session, `53199730` puis `53199778` au rejeu : le bloc avance |
| Confondre longueur hex et octets | `len(code)=18690` caractères ⇒ `9344` octets (`CODE_BYTES`) |
| Interroger une EOA | `eth_getCode` renvoie `0x`, `CODE_BYTES=0`, verdict FAIL |
| Chaîne non vérifiée | même adresse possible sur un testnet ; `--expect-chain` est la garde |
| Sortie non ASCII | console Windows cp1252 : le script n'émet que de l'ASCII |
| Interroger l'adresse du proxy | USDC Base : proxy 1 852 octets, `balanceOf(address)` ABSENT → `RESULT FAIL (1)` ; implémentation 23 464 octets → PRESENT, PASS |
| Signer une fonction à tuple | refus `rc=2` ; `aggregate((address,bytes)[])` doit être hashé à la main (`0x252dba42`) puis recherché dans le code |

## Checklist

- [ ] Artefact lu par chemin absolu affiché, `ABI_VALID=YES`
- [ ] `FUNCTION` correspond à l'appel réel du script (nom et types)
- [ ] `IN_ABI=YES`
- [ ] `CHAIN` égale la chaîne attendue, `BLOCK` consigné avec la date
- [ ] `CODE_BYTES > 0`
- [ ] `SELECTOR_IN_BYTECODE=PRESENT`
- [ ] `RESULT PASS`, code 0
- [ ] Aucune transaction, aucune clé manipulée
- [ ] Limites reportées (proxy, une seule fonction, bloc daté)

## Resources

- `scripts/verifier_abi_deploye.py` : contrôle lecture seule, code 0/1/2, sortie ASCII `KEY=VALUE`.
- `references/cas-almizan-a089-2026-10-28.md` : erreur verbatim, sortie de session, rejeu, empreintes, matrice de tests.
