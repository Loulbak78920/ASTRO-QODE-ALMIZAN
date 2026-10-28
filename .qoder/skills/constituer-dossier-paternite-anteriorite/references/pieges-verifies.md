# Pieges verifies et regles defensives

Chaque entree distingue ce qui a ete **observe** dans un run reel de ce qui est une
**regle defensive** pour les runs futurs.

## 1. Windows : `python` peut etre le stub Microsoft Store

Observe sur cette machine :

```text
C:\Users\Administrateur\AppData\Local\Microsoft\WindowsApps\python
Python est introuvable ...
```

`py -3 -V` repond `Python 3.14.7`. Les scripts du dossier s'appellent donc avec
`py -3`, jamais avec `python` nu. Verifier avant de lancer une chaine :

```bat
py -3 -V
```

Si `py` est absent, chercher l'executable reel et l'utiliser explicitement.

## 2. Console cp1252 et accents

Observe sur cette machine : un script qui imprime un caractere non representable
dans la page de code console echoue avec

```text
UnicodeEncodeError: 'charmap' codec can't encode character ...
```

Regle : dans le lanceur, poser

```bat
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
```

et, dans chaque script, reconfigurer `sys.stdout` et `sys.stderr` en UTF-8 avec
`errors="replace"`. Garder les statuts machine (`VERDICT`, `RESULTAT`, codes) en
ASCII pour qu'ils restent lisibles meme si la console les mangent.

## 3. `solcjs` n'accepte pas `--bin-runtime`

Observe dans le run source, code de retour 1 :

```text
error: unknown option '--bin-runtime'
```

La sortie d'aide confirme que `solcjs` n'expose pas cette option. Regle : compiler
en **standard-json**, demander explicitement `evm.bytecode.object` et
`evm.deployedBytecode.object`, puis parser la reponse a partir du premier `{` :

```text
npx --yes solc@<x.y.z> --standard-json
```

Ne pas se fier a un `solc` global : epingler la version et refuser un format de
version non conforme (`solc@x.y.z`).

## 4. Le recu de transaction ne garantit pas `blockTimestamp`

Regle defensive : ne jamais supposer que `eth_getTransactionReceipt` fournit
`blockTimestamp` au niveau superieur. Lire le champ s'il existe, sinon appeler
`eth_getBlockByNumber(receipt.blockNumber)` et prendre `timestamp`.

Preuve dans le cas de reference : le resultat de verification contient un
`bloc_hash`, champ renseigne uniquement dans la branche de repli. Le repli a donc
effectivement servi.

Ne pas confondre l'horodatage du bloc avec un `blockTimestamp` present dans les
journaux d'evenements : un journal peut porter ce nom sans que le recu le porte.

## 5. La comparaison brute du bytecode est trompeuse

Observe sur le contrat de reference :

| Comparaison | Prefixe commun | Difference |
|---|---|---|
| runtime recompile / code on-chain, brut | 1 840 octets (19,69 %) | 330 caracteres |
| apres masquage des adresses immuables | 9 301 octets (99,54 %) | 61 caracteres |

Les valeurs immuables (adresses de tresorerie, cle doree) sont injectees dans le
runtime au deploiement : elles n'existent pas dans le modele compile avant
construction. Une comparaison brute conclut a tort a une divergence.

Regle : masquer chaque adresse immuable connue sous ses deux formes
(`0x` + 40 hex, ou 24 zeros + 40 hex), puis comparer. Documenter la liste des
adresses masquees dans le rapport.

## 6. Les differences restantes sont souvent l'auxdata

Apres masquage, les 61 caracteres restants se situent dans l'auxdata CBOR
(empreinte IPFS et version du compilateur). Ce sont des metadonnees, pas du code
executable. Une correspondance forte n'est pas une identite de texte : commentaires,
espaces et reglages de compilation changent l'auxdata sans changer la logique.

Regle : extraire l'auxdata des deux cotes, comparer le digest IPFS, et nommer le
verdict `CORRESPONDANCE_FORTE` plutot que `IDENTIQUE` quand seul l'auxdata differe.

## 7. Sceller apres avoir tout ecrit, et exclure le sceau

Regle : le repertoire du manifeste (`SCEAU/`) et les caches (`__pycache__/`,
`.git/`) sont exclus du scellement. Sinon le manifeste se contient lui-meme et la
racine change a chaque generation.

Le verificateur doit controler quatre choses, pas une :

1. chaque empreinte declaree correspond au fichier ;
2. chaque taille declaree correspond ;
3. aucun fichier scelle ne manque ;
4. aucun fichier present n'a ete ajoute apres le scellement.

Une racine recalculee a partir du manifeste prouve seulement la coherence interne du
manifeste. Sans ancrage externe, elle ne date rien.

## 8. GitHub sans authentification : 404 n'est pas une preuve d'absence

Sans jeton, `GET /repos/{owner}/{repo}` renvoie 404 aussi bien pour un depot prive
que pour un depot inexistant. Le statut correct est
`PRIVE_OU_INEXISTANT_SANS_AUTHENTIFICATION`, jamais `DEPOT ABSENT`.

Deux horloges different :

- `created_at`, `pushed_at` : dates serveur, etablies par GitHub ;
- `commit.committer.date` : date declaree par le client Git.

Une date de commit ne prouve pas a elle seule l'heure de publication. Elle s'appuie
sur la date serveur de creation du depot et sur l'historique des push.

## 9. DOI : 200, 410 et 404 ne veulent pas dire la meme chose

| Code API Zenodo | Statut | Lecture |
|---|---|---|
| 200 | `ENREGISTRE` | le DOI resout et le record existe |
| 410 | `SUPPRIME` | record supprime ; la pierre tombale peut conserver une date de citation |
| 404 | `NON_ENREGISTRE` | aucun record a cet identifiant |

Une erreur reseau ou un 5xx donne `INDETERMINE`, jamais `NON_ENREGISTRE`. Une
suppression de DOI n'efface pas l'anteriorite factuelle : elle prive seulement d'un
ancrage registrar.

## 10. IPFS : disponibilite partielle

Interroger plusieurs portails (`ipfs.io`, `dweb.link`, `w3s.link`,
`gateway.pinata.cloud`). Un portail qui ne repond pas ne prouve pas que le contenu
n'existe pas. Le statut est `DISPONIBLE_PARTIELLEMENT` ou
`INDISPONIBLE_AU_MOMENT_DU_CONTROLE`, avec l'heure et l'URL finale de chaque essai.

## 11. Ne jamais ecrire dans la source

L'inventaire, la compilation et les ancrages sont en lecture seule. Les sorties vont
dans `PREUVES/`, `DONNEES/`, `DOSSIER/` et `SCEAU/`. `npx` cree son cache ailleurs :
ne pas le rediriger dans le corpus.

## 12. Regenerer puis resceller, jamais l'inverse

Toute regeneration de document change les empreintes. L'ordre est : generer, puis
sceller, puis verifier. Si un fichier est ajoute apres le scellement, le
verificateur doit le signaler comme `AJOUTE` et retourner 1, meme si tous les
fichiers scelles sont intacts.

## 13. Ce qui reste non prouve

Un hash local, un sceau Merkle et une recompilation prouvent la coherence technique.
Ils ne prouvent ni l'originalite, ni la copie par un tiers, ni l'intention dolosive.
Ces trois elements exigent des pieces externes : expertise, constat, reproduction
identifiee, manoeuvre datee.
