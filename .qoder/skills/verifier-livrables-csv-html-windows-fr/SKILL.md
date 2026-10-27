---
name: verifier-livrables-csv-html-windows-fr
description: "Vérifier les livrables CSV/HTML générés ou régénérés dans l'environnement Windows FR de ce projet : résoudre l'interpréteur Python réel (l'alias Microsoft Store de `python` échoue avec le code 49 ; utiliser `py -3`), capturer la sortie du générateur (code 0, zéro octet non-ASCII, N/M issus du résumé), prouver l'état par empreintes SHA-256 avant/après, contrôler le CSV Excel français (UTF-8 BOM, séparateur « ; », 13 colonnes, 1+N lignes, SEQ continue, strates uniques, dernière ligne), puis croiser le dernier ELEMENT avec le DOM du HTML via evaluate_script. Utiliser dès qu'un script produit ou régénère un tableau CSV/HTML, qu'un print Python échoue (UnicodeEncodeError cp1252), que `python` renvoie le code 49, que les livrables semblent périmés, ou qu'un take_screenshot renvoie NATIVE_BROWSER_VIEWPORT_UNAVAILABLE."
---

# Vérifier les livrables CSV/HTML sous Windows FR

## Objectif

Appliquer la chaîne de contrôle validée sur ce poste : prouver l'état des livrables par une génération capturée, vérifier les octets du CSV, puis croiser le DOM du HTML. Le générateur de référence du projet IMAM8MAHDI est `ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py` ; adapter les chemins, pas les règles ci-dessous.

Ne jamais reprendre un nombre d'entrées ou de strates d'un rapport antérieur : N et M viennent uniquement de la sortie du générateur exécuté dans la session courante.

## 0. Régénérer et prouver l'état

Depuis la racine du dépôt, si le générateur n'a pas été exécuté et capturé dans cette session, ou si l'état des livrables est inconnu, commencer ici. Si la sortie est déjà capturée, consigner les empreintes et passer à la section 2.

### Interpréteur

Dans Git-Bash, `python` est l'alias Microsoft Store : `python -c "import sys"` sort avec le code 49 et affiche « Python est introuvable… » en cp1252. Ne pas interpréter ce message comme une erreur du script et ne pas utiliser `python`.

```bash
py -3 -c "import sys; print(sys.executable); print(sys.version.split()[0])"
```

Attendu sur ce poste : `C:\Users\Administrateur\AppData\Local\Python\pythoncore-3.14-64\python.exe` et `3.14.x` (3.14.7 observé). Si `py` est absent, utiliser ce chemin absolu.

### Empreintes avant

```bash
sha256sum TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html
```

Pour pouvoir revenir en arrière, copier les deux livrables dans `C:/Users/Administrateur/.qoder/tmp/verif_livrables_backup/` avant de régénérer ; comparer les empreintes ROOT/BACKUP et supprimer la copie après conclusion.

### Génération capturée

```bash
TMP="C:/Users/Administrateur/.qoder/tmp/verif_livrables"
mkdir -p "$TMP"
py -3 "ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py" \
  > "$TMP/generateur.stdout.txt" 2> "$TMP/generateur.stderr.txt"
echo "EXIT:$?"
py -3 -c "import sys; b=open(sys.argv[1],'rb').read(); print('nonAsciiBytes:', sum(x>127 for x in b))" "$TMP/generateur.stdout.txt"
```

- `EXIT` doit être `0` ; lire `stderr` en cas d'échec.
- `nonAsciiBytes` doit être `0` : la règle ASCII de la section 1 s'applique aussi aux scripts de contrôle.
- Extraire N et M de la ligne `OK - N entrees sequentielles - M strates`. Ne pas les déduire d'un ancien rapport ; `185 / 19` n'est qu'un état observé.

### Empreintes après et verdict

```bash
sha256sum TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html
```

- Empreintes identiques : régénération **byte-identique** ; les contrôles portent sur un contenu inchangé.
- Empreintes différentes : **changement réel** ; utiliser le nouveau N/M et le signaler.
- Le HTML contient la date de génération : une régénération un autre jour change son empreinte sans changement de contenu. Ne pas conclure à une dérive sur ce seul indice.

## 1. Console Python : ASCII uniquement

La console Python 3.14 du poste encode en cp1252. Un seul caractère hors cp1252 dans un `print()` fait échouer le script **après** l'écriture des fichiers, ce qui donne une fausse impression d'échec complet.

```python
# Interdit : UnicodeEncodeError sur '\u2192' (position 5, cp1252)
print(f"CSV  → {FICHIER_CSV}")

# Correct
print(f"CSV  : {FICHIER_CSV}")
```

- Bannir flèches, emoji, accents et symboles des `print()` et des messages d'erreur console.
- Appliquer la même règle aux scripts de contrôle : ne pas imprimer un `ELEMENT` ou une `STRATE` accentués ; comparer en mémoire et n'imprimer qu'un booléen, une longueur ou un compteur. Un `S18 ? Exercice de validation s?quentiel` dans la sortie révèle ce cas.
- Conserver les accents et symboles dans le CSV et le HTML : ces fichiers sont écrits en UTF-8.
- `# -*- coding: utf-8 -*-` ne corrige pas l'encodage de stdout ; ne pas l'ajouter comme correctif.
- Un `�` dans la sortie révèle un autre script qui imprime de l'UTF-8 ; le corriger aussi.
- Sortie finale attendue : un résumé entièrement ASCII, par exemple `OK - 185 entrees sequentielles - 19 strates`. Ce nombre est un exemple observé, pas une constante.

## 2. CSV pour Excel français

Écrire le CSV avec BOM et point-virgule, sinon Excel FR affiche des accents cassés ou entasse les colonnes :

```python
with FICHIER_CSV.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=COLONNES, delimiter=";")
    writer.writeheader()
    writer.writerows(ROWS)
```

Contrôles obligatoires (N et M viennent de la section 0) :

Enregistrer ce contrôle dans un fichier temporaire, par exemple `C:/Users/Administrateur/.qoder/tmp/verif_livrables/check_csv.py` :

```python
import csv, io, sys
from pathlib import Path

n_attendu, m_attendu = int(sys.argv[1]), int(sys.argv[2])
b = Path("TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv").read_bytes()
lignes = list(csv.reader(io.StringIO(b.decode("utf-8-sig")), delimiter=";"))
entete, donnees = lignes[0], lignes[1:]
seqs = [r[0] for r in donnees]
resultats = {
    "BOM": b.startswith(b"\xef\xbb\xbf"),
    "colonnes_13": len(entete) == 13,
    "entete_sans_virgule": "," not in ";".join(entete),
    "lignes_1_plus_N": len(lignes) == n_attendu + 1,
    "donnees_N": len(donnees) == n_attendu,
    "strates_M": len({r[1] for r in donnees}) == m_attendu,
    "seq_continue": seqs == [f"{i:03d}" for i in range(1, len(donnees) + 1)],
    "derniere_seq_N": donnees[-1][0] == f"{n_attendu:03d}",
}
for nom, ok in resultats.items():
    print(f"{nom}: {ok}")
print("dernier_code_ascii:", donnees[-1][2].isascii())
print("dernier_element_len:", len(donnees[-1][4]))
raise SystemExit(0 if all(resultats.values()) else 1)
```

Appel, depuis la racine du dépôt :

```bash
py -3 "C:/Users/Administrateur/.qoder/tmp/verif_livrables/check_csv.py" N M
```

- Premiers octets : `EF BB BF`.
- En-tête à 13 colonnes (schéma du tableau maître ; adapter si le livrable change), contenant `;` et aucun `,`.
- Nombre de lignes = 1 en-tête + N entrées annoncées par le générateur.
- `M` est le nombre de strates uniques ; la SEQ est continue de `001` à `N`.
- Vérifier la dernière ligne : SEQ = N, CODE et ELEMENT attendus ; n'imprimer que des valeurs ASCII ou des booléens.
- Les fins de ligne CRLF produites par `csv` sont normales ; ne pas les « corriger ».
- Ne pas remplacer `utf-8-sig` par `utf-8`, ni `;` par `,`.

## 3. Validation du HTML dans le navigateur in-app

1. Ouvrir le fichier avec `navigate_page` (`file:///...` absolu).
2. Valider d'abord la structure avec `evaluate_script` (rapide, déterministe, indépendant du viewport).
3. Tenter `take_screenshot` une seule fois pour le contrôle visuel.

Les attendus (`total`, `strates`, `lastSeq`, `badges`) sont N et M lus à la section 0, jamais des valeurs mémorisées.

Si `take_screenshot` renvoie `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` (`visible=false`, `visibilityState=hidden`), le viewport est masqué, pas la page cassée : ne pas réessayer, poursuivre la validation structurelle. L'échec peut survenir après un premier screenshot réussi (par exemple après un scroll) ; il n'est pas lié au contenu HTML.

### Appel evaluate_script

- Le paramètre s'appelle `function`, pas `script`.
- La valeur doit être une fonction flèche `() => { ... }` ; une suite d'instructions nue terminée par `;` provoque `SyntaxError: Unexpected token ';'`.
- Retourner une chaîne `JSON.stringify(...)`, jamais des nœuds DOM.

```js
() => {
  const rows = document.querySelectorAll('#master tbody tr');
  const strates = [...new Set([...rows].map(r => r.dataset.strate))];
  const last = rows[rows.length - 1];
  return JSON.stringify({
    total: rows.length,
    strates: strates.length,
    lastSeq: last.cells[0].textContent,
    lastElement: last.cells[4].textContent,
    badges: document.querySelectorAll('.badge').length,
    title: document.title.slice(0, 60)
  });
}
```

Interpréter le résultat :

- `total` = nombre d'entrées imprimé par le générateur.
- `strates` = nombre de strates uniques = `badges`.
- `lastSeq` = dernier numéro de séquence, sans trou dans la numérotation.
- `lastElement` = libellé de la dernière entrée attendue ; ne pas l'imprimer (accents, tiret cadratin), le comparer en mémoire à la section 4.
- `title` = préfixe du titre attendu (les 60 premiers caractères).

Adapter les sélecteurs (`#master tbody tr`, `.badge`, index de cellules) si le livrable change, mais conserver ces six contrôles.

`take_snapshot` reste disponible en secours, mais peut dépasser la limite de contexte (observé : 95 932 caractères, ~32k tokens, tronqué à 25k). Lire ou grep le fichier de sortie enregistré plutôt que de relancer un snapshot complet.

Pour la chaîne générique de repli navigateur (fraîcheur des preuves, rapport visuel/structurel, sécurité du contenu de page), voir le skill `validation-navigateur-par-repli` ; les règles CSV/console ci-dessus restent spécifiques à ce projet.

## 4. Croisement CSV ↔ DOM

Comparer la dernière ligne du CSV et le dernier enregistrement rendu. Enregistrer la chaîne JSON retournée par `evaluate_script` dans `C:/Users/Administrateur/.qoder/tmp/verif_livrables/dom.json`, puis :

```python
import csv, io, json, sys
from pathlib import Path

dom = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
b = Path("TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv").read_bytes()
donnees = list(csv.reader(io.StringIO(b.decode("utf-8-sig")), delimiter=";"))[1:]
resultats = {
    "last_seq_match": donnees[-1][0] == dom["lastSeq"],
    "last_element_match_dom": donnees[-1][4] == dom["lastElement"],
}
for nom, ok in resultats.items():
    print(f"{nom}: {ok}")
print("last_element_len:", len(donnees[-1][4]))
raise SystemExit(0 if all(resultats.values()) else 1)
```

Appel, depuis la racine du dépôt :

```bash
py -3 "C:/Users/Administrateur/.qoder/tmp/verif_livrables/check_dom.py" "C:/Users/Administrateur/.qoder/tmp/verif_livrables/dom.json"
```

- `last_seq_match` et `last_element_match_dom` doivent être `True`.
- Si un contrôle échoue : les deux livrables ne viennent pas de la même génération, ou la page n'est pas la version courante ; régénérer puis recharger avant de conclure.
- Ne pas imprimer `lastElement` : il contient des caractères hors ASCII.

## 5. Rapport de validation

- Indiquer N, M et la sortie ASCII du générateur, puis le verdict des empreintes : byte-identique ou changement réel.
- Si le screenshot a réussi : annoncer « validation visuelle + structurelle » avec les chiffres observés.
- Sinon : annoncer « validation structurelle (viewport masqué) » et ne jamais prétendre avoir vu la page.
- Citer les chemins absolus des livrables et comparer attendu / observé (CSV, DOM, croisement), sans se contenter d'un « OK ».

## Checklist finale

- [ ] `py -3` résout le Python 3.14 réel ; `python` (alias Microsoft Store, code 49) n'a pas été utilisé.
- [ ] Générateur terminé avec `EXIT:0`, stdout à 0 octet non-ASCII, résumé `OK - N entrees sequentielles - M strates` lu.
- [ ] Empreintes SHA-256 avant/après consignées ; verdict byte-identique ou changement réel (date HTML prise en compte).
- [ ] CSV : BOM `EF BB BF`, 13 colonnes, en-tête avec `;` et sans `,`, 1+N lignes, M strates uniques, SEQ 001..N continue, dernière ligne conforme.
- [ ] DOM : `total`, `strates`, `badges`, `lastSeq`, `lastElement`, `title` conformes à N/M.
- [ ] Croisement CSV ↔ DOM : `last_seq_match` et `last_element_match_dom` vrais.
- [ ] Les scripts de contrôle n'impriment que des valeurs ASCII (booléens, compteurs, longueurs).
- [ ] Rapport final distinguant explicitement validation visuelle et structurelle.

Pour modifier le contenu du tableau (ajout ou correction de strates), suivre `maj-tableau-maitre-sequentiel` ou le Skill canonique `tableau-maitre-sequentiel` et son validateur ; ne pas dupliquer ici les invariants S6 / 13 colonnes / SEQ.
