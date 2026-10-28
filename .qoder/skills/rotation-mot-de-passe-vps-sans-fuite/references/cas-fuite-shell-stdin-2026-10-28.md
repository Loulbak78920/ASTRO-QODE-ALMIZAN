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

## 8. Correctifs appliqués au script de référence (2026-10-28, hors production)

Les constats de §6 décrivent la version `0aa8b05a25d79878…` ; la version issue de ces trois
correctifs portait SHA-256 `a9d133d7db58b07afbafd4e17c7c4fbb156ce9628436c2b8eb829c052b4b8d37`,
10 463 octets, et ne présentait plus ces faiblesses.

1. `_accepter_mot_de_passe` (exception large) est remplacée par `_sonde_auth` : seule
   `paramiko.AuthenticationException` rend `False` (refus) ; transport, socket, handshake
   et toute autre exception rendent `None` (INCONCLUSIF).
2. Ancien mot de passe encore accepté : échec bloquant rc 2, secrets locaux non modifiés ;
   un `INCONCLUSIF` sur l'ancien est lui aussi un échec (rc 2), jamais une révocation.
3. Filet de secours obligatoire : le préflight exige `_accepter_cle` à `True`, c'est-à-dire
   connexion par clé seule **et** `sudo -n true` rc 0 ; sinon rc 1 sans aucune écriture.
   `_accepter_cle` ne capture plus que `AuthenticationException`, le reste est INCONCLUSIF.

Vérification : 35 assertions hors production, 35 PASS, 0 FAIL, E/S réseau remplacées —
table de décision de `rotation()` (clé absente/inconclusive, nominal, nouveau refusé puis
restauration par la session ouverte, nouveau inconclusif, ancien encore accepté, ancien
inconclusif, `chpasswd` rc≠0, clé post-rotation), tri-état réel des deux sondes et
`verifier()`. Aucune connexion au VPS, aucune rotation exécutée, fichier de secrets réel
non lu. À ce stade, `AutoAddPolicy` était encore en place ; voir §9.

## 9. Politique de clé d'hôte (2026-10-28, corrigée et exercée)

`AutoAddPolicy` acceptait n'importe quelle clé présentée : un interposé réseau pouvait
recevoir le mot de passe transmis à `chpasswd`. Le fichier porte désormais
SHA-256 `5d27b340481a1dc9e6b10014be1aeb4795dd98a50659a9d0cadab437592fe46c`, 11 939 octets.

Modifications :

1. `_ouvrir()` crée le client avec `load_system_host_keys()` (sous Windows :
   `~/.ssh/known_hosts`) et `RejectPolicy()` à la place de `AutoAddPolicy`.
2. `_verifier_cle_hote()` relit la clé réellement négociée
   (`get_transport().get_remote_server_key()`), calcule l'empreinte OpenSSH
   (`SHA256:` + base64 sans `=` du SHA-256 des octets de la clé) et exige qu'elle
   corresponde à `EMPREINTES_HOTE` pour son type. Une clé inconnue, d'un type non listé
   ou d'empreinte divergente lève `CleHoteInattendue` après fermeture du canal.
3. `_client` et `_accepter_cle` passent par ce contrôle ; `CleHoteInattendue` rend
   `False` (REFUSE) dans `_accepter_cle`, donc l'échec bloque la rotation au préflight.
4. `main()` attrape `paramiko.SSHException` et rend rc 1 avec `RESULT FAIL : <message>`,
   sans trace Python.

Empreintes épinglées (hôte `51.222.159.232`, lues dans `known_hosts` et confirmées par
`ssh-keyscan` le 2026-10-28, identiques des deux côtés) :

| Type | Empreinte |
|---|---|
| `ssh-ed25519` | `SHA256:UA6qiQRyKtkzxcH8yg8Ga1TPfQq5ZnF2bpmRZknSD0w` |
| `ecdsa-sha2-nistp256` | `SHA256:ETIJFp39VUDqnO0R16apxH/9YkMNCHyprIWatV5uvpw` |
| `ssh-rsa` | `SHA256:XHRSl0rYKQ/CRMwel09oXzKay7PuZmDltvIfdku8eEk` |

Vérification hors ligne : 24 assertions PASS (chargement `known_hosts`, `RejectPolicy`,
clé épinglée acceptée, clé inconnue rejetée et canal fermé, type non listé rejeté,
`_client` accepté/rejeté, `_accepter_cle` à `True`/`False`/`False`/`None`, table de
décision de `rotation()`), puis 8 assertions de régression PASS (tri-état des sondes,
`verifier()` rc 1/1/0). Aucune rotation exécutée, fichier de secrets réel non lu.

Vérification en lecture seule sur l'hôte réel : `_accepter_cle` rend `True`
(`CLE_HOTE_ET_SUDO OK`) ; en remplaçant l'empreinte épinglée par une valeur arbitraire,
la même sonde rend `False` (`PIN_NEGATIF REFUSE`), ce qui prouve que l'épinglage est
actif et non contourné par `known_hosts`.
