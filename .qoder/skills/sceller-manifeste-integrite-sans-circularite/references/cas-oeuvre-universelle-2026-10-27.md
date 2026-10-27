# Cas vérifié — manifeste d'intégrité de l'œuvre universelle, 2026-10-27/28

## Objet

Source : session Qoder `de5bacf6-50d0-42ce-b890-f3149acbbd91` (« Équations et résolution de l'ignorance »), lue le 2026-10-28. Au moment de la lecture : `runtimeState: running`, `activeTurnId: 74e0c611-c04e-4fe4-b3db-f5636d7e7626` (déploiement VPS en cours), `revision: 167`, `hasMoreBefore: true`. Les lignes JSONL citées sont un instantané ; le fichier peut être réécrit par compaction.

Projet : `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME`.

## Chronologie (UTC, 2026-10-27)

| Heure | Événement | Preuve |
|---|---|---|
| 22:30:59 | Écriture initiale du module de scellement ; globs incluent `web_cloud/oeuvre_universelle.html`, `_en`, `_ar` | Write, JSONL l. 1881 |
| 22:31:23 | Ces trois pages sont retirées des globs, 24 s après | Edit, JSONL l. 1886 |
| 22:32:46 | Première génération ; racine `18ef420af560f6aa04b6dc1c868aa91bca133cc68713f4c130174494cb84feb2` | Bash, JSONL l. 1905 |
| 22:39:15 | Écriture du fichier de test couvert | Write, JSONL l. 2177 |
| 22:40:16 | Génération avant correction des tests ; racine `5705ec3f46dc3baf2266f74a78d8186467b1d8733f58ec08b4947b8c1c32c091` | Bash, JSONL l. 2232 |
| 22:40:27 | Deux échecs sans rapport avec le manifeste : `variables.strip()` et guillemets `hreflang` | JSONL l. 2249 |
| 22:40:37 | Corrections du test | Edits, JSONL l. 2257–2258 |
| 22:41:07 | Génération + vérification : `ok: true`, 149 fichiers, racine `9e47b14b24ef39240fd00623ee1871e6c465e63ae3bd115322fd6fac598be86d` | Bash, JSONL l. 2277 |
| 22:42:27 | Contrôle final croisé : manifeste = résumé = même racine, 149 ; les trois pages contiennent les 16 premiers caractères de la racine (`True` trois fois) | Bash, JSONL l. 2366–2368 |

## Ce qui a réellement été corrigé

1. **Circularité évitée par conception.** Le premier glob incluait les trois pages générées qui affichent la racine. Si elles étaient restées scellées, chaque génération aurait modifié la racine en modifiant les pages. Le retrait a eu lieu avant la première génération de pages : aucun échec n'a été observé, la décision est anticipatoire.
2. **Rescellement après création du test.** Le module listait le test avant son existence ; un glob ne signale pas un fichier absent. Après écriture et correction du test, une régénération a produit 149 fichiers et la racine finale.
3. **Aucune correction utilisateur sur le manifeste.** Les messages utilisateur visibles portent sur l'œuvre puis sur le déploiement VPS ; le retrait des pages est une auto-correction de l'agent. Ne pas écrire « corrigé après retour utilisateur ».

Les deux échecs de tests du 22:40:27 concernent la structure du registre et les guillemets `hreflang`, pas le manifeste.

## Contrôles exécutés le 2026-10-28 (lecture seule)

```text
ok: true
nb_fichiers: 149
ecarts: []
racine_merkle_sha256: 9e47b14b24ef39240fd00623ee1871e6c465e63ae3bd115322fd6fac598be86d
```

- Racine recalculée sur les empreintes stockées : identique à la racine déclarée.
- Ensemble couvert recalculé : 149 listés, 149 observés, `EXTRA` vide, `MISSING` vide.
- `tests/test_oeuvre_universelle.py` figure dans la liste scellée.
- Les pages `oeuvre_universelle.html`, `_en`, `_ar` et le résumé contiennent la racine et ne sont pas scellés.

## Empreintes des artefacts au moment du relevé

| Fichier | SHA-256 | Octets |
|---|---|---|
| `resultats/oeuvre_universelle/manifeste_anteriorite.json` | `cf165d41b534cdaaf5ea314d2613e19284671f88bd93b508048acceee36284a4` | 37862 |
| `resultats/oeuvre_universelle/MANIFESTE_ANTERIORITE.md` | `64f6a3c06e9d9c01b45028e08b8492b5bee1fb5e8284122d1ee0b394a97b17cb` | 18851 |
| `resultats/oeuvre_universelle/resume.json` | `5b5ff89a9851fb51db9a33b497f91770d23498e035e71ce8822141f82b932046` | 90153 |
| `web_cloud/oeuvre_universelle.html` | `5eef92fc3dcfd72471bb53f5358f291f564910bdab55717da4af954ea3941aaa` | 112709 |
| `web_cloud/oeuvre_universelle_en.html` | `db122f5a3bdf01dee89364629c7ef0a5b355705bdbbef4060d0003d11b3fd326` | 109443 |
| `web_cloud/oeuvre_universelle_ar.html` | `a83f3a2e947d1ebbd273fa2ce97a3ed9ac9ef6dfbe4a5100c69eca0fae3d5545` | 118377 |
| `oeuvre_universelle/manifeste_anteriorite.py` | `f184a81efacece0072bd734201ca8d1edcad84f83d37959eb9f3d95e4143b5ee` | 7297 |
| `oeuvre_universelle/generer_page_oeuvre.py` | `dadd1fef045bac58ac7a7a99a1a7c8ef31ad39b08049c2281f348779c4bd6654` | 48210 |
| `tests/test_oeuvre_universelle.py` | `cb025aa36bfe1b9bb0c79c03556deb54cc73d61be9c80052118be8902d7cd5bd` | 13910 |

Ces valeurs sont liées à ce relevé : toute régénération du manifeste ou des pages les change.

Régénération postérieure, 2026-10-27T23:26:32Z : le manifeste vaut alors `a597e9a9…`, `MANIFESTE_ANTERIORITE.md` `a0daba2b…`, `resume.json` `e24ca7cf…`, les pages `2a25372e…`, `d7a03de5…`, `23bde381…` ; racine et compteur inchangés. Le tableau ci-dessus reste un instantané du relevé, pas l'état courant.

## Limites du cas

- **Pas de preuve d'antériorité légale.** Le `mtime` est local et forgeable ; la racine n'a pas été ancrée (OpenTimestamps, DOI, dépôt public non exécutés au relevé).
- **Le vérificateur d'origine ne détecte pas les ajouts.** `verifier_manifeste()` parcourt uniquement `manifeste["fichiers"]` : un fichier couvert ajouté après scellement n'apparaît jamais comme `EXTRA`. Le script fourni par ce Skill comble ce trou.
- **Le test de vérification régénère avant de vérifier.** `test_manifeste_verifiable` appelle `construire_manifeste(ecrire=True)` puis `verifier_manifeste()` : il prouve que le générateur et le vérificateur sont cohérents, pas que le manifeste stocké était à jour. C'est une lecture du code, pas un échec reproduit.
- **La session source était encore en cours** (déploiement VPS) au relevé : l'état du projet peut évoluer après ces empreintes.
- **Le rapport final de la session source annonce 149 fichiers et la racine `9e47b14b…`** ; ce cas les a revérifiés indépendamment, sans reprendre les chiffres du résumé.

## Contrôle réel en conditions d'usage — 2026-10-27T23:22Z

Session `9948e777-3bfe-4fbe-81f2-f538f0479ee3`, tour « reload les skills pour tester le nouveau skill ». Périmètre `ASTRO-Q°ODE_SYSTEME` ; manifeste alors `cf165d41b534cdaaf5ea314d2613e19284671f88bd93b508048acceee36284a4` (37 862 octets), racine `9e47b14b…`, 149 fichiers.

Commande exécutée (Bash du 23:22:07Z), lancée depuis la racine scellée avec chemins relatifs :

```bash
cd .../ASTRO-Q°ODE_SYSTEME
SK=.../.qoder/skills/sceller-manifeste-integrite-sans-circularite
py -3 -B "$SK/scripts/verifier_manifeste_sans_circularite.py" \
  --manifest resultats/oeuvre_universelle/manifeste_anteriorite.json --racine . \
  --glob ... (16 motifs) \
  --porteur-de-racine web_cloud/oeuvre_universelle.html \
  --porteur-de-racine web_cloud/oeuvre_universelle_en.html \
  --porteur-de-racine web_cloud/oeuvre_universelle_ar.html \
  --porteur-de-racine resultats/oeuvre_universelle/resume.json \
  --porteur-de-racine resultats/oeuvre_universelle/manifeste_anteriorite.json \
  --porteur-de-racine resultats/oeuvre_universelle/MANIFESTE_ANTERIORITE.md
```

```text
RC=0
FILES 149
COUVERTS 149
RACINE_MANIFESTE 9e47b14b24ef39240fd00623ee1871e6c465e63ae3bd115322fd6fac598be86d
RACINE_CALCULEE 9e47b14b24ef39240fd00623ee1871e6c465e63ae3bd115322fd6fac598be86d
RACINE_FICHIER web_cloud/oeuvre_universelle.html MATCH
RACINE_FICHIER web_cloud/oeuvre_universelle_en.html MATCH
RACINE_FICHIER web_cloud/oeuvre_universelle_ar.html MATCH
RACINE_FICHIER resultats/oeuvre_universelle/resume.json MATCH
RACINE_FICHIER resultats/oeuvre_universelle/manifeste_anteriorite.json MATCH
RACINE_FICHIER resultats/oeuvre_universelle/MANIFESTE_ANTERIORITE.md MATCH
RESULT OK
```

Les 16 motifs sont ceux de `GLOBS_SELECTIONNES` dans `oeuvre_universelle/manifeste_anteriorite.py` (l. 37-54) : égalité vérifiée par comparaison programmatique le 2026-10-28 (`CONST 16 USED 16 EQUAL True`). La constante appartient au module de scellement, pas à `generer_page_oeuvre.py`.

Preuve de non-écriture :

- Manifeste : `cf165d41…` avant (23:13:16Z) et après (23:22:17Z), identique.
- `find . -name "*.pyc" -newermt "2026-10-28 00:20"` vide à 23:29:12Z (locale UTC+1) : aucune fixture ni cache laissé par le contrôle.
- **Limite** : le `git status --porcelain 2>/dev/null` lancé au même moment ne prouve rien. Le dossier n'est pas un dépôt Git (`git rev-parse --is-inside-work-tree` → code 128, mesuré le 2026-10-28) ; stderr masqué, la sortie vide a été lue à tort comme un état propre.
- Les `__pycache__` présents (`__pycache__`, `oeuvre_universelle/__pycache__`) datent de la session source (22:28–22:32 UTC), antérieurs à ce contrôle. Le scellement les exclut (`EXCLUSIONS` dans le module), donc ils ne produisent pas de `EXTRA` ; `-B` sert à garantir zéro écriture, pas à prévenir un `EXTRA`.

Seconde exécution à 23:27:07Z, après régénération (manifeste `a597e9a9…`, racine inchangée) : sortie identique, `RESULT OK`, rc 0, 6 `MATCH`.

Rejeu du 2026-10-28 à 00:38 locale (23:38:17Z), avec la commande telle que documentée dans l'étape 5 après mise à jour : `RESULT OK`, rc 0, 149 fichiers, 6 `MATCH` ; les SHA-256 des six artefacts sont identiques avant et après, aucun `.pyc` nouveau ; `git rev-parse --is-inside-work-tree` répond 128, donc aucun contrôle Git n'est disponible sur ce périmètre.

État de la source au relevé : `runtimeState: running`, `revision: 10`, dernier tour (« Redéployer la page sur al-mizan.world ») encore en streaming et sans rapport avec ce contrôle. Aucune correction utilisateur sur le manifeste dans cette session.
