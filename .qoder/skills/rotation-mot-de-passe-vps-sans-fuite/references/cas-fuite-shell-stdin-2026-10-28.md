# Cas : fuite du mot de passe sudo dans le stderr d'un déploiement (2026-10-28)

Source : session Qoder `9948e777-3bfe-4fbe-81f2-f538f0479ee3` (« 创建可复用技能 »), lue le 2026-10-28 avec `turnLimit=20`, `hasMoreBefore=false`, `revision=45`, `runtimeState=running`. Les secret est remplacé partout par `<secret>`. Les heures des messages sont en UTC ; les sorties d'outils sont horodatées par les estampilles qu'elles affichent.

## 1. Chronologie

| Heure (UTC) | Événement | Preuve |
|---|---|---|
| 2026-10-27T23:53:52Z | L'utilisateur demande de corriger deux défauts puis de redéployer | message utilisateur |
| 2026-10-28, déploiement estampillé `20261028T000644Z` | Le déploiement réussit (`RESULT OK`) mais le stderr contient la ligne ci-dessous | sortie d'outil |
| même tour | L'agent rapporte spontanément : « Un incident à signaler : le mot de passe sudo a été renvoyé en clair dans le stderr de la session » | message assistant |
| 2026-10-28T00:21:44Z | L'utilisateur demande de préparer la rotation ; l'agent écrit l'outil et exécute les contrôles en lecture seule | message + sorties |
| 2026-10-28T00:24:30Z | L'utilisateur autorise `--appliquer` ; rotation rc 0 et vérifications | message + sortie |
| 2026-10-28T00:27:36Z | Tour suivant : rotation de `MIZAN_VPS_API_KEY` — **hors portée** de ce Skill, encore en cours à la lecture | message |

Aucune correction utilisateur n'a été nécessaire sur la rotation : la fuite a été détectée et signalée par l'agent lui-même, et la rotation a été autorisée en un seul tour.

## 2. La fuite (verbatim)

Ligne observée dans la sortie du déploiement, telle quelle hors secret :

```text
STDERR: bash: line 1: <secret>: command not found
```

Le mot de passe a donc été lu par `bash` comme **une ligne de script**, exécuté comme nom de commande, puis réaffiché par bash dans son message d'erreur — donc dans le transcript. Le secret contenait des caractères actifs (`!`, `#`), ce qui rendait l'interprétation certaine. Deux causes cumulées :

1. sur cet hôte `sudo` est NOPASSWD, donc `sudo -S` ne consomme pas la ligne envoyée sur stdin ;
2. la commande distante était un shell lisant son script sur stdin (`bash -s`), qui a exécuté cette ligne.

Le déploiement lui-même a réussi (`INSTALL rc=0`, 6 fichiers `MATCH`) : la fuite est un effet de bord silencieux, pas une erreur de déploiement. C'est pourquoi seul un examen explicite du stderr la révèle.

## 3. Contrôles en lecture seule avant rotation (verbatim)

```text
user/id: ubuntu
1000
sudo -n: rc=0
sshd auth: maxauthtries 6
permitrootlogin without-password
pubkeyauthentication yes
passwordauthentication yes
authorized_keys: present n=1
passwd tools: /usr/bin/passwd
/usr/sbin/chpasswd
/usr/bin/shred
last chpasswd in auth.log: 1
locked: ubuntu P 2026-10-24 0 99999 7 -1
```

Clé locale ↔ `authorized_keys` distant : même empreinte `SHA256:560+Ro99…`, une entrée. L'agent a aussi relevé que `mot_de_passe_ssh` et `mot_de_passe_permanent` portaient le **même** secret compromis.

Plan de l'outil (aucune modification), hôte remplacé par `<hote>` :

```text
PLAN (aucune modification ; relancer avec --appliquer)
  hote ................... <hote>
  utilisateur ............ ubuntu
  password auth courante . OK
  sudo -n ................ OK
  chpasswd ............... OK
  cle ed25519 ............ OK
  secrets ................ <...>\secrets\ovh_vps_ssh.json
  actions ................ sudo -n chpasswd (stdin) ; verification par connexion neuve ;
                           refus de l'ancien ; mise a jour atomique du JSON local
rc=0
```

## 4. Rotation exécutée (verbatim)

```text
PREFLIGHT
  utilisateur ............ ubuntu
  sudo -n ................ OK
  chpasswd ............... OK
  cle ed25519 ............ OK
Nouveau mot de passe ... OK (connexion independante)
Ancien mot de passe .... REFUSE
secrets locaux ......... A JOUR
cle ed25519 ............ OK
RESULT OK
RC=0
```

Note datée inscrite dans le fichier de secrets : `2026-10-28T00:25:40Z`. Contrôle post-rotation de la chaîne de déploiement rapporté : chargeur du projet → clés attendues non vides ; connexion paramiko « style déploiement » → `ubuntu | SUDO_OK | rc 0`.

Documentation mise à jour au même moment, `docs/EXPLOITATION_VPS.md:68` :

> Sur ce VPS, `ubuntu` dispose de `sudo` **sans mot de passe** (`sudo -n true` → 0). Ne jamais lui passer le mot de passe du compte : `sudo -S` le consomme, et un `bash -s` le prendrait pour une commande et le réafficherait dans stderr (incident du 2026-10-28). Utiliser `sudo -n` ou `sudo` seul.

## 5. Réexamen local du 2026-10-28

Lecture seule, aucune valeur de secret affichée :

```text
keys ['hote', 'mot_de_passe_permanent', 'mot_de_passe_ssh', 'mot_de_passe_temporaire', 'note', 'user']
vide temporaire True
ssh==permanent True
note_prefix Mot de passe tourne
tmp_exists False
```

Cohérent avec la sortie de rotation. Deux réserves :

- `secrets/ovh_vps_ssh.json` porte un `mtime` du 2026-10-28 01:25, **postérieur** à la rotation de 00:25:40Z : une autre session active a modifié le fichier après coup (la session source est encore `running`). Les invariants ci-dessus restent vrais à l'instant de la lecture.
- `ASTRO-Q°ODE_SYSTEME` **n'est pas un dépôt Git** (`fatal: not a git repository`) : on ne peut pas affirmer que `secrets/` est ignoré par Git. Dans un projet versionné, le vérifier avec `git check-ignore -v`.

## 6. Faiblesses de l'implémentation de référence (lecture de code, non exercées)

Fichier lu : `ASTRO-Q°ODE_SYSTEME/deploiement_vps/rotation_mot_de_passe_ovh.py`, 8 908 octets, SHA-256 `0aa8b05a25d79878…` (préfixe), `mtime` 2026-10-28 01:23. Ce `mtime` est **postérieur** à l'exécution de 00:24 : la version lue n'est donc pas prouvablement celle qui a tourné ; seule la sortie verbatim de §4 atteste l'exécution.

1. `_accepter_mot_de_passe` (l. 61-68) attrape `Exception` et rend `False`. Un timeout ou un handshake raté est donc indiscernable d'un refus d'authentification : la ligne `Ancien mot de passe .... REFUSE` peut être un faux positif de révocation. Correctif attendu : ne capturer que `paramiko.AuthenticationException`, et traiter le reste comme `INCONCLUSIF`.
2. Ancien mot de passe encore accepté (l. 176-177) : simple `AVERTISSEMENT`, puis `RESULT OK` et rc 0 (l. 185). Une rotation non effective peut donc être rapportée comme réussie. Correctif attendu : en faire un échec bloquant.

Ces deux points sont des constats de lecture, **pas** des incidents observés dans la session.

## 7. Classement des affirmations

| Affirmation | Niveau |
|---|---|
| La ligne de stderr contenant le secret a été produite | REPRODUCED (sortie d'outil verbatim) |
| La rotation a rendu l'ancien mot de passe refusé et rc 0 | REPRODUCED (sortie verbatim) |
| Les préflight `sudo -n`, `chpasswd`, clé et `sshd` étaient verts | REPRODUCED (sortie verbatim) |
| La règle NOPASSWD a été consignée dans la doc | DOCUMENTED (`EXPLOITATION_VPS.md:68`) |
| Les deux faiblesses de code ci-dessus | INFERRED (lecture), non exercées |
| Le fichier de secrets actuel est cohérent avec la rotation | REPRODUCED (réexamen local), avec réserve de `mtime` |

Aucune preuve visuelle ni aucun test de connexion n'a été refait ici : ne pas le sous-entendre.
