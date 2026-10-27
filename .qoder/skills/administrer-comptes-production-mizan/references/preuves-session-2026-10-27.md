# Preuves — création du compte administrateur de production (27/10/2026)

Source : session Qoder `55f63550-7c8d-4f9e-b0a9-e73686cc2765`, titre « Mettre à jour le site web ». Snapshot lu le 27/10/2026 : `revision` 709, `runtimeState: running`, `hasMoreBefore: true`. Les messages couverts ici sont ceux du tour `02a63c12-a163-41fe-a415-77cef50b1755`, déclenché par le message utilisateur « Créer un compte administrateur en production » (2026-10-27T05:15:01Z). Aucune valeur de mot de passe, de jeton ou de cookie n'est reproduite.

## 1. Chronologie observée

| Heure (UTC) | Événement | Preuve |
| :--- | :--- | :--- |
| 05:15 | Inspection du module : signatures `creer_admin`, `_lire_mot_de_passe`, règles de validation | lectures du module de comptes et du module de garde |
| ~05:16 | Première création : rc 1, traceback `PermissionError` sur `secrets/` | sortie `creation_rc: 1` |
| ~05:17 | Diagnostic : racine `/opt/al-mizan/ASTRO-Q°ODE_SYSTEME` en `root:root` | `ls -ld` |
| ~05:17 | Réparation : `chown -R ubuntu:ubuntu` + `secrets/` en 700 | `rc= 0`, `drwx------ ubuntu ubuntu … secrets` |
| 05:17:48 | Création réussie : `id 1`, handle `archonte`, `admin`, `actif` | JSON de la CLI + base |
| ~05:18 | Connexion HTTPS 200 type admin, `/api/v1/admin/devis` 200, déconnexion 200 | sortie de vérification |
| 05:19:34 | Fin du tour ; aucun redémarrage du service | `NRestarts=0` |
| 05:19:58 | Nouveau tour : demande de vérification du statut et de l'authentification | message utilisateur |
| 05:20:26 | `/comptes/moi`, `/comptes/sessions`, `/admin/statistiques`, page `/compte` vérifiés | sortie du pilote |

## 2. Échec initial (verbatim, tronqué)

```
ssh_user: ubuntu
comptes_existants: 0 admins: 0
creation_rc: 1
creation_echec: Traceback (most recent call last):
  File "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/module_comptes_utilisateurs_mizan.py", line 1534, in <module>
    raise SystemExit(main())
  File "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/module_comptes_utilisateurs_mizan.py", line 1497, in main
    profil = gestionnaire.creer_admin(
  File "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/module_comptes_utilisateurs_mizan.py", line 564, in creer_admin
    self._journaliser(conn, "admin_cree", user_id, f"user:{user_id}", "succes", hacher_ip(ip))
  File "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/module_garde_cybernetique_mizan.py", line 79, in hacher_ip
    return empreinte(ip or "inconnue", "ip")
  File "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/module_garde_cybernetique_mizan.py", line 75, in empreinte
    return hmac.new(_secret_garde(), message, hashlib.sha256).hexdigest()
  File "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/module_garde_cybernetique_mizan.py", line 60, in _secret_garde
    chemin.parent.mkdir(parents=True, exist_ok=True)
  File "/usr/lib/python3.12/pathlib.py", line 1313, in mkdir
    os.mkdir(self, mode)
PermissionError: [Errno 13] Permission denied: '/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets'
```

Enseignements :

- L'exception sort du bloc `try` qui ne capture que `ErreurComptes` : rc 1 et traceback, sans JSON métier.
- `comptes_existants: 0` **après** l'échec : l'INSERT a été annulé par le bloc transactionnel, la relance est sûre.
- Les numéros de ligne sont ceux du fichier de production à cette date ; les citer comme repères, pas comme ancres stables.

## 3. Diagnostic et réparation

Inspection :

```
ls: cannot access '/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets': No such file or directory
drwxr-xr-x  3 root   root    4096 Oct 24 19:29 /opt
drwxr-xr-x  7 ubuntu ubuntu  4096 Oct 25 02:54 /opt/al-mizan
drwxr-xr-x 11 root   root   12288 Oct 27 05:13 /opt/al-mizan/ASTRO-Q°ODE_SYSTEME
uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu)
```

Au constat (05:17), la racine appartient à `root` et son horodatage suit l'extraction de la mise à jour (05:13), alors que le service tourne en `ubuntu` : `_secret_garde()` ne peut pas créer son répertoire. Le lien causal exact avec l'extraction n'a pas été instrumenté ; la chronologie ci-dessus est ce qui a été observé.

Après réparation :

```
rc= 0
drwxr-xr-x 12 ubuntu ubuntu 12288 Oct 27 05:17 /opt/al-mizan/ASTRO-Q°ODE_SYSTEME
drwx------  2 ubuntu ubuntu  4096 Oct 27 05:17 /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets
```

Le runbook de déploiement prévoit un `chown` (section 5.3) ; après l'extraction, la racine était néanmoins en `root:root` (constat ci-dessus). La raison exacte de cette non-application n'a pas été observée dans cette session.

## 4. Création réussie et contrôles (verbatim)

```
ssh_user: ubuntu
comptes_existants: 0 admins: 0
creation_rc: 0
profil: {'id': 1, 'handle': 'archonte', 'type_compte': 'admin', 'statut': 'actif'}
connexion_http: 200 type: admin code: None
admin_devis_http: 200 succes: True
deconnexion_http: 200
stats_publiques: {'comptes_actifs': 1, 'particuliers': 0, 'entreprises': 0, 'secteur_public': 0, 'domaines_verifies': 0}
secrets: C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\administrateur_production_al_mizan.json
```

État du service et des permissions :

```
ubuntu:ubuntu 600 32 /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/secrets/mizan_garde_secret.key
ubuntu:ubuntu 600 118784 /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/memoire_aq/almizan_comptes.sqlite3
active
NRestarts=0
[(1, 'archonte', 'admin', 'actif', 1)]
```

Sortie de vérification (tour suivant, 05:20:26) :

```
authentification: 200 code: None
profil:
  id = 1
  handle = archonte
  nom_affichage = Administration Al-Mizan
  type_compte = admin
  statut = actif
  email = admin@al-mizan.world
  email_verifie = True
  verification_niveau = 0
  domaine_verifie = None
  double_validation = False
  score_confiance = 0.35
sessions: 200 nombre: 1
admin_statistiques: 200 succes: True
page_compte: {'carte_admin': True, 'bouton_devis_admin': True, 'bouton_verifs': True, 'carte_devis_client': True}
deconnexion: 200
secrets_fichier: {'octets': 381, 'gitignore': True}
```

Contrôle négatif observé lors du tour de déploiement précédent : `admin devis anonyme 401`.

## 5. Contrat de la CLI (extraits du code lu)

- `--creer-admin` exige `--email`, `--nom` et `--handle` ; sinon `SystemExit`.
- `--mot-de-passe-stdin` lit une ligne sur stdin et la nettoie ; `--mot-de-passe` existe mais est explicitement déconseillé (historique shell) ; sinon double saisie `getpass`.
- Le compte est inséré avec `type_compte='admin'`, `statut='actif'`, `email_verifie=1`, mot de passe haché ; aucun email n'est envoyé.
- Erreurs métier : `DONNEES_INVALIDES`, `MOT_DE_PASSE_FAIBLE`, `COMPTE_EXISTANT` (409), retour rc 2 avec JSON `succes: false`.
- Unicité testée sur `email` et sur `handle_compare`.

## 6. Règles de validation lues dans le module de garde

- Email : format, ≤ 254, domaine non-IP, pas de point en bord de partie locale ni `..`.
- Handle : 3–32, minuscules/chiffres/`._-`, pas de séparateur aux extrémités, pas `..`/`__`/`--`, liste de réservés (`admin`, `administrateur`, `root`, `system`, `support`, `mizan`, `al-mizan`, `imam8mahdi`, `compte`, `contact`, …).
- Nom affiché : 2–80, caractères de contrôle refusés, espaces normalisés.
- Mot de passe : 12–128, au moins une lettre et un chiffre, absent des mots courants (`administrateur`, `al-mizan2026`, `mizan2026`, …), ne contient ni la partie locale de l'email (≥ 3) ni le handle (≥ 3).

## 7. Secret local

- Chemin : `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\administrateur_production_al_mizan.json`, 381 octets.
- Clés : `email`, `handle`, `nom_affichage`, `mot_de_passe`, `role`, `service`, `cree_le`, `note`.
- ACL relevée : un seul principal `PC-JG45TT2\Administrateur:(F)`, héritage supprimé.
- `secrets/` est ignoré par `.gitignore` ; ne jamais déplacer le fichier hors de ce dossier ni le committer.

## 8. Limites constatées

- L'agrégat public `statut_public` inclut l'administrateur (`comptes_actifs: 1`) ; il ne mesure pas des utilisateurs métier.
- SMTP absent : double validation inutilisable ; `double_validation` reste `False`.
- L'admin a `verification_niveau = 0` et `score_confiance = 0.35` : ne pas revendiquer un niveau vérifié.
- Aucun redémarrage du service n'a été nécessaire après la réparation du propriétaire ; ce point n'a été observé qu'une fois.
- La révocation de session n'a pas été testée par une requête post-déconnexion : seule la réponse 200 du logout figure dans le snapshot. Le rapport de session affirme la révocation ; la preuve 401 manque.
- Le mot de passe stocké mesure 31 caractères (revérifié localement le 27/10/2026), alors que le rapport de session annonçait 28 ; ne pas figer ce nombre, seule la validation de politique a été rejouée.
- Au moment du snapshot, le tour de vérification suivant était encore en cours (`status: streaming`) : les éléments ci-dessus sont les seuls confirmés par des sorties d'outils.
- Non vérifié dans cette session : usage de la 2FA, envoi d'email, connexion depuis un autre poste, comportement après rotation de mot de passe.

## 9. Contrôles ajoutés après revue (27/10/2026)

### 9.1 Révocation de session

Les deux tours de vérification de `55f63550` n'observent que la réponse du logout : `deconnexion_http: 200` (tour de création), puis `sessions: 200 nombre: 1` … `deconnexion: 200` (tour de contrôle). Aucune requête n'est faite avec l'ancien cookie après le logout ; « session révoquée » n'était donc pas observé. Le Skill exige désormais de rejouer `GET /api/v1/comptes/moi` avec l'ancien cookie et d'attendre 401. Ce 401 n'a pas encore été observé en production ; il reste à établir au prochain contrôle.

### 9.2 Contrat de drapeaux de la CLI

Commande exécutée dans la session de création `e4b7c222` (2026-10-27T05:25:10Z) :

```
py -3 -B module_comptes_utilisateurs_mizan.py --help 2>&1 | grep -E -- "--creer-admin|--mot-de-passe-stdin|--email|--handle|--nom"
```

Résultat : `RC=0`, `exitCode: 0`, cinq drapeaux présents (`--creer-admin`, `--email`, `--nom`, `--handle`, `--mot-de-passe-stdin`). Rejouée le 2026-10-27T06:28+01:00 : `RC=0`. `-B` évite de créer `__pycache__` dans le dépôt. La variante `python3 -B` sur le VPS n'a pas encore été exécutée ; elle est un critère de préflight, pas une observation.
