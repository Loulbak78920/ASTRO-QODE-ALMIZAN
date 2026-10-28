---
name: retirer-repli-secret-echec-ferme
description: "Retirer d'un service une valeur de repli codée en dur et le rendre fail-closed : faire trancher le comportement quand la variable manque, remplacer la constante par un accesseur lu à chaque signature et un pré-contrôle qui refuse le démarrage, mettre à jour tous les imports de la constante, conserver le contrôle de rotation par empreinte sha256[:8], rendre l'EnvironmentFile= du secret obligatoire dans le template et dans chaque générateur d'unité, donner un secret propre aux modules de test qui exercent les routes émettrices (import os avant setdefault), marquer la documentation « non déployé », puis prouver par env -u (EXIT=1), tests verts, zéro littéral dans le paquet et skill-file-qa. Couvre le retrait, pas la rotation (`rotation-secret-systemd-vps-mizan`), ni le déploiement, ni l'assainissement de jetons personnels. 移除硬编码回退值并改为失败关闭：访问器、启动拒绝、systemd 必选 EnvironmentFile、测试夹具、sha8 对照、证明与验收。"
---

# Retirer une valeur de repli et fermer par défaut

## Portée

Supprimer une valeur de repli codée en dur (secret HMAC, clé, jeton) d'un service qui la porte encore, et le rendre **fail-closed** : sans variable d'environnement, il refuse au lieu de signer avec une valeur publique. Couvre les porteurs qui réintroduiraient le repli : générateurs d'unité systemd, tests, documentation, paquet de preuves.

Cas d'origine : un paquet `rotation-secret-systemd-vps-mizan` avait passé `skill-file-qa` alors que sa documentation « sans valeur de secret » recopiait une valeur de repli encore active dans le code.

## Délégation

| Besoin | Skill |
| :--- | :--- |
| Faire tourner le secret et prouver l'ancien refusé | `rotation-secret-systemd-vps-mizan`, `rotation-cle-api-service-systemd` |
| Déployer le correctif sur le VPS | `deployer-site-sans-dol-vps` |
| Retirer des jetons personnels d'un paquet Skill | `sanitiser-paquet-skill-jetons-sensibles` |
| Valider le paquet écrit | `skill-file-qa` |

Hors portée : réécrire l'historique Git, déplacer ou publier les sauvegardes `.bak` déjà produites, choisir seul le comportement de production.

## 1. Invariants

1. **La valeur ne sort jamais.** Ni stdout, ni stderr, ni argv, ni une ligne de `grep` affichée. Rapporter longueur et `sha256[:8]` ; masquer les jetons avant de juger un scan.
2. **Le comportement se tranche avec l'utilisateur avant l'édition.** Refuser au démarrage, refuser à chaque usage, ou générer un secret éphémère sont trois productions différentes. Ne pas improviser pendant une rotation.
3. **Zéro littéral à la fin** — code, générateurs, documentation et paquet de preuves. Seul le sha8 du secret historique peut rester.
4. **Lecture à l'usage, pas à l'import.** Une constante de module fige l'environnement au moment de l'import ; un test qui pose la variable après l'import échoue quand même.
5. **Tous les porteurs d'unité, pas seulement le template.** Chaque générateur embarque sa propre ligne `EnvironmentFile=`.
6. **Un test qui passe ne prouve rien s'il ne signe pas.** Identifier les routes émettrices avant de conclure.
7. **Local n'est pas déployé.** Tant qu'aucun déploiement autorisé n'a eu lieu, écrire « non déployé » dans la documentation et le rapport.
8. **`skill-file-qa` ne scanne pas les secrets.** Un `RESULT PASS` ne dit rien sur la présence d'une valeur.

## 2. Trancher le comportement

Poser la question une fois, avec l'effet observable et non le mécanisme :

| Choix | Effet | Quand |
| :--- | :--- | :--- |
| Refus au démarrage + erreur à la signature | Le service ne démarre pas sans variable ; une route émettrice répond 500 | Retenu le 2026-10-28 pour le HMAC |
| Refus à chaque usage seulement | Le service démarre, les routes émettrices échouent | Si un démarrage dégradé est acceptable |
| Secret éphémère | Les signatures changent à chaque redémarrage | Uniquement si aucun client ne vérifie les signatures |

Ne pas proposer « continuer avec une valeur » : c'est le défaut qu'on retire.

## 3. Recenser sans afficher

```bash
grep -rn 'os.environ.get("<VAR>"' <depot> --include='*.py'
grep -rn '^EnvironmentFile=.*<fichier-env>' <depot>
grep -rln '<VAR>' <depot>/.qoder/skills/<paquet>/
```

Ne jamais afficher le second argument d'un `os.environ.get` : c'est la valeur. Compter les fichiers et les lignes, pas les valeurs.

Porteurs à inventorier :

| Porteur | Ce qu'on y cherche |
| :--- | :--- |
| Service | constante de module avec valeur de repli |
| Modules consommateurs | import de la constante, usage à la signature |
| Outil de rotation | constante `SECRET_DEFAUT` contenant la valeur |
| Template systemd | `EnvironmentFile=` avec ou sans `-`, ligne `Environment=` legacy |
| Chaque générateur d'unité | copie embarquée de la même ligne |
| Tests | modules qui importent le service ou frappent une route émettrice |
| Documentation | valeur en clair, statut de déploiement |
| Paquet de preuves | description, corps, références ; mention « aucune valeur » |

## 4. Remplacer la constante par un accesseur

```python
def secret_webhooks_requis() -> bytes:
    """Secret HMAC des webhooks : uniquement fourni par l'environnement, sans valeur de repli."""
    secret = os.environ.get("MIZAN_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise RuntimeError(
            "MIZAN_WEBHOOK_SECRET absent : signature des webhooks impossible."
        )
    return secret.encode("utf-8")
```

- `strip()` : une variable vide ou blanche vaut absente.
- `RuntimeError` : l'appelant décide du comportement visible.
- L'appel se fait au point d'usage, par exemple à la signature : `hmac.new(secret_webhooks_requis(), ...)`.
- Pré-contrôle au démarrage, avant la création du serveur et des instances :

```python
try:
    secret_webhooks_requis()
except RuntimeError as erreur:
    raise SystemExit(f"[ERREUR] Démarrage refusé : {erreur}")
```

Ne pas conserver de valeur par défaut calculée au module, même vide.

## 5. Mettre à jour les consommateurs

```bash
grep -rn 'HMAC_SECRET_WEBHOOKS\|secret_webhooks_requis' <depot> --include='*.py'
```

Remplacer l'import de la constante par l'import de la fonction, puis chaque usage par l'appel. Un import résiduel de la constante supprimée échoue en `ImportError` au chargement, pas à la signature : le test le plus utile est l'import du module consommateur.

## 6. Garder le contrôle de rotation sans littéral

L'outil de rotation doit encore reconnaître un service resté sur l'ancienne valeur, sans conserver cette valeur :

```python
EMPREINTE_SECRET_DEFAUT_SHA8 = "ee9faafa"  # sha256[:8] du seul repli historique
```

```bash
echo "SECRET_DEFAUT=$([ "$SECRET_SHA8" = "{EMPREINTE_SECRET_DEFAUT_SHA8}" ] && echo OUI || echo NON)"
```

La comparaison porte sur le `SECRET_SHA8` lu dans l'environnement du processus, jamais sur une valeur. Calculer le sha8 une seule fois depuis une sauvegarde en `600` hors dépôt, et ne conserver que le sha8 :

```bash
py -3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read().strip()).hexdigest()[:8])" <fichier-600-hors-depot>
```

Un sha8 est une empreinte stable, pas un secret ; il peut rester dans le dépôt et la documentation.

## 7. Aligner tous les générateurs d'unité

`EnvironmentFile=` **sans** `-` rend le fichier obligatoire : systemd refuse de démarrer si le secret manque. Avec `-`, l'absence est tolérée et l'ancien chemin de repli redevient atteignable.

- Corriger le template **et** chaque générateur qui embarque sa propre copie de l'unité.
- Vérifier ensuite : `grep -rn '^EnvironmentFile=.*<fichier-env>' <depot>` doit lister le template et tous les générateurs, tous sans `-`.
- Ne pas rendre obligatoire un autre secret par copier-coller : la clé d'API peut rester optionnelle si la décision ne la concerne pas.
- Retirer toute ligne `Environment=<VAR>=` legacy du service.

## 8. Donner un secret aux tests

Repérer les routes qui émettent réellement (commande, interaction, webhook entrant, orchestrateur unifié) : elles appellent l'accesseur et échouent sans variable.

Chaque module qui importe le service ou frappe une route émettrice pose son propre secret **avant** l'import :

```python
import os

os.environ.setdefault(
    "MIZAN_WEBHOOK_SECRET", "secret_test_webhooks_<module>_2026"
)
import passerelle_api_vps_mizan  # l'import du service vient après
```

- `import os` doit exister : le 2026-10-28, l'ajout du `setdefault` dans un module sans `import os` a produit `NameError: name 'os' is not defined` au chargement.
- Une valeur distincte par module ; jamais un secret de production.
- Ce projet n'a pas de `conftest.py` dans `tests/` : chaque module est responsable.
- Sans secret, l'accesseur lève et la route qui attrape `Exception` répond 500. C'est déduit du code, pas observé dans la session du 2026-10-28.
- Un module qui n'émet pas passe sans variable : absence d'échec n'est pas preuve.
- Un `__pycache__` d'une ancienne constante peut masquer le changement : lancer avec `-B` ou nettoyer le cache.

## 9. Documentation et paquet de preuves

- Remplacer la valeur par le sha8, avec la date et « non déployé ».
- Une phrase « aucune valeur de secret » doit être vérifiée ligne par ligne : le validateur ne la contrôle pas.
- Dans un paquet Skill, contrôler description, corps et références, pas seulement le code.
- Garder explicite l'état de production : elle peut encore exécuter l'ancien code.

## 10. Preuves

```bash
cd <racine>
env -u MIZAN_WEBHOOK_SECRET py -3 passerelle_api_vps_mizan.py; echo "EXIT=$?"
# attendu
# [ERREUR] Démarrage refusé : MIZAN_WEBHOOK_SECRET absent : signature des webhooks impossible.
# EXIT=1
```

- Accesseur : absent → `RuntimeError` avec le message ci-dessus ; présent → `bytes` de la longueur attendue.
- Tests : nommer les modules et leurs compteurs, pas seulement « tests OK ».
- Littéral : 0 occurrence dans le code, la documentation et le paquet, sans afficher la valeur.
- `skill-file-qa` : `RESULT PASS`, avec l'empreinte de début et de fin.
- Interdit : `systemctl show -p Environment` affiche la valeur. Lire `/proc/<pid>/environ` réduit à longueur et sha8, selon le Skill de rotation.

## 11. Pièges

| Piège | Effet | Correctif |
| :--- | :--- | :--- |
| `EnvironmentFile=-` laissé dans un générateur | Un déploiement ultérieur réintroduit le démarrage tolérant | Corriger le template et chaque générateur, puis compter les occurrences |
| Constante lue à l'import | Un test qui pose la variable après l'import échoue | Accesseur fonctionnel, appelé à l'usage |
| Test sans `import os` | `NameError` au chargement, avant tout test | Ajouter `import os` avec le `setdefault` |
| Test qui n'émet pas | Vert sans secret, faux sentiment de sécurité | Lister les routes émettrices et les modules qui les frappent |
| `SECRET_DEFAUT` conservé en clair | La valeur reste dans le dépôt | Comparer `SECRET_SHA8` au sha8 |
| Documentation « aucune valeur » non relue | Le paquet publie le secret malgré un QA PASS | Vérifier chaque ligne, y compris description et références |
| Production non déployée mais annoncée corrigée | Fausse preuve d'exploitation | Écrire « non déployé » et donner l'état réel |
| Ancienne valeur encore dans un transcript ou un `.bak` | Fuite persistante malgré le code propre | Révoquer la valeur ; ne pas publier les sauvegardes |

## 12. Checklist

- [ ] Comportement tranché par l'utilisateur, écrit dans le rapport.
- [ ] Accesseur sans valeur de repli, appelé à la signature et au démarrage.
- [ ] Tous les imports de la constante remplacés ; modules consommateurs importables.
- [ ] Outil de rotation : sha8 seul, comparaison sur le processus.
- [ ] Template et tous les générateurs : `EnvironmentFile=` sans `-` pour ce secret seulement.
- [ ] Modules de test émettant : `import os` + secret propre avant l'import.
- [ ] Documentation et paquet : sha8, date, « non déployé », phrase « aucune valeur » vérifiée.
- [ ] `env -u` → `Démarrage refusé` et `EXIT=1`.
- [ ] Tests nommés et comptés ; 0 littéral ; `skill-file-qa` PASS avec empreintes.
- [ ] Aucun déploiement ni rotation effectué sans autorisation distincte.

## Limites

- Le correctif local ne change pas la production : son unité et son processus peuvent encore porter l'ancien comportement jusqu'au déploiement.
- Une rotation révoque la valeur mais ne la retire ni des transcripts ni des sauvegardes déjà produites.
- Les secrets de test sont des fixtures : ils ne doivent jamais être réutilisés en production.
- Le sha8 empêche de recopier la valeur, il ne prouve pas qu'elle est révoquée.

## Ressources

`references/cas-2026-10-28-retrait-repli-hmac.md` — déclencheur, décisions, fichiers et empreintes, preuves rejouables, écarts constatés.
