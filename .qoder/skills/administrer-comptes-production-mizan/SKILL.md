---
name: administrer-comptes-production-mizan
description: "Créer et contrôler un compte administrateur Al-Mizan en production : préflight SSH et arborescence, génération et validation locale du mot de passe, transmission uniquement sur stdin à la CLI --creer-admin, réparation du répertoire secrets/ si le déploiement a changé son propriétaire, puis preuve par connexion HTTPS, appel d'une route admin et déconnexion. Utiliser pour créer un administrateur, débloquer une création de compte admin, vérifier le statut ou l'authentification d'un administrateur en production. 创建或验证生产环境管理员账户。"
---

# Administrer un compte administrateur en production

## Portée

Créer un compte admin actif dans la base SQLite de production, lever un blocage de création causé par un mauvais propriétaire de l'arborescence, vérifier réellement la connexion et une route admin, puis ranger le secret localement.

Hors portée : déploiement du site (`deployer-site-sans-dol-vps`), SMTP et double validation, rotation du mot de passe SSH, réinitialisation du mot de passe administrateur, revue des comptes entreprise/public.

## 1. Invariants

1. **Le mot de passe ne circule que sur stdin.** Toujours `--mot-de-passe-stdin`. Jamais `--mot-de-passe`, jamais en argument de `ssh`, de `sudo` ou d'un interpréteur, jamais en variable exportée, jamais affiché, journalisé ou recopié dans un fichier du dépôt. Ne pas utiliser `set -x`, `ssh -v` ni un wrapper qui journalise ses arguments.
2. **Confirmer avant toute écriture en production.** Créer un compte est une action partagée et visible ; un accord donné une fois ne vaut pas pour les comptes suivants.
3. **La vérification est en lecture seule**, suivie d'une déconnexion ; la révocation n'est acquise qu'après un 401 obtenu avec l'ancien cookie.
4. **Aucune affirmation sans sortie observée.** Les limites (SMTP, agrégats publics) sont énoncées, pas masquées.
5. **Le secret ne quitte pas `secrets/`.** Dossier déjà ignoré par Git, fichier à ACL restreinte.
6. **Un échec ne laisse pas de compte.** L'INSERT est dans un bloc transactionnel : en cas d'exception, le compte est annulé (constaté : 0 compte après la panne). Recompter avant de réessayer.

## 2. Repères (valeurs constatées le 27/10/2026, à revérifier)

| Élément | Valeur |
| :--- | :--- |
| Source locale | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME` |
| Racine VPS | `/opt/al-mizan/ASTRO-Q°ODE_SYSTEME` |
| Service | `al-mizan-api-vps` (systemd), utilisateur observé `ubuntu` |
| CLI comptes | `module_comptes_utilisateurs_mizan.py` (module de la racine VPS) |
| Base | `memoire_aq/almizan_comptes.sqlite3` (défaut `MIZAN_DB_PATH` sinon) |
| Secret local | `ASTRO-Q°ODE_SYSTEME\secrets\administrateur_production_al_mizan.json` |
| Documentation | `ASTRO-Q°ODE_SYSTEME\docs\COMPTES_ET_SECURITE.md` §10.1 |
| Identité SSH | compte `ubuntu` ; réutiliser le mécanisme de `deployer-site-sans-dol-vps` |

Le module local `python` est l'alias Microsoft Store et échoue ; utiliser `py -3` en local et `python3` sur le VPS.

## 3. Règles de validation imposées par le module

| Champ | Règle | Message d'échec |
| :--- | :--- | :--- |
| Email | format valide, ≤ 254, domaine non-IP | `Format d'adresse email invalide.` |
| Handle | 3–32, minuscules/chiffres/`._-`, pas de séparateur aux extrémités, pas de `..`, `__`, `--`, pas réservé | `Identifiant : 3 à 32 caractères…` |
| Nom affiché | 2–80 caractères, espaces normalisés, pas de caractères de contrôle | `Le nom affiché doit contenir entre 2 et 80 caractères.` |
| Mot de passe | 12–128, au moins une lettre et un chiffre, absent de la liste des mots courants, ne contient ni la partie locale de l'email (≥ 3 car.) ni le handle (≥ 3 car.) | `Le mot de passe doit contenir entre 12 et 128 caractères.` / `…au moins une lettre et un chiffre.` / `Le mot de passe ne doit pas contenir votre identifiant.` |
| Unicité | email **ou** handle comparé déjà présent | code `COMPTE_EXISTANT` (409) |

Handles réservés (extrait) : `admin`, `administrateur`, `root`, `system`, `support`, `mizan`, `al-mizan`, `imam8mahdi`, `compte`, `contact`. Choisir un handle distinct, ex. `archonte`.

Valider **localement** chaque champ avant l'envoi : un rejet côté serveur renvoie `DONNEES_INVALIDES` ou `MOT_DE_PASSE_FAIBLE` avec rc 2 et n'écrit rien, mais fait perdre un aller-retour.

## 4. Séquence

### 4.1 Préflight (lecture seule)

```bash
ssh ubuntu@<hôte> 'systemctl cat al-mizan-api-vps | grep -E "^(User|Group)="; \
  ls -ld /opt/al-mizan /opt/al-mizan/ASTRO-Q°ODE_SYSTEME; \
  ls -ld /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets 2>&1; \
  stat -c "%U:%G %a %n" /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/memoire_aq/almizan_comptes.sqlite3 2>&1'
ssh ubuntu@<hôte> 'cd /opt/al-mizan/ASTRO-Q°ODE_SYSTEME && python3 module_comptes_utilisateurs_mizan.py --lister-utilisateurs'
```

Critères : racine `ubuntu:ubuntu`, base `ubuntu:ubuntu 600`, CLI présente. Si la racine est `root:root` ou si `secrets/` est absent avec une racine non inscriptible → appliquer 4.4 avant toute création.

Contrôler aussi le contrat de drapeaux de la CLI, en local (source) et sur le VPS (module réellement exécuté) :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B module_comptes_utilisateurs_mizan.py --help 2>&1 | grep -E -- "--creer-admin|--mot-de-passe-stdin|--email|--handle|--nom"; echo "RC=${PIPESTATUS[0]}"
ssh ubuntu@<hôte> 'cd /opt/al-mizan/ASTRO-Q°ODE_SYSTEME && python3 -B module_comptes_utilisateurs_mizan.py --help' | grep -E -- '--creer-admin|--mot-de-passe-stdin|--email|--handle|--nom'; echo "RC=${PIPESTATUS[0]}"
```

Attendu : `RC=0` et les cinq drapeaux dans les deux sorties. Un écart entre local et VPS signale une version déployée différente : arrêter et aligner via `deployer-site-sans-dol-vps` avant toute création. `-B` évite d'écrire `__pycache__` dans le dépôt. La commande locale a été exécutée le 27/10/2026 (`RC=0`) ; la variante VPS reste à exécuter au premier préflight.

Décider ensuite, avant de générer quoi que ce soit :

- Le couple email/handle demandé figure déjà dans `--lister-utilisateurs` → **ne pas créer**, passer à 4.5 pour vérifier l'accès existant, et ne jamais réécrire le secret de ce compte.
- Compte absent avec un secret existant → reprise du compte (4.2 puis 4.3), sans changer le mot de passe stocké.
- Compte existant mais secret introuvable → ne pas créer de doublon ; la réinitialisation du mot de passe est hors portée et doit être décidée explicitement.
- Nouveau compte → fichier de secret distinct et mot de passe neuf, jamais celui d'un autre compte.

### 4.2 Générer et valider le mot de passe localement

Deux cas, à trancher avec la décision de 4.1 :

- **Reprise** (secret existant, compte absent de la base) : relire le fichier existant et valider son mot de passe, sans jamais le réécrire.
- **Nouveau compte** : générer dans un pilote hors dépôt (`%TEMP%`), écrire le JSON dans un fichier **propre au compte** sous `secrets/`, et n'afficher que le chemin et la longueur — jamais la valeur.

Ne jamais écraser un fichier de secret existant. `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\administrateur_production_al_mizan.json` porte le mot de passe du compte `archonte` déjà en production : le remplacer avant une création qui échoue en `COMPTE_EXISTANT` laisserait un fichier incompatible avec la base. Pour un nouvel administrateur, utiliser un fichier distinct sous `secrets/`, nommé d'après le handle, et un mot de passe neuf ; ne jamais réutiliser le secret d'un autre compte.

```python
import json, secrets, string
mdp = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(28))
# vérifier : 12 <= len(mdp) <= 128, une lettre et un chiffre,
# pas la partie locale de l'email (>=3) ni le handle (>=3), pas un mot courant
```

Forme du fichier (clés constatées) : `email`, `handle`, `nom_affichage`, `mot_de_passe`, `role`, `service`, `cree_le`, `note`. L'écrire avec `encoding="utf-8"`.

Appliquer l'ACL **immédiatement après l'écriture**, avant 4.3, pour ne pas laisser le secret avec les ACL héritées :

```powershell
$secret = "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\administrateur_production_al_mizan.json"
icacls $secret /inheritance:r /grant:r "$env:USERNAME:(F)"
icacls $secret
```

Attendu : un seul principal (`<machine>\<compte>:(F)`), aucun `(I)` hérité. Adapter `$secret` au fichier du compte concerné ; ne jamais estimer l'état d'une ACL depuis un `ls` Git Bash.

### 4.3 Créer le compte (secret sur stdin)

Le mot de passe est relu depuis le fichier local, transmis par here-string à `ssh`, puis la variable est effacée. La here-string ajoute un saut de ligne ; la CLI lit une ligne et la nettoie (`rstrip("\r\n")`), donc c'est compatible — mais le mot de passe lui-même ne doit contenir aucun saut de ligne.

La commande ci-dessous rejoue l'identité constatée (`archonte`). Pour un nouvel administrateur, remplacer email, nom, handle et le chemin du secret par ceux du nouveau compte, avec un mot de passe neuf.

```bash
set +x
MDP="$(py -3 -c 'import json,io;print(json.load(io.open(r"C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\administrateur_production_al_mizan.json",encoding="utf-8"))["mot_de_passe"],end="")')"
ssh ubuntu@<hôte> 'cd /opt/al-mizan/ASTRO-Q°ODE_SYSTEME && python3 module_comptes_utilisateurs_mizan.py --creer-admin --email admin@al-mizan.world --nom "Administration Al-Mizan" --handle archonte --mot-de-passe-stdin' <<< "$MDP"
unset MDP
```

Sorties attendues :

- rc 0 et JSON `{"cree": true, "utilisateur": {...}}` avec `type_compte: admin`, `statut: actif`, `email_verifie: true` (le compte est créé actif, aucun email n'est envoyé).
- rc 2 et `{"succes": false, "code": ..., "message": ...}` : erreur métier, rien n'est écrit ; corriger le champ concerné. `COMPTE_EXISTANT` n'est pas une erreur de champ : le compte existe déjà — ne pas réessayer, ne pas réécrire le secret, passer à 4.5.
- rc 1 et traceback : erreur non gérée, voir 4.4. Recompter les comptes avant de relancer.

Le compte admin reçoit `verification_niveau = 0`, `score_confiance = 0.35` (observé) : c'est normal, ne pas prétendre à un niveau vérifié.

### 4.4 Réparer `secrets/` inaccessible (incident vérifié)

Symptôme : traceback dans `creer_admin → _journaliser → hacher_ip → empreinte → _secret_garde → mkdir`, puis :

```
PermissionError: [Errno 13] Permission denied: '/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets'
```

Cause observée : après l'extraction de la mise à jour, la racine était en `root:root` alors que le service tourne en `ubuntu` et que le module de garde doit créer `secrets/`. Le mécanisme exact de cette non-application n'a pas été instrumenté.

Tester d'abord si `sudo` est déjà autorisé sans mot de passe. Ne jamais envoyer le mot de passe SSH à l'aveugle : lors du déploiement, le cache `sudo` actif et un `echo … | sudo -S` ont fait apparaître le mot de passe dans un message d'erreur.

```bash
ssh ubuntu@<hôte> 'sudo -n true && echo sudo_sans_mdp'
```

Si la commande échoue, ouvrir une session interactive (`ssh -t`) et saisir le mot de passe dans l'invite de `sudo`, jamais sur la ligne de commande.

Réparer au minimum nécessaire — changer le propriétaire de la racine et créer `secrets/`, **sans `-R`** :

```bash
ssh ubuntu@<hôte> 'sudo chown ubuntu:ubuntu /opt/al-mizan/ASTRO-Q°ODE_SYSTEME && \
  sudo install -d -m 700 -o ubuntu -g ubuntu /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets && \
  ls -ld /opt/al-mizan/ASTRO-Q°ODE_SYSTEME /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets'
```

Un `chown -R` est plus large que l'incident : il changerait aussi les sauvegardes `root:root 600`. Si d'autres chemins restent non inscriptibles pour le service, les lister avant de les corriger explicitement :

```bash
ssh ubuntu@<hôte> 'find /opt/al-mizan/ASTRO-Q°ODE_SYSTEME -maxdepth 2 ! -user ubuntu -printf "%u:%g %m %p\n" | head -50'
```

Vérifier ensuite `mizan_garde_secret.key` (attendu `ubuntu:ubuntu 600`) et la base (`ubuntu:ubuntu 600`). Le service n'a pas eu besoin d'être redémarré lors de l'incident ; ne redémarrer que si un état d'erreur est observé. Corriger aussi la cause dans le flux de déploiement (voir `deployer-site-sans-dol-vps`, étape de transfert).

### 4.5 Prouver l'accès (lecture seule)

Pilote temporaire hors dépôt, supprimé après usage ; il lit le secret local, gère le cookie de session, et n'imprime que codes HTTP, type de compte et booléens.

| Contrôle | Attendu |
| :--- | :--- |
| `POST /api/v1/comptes/connexion` | 200, `utilisateur.type_compte = admin` |
| `GET /api/v1/admin/devis` avec session | 200, `succes: true` |
| `GET /api/v1/admin/devis` sans session | 401 (contrôle négatif) |
| `GET /api/v1/comptes/moi` | 200, `statut: actif`, `email_verifie: true` |
| `GET /api/v1/comptes/sessions` | 200, une session courante |
| `GET /api/v1/admin/statistiques` | 200, `par_type: {"admin": 1}` |
| `POST /api/v1/comptes/deconnexion` | 200 |
| Rejouer `GET /api/v1/comptes/moi` avec l'ancien cookie | 401 ; sans ce contrôle, ne pas affirmer que la session est révoquée |
| Pages `/connexion` et `/compte` | 200, cartes admin visibles |
| `journalctl -u al-mizan-api-vps` sur la fenêtre | aucune erreur |

### 4.6 Vérifier le rangement du secret

- Fichier sous `secrets/` (déjà ignoré par `.gitignore`), jamais hors de ce dossier.
- ACL restreinte appliquée en 4.2 ; la revérifier et consigner un seul principal sans héritage.

```powershell
icacls "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\administrateur_production_al_mizan.json"
```

Attendu : un seul principal (`<machine>\<compte>:(F)`), aucun `(I)` hérité. Ne jamais estimer l'état d'une ACL depuis un `ls` Git Bash.

## 5. Pièges

| Piège | Comportement observé | Parade |
| :--- | :--- | :--- |
| Handle `admin` | rejeté, réservé | utiliser `archonte` ou un handle libre |
| Séparateurs consécutifs / aux extrémités | rejet `handle_valide` | 3–32, un seul `._-` entre segments |
| Mot de passe contenant l'email ou le handle | `MOT_DE_PASSE_FAIBLE` | générer aléatoirement puis tester ces inclusions |
| Base de production en `root:root` | `PermissionError` sur `secrets/`, rc 1 | 4.4, puis recompter avant relance |
| Exception non gérée | traceback sans JSON métier | ne pas conclure à une écriture partielle : sur cette panne, le compte a été annulé |
| `sudo` avec cache de mot de passe | un `echo … \| sudo -S` peut faire apparaître le mot de passe dans la sortie (observé lors du déploiement) | tester `sudo -n true` avant toute réparation ; sinon `ssh -t` et saisie interactive |
| `python` local | alias Microsoft Store en échec | `py -3` |
| Here-string | ajoute un `\n` | accepté par la CLI ; interdit seulement les mots de passe multilignes |
| Mot de passe en argument | visible dans l'historique et `ps` | uniquement `--mot-de-passe-stdin` |

## 6. Limites et effets connus

- `GET /api/v1/comptes/statut_public` compte les administrateurs dans `comptes_actifs` (observé `1`, avec `particuliers: 0`). Ne pas présenter cet agrégat comme un nombre d'utilisateurs métier.
- La révocation de session après déconnexion n'est prouvée que par le 401 de l'ancien cookie (4.5) ; le seul code 200 du logout ne suffit pas.
- SMTP non configuré : la double validation par email est inutilisable ; ne pas l'activer depuis l'espace compte.
- La création ne déclenche aucun email ; `email_verifie` est forcé à vrai pour un admin.
- La rotation du mot de passe administrateur et du mot de passe SSH n'est pas automatique ; elle demande une décision explicite.

## 7. Checklist finale

- [ ] Préflight : identité du service, racine `ubuntu:ubuntu`, base `600`, `secrets/` présent ou réparé sans `chown -R`.
- [ ] CLI : `--help` rc 0 et cinq drapeaux identiques en local et sur le VPS ; sinon arrêt et alignement.
- [ ] Décision prise avant génération : compte existant → aucun secret réécrit ; nouveau compte → fichier et mot de passe propres.
- [ ] Compte compté avant création ; zéro écriture après un échec métier.
- [ ] Mot de passe généré localement, validé, transmis par stdin seulement ; ACL appliquée dès l'écriture.
- [ ] Création rc 0, profil `admin`, `actif`, `email_verifie: true`.
- [ ] Connexion HTTPS 200 type `admin` ; `/api/v1/admin/devis` 200 ; anonyme 401.
- [ ] Déconnexion 200, puis ancien cookie refusé en 401.
- [ ] Secret dans `secrets/`, ACL à un seul principal, valeur jamais affichée.
- [ ] Limites SMTP et agrégat public énoncées dans le rapport.

## Références

- `references/preuves-session-2026-10-27.md` — sorties brutes, traceback, horodatage et limites de la session source.
- `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\docs\COMPTES_ET_SECURITE.md` — §10.1 CLI d'administration.
- Skill `deployer-site-sans-dol-vps` — déploiement, sauvegarde et étape `chown` liée au blocage constaté.
