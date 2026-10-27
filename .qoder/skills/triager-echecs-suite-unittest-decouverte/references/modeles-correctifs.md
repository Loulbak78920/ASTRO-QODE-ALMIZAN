# Modèles de correctifs — découverte `unittest`

Chaque modèle suit la même discipline : reproduire le mode d'échec, corriger la cause, re-prouver le comportement, distinguer la preuve observée de la conclusion déclarée.

## 1. Artefact d'ordre d'import

### Avant — constante figée à l'import

```python
import os

CLE_API = os.environ.get("MIZAN_VPS_API_KEY", "").strip()


def authentifie(token: str) -> bool:
    if not CLE_API:
        return False
    return hmac.compare_digest(token, CLE_API)
```

Le module ciblé pose sa clé avant son propre import, donc il passe seul. En découverte, un autre module importe la cible le premier : `CLE_API` vaut `""` pour tout le processus.

### Après — lecture à chaque appel, fermée par défaut

```python
import os


def cle_api_attendue() -> str:
    """Lit la clé à chaque requête : l'absence de variable ferme les routes protégées."""
    return os.environ.get("MIZAN_VPS_API_KEY", "").strip()


def authentifie(token: str) -> bool:
    cle = cle_api_attendue()
    if not cle:
        return False
    return hmac.compare_digest(token, cle)
```

Rechercher les anciens importateurs de la constante supprimée :

```bash
grep -rn "CLE_API" --include=*.py .
```

Un import résiduel produit `ImportError`, pas un 401 : c'est un signal distinct à corriger avant de relancer.

### Sonde dans un processus enfant

```bash
env -u MIZAN_VPS_API_KEY PYTHONIOENCODING=utf-8 py -3 -B -c "import os, sys; sys.path.insert(0, '.'); import module_sas_biometrique_souverain, passerelle_api_vps_mizan as p; print('fonction:', repr(p.cle_api_vps_attendue())); print('constante:', repr(getattr(p, 'CLE_API_VPS', 'ABSENTE')))"
```

Attendu après correction : `fonction: ''`, puis une valeur non vide dès que la variable est posée dans le processus.

## 2. Isolation des tests

### Avant — clé posée trop tard

```python
from passerelle_api_vps_mizan import ServeurPasserelleAPIVPS, CLE_API_VPS_DEFAUT

os.environ.setdefault("MIZAN_VPS_API_KEY", "cle_test")  # trop tard
```

L'import a déjà figé la constante. De plus, l'assertion utilise la constante importée, donc elle teste l'ordre d'import, pas la requête.

### Après — clé avant l'import, valeur locale pour l'assertion

```python
import os

CLE_TEST_API = os.environ.setdefault(
    "MIZAN_VPS_API_KEY", "cle_test_passerelle_api_vps_2026_securisee"
)

from passerelle_api_vps_mizan import ServeurPasserelleAPIVPS  # noqa: E402

headers = {"Authorization": f"Bearer {CLE_TEST_API}"}
```

Piège : `setdefault` ne remplace pas une variable exportée vide. Si `MIZAN_VPS_API_KEY=""` peut exister dans le shell, utiliser :

```python
CLE_TEST_API = os.environ.get("MIZAN_VPS_API_KEY") or "cle_test_passerelle_api_vps_2026_securisee"
os.environ["MIZAN_VPS_API_KEY"] = CLE_TEST_API
```

### Test négatif sans variable

```python
from unittest import mock

with mock.patch.dict(os.environ):
    os.environ.pop("MIZAN_VPS_API_KEY", None)
    # requête protégée : doit répondre 401
```

Ne pas patcher la constante du module : cela validerait l'ordre d'import, pas la fermeture par défaut.

## 3. Cycle de vie du serveur

### Avant — `shutdown()` seul

```python
def arreter(self):
    if self.httpd:
        self.httpd.shutdown()
```

`shutdown()` arrête la boucle `serve_forever`, mais ne ferme pas la socket d'écoute. D'où `ResourceWarning: unclosed <socket.socket ... laddr=('0.0.0.0', 8098)>`.

### Après — fermeture complète et références remises à zéro

```python
def arreter(self):
    """Arrête le serveur et libère le port d'écoute."""
    if not self.httpd:
        return
    self.httpd.shutdown()
    self.httpd.server_close()
    if self.thread:
        self.thread.join(timeout=5.0)
        self.thread = None
    self.httpd = None
```

Dans `tearDownClass`, appeler seulement `arreter()`. Un `server_close()` supplémentaire après coup est redondant ou inopérant, puisque `httpd` vaut `None`.

### Preuve de libération du port

```python
import socket

s = socket.socket()
s.bind(("127.0.0.1", 8096))
s.close()
```

Cette opération échoue avec `OSError` si la socket précédente écoute encore. Elle complète la porte `-W error::ResourceWarning`, qui ne couvre pas tous les chemins de fermeture.

## 4. Mise à jour d'assertion

1. Exécuter l'artefact réel avant de toucher au test.
2. Compter depuis l'artefact, pas depuis la constante écrite dans le test.
3. Si l'artefact est correct, aligner l'assertion sur le comportement honnête.
4. Si l'artefact est faux, corriger la source.
5. Conserver une assertion qui vérifie encore quelque chose et mettre à jour la docstring.

### Exemple A — comptage de scripts

```python
# Avant
self.assertEqual(len(fichiers_aq), 8)

# Après : neuf scripts `.aq` présents et exécutés
self.assertEqual(len(fichiers_aq), 9)
```

Référence projet : `ASTRO-Q°ODE_SYSTEME/tests/test_suite_complete.py:238`.

### Exemple B — formulation commerciale

```python
# Après : vérifier les termes qui portent le sens
self.assertIn("partage 50/50", rep2.reponse_vocale_et_texte)
self.assertIn("Riba 0 %", rep2.reponse_vocale_et_texte)
```

Référence projet : `ASTRO-Q°ODE_SYSTEME/tests/test_suite_complete.py:947-948`.

Ne pas remplacer une assertion précise par une sous-chaîne commode qui ne vérifie plus le partage ni l'usure.

## 5. Hygiène des caches

1. Instantané horodaté avant toute suppression :

```bash
find . -name "*.pyc" -printf "%TY-%Tm-%Td %TH:%TM %p\n" | sort
```

2. Identifier les fichiers créés pendant la fenêtre de la session et appartenant aux modules exécutés.
3. Supprimer par chemins explicites, jamais par `rm -rf __pycache__`.
4. Conserver les `.pyc` plus anciens et ceux d'une autre version (`cpython-312` à côté de `cpython-314`), souvent produits par une session concurrente.

```bash
rm -f tests/__pycache__/test_passerelle_api_vps.cpython-314.pyc
rm -f tests/__pycache__/test_sas_biometrique_souverain.cpython-314.pyc
```

La liste se construit depuis l'instantané, pas depuis un glob. Utiliser `-B` pendant les sondes évite d'en créer de nouveaux.

## 6. Statut des preuves

Dans le rapport, séparer :

- **Observé** : sortie brute conservée (journal, comptage, extrait de trace).
- **Déclaré** : conclusion présente dans un résumé ou un bilan, sans sortie brute correspondante dans la fenêtre lue.
- **Non étayé** : méthode citée mais absente des preuves disponibles ; ne pas la présenter comme rejouée.

Le dossier `cas-passerelle-mizan-2026-10-27.md` applique cette matrice.
