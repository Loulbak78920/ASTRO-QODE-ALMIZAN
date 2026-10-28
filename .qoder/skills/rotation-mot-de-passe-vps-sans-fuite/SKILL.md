---
name: rotation-mot-de-passe-vps-sans-fuite
description: "Faire tourner le mot de passe d'un compte VPS sans jamais l'exposer : préflight en lecture seule (clé SSH de secours présente dans authorized_keys, `sudo -n`, `chpasswd`, `passwd -S`), génération de 32 caractères sans métacaractère shell, application uniquement sur stdin de `sudo -n chpasswd` (jamais `sudo -S`, jamais `bash -s`, jamais en argv), vérification par connexion neuve exigeant l'ancien mot de passe REFUSÉ par authentification et non par une erreur réseau, rollback automatique via la session encore ouverte, réécriture atomique du fichier secrets, puis preuve que la chaîne de déploiement charge le nouveau secret. Utiliser après une exposition de mot de passe dans un transcript, un stderr ou un argv, ou pour toute rotation planifiée, y compris quand `sudo` est NOPASSWD. 无泄漏地轮换 VPS 账户密码，绝不把密码交给 sudo -S 或 bash -s。"
---

# Rotation d'un mot de passe de compte VPS sans fuite

## Portée

Faire tourner le mot de passe SSH/sudo d'un compte Unix distant, prouver que l'ancien est révoqué, et laisser le fichier de secrets et la chaîne de déploiement cohérents — sans qu'aucune sortie ne contienne le secret.

Hors portée : rotation d'une clé d'API applicative (`MIZAN_VPS_API_KEY`), création de comptes (`administrer-comptes-production-mizan`), passage de `sshd` en clé seule (`PasswordAuthentication no`), déploiement du site (`deployer-site-sans-dol-vps`). Chacun est une opération distincte : ne pas annoncer « rotations terminées » après n'avoir traité que le mot de passe.

## 1. Invariants

1. **Le secret n'apparaît nulle part.** Ni stdout, ni stderr, ni argv, ni fichier temporaire, ni journal, ni transcript. Pas de préfixe, de suffixe ni de longueur affichés. Toute commande lancée doit être relue en pensant : « que verra le transcript si elle échoue ? ».
2. **Sur un hôte NOPASSWD, ne jamais transmettre le mot de passe du compte.** Si `sudo -n true` rend 0, `sudo -S` n'a rien à consommer : la ligne envoyée sur stdin continue vers la commande distante, et si celle-ci est `bash -s` (qui lit son script sur stdin) la ligne devient une commande que bash exécute puis réaffiche dans stderr. Utiliser `sudo -n` (ou `sudo` seul), jamais `sudo -S`.
3. **Le nouveau mot de passe n'est écrit que sur stdin de `sudo -n chpasswd`.** Pas de `echo`, pas de `printf` vers un shell, pas de `passwd` interactif, pas de fichier `.tmp` contenant le secret.
4. **Filet de secours obligatoire avant toute écriture.** La clé privée locale doit être présente dans `authorized_keys` distant (même empreinte) **et** une connexion par clé seule doit réussir `sudo -n true` (rc 0). Sans ce filet, refuser et s'arrêter : une rotation ratée sans clé verrouille le compte.
5. **Une preuve est une sortie observée.** « Ancien REFUSÉ » ne vaut que si le refus est une erreur d'authentification. Un timeout, un handshake SSL, un DNS ou un `NoValidConnectionsError` est **INCONCLUSIF** : il ne prouve pas la révocation.
6. **Confirmation humaine avant l'écriture en production.** Une rotation est une action visible et irréversible pour les autres usages du secret. Un accord donné pour une rotation ne couvre pas la suivante.
7. **Une rotation de mot de passe ne nettoie pas une fuite.** Le secret déjà exposé (transcript, sauvegarde, argv de processus) reste lisible ; on ne l'archive pas, on le révoque. Ne jamais conserver l'ancien dans un backup local du fichier de secrets.

## 2. Séquence

### 2.1 Inventorier avant de toucher

Lister qui lit le secret (`grep` du nom de clé et du nom de fichier, côté local et côté serveur) et vérifier que le fichier de secrets n'est pas suivi par Git (`git check-ignore -v <fichier>` ; si le projet n'est pas un dépôt, le dire, ne pas supposer une règle `.gitignore`). Chercher une copie en dur du secret dans les scripts : un script qui ne passe pas par le chargeur continuera de fonctionner avec l'ancien secret après la rotation.

### 2.2 Préflight en lecture seule

Sur une connexion déjà authentifiée par mot de passe :

```text
id -un
sudo -n true                     # rc 0 obligatoire
command -v chpasswd              # présent obligatoire
sudo -n passwd -S <user>         # compte verrouillé ? (L)
sudo -n sshd -T | tr A-Z a-z | grep -E 'passwordauthentication|permitrootlogin'
ssh-keygen -lf ~/.ssh/id_ed25519.pub   # empreinte locale
```

Puis, avec la clé seule (pas de mot de passe) : se connecter et exécuter `sudo -n true`. Compter les entrées de `authorized_keys` et comparer l'empreinte. **Aucun préflight partiel ne justifie de continuer.**

Vérifier aussi la cohérence du fichier de secrets : `mot_de_passe_ssh` et `mot_de_passe_permanent` portent souvent le même secret ; `mot_de_passe_temporaire` doit être vide.

### 2.3 Générer

32 caractères, au moins une majuscule, une minuscule et un chiffre, tirés de `secrets.choice` sur un alphabet sans espace ni métacaractère shell. Alphabet de référence : `A-Za-z0-9-_` (sans `0`/`O`, `1`/`l`/`I` pour la lisibilité). Ne jamais générer avec un caractère que le shell, `sudoers` ou un parseur de configuration interprète (`$`, `!`, `#`, `&`, `|`, `;`, `'`, `"`, espace).

### 2.4 Appliquer

Une seule voie : ouvrir un canal `exec_command("sudo -n chpasswd")`, écrire `<user>:<mot_de_passe>\n` sur son stdin, fermer l'écriture, lire le code de retour.

```python
stdin, out, err = client.exec_command("sudo -n chpasswd")
stdin.write(f"{user}:{mdp}\n"); stdin.flush(); stdin.channel.shutdown_write()
ok = out.channel.recv_exit_status() == 0
```

Interdits : `sudo -S`, `bash -c`, `bash -s`, `ssh host "echo ... | chpasswd"`, toute concaténation du secret dans une ligne de commande.

### 2.5 Vérifier (connexion neuve, deux fois)

1. Connexion **neuve** avec le nouveau mot de passe : doit réussir.
2. Connexion **neuve** avec l'ancien : doit lever `paramiko.AuthenticationException`. Capter **cette exception seulement** ; toute autre exception (timeout, socket, handshake) doit être rapportée `INCONCLUSIF` et relancée.

Si l'ancien est encore accepté, ce n'est pas un avertissement : c'est un échec de rotation (arrêter, rc non nul, ne pas mettre à jour le fichier de secrets).

### 2.6 Rollback

Si le nouveau mot de passe est refusé, réappliquer l'ancien via **la session encore ouverte** (elle a été authentifiée avant le changement), puis sortir en code 2. Ne pas ouvrir une nouvelle connexion avec l'ancien pour réparer : elle échouerait et le compte resterait bloqué.

### 2.7 Persister atomiquement

Lire le JSON, écrire `mot_de_passe_ssh` **et** `mot_de_passe_permanent`, vider `mot_de_passe_temporaire`, ajouter une note datée en UTC. Écrire dans `<fichier>.tmp` du même répertoire puis `Path.replace()`. Vérifier après coup : aucune `.tmp` résiduelle, rechargement du fichier rendant bien la nouvelle valeur.

### 2.8 Prouver la chaîne de déploiement

Recharger via le chargeur du projet (jamais en relisant le JSON à la main dans un one-liner), vérifier que les clés attendues sont présentes et non vides, puis ouvrir une connexion paramiko « style déploiement » et exécuter `sudo -n true`. N'afficher que des marqueurs (`OK`, `SUDO_OK`, `rc 0`). Si le déploiement utilise encore l'ancien secret, la rotation est incomplète.

### 2.9 Tracer

Consigner la date UTC de la rotation et l'avertissement NOPASSWD dans la documentation d'exploitation du projet, et mettre à jour la note de mémoire projet. Retirer la rotation de la liste des actions en attente ; ne pas y ajouter les opérations voisines non faites.

### 2.10 Nettoyer

Supprimer les `.pyc`/`__pycache__` créés par la compilation, toute fixture, tout `.tmp`, et les scripts jetables de déploiement. Vérifier qu'aucun fichier créé pendant l'opération ne contient le secret.

## 3. Critères de sortie observables

| Contrôle | Attendu |
|---|---|
| `sudo -n true` avant et après | rc 0 |
| Nouveau mot de passe, connexion neuve | accepté |
| Ancien mot de passe, connexion neuve | `AuthenticationException` (pas un timeout) |
| Fichier de secrets | `mot_de_passe_ssh` = nouveau, `mot_de_passe_permanent` = nouveau |
| `mot_de_passe_temporaire` | vide |
| `.tmp` résiduelle | aucune |
| Clé ed25519 | toujours acceptée |
| Chaîne de déploiement | charge le nouveau secret, `SUDO_OK`, rc 0 |
| Sortie complète | ne contient jamais le secret |
| Audit local (`scripts/auditer_secrets_locaux.py`) | `RESULT OK`, rc 0 |

## 4. Pièges

| Piège | Symptôme observé | Correctif |
|---|---|---|
| `sudo -S` + `bash -s` sur hôte NOPASSWD | `bash: line 1: <secret>: command not found` dans stderr, recopié dans le transcript | `sudo -n` ; ne jamais mettre un secret sur le stdin d'un shell |
| Sonde d'authentification qui attrape `Exception` | une panne réseau est rapportée « ancien REFUSÉ » et passe pour une révocation | ne capturer que `AuthenticationException` ; transport = INCONCLUSIF |
| Ancien encore accepté traité en simple `AVERTISSEMENT` | rc 0 avec un secret non révoqué | en faire un échec bloquant |
| Même secret sous deux clés | une seule clé tournée, l'autre reste valide | tourner toutes les clés qui portent le secret |
| Caractère actif dans le mot de passe | interprété par le shell ou le parseur de config | alphabet sans métacaractère |
| Rotation confondue avec les actions voisines | « tout est fait » alors que la clé d'API et `sshd` n'ont pas bougé | lister chaque rotation séparément |
| Sessions SSH déjà ouvertes | « révoqué » mais une session continue | normal ; fermer les sessions, ne pas conclure à l'échec |
| Copie résiduelle du secret (transcript, backup) | secret encore lisible après rotation | révoquer, ne pas archiver l'ancien |

## 5. Vérification locale après coup

```bash
py -3 -B scripts/auditer_secrets_locaux.py --secrets <chemin du json> --racine <racine du projet>
```

Sortie attendue (ASCII, sans secret) : `RESULT OK`, rc 0. Un `FUITE <fichier>:<ligne>` signale le secret hors du fichier de secrets ; un `ANTIPATTERN ... sudo -S` rappelle les commandes à migrer vers `sudo -n`. L'audit est **local et en lecture seule** : il ne remplace pas les contrôles distants de §2.5.

## 6. Ressources

- `scripts/auditer_secrets_locaux.py` — audit local en lecture seule (forme du JSON, `.tmp`, fuite du secret, anti-modèles `sudo -S`/`bash -s`). Aucune connexion réseau, aucun secret affiché.
- `references/cas-fuite-shell-stdin-2026-10-28.md` — chronologie et sorties verbatim de l'incident qui a motivé ce Skill, y compris les deux faiblesses de code à corriger lors d'une réutilisation.
- Implémentation de référence déjà exécutée sur ce VPS : `ASTRO-Q°ODE_SYSTEME/deploiement_vps/rotation_mot_de_passe_ovh.py` (plan par défaut, `--verifier`, `--appliquer`). La réutiliser telle quelle plutôt que d'en écrire une seconde ; si elle est modifiée, la revalider avant exécution.

## 7. Articulation avec les Skills voisins

- `administrer-comptes-production-mizan` : crée et vérifie des comptes administrateur ; exclut explicitement la rotation du mot de passe SSH — déléguer ici.
- `deployer-site-sans-dol-vps` et `verifier-journaux-nginx-vps` : décrivent `sudo -S` avec le mot de passe sur stdin. Sur un hôte où `sudo -n true` rend 0, préférer `sudo -n` ; ne pas recopier cette forme dans un nouveau script.
- `skill-file-qa` : à relancer après toute modification de ce paquet.
