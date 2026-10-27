---
name: maj-tableau-maitre-sequentiel
description: "Mettre à jour le tableau maître séquentiel unifié d'IMAM8MAHDI (AL-MIZAN × ASTRO-Q°ODE) : cartographier un nouveau contenu en strate(s), ajouter les entrées via add() dans ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py, régénérer les livrables CSV/HTML à la racine, puis valider la séquence continue, les 13 colonnes, les sommes de magnitudes 40/313/63 et la structure HTML. Utiliser dès qu'un nouvel envoi de briques (concepts, images, actes) doit être harmonisé dans le tableau, ou pour étendre/corriger une strate existante."
---

# Mettre à jour le tableau maître séquentiel unifié

Skill de compatibilité. Le Skill canonique `tableau-maitre-sequentiel` et son validateur font foi ; en cas de divergence, suivre le canonique. Ne pas supprimer ce Skill sans décision explicite.

## Quand l'utiliser

- L'utilisateur envoie de nouvelles briques (concepts, images, actes, exports) à harmoniser dans le tableau maître.
- Il faut ajouter, corriger ou relier une strate existante.
- Il faut vérifier l'intégrité du CSV, du HTML et de la numérotation après une modification.

## Invariants non négociables

1. **Source unique** : `ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py`. Le CSV et le HTML racine sont des artefacts générés ; ne jamais les éditer à la main.
2. **13 colonnes** : `COLONNES` reste la référence. Ne pas changer le schéma pour un simple ajout de contenu.
3. **SEQ automatique** : `add()` attribue `SEQ` selon la position. Ne jamais écrire de numéro de séquence à la main.
4. **S6 scellé** : les états de matière respectent les magnitudes 40 / 313 / 63, les comptes Soleil 4 plasma / Terre 7 / Lune 9 (+ origine Hélium 0) et la distribution de `_repartir_somme_unique`. Ne pas ajouter de ligne à S6 sans décision explicite et sans preuve de la source.
5. **Horloge-noyau A137** : `horloge_noyau/` est lisible et exécutable, mais **jamais modifiable**. Ne rien y écrire.
6. **Valeurs dérivées** : ne jamais coder en dur une valeur issue d'une répartition ou d'une somme. Appeler l'algorithme de la source de vérité.
7. **Livrables** : le CSV doit rester en UTF-8 BOM avec séparateur `;` ; le HTML doit rester aligné sur le CSV.
8. **Clé unique** : `SEQ`. `CODE` n'est pas unique (5 doublons S6 hérités : `ÉT-T-05`, `ÉT-T-06`, `ÉT-T-07`, `ÉT-L-08`, `ÉT-L-09`) ; ne pas l'utiliser comme clé.

## Procédure

### 1. Établir la référence (lecture seule)

Lire, dans cet ordre :

- `ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py` : `add()`, la dernière strate, le commentaire `# Écriture du CSV`.
- `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_physique.py` : `_repartir_somme_unique` (source de vérité).
- `ASTRO-Q°ODE_SYSTEME/horloge_noyau/VERROU.json` : confirmer `ecriture: false`.
- `references/cartographie-strates.md` : choisir la strate cible.

Lancer le validateur pour connaître l'état de départ :

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\maj-tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

### 2. Cartographier le contenu

- Nouveau domaine ou lot de briques : créer une nouvelle strate `S<n+1>` en fin de tableau. C'est le choix par défaut, car il préserve les SEQ existantes.
- Extension ou correction d'une strate existante : ajouter les lignes dans son bloc. La SEQ des lignes suivantes se décale automatiquement ; le signaler dans le rapport.
- Remplir une colonne de lien quand le contenu s'y prête : `matiere`, `terre`, `lune`, `soleil` ou `quantique_bio`. Ne pas inventer de lien pour un axiome ou une constante pure. Exceptions historiques sans lien : les 10 lignes S0, S5 080–082 (`CX-04` à `CX-06`) et S15 166 (`LN`).
- Renseigner `source` pour chaque ligne. Harmoniser le libellé en français, sans perdre les termes techniques.
- Ne pas ajouter de ligne à S6 pour du contenu de matière non scellé : créer une strate liée à S6.

### 3. Ajouter les entrées

Insérer le bloc après la dernière strate (actuellement S18) et **avant** le commentaire `# Écriture du CSV` :

```python
# ────────────────────────────────────────────────────────────────────────────
# STRATE 19 — THÈME DE LA NOUVELLE STRATE
# ────────────────────────────────────────────────────────────────────────────
S19 = "S19 · Thème de la nouvelle strate"
add(S19, "CODE-1", "Famille logique", "Élément",
    "Rôle / description en français",
    matiere="lien avec une strate matière",
    terre="cycle Terre", lune="cycle Lune", soleil="cycle Soleil",
    quantique_bio="lien avec la couche quantique / BIO",
    valeur="valeur ou formule", source="source précise")
```

- Ne pas écrire `SEQ` : `add()` s'en charge.
- Conserver l'ordre des strates : le validateur vérifie que chaque strate forme un bloc contigu.
- Mettre à jour le docstring d'en-tête du générateur (nombre d'entrées et liste des strates).
- Ajouter la clé de couleur de la nouvelle strate dans `COULEURS_STRATE` ; sinon le badge utilisera le bleu par défaut.
- La date du HTML est générée dynamiquement ; ne pas la coder en dur.

### 4. Traiter les valeurs dérivées

- Utiliser `_repartir_somme_unique` du générateur (copie exacte de `lib_physique.py`) ou l'importer en lecture seule depuis la bibliothèque scellée.
- Ne jamais remplacer un appel par une liste de nombres littéraux, même si la somme est correcte : la distribution doit rester celle de la source de vérité.
- Pour S6, ne pas modifier les totaux 40 / 313 / 63. Le validateur compare la distribution complète, pas seulement la somme.
- Vérifier les sommes et la distribution avec le validateur avant de conclure.

### 5. Régénérer

Depuis le dossier du générateur :

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
py -3 generer_tableau_maitre_sequentiel.py
```

Attendre un résumé ASCII du type `OK - N entrees sequentielles - M strates`, puis vérifier que les deux chemins racine sont ceux du tableau maître.

En cas de `UnicodeEncodeError` : les fichiers ont déjà été écrits, mais l'affichage a échoué. Garder les messages console en ASCII et consulter le skill `verifier-livrables-csv-html-windows-fr`.

### 6. Valider

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\maj-tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

Le script vérifie notamment :

- CSV : BOM `EF BB BF`, en-tête 13 colonnes avec `;`, SEQ `001..N` continue, strates contiguës.
- S6 : sommes 40 / 313 / 63 et distribution identique à `lib_physique.py`.
- Générateur : présence de `_repartir_somme_unique`, 13 colonnes, verrou A137.
- HTML : mêmes lignes et mêmes cellules que le CSV, 13 colonnes, `N` badges, dernière SEQ = `N`.

Un avertissement n'est pas un échec, mais il doit être corrigé s'il entre dans le périmètre de la modification, sinon être signalé.

Pour un contrôle navigateur, suivre `verifier-livrables-csv-html-windows-fr` : ouvrir le fichier, exécuter `evaluate_script` avec une fonction flèche, puis tenter un seul screenshot. Si le viewport est masqué (`NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`), ne pas réessayer et annoncer **validation structurelle uniquement**. Ne jamais prétendre avoir vu la page sans screenshot réussi.

### 7. Rapporter

Format attendu :

```text
N entrées · M strates · SEQ 001–N
S6 40/313/63 · 4/7/9 + origine 0 : OK
CSV 13 colonnes / BOM / ; : OK
HTML N lignes · M badges · 13 colonnes · contenu = CSV : OK
Visuel : vérifié | non vérifié (viewport masqué)
Fichiers : <chemins absolus>
```

Comparer attendu / observé, citer les chemins, et distinguer explicitement validation visuelle et structurelle.

## Pièges observés

| Symptôme | Cause | Correctif |
|---|---|---|
| Sommes 39 / 312 / 62 | valeurs d'état codées en dur | utiliser `_repartir_somme_unique` et valider la distribution |
| SEQ décalée après ajout | insertion au milieu d'une strate | préférer une nouvelle strate en fin ; si le décalage est voulu, le signaler |
| HTML différent du CSV | CSV édité à la main ou génération partielle | régénérer les deux livrables, puis relancer le validateur |
| `UnicodeEncodeError` cp1252 | flèche, emoji ou caractère hors cp1252 dans un `print()` | messages console en ASCII ; voir le skill voisin |
| `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` | viewport in-app masqué | validation structurelle, pas de nouveau screenshot |
| Badge bleu par défaut | clé absente de `COULEURS_STRATE` | ajouter la clé exacte de la strate |
| Date ou plage SEQ obsolète | docstring / date codés en dur | mettre à jour le docstring ; la date HTML est dynamique |
| `CODE` utilisé comme clé | doublons S6 hérités | utiliser `SEQ` comme clé unique |
| Lien inventé | règle « un lien partout » mal appliquée | exceptions S0 / constantes pures documentées |

## Ressources

- Skill canonique `tableau-maitre-sequentiel` : procédure, référence S6 et validateur de référence. En cas de divergence, il fait foi.
- `C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py` : validateur canonique (codes 0/1/2, `--strict-warnings`, `--allow-external`).
- `scripts/verifier_tableau_maitre.py` : validateur historique conservé, lecture seule, sortie ASCII.
- `references/cartographie-strates.md` : carte des strates S0–S18 et règles de placement.
- Skill `verifier-livrables-csv-html-windows-fr` : chaîne Windows FR générique (stdout ASCII, CSV BOM/`;`, `evaluate_script`, fallback viewport). Ne pas dupliquer cette chaîne ici.

## Définition de terminé

- [ ] Le contenu est rattaché à une strate, avec `source` et un lien quand il existe (exceptions historiques documentées).
- [ ] Le générateur a produit le CSV et le HTML ; aucun livrable n'a été édité à la main.
- [ ] Le validateur ne signale aucun échec dur ; les avertissements sont expliqués ou corrigés.
- [ ] Le rapport donne N, M, la plage SEQ, les sommes S6 et les comptes 4/7/9 + origine 0, le contrôle HTML et les chemins.
- [ ] La mention « visuel vérifié » n'apparaît que si un screenshot a réellement réussi.
