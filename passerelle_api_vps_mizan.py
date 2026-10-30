# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
    PASSERELLE API REST LÉGÈRE & WEBHOOKS DISTANTS POUR VPS AL-MIZAN
      COMMUNICATION ASYNCHRONE, TÉLÉMÉTRIE 12D, CONTRÔLE & WEBHOOKS
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Système          : ASTRO-Q°ODE / AL-MIZAN
Rôle             : Architecte Principal des Systèmes Autonomes & Réseaux Distants

LE JUSTE MILIEU :
  Permet d'exposer sur un serveur VPS (ou passerelle réseau distante) une API
  REST ultra-légère sans framework lourd et un gestionnaire de Webhooks pour :
    1. LIRE les données physiques et cognitives en temps réel (Tenseur 12D,
       8 288 synapses, statut de la boucle infinie, bibliothèque).
    2. RECEVOIR des réponses vivantes formulées par l'IA et Gemini.
    3. ENVOYER des commandes proactives au moteur physique Al-Mizan.
    4. ÉMETTRE des webhooks événementiels vers des clients externes
       (alertes cryogéniques, quittances de partage 50/50, cycles scellés).
===============================================================================
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, asdict
import hashlib
import hmac
import http.server
import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

# Imports des modules fondamentaux locaux
from module_ia_autonome_boucle_fermee_mizan import (
    AGENT_IA_AUTONOME,
    BRIDE_MIZAN,
    PLAFOND_EFFECTIF,
    KILLSWITCH_MK,
    TEMP_NOMINALE_MK,
    TypeActionProactive,
)
from moteur_boucle_infinie_synaptique_bibliotheque import MOTEUR_BOUCLE_INFINIE
from module_memoire_dynamique_hybride_rag import MOTEUR_MEMOIRE_HYBRIDE
from noyau_logique_interactif_ia import NOYAU_LOGIQUE_INTERACTIF
from moteur_intelligence_generative_vivante import MOTEUR_INTELLIGENCE_GENERATIVE
from module_sas_biometrique_souverain import (
    SAS_BIOMETRIQUE_SOUVERAIN,
    PreuveMultimodaleSoumise,
)
from module_couche_intermediaire_sync_traduction import (
    COUCHE_INTERMEDIAIRE_SYNC,
    TypeTechnologieAsynchrone,
    NiveauPrioriteSynchrone,
)
from moteur_economie_islamique_mizan import MOTEUR_ISLAMIQUE
from agent_de_code_harmonisateur_mizan import AGENT_CODE_AL_MIZAN
from gestionnaire_acceleration_gpu_mizan import GESTIONNAIRE_GPU
from moteur_voix_serveur_hybride_mizan import MOTEUR_VOIX_HYBRIDE
from moteur_acoustique_harmonique_horloge_mizan import MOTEUR_ACOUSTIQUE
from moteur_spectre_ecoute_harmonique_mizan import MOTEUR_SPECTRE_ECOUTE
from orchestrateur_synchronisation_totale_mizan import ORCHESTRATEUR_SYNCHRO_TOTALE
from module_inventaire_hub_imam8mahdi import INVENTAIRE_HUB
from module_comptes_utilisateurs_mizan import (
    DUREE_SESSION_JOURS,
    ErreurComptes,
    GestionnaireComptes,
)
from module_garde_cybernetique_mizan import origine_autorisee
import module_offres_mizan as offres_mizan
import module_messagerie_mizan as messagerie

# Clé d'API VPS : uniquement fournie par l'environnement. Absente, les routes protégées restent fermées.
def cle_api_vps_attendue() -> str:
    """Lit la clé à chaque requête : l'absence de variable ferme les routes protégées."""
    return os.environ.get("MIZAN_VPS_API_KEY", "").strip()

def secret_webhooks_requis() -> bytes:
    """Secret HMAC des webhooks : uniquement fourni par l'environnement, sans valeur de repli."""
    secret = os.environ.get("MIZAN_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise RuntimeError(
            "MIZAN_WEBHOOK_SECRET absent : signature des webhooks impossible."
        )
    return secret.encode("utf-8")

CHEMIN_FAVICON = Path(__file__).resolve().parent / "web_cloud" / "favicon.ico"
GESTIONNAIRE_COMPTES = GestionnaireComptes()

PAGES_COMPTES = {
    "/inscription": "compte_inscription.html",
    "/connexion": "compte_connexion.html",
    "/compte": "compte_espace.html",
    "/compte/": "compte_espace.html",
    "/verification": "compte_verification.html",
    "/cgu": "cgu.html",
    "/confidentialite": "confidentialite.html",
    "/cgv": "cgv.html",
    "/conditions-generales-de-vente": "cgv.html",
    "/cookies": "cookies.html",
    "/traceurs": "cookies.html",
    "/signalement": "signalement.html",
    "/signaler": "signalement.html",
}

PAGES_QUBIT = {
    "/qubit-logique": "qubit_logique.html",
    "/qubit_logique": "qubit_logique.html",
    "/qubit": "qubit_logique.html",
}

PAGES_PUBLIQUES = {
    "/offres": "offres.html",
    "/tarifs": "offres.html",
    "/services": "services.html",
    "/statut": "statut.html",
    "/etat-du-service": "statut.html",
    "/securite": "securite.html",
    "/accessibilite": "accessibilite.html",
    "/contact": "contact.html",
    "/developpeurs": "developpeurs.html",
    "/api-docs": "developpeurs.html",
    "/portefeuille": "portefeuille_souverain.html",
    "/portefeuille-souverain": "portefeuille_souverain.html",
    "/wallet": "portefeuille_souverain.html",
    "/observateur-triniter": "observateur_triniter.html",
    "/observateur_triniter": "observateur_triniter.html",
    "/oeuvre-universelle": "oeuvre_universelle.html",
    "/oeuvre-universelle/": "oeuvre_universelle.html",
    "/oeuvre-universelle/en": "oeuvre_universelle_en.html",
    "/oeuvre-universelle/ar": "oeuvre_universelle_ar.html",
    "/riemann": "hypothese_riemann.html",
    "/riemann/": "hypothese_riemann.html",
    "/riemann/en": "hypothese_riemann_en.html",
    "/riemann/ar": "hypothese_riemann_ar.html",
    "/hypothese-riemann": "hypothese_riemann.html",
    "/hypothese-riemann/en": "hypothese_riemann_en.html",
    "/hypothese-riemann/ar": "hypothese_riemann_ar.html",
    "/oeuvre-universelle/riemann": "hypothese_riemann.html",
    "/oeuvre-universelle/riemann/en": "hypothese_riemann_en.html",
    "/oeuvre-universelle/riemann/ar": "hypothese_riemann_ar.html",
    "/quatrieme-dimension": "quatrieme_dimension.html",
    "/quatrieme-dimension/": "quatrieme_dimension.html",
    "/quatrieme-dimension/en": "quatrieme_dimension_en.html",
    "/quatrieme-dimension/ar": "quatrieme_dimension_ar.html",
    "/quatrieme_dimension": "quatrieme_dimension.html",
    "/4d": "quatrieme_dimension.html",
    "/gravitation-quantique-boucles": "gravitation_quantique_boucles.html",
    "/gravitation-quantique-boucles/": "gravitation_quantique_boucles.html",
    "/gravitation-quantique-boucles/en": "gravitation_quantique_boucles_en.html",
    "/gravitation-quantique-boucles/ar": "gravitation_quantique_boucles_ar.html",
    "/gravitation_quantique_boucles": "gravitation_quantique_boucles.html",
    "/reglement-dettes-redistribution": "reglement_dettes_redistribution.html",
    "/reglement-dettes-redistribution/": "reglement_dettes_redistribution.html",
    "/reglement-dettes-redistribution/en": "reglement_dettes_redistribution_en.html",
    "/reglement-dettes-redistribution/ar": "reglement_dettes_redistribution_ar.html",
    "/reglement_dettes_redistribution": "reglement_dettes_redistribution.html",
    "/retro-ingenierie-ia": "retro_ingenierie_ia.html",
    "/retro-ingenierie-ia/": "retro_ingenierie_ia.html",
    "/retro-ingenierie-ia/en": "retro_ingenierie_ia_en.html",
    "/retro-ingenierie-ia/ar": "retro_ingenierie_ia_ar.html",
    "/retro_ingenierie_ia": "retro_ingenierie_ia.html",
    "/traducteur-multimedia": "traducteur_multimedia.html",
    "/traducteur-multimedia/": "traducteur_multimedia.html",
    "/traducteur-multimedia/en": "traducteur_multimedia_en.html",
    "/traducteur-multimedia/ar": "traducteur_multimedia_ar.html",
    "/traducteur_multimedia": "traducteur_multimedia.html",
}

CHEMIN_RESUME_OEUVRE = (
    Path(__file__).resolve().parent / "resultats" / "oeuvre_universelle" / "resume.json"
)
CHEMIN_MANIFESTE_OEUVRE = (
    Path(__file__).resolve().parent
    / "resultats"
    / "oeuvre_universelle"
    / "manifeste_anteriorite.json"
)

CHEMIN_RESUME_QUBIT = Path(__file__).resolve().parent / "resultats" / "qubit_logique" / "resume.json"
CHEMIN_MODULE_QUBIT = Path(__file__).resolve().parent / "qubit_logique_mizan.py"


def construire_etat_composants() -> Dict[str, Any]:
    """État instantané et honnête des composants, sans donnée personnelle.

    Aucun historique de disponibilité n'est conservé : la réponse décrit le
    moment présent, pas un uptime contractuel.
    """
    composants: List[Dict[str, str]] = [
        {
            "code": "passerelle",
            "nom": "Passerelle HTTP",
            "statut": "opérationnel",
            "detail": "Le service répond à cette requête.",
        }
    ]
    try:
        stats = GESTIONNAIRE_COMPTES.statistiques()
        composants.append({
            "code": "comptes",
            "nom": "Comptes et sessions",
            "statut": "opérationnel",
            "detail": f"{stats['sessions_actives']} session(s) active(s), "
                      f"{stats['devis_total']} demande(s) de devis.",
        })
    except Exception:
        composants.append({
            "code": "comptes",
            "nom": "Comptes et sessions",
            "statut": "indisponible",
            "detail": "Base de comptes inaccessible.",
        })

    statut_qubit, detail_qubit = "absent", "Artefacts non générés : exécuter py -3 qubit_logique_mizan.py --rapport."
    if CHEMIN_RESUME_QUBIT.is_file():
        try:
            resume = json.loads(CHEMIN_RESUME_QUBIT.read_text(encoding="utf-8"))
            empreinte_courante = hashlib.sha256(CHEMIN_MODULE_QUBIT.read_bytes()).hexdigest()
            if resume.get("source", {}).get("sha256") == empreinte_courante:
                statut_qubit, detail_qubit = "opérationnel", "Artefacts à jour ; page et API servies."
            else:
                statut_qubit, detail_qubit = "périmé", "Artefacts antérieurs au module : régénérer avec --rapport."
        except Exception:
            statut_qubit, detail_qubit = "illisible", "Artefacts illisibles : régénérer avec --rapport."
    composants.append({
        "code": "qubit",
        "nom": "Qubit logique [[7,1,3]]",
        "statut": statut_qubit,
        "detail": detail_qubit,
    })

    if os.environ.get("MIZAN_OUTBOX_MODE") == "1":
        composants.append({
            "code": "messagerie",
            "nom": "Messagerie transactionnelle",
            "statut": "développement",
            "detail": "Mode outbox actif : les emails ne sont pas envoyés. Ne pas utiliser en production.",
        })
    elif messagerie.messagerie_disponible():
        composants.append({
            "code": "messagerie",
            "nom": "Messagerie transactionnelle",
            "statut": "configurée",
            "detail": "Un SMTP est configuré ; la délivrabilité n'est pas mesurée ici.",
        })
    else:
        composants.append({
            "code": "messagerie",
            "nom": "Messagerie transactionnelle",
            "statut": "non configurée",
            "detail": "Inscription et double validation refuseraient en 503 tant qu'aucun SMTP n'est configuré.",
        })

    composants.extend([
        {
            "code": "webhooks",
            "nom": "Webhooks sortants",
            "statut": "partiel",
            "detail": "Inscription non authentifiée et cible interne possible : durcissement requis avant usage réel.",
        },
        {
            "code": "paiements",
            "nom": "Paiements en ligne",
            "statut": "spécifié",
            "detail": "Aucun encaissement : les offres passent par une demande de devis.",
        },
        {
            "code": "quotas",
            "nom": "Quotas d'usage",
            "statut": "partiels",
            "detail": "Seules les limites de sécurité des comptes sont appliquées ; les quotas d'offres sont déclarés.",
        },
    ])

    critique_en_panne = any(c["statut"] in ("indisponible", "illisible") for c in composants)
    return {
        "succes": True,
        "statut_global": "dégradé" if critique_en_panne else "opérationnel (limites déclarées)",
        "horodatage_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "composants": composants,
        "disponibilite": {
            "mesure": "non instrumentée",
            "detail": "Aucun historique d'uptime n'est conservé ; cette page décrit l'état instantané.",
        },
        "note": "Un statut « opérationnel » ne vaut ni certification ni engagement de service.",
    }


def valider_cible_audit_publique(url: str) -> tuple[bool, str, str]:
    """Autorise uniquement une cible http/https sur port 80/443 dont toutes les
    adresses résolues sont publiques (anti-SSRF : bloque loopback, privé,
    link-local, CGNAT et réservé). Retourne (autorise, erreur, adresse_testee)."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"URL illisible : {e}", ""

    if parsed.scheme not in ("http", "https"):
        return False, "Schéma non autorisé (http ou https uniquement).", ""
    if parsed.username or parsed.password:
        return False, "Identifiants intégrés à l'URL refusés.", ""

    hote = parsed.hostname or ""
    if not hote:
        return False, "Hôte absent de l'URL.", ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in (80, 443):
        return False, "Port non autorisé (80 ou 443 uniquement).", ""

    try:
        infos = socket.getaddrinfo(hote, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except Exception as e:
        return False, f"Résolution DNS impossible : {e}", ""

    adresses = sorted({infos_item[4][0] for infos_item in infos})
    if not adresses:
        return False, "Aucune adresse réseau résolue.", ""
    for ip in adresses:
        try:
            adresse = ipaddress.ip_address(ip.split("%")[0])
        except ValueError:
            return False, f"Adresse réseau illisible : {ip}", ""
        if not adresse.is_global:
            return False, f"Cible non publique refusée ({ip}).", ""
    return True, "", adresses[0]


class _SansRedirection(urllib.request.HTTPRedirectHandler):
    """Refuse toute redirection HTTP pour empêcher un contournement de la
    validation anti-SSRF par rebond vers une adresse interne."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class InscriptionWebhook:
    """Modèle d'un webhook distant enregistré."""
    id_webhook: str
    url_cible: str
    evenements: List[str]  # Ex: ["ALERTE_CRYO", "CYCLE_IA", "COMMANDE_EXEC"]
    date_inscription_iso: str
    actif: bool = True
    total_livraisons_reussies: int = 0
    dernier_echec_str: Optional[str] = None


class GestionnaireWebhooksVPS:
    """Gestionnaire de notification par webhooks vers les abonnés distants."""

    def __init__(self):
        self.abonnements: Dict[str, InscriptionWebhook] = {}
        self.historique_evenements: collections.deque = collections.deque(maxlen=100)
        self.verrou = threading.Lock()

    def inscrire_webhook(self, url_cible: str, evenements: Optional[List[str]] = None) -> InscriptionWebhook:
        """Inscrit une nouvelle URL de webhook distant."""
        with self.verrou:
            id_hook = f"HOOK-{hashlib.md5(url_cible.encode()).hexdigest()[:8]}"
            evts = evenements or ["TOUS"]
            inscription = InscriptionWebhook(
                id_webhook=id_hook,
                url_cible=url_cible,
                evenements=evts,
                date_inscription_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                actif=True,
            )
            self.abonnements[id_hook] = inscription
            return inscription

    def desinscrire_webhook(self, id_webhook: str) -> bool:
        """Supprime une souscription webhook."""
        with self.verrou:
            if id_webhook in self.abonnements:
                del self.abonnements[id_webhook]
                return True
            return False

    def emettre_evenement(self, type_evenement: str, donnees: Dict[str, Any]):
        """Diffuse un événement en arrière-plan à tous les webhooks souscrits."""
        charge_utile = {
            "type_evenement": type_evenement,
            "horodatage_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "systeme": "ASTRO-Q°ODE / AL-MIZAN VPS GATEWAY",
            "donnees": donnees,
            "bride_mizan": BRIDE_MIZAN,
        }

        # Signature HMAC-SHA256 pour authenticité (secret obligatoire, sans repli)
        donnees_octets = json.dumps(charge_utile, sort_keys=True).encode("utf-8")
        signature_hmac = hmac.new(secret_webhooks_requis(), donnees_octets, hashlib.sha256).hexdigest()
        charge_utile["signature_hmac_sha256"] = signature_hmac

        with self.verrou:
            self.historique_evenements.append(charge_utile)
            cibles = [
                h for h in self.abonnements.values()
                if h.actif and ("TOUS" in h.evenements or type_evenement in h.evenements)
            ]

        # Envoi asynchrone pour ne pas ralentir le serveur
        def _diffuser():
            for hook in cibles:
                try:
                    req = urllib.request.Request(
                        hook.url_cible,
                        data=json.dumps(charge_utile).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "X-AlMizan-Signature": signature_hmac,
                            "User-Agent": "AlMizan-VPS-Webhook-Dispatcher/1.0",
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=4.0) as rep:
                        if rep.status in [200, 201, 202, 204]:
                            hook.total_livraisons_reussies += 1
                except Exception as e:
                    hook.dernier_echec_str = f"{time.strftime('%H:%M:%S')} - {str(e)[:100]}"

        threading.Thread(target=_diffuser, daemon=True).start()


GESTIONNAIRE_WEBHOOKS = GestionnaireWebhooksVPS()


class GestionnaireRequetesPasserelleVPS(http.server.BaseHTTPRequestHandler):
    """
    Gestionnaire HTTP REST & Webhook ultra-léger pour le serveur VPS.
    Ne nécessite aucune bibliothèque tierce, 100% Python standard.
    """

    def do_HEAD(self):
        """Gestionnaire de requêtes HEAD conforme pour vérification SSL et sondes réseau."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Powered-By", "Al-Mizan-Souverain-135MHz")
        self.end_headers()

    def _verifier_authentification(self) -> bool:
        """
        Vérifie une clé d'API VPS fournie par l'environnement.

        Fermé par défaut : sans MIZAN_VPS_API_KEY configurée, aucune requête
        n'est authentifiée. La session biométrique est une démonstration et ne
        confère aucun droit sur ces routes.
        """
        cle_attendue = cle_api_vps_attendue()
        if not cle_attendue:
            return False
        auth_header = self.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        else:
            # Permettre aussi le passage par paramètre d'URL ?token=...
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            token = params.get("token", [""])[0]

        return bool(token) and hmac.compare_digest(token, cle_attendue)

    def _repondre_json(self, donnees: Dict[str, Any], statut_code: int = 200):
        """Formate et émet une réponse JSON standardisée."""
        self.send_response(statut_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(donnees, ensure_ascii=False, indent=2).encode("utf-8"))

    NOM_COOKIE_SESSION = "mizan_session"

    def _ip_client(self) -> str:
        """Adresse réelle : n'en-tête X-Forwarded-For que derrière un proxy local."""
        ip = self.client_address[0] if self.client_address else "127.0.0.1"
        if ip in {"127.0.0.1", "::1"}:
            xff = self.headers.get("X-Forwarded-For", "")
            candidat = xff.split(",")[-1].strip() if xff else self.headers.get("X-Real-IP", "").strip()
            if candidat:
                try:
                    ipaddress.ip_address(candidat.split("%")[0])
                    return candidat
                except ValueError:
                    pass
        return ip

    def _agent_client(self) -> str:
        return str(self.headers.get("User-Agent", ""))[:300]

    def _lire_cookies(self) -> Dict[str, str]:
        cookies: Dict[str, str] = {}
        for morceau in self.headers.get("Cookie", "").split(";"):
            cle, _, valeur = morceau.strip().partition("=")
            if cle:
                cookies[cle] = valeur
        return cookies

    def _jeton_session(self) -> str:
        return self._lire_cookies().get(self.NOM_COOKIE_SESSION, "")

    def _requete_https(self) -> bool:
        if self.headers.get("X-Forwarded-Proto", "").lower() == "https":
            return True
        hote = self.headers.get("Host", "").split(":")[0].lower()
        return hote not in {"127.0.0.1", "localhost", "::1", ""}

    def _entetes_session(self, jeton: str) -> List[tuple[str, str]]:
        morceaux = [
            f"{self.NOM_COOKIE_SESSION}={jeton}",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
            f"Max-Age={DUREE_SESSION_JOURS * 86400}",
        ]
        if self._requete_https():
            morceaux.append("Secure")
        return [("Set-Cookie", "; ".join(morceaux))]

    def _entetes_suppression_session(self) -> List[tuple[str, str]]:
        morceaux = [
            f"{self.NOM_COOKIE_SESSION}=",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
            "Max-Age=0",
        ]
        if self._requete_https():
            morceaux.append("Secure")
        return [("Set-Cookie", "; ".join(morceaux))]

    def _repondre_json_prive(
        self,
        donnees: Dict[str, Any],
        statut_code: int = 200,
        entetes: Optional[List[tuple[str, str]]] = None,
    ):
        """Réponse JSON sans cache ni CORS permissif, pour données de compte."""
        self.send_response(statut_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for cle, valeur in entetes or []:
            self.send_header(cle, valeur)
        self.end_headers()
        self.wfile.write(json.dumps(donnees, ensure_ascii=False, indent=2).encode("utf-8"))

    def _repondre_erreur_comptes(self, erreur: ErreurComptes):
        entetes = [("Retry-After", str(int(erreur.retry_after)))] if erreur.retry_after else []
        self._repondre_json_prive(
            {"succes": False, "code": erreur.code, "erreur": erreur.message},
            erreur.statut_http,
            entetes,
        )

    def _verifier_csrf(self) -> None:
        if not origine_autorisee(self.headers.get("Origin", "")):
            raise ErreurComptes("ORIGINE_REFUSEE", "Origine de la requête refusée.", 403)
        if self.headers.get("X-Mizan-CSRF", "") != "1":
            raise ErreurComptes("CSRF_REFUSE", "En-tête anti-CSRF absent ou invalide.", 403)

    def _utilisateur_courant(self) -> Optional[Dict[str, Any]]:
        try:
            return GESTIONNAIRE_COMPTES.obtenir_utilisateur_par_session(self._jeton_session())
        except Exception:
            return None

    def _exiger_utilisateur(self) -> Dict[str, Any]:
        profil = self._utilisateur_courant()
        if not profil:
            raise ErreurComptes("NON_CONNECTE", "Connexion requise.", 401)
        return profil

    def _exiger_admin(self) -> Dict[str, Any]:
        profil = self._exiger_utilisateur()
        if profil.get("type_compte") != "admin":
            raise ErreurComptes("ACCES_REFUSE", "Accès réservé à l'administration.", 403)
        return profil

    def _servir_page_web_cloud(self, nom_fichier: str, statut_code: int = 200) -> bool:
        chemin_page = Path(__file__).resolve().parent / "web_cloud" / nom_fichier
        if not chemin_page.is_file():
            return False
        contenu = chemin_page.read_text(encoding="utf-8")
        self.send_response(statut_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(contenu.encode("utf-8"))
        return True

    def _entier(self, data: Dict[str, Any], cle: str, defaut: int = 0) -> int:
        try:
            return int(data.get(cle, defaut))
        except (TypeError, ValueError):
            raise ErreurComptes("DONNEES_INVALIDES", f"Le champ '{cle}' doit être un entier.", 400)

    def do_OPTIONS(self):
        """Gestion des requêtes CORS préliminaires."""
        self._repondre_json({"status": "CORS_PREFLIGHT_OK"})

    def _traiter_get_comptes(self, chemin: str, parsed_url: urllib.parse.ParseResult) -> None:
        """Lecture des données de compte et des vues d'administration."""
        try:
            if chemin in ["/api/v1/comptes/statut_public", "/api/v1/comptes/statistiques_publiques"]:
                stats = GESTIONNAIRE_COMPTES.statistiques()
                self._repondre_json_prive({
                    "succes": True,
                    "statistiques_publiques": {
                        "comptes_actifs": stats["par_statut"].get("actif", 0),
                        "particuliers": stats["par_type"].get("particulier", 0),
                        "entreprises": stats["par_type"].get("entreprise", 0),
                        "secteur_public": stats["par_type"].get("public", 0),
                        "domaines_verifies": stats.get("domaines_verifies", 0),
                    },
                    "note": "Agrégats sans données personnelles.",
                })
                return

            profil = self._exiger_utilisateur()

            if chemin == "/api/v1/comptes/devis":
                self._repondre_json_prive({
                    "succes": True,
                    "devis": GESTIONNAIRE_COMPTES.lister_devis_utilisateur(profil["id"]),
                    "note": "Aucun paiement n'est encaissé ; un devis écrit reste nécessaire avant toute activation.",
                })
            elif chemin == "/api/v1/admin/devis":
                self._exiger_admin()
                valeurs = urllib.parse.parse_qs(parsed_url.query).get("limite", ["200"])
                try:
                    limite = max(1, min(int(valeurs[0]), 500))
                except (TypeError, ValueError):
                    limite = 200
                self._repondre_json_prive({
                    "succes": True,
                    "devis": GESTIONNAIRE_COMPTES.lister_devis_admin(limite),
                })
            elif chemin == "/api/v1/comptes/moi":
                self._repondre_json_prive({"succes": True, "utilisateur": profil})
            elif chemin == "/api/v1/comptes/sessions":
                sessions = GESTIONNAIRE_COMPTES.lister_sessions(profil["id"], self._jeton_session())
                self._repondre_json_prive({"succes": True, "sessions": sessions})
            elif chemin == "/api/v1/comptes/export":
                export = GESTIONNAIRE_COMPTES.exporter_utilisateur(
                    profil["id"], self._jeton_session(), self._ip_client()
                )
                self._repondre_json_prive(
                    {"succes": True, "export": export},
                    200,
                    [("Content-Disposition", 'attachment; filename="al-mizan-donnees.json"')],
                )
            elif chemin == "/api/v1/admin/verifications":
                self._exiger_admin()
                limite = 200
                valeurs = urllib.parse.parse_qs(parsed_url.query).get("limite", ["200"])
                try:
                    limite = max(1, min(int(valeurs[0]), 500))
                except (TypeError, ValueError):
                    limite = 200
                self._repondre_json_prive({
                    "succes": True,
                    "verifications": GESTIONNAIRE_COMPTES.lister_verifications(limite),
                })
            elif chemin == "/api/v1/admin/utilisateurs":
                self._exiger_admin()
                self._repondre_json_prive({
                    "succes": True,
                    "utilisateurs": GESTIONNAIRE_COMPTES.lister_utilisateurs(200),
                })
            elif chemin == "/api/v1/admin/journal":
                self._exiger_admin()
                self._repondre_json_prive({
                    "succes": True,
                    "journal": GESTIONNAIRE_COMPTES.journal_recent(200),
                })
            elif chemin == "/api/v1/admin/statistiques":
                self._exiger_admin()
                self._repondre_json_prive({
                    "succes": True,
                    "statistiques": GESTIONNAIRE_COMPTES.statistiques(),
                })
            else:
                self._repondre_json_prive({"succes": False, "erreur": "Route comptes introuvable."}, 404)
        except ErreurComptes as erreur:
            self._repondre_erreur_comptes(erreur)

    def _traiter_post_comptes(self, chemin: str, data: Dict[str, Any]) -> None:
        """Écritures de compte : toutes protégées par origine + en-tête anti-CSRF."""
        try:
            self._verifier_csrf()
            ip = self._ip_client()
            agent = self._agent_client()

            if chemin == "/api/v1/comptes/inscription":
                resultat = GESTIONNAIRE_COMPTES.creer_utilisateur(
                    email=str(data.get("email", "")),
                    mot_de_passe=str(data.get("mot_de_passe", "")),
                    nom_affichage=str(data.get("nom_affichage", "")),
                    handle=str(data.get("handle", "")),
                    type_compte=str(data.get("type_compte", "particulier")).strip().lower(),
                    organisation=str(data.get("organisation", "")),
                    ip=ip,
                )
                self._repondre_json_prive({
                    "succes": True,
                    "message": "Compte créé. Consultez votre email pour l'activer.",
                    "user_id": resultat["user_id"],
                    "email_verifie": False,
                }, 201)

            elif chemin == "/api/v1/comptes/verification":
                profil = GESTIONNAIRE_COMPTES.verifier_email(str(data.get("token", "")))
                self._repondre_json_prive({
                    "succes": True,
                    "verifie": True,
                    "utilisateur": profil,
                    "message": "Adresse vérifiée. Vous pouvez vous connecter.",
                })

            elif chemin == "/api/v1/comptes/renvoyer-verification":
                GESTIONNAIRE_COMPTES.renvoyer_verification(str(data.get("email", "")), ip=ip)
                self._repondre_json_prive({
                    "succes": True,
                    "message": "Si un compte non vérifié existe, un nouveau lien a été envoyé.",
                })

            elif chemin == "/api/v1/comptes/connexion":
                resultat = GESTIONNAIRE_COMPTES.authentifier(
                    str(data.get("email", "")), str(data.get("mot_de_passe", "")), ip=ip, agent=agent
                )
                if resultat["deux_facteurs_requis"]:
                    self._repondre_json_prive({
                        "succes": True,
                        "deux_facteurs_requis": True,
                        "jeton_defi": resultat["jeton_defi"],
                        "message": "Un code de validation a été envoyé par email.",
                    })
                else:
                    self._repondre_json_prive(
                        {"succes": True, "utilisateur": resultat["utilisateur"]},
                        200,
                        self._entetes_session(resultat["jeton_session"]),
                    )

            elif chemin == "/api/v1/comptes/connexion/2fa":
                resultat = GESTIONNAIRE_COMPTES.valider_defi_connexion(
                    str(data.get("jeton_defi", "")), str(data.get("code", "")), ip=ip, agent=agent
                )
                self._repondre_json_prive(
                    {"succes": True, "utilisateur": resultat["utilisateur"]},
                    200,
                    self._entetes_session(resultat["jeton_session"]),
                )

            elif chemin == "/api/v1/comptes/deconnexion":
                GESTIONNAIRE_COMPTES.deconnecter(self._jeton_session(), ip=ip)
                self._repondre_json_prive(
                    {"succes": True, "message": "Session fermée."}, 200, self._entetes_suppression_session()
                )

            elif chemin == "/api/v1/comptes/sessions/revoquer":
                profil = self._exiger_utilisateur()
                GESTIONNAIRE_COMPTES.verifier_mot_de_passe_utilisateur(
                    profil["id"], str(data.get("mot_de_passe", ""))
                )
                nombre = GESTIONNAIRE_COMPTES.revoquer_toutes_sessions(profil["id"])
                self._repondre_json_prive(
                    {"succes": True, "sessions_revoquees": nombre, "message": "Toutes les sessions ont été fermées."},
                    200,
                    self._entetes_suppression_session(),
                )

            elif chemin == "/api/v1/comptes/double-validation":
                profil = self._exiger_utilisateur()
                actif = str(data.get("actif", "")).strip().lower() in {"1", "true", "oui", "yes"}
                resultat = GESTIONNAIRE_COMPTES.definir_double_validation(
                    profil["id"], actif, str(data.get("mot_de_passe", "")), ip=ip
                )
                self._repondre_json_prive({"succes": True, **resultat})

            elif chemin == "/api/v1/comptes/reinitialisation/demander":
                GESTIONNAIRE_COMPTES.demander_reinitialisation(str(data.get("email", "")), ip=ip)
                self._repondre_json_prive({
                    "succes": True,
                    "message": "Si un compte actif existe, un lien de réinitialisation a été envoyé.",
                })

            elif chemin == "/api/v1/comptes/reinitialisation/confirmer":
                resultat = GESTIONNAIRE_COMPTES.reinitialiser_mot_de_passe(
                    str(data.get("token", "")), str(data.get("mot_de_passe", "")), ip=ip
                )
                self._repondre_json_prive({"succes": True, **resultat})

            elif chemin == "/api/v1/comptes/domaines/demander":
                profil = self._exiger_utilisateur()
                demande = GESTIONNAIRE_COMPTES.demander_verification_domaine(
                    profil["id"], str(data.get("domaine", "")), ip=ip
                )
                self._repondre_json_prive({"succes": True, **demande})

            elif chemin == "/api/v1/comptes/supprimer":
                profil = self._exiger_utilisateur()
                resultat = GESTIONNAIRE_COMPTES.supprimer_compte(
                    profil["id"],
                    str(data.get("mot_de_passe", "")),
                    str(data.get("confirmation", "")),
                    ip=ip,
                )
                self._repondre_json_prive(
                    {"succes": True, **resultat}, 200, self._entetes_suppression_session()
                )

            elif chemin == "/api/v1/admin/verifications/approuver":
                admin = self._exiger_admin()
                resultat = GESTIONNAIRE_COMPTES.approuver_verification(
                    self._entier(data, "user_id"),
                    admin["id"],
                    self._entier(data, "niveau", 1),
                    str(data.get("domaine", "")),
                    str(data.get("note", "")),
                    ip=ip,
                )
                self._repondre_json_prive({"succes": True, **resultat})

            elif chemin == "/api/v1/admin/verifications/refuser":
                admin = self._exiger_admin()
                resultat = GESTIONNAIRE_COMPTES.refuser_verification(
                    self._entier(data, "user_id"), admin["id"], str(data.get("note", "")), ip=ip
                )
                self._repondre_json_prive({"succes": True, **resultat})

            elif chemin == "/api/v1/admin/utilisateurs/suspendre":
                admin = self._exiger_admin()
                cible = self._entier(data, "user_id")
                if cible == int(admin["id"]):
                    raise ErreurComptes("ACTION_REFUSEE", "Impossible de suspendre votre propre compte.", 400)
                resultat = GESTIONNAIRE_COMPTES.suspendre_utilisateur(
                    cible, admin["id"], str(data.get("note", "")), ip=ip
                )
                self._repondre_json_prive({"succes": True, **resultat})

            elif chemin == "/api/v1/admin/utilisateurs/reactiver":
                admin = self._exiger_admin()
                resultat = GESTIONNAIRE_COMPTES.reactiver_utilisateur(
                    self._entier(data, "user_id"), admin["id"], ip=ip
                )
                self._repondre_json_prive({"succes": True, **resultat})

            elif chemin == "/api/v1/comptes/devis":
                profil = self._exiger_utilisateur()
                resultat = GESTIONNAIRE_COMPTES.creer_devis(
                    profil["id"],
                    str(data.get("offre_code", "")),
                    str(data.get("besoins", "")),
                    self._entier(data, "volume_utilisateurs", 1),
                    ip=ip,
                )
                self._repondre_json_prive({
                    "succes": True,
                    "devis": resultat,
                    "message": "Demande de devis enregistrée. Aucun paiement n'est demandé.",
                }, 201)

            elif chemin == "/api/v1/comptes/devis/annuler":
                profil = self._exiger_utilisateur()
                resultat = GESTIONNAIRE_COMPTES.annuler_devis(
                    profil["id"], self._entier(data, "devis_id"), ip=ip
                )
                self._repondre_json_prive({"succes": True, "devis": resultat})

            elif chemin == "/api/v1/admin/devis/statut":
                admin = self._exiger_admin()
                resultat = GESTIONNAIRE_COMPTES.mettre_a_jour_devis(
                    self._entier(data, "devis_id"),
                    admin["id"],
                    str(data.get("statut", "")),
                    str(data.get("note", "")),
                    data.get("montant_propose_centimes"),
                    ip=ip,
                )
                self._repondre_json_prive({"succes": True, "devis": resultat})

            else:
                self._repondre_json_prive({"succes": False, "erreur": "Route comptes introuvable."}, 404)
        except ErreurComptes as erreur:
            self._repondre_erreur_comptes(erreur)

    def do_GET(self):
        """Endpoints REST de Lecture de données & Monitoring."""
        parsed_url = urllib.parse.urlparse(self.path)
        chemin = parsed_url.path

        # 0. Portail Public & Sas Souverain Universel (HTML)
        if chemin in ["/", "/index.html", "/public", "/accueil"]:
            chemin_html = Path(__file__).resolve().parent / "web_cloud" / "portail_public_al_mizan.html"
            if chemin_html.exists():
                with open(chemin_html, "r", encoding="utf-8") as f:
                    contenu_html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(contenu_html.encode("utf-8"))
                return

        # 0.TABLEAU_MAITRE Tableau Maître Séquentiel Unifié (226 entrées · 22 strates)
        elif chemin in ["/tableau", "/tableau-maitre", "/tableau-sequentiel", "/tableau-maitre-sequentiel"]:
            chemin_tab = Path(__file__).resolve().parent / "web_cloud" / "tableau_maitre_sequentiel.html"
            if chemin_tab.exists():
                with open(chemin_tab, "r", encoding="utf-8") as f:
                    tab_html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(tab_html.encode("utf-8"))
                return

        # 0.LIVRE_BLANC Livre Blanc Officiel Al-Mizan × ASTRO-Q°ODE (Jeton MZN Souverain)
        elif chemin in ["/livre-blanc", "/whitepaper", "/mzn", "/livre_blanc"]:
            chemin_lb = Path(__file__).resolve().parent / "web_cloud" / "livre_blanc_almizan.html"
            if chemin_lb.exists():
                with open(chemin_lb, "r", encoding="utf-8") as f:
                    lb_html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(lb_html.encode("utf-8"))
                return

        # 0.HUB_PONTS Hub des Ponts Synchrones Al-Mizan
        elif chemin in ["/ponts", "/hub-ponts", "/ponts-synchrones", "/hub"]:
            chemin_ponts = Path(__file__).resolve().parent / "web_cloud" / "hub_ponts_synchrones.html"
            if chemin_ponts.exists():
                with open(chemin_ponts, "r", encoding="utf-8") as f:
                    ponts_html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(ponts_html.encode("utf-8"))
                return

        # 0.VIDEO Promotionnelle YouTube (MP4)
        elif chemin in ["/video", "/video-promotion", "/al_mizan_promotion_youtube_1080p.mp4"]:
            chemin_video = Path(__file__).resolve().parent / "web_cloud" / "al_mizan_promotion_youtube_1080p.mp4"
            if chemin_video.exists():
                taille = chemin_video.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(taille))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                with open(chemin_video, "rb") as f_vid:
                    shutil.copyfileobj(f_vid, self.wfile)
                return

        # 0.POUPEES Cartographie Poupées 1 à 27
        elif chemin in ["/poupees", "/cartographie", "/poupees-russes"]:
            chemin_poupees = Path(__file__).resolve().parent / "web_cloud" / "cartographie_poupees_1_a_27.html"
            if chemin_poupees.exists():
                with open(chemin_poupees, "r", encoding="utf-8") as f:
                    poupees_html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(poupees_html.encode("utf-8"))
                return

        # 0.PRODUIT Console de Monitoring & SOC de Cybersécurité
        elif chemin in ["/console", "/monitoring", "/soc", "/cyber"]:
            chemin_soc = Path(__file__).resolve().parent / "web_cloud" / "monitoring_cybersecurite.html"
            if chemin_soc.exists():
                with open(chemin_soc, "r", encoding="utf-8") as f:
                    soc_html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(soc_html.encode("utf-8"))
                return

        # 0.RIEMANN Dossier PDF et figure (binaires, lecture seule)
        elif chemin in [
            "/hypothese-riemann.pdf",
            "/riemann.pdf",
            "/oeuvre-universelle/riemann.pdf",
        ]:
            chemin_pdf = Path(__file__).resolve().parent / "web_cloud" / "hypothese_riemann.pdf"
            if chemin_pdf.is_file():
                contenu_pdf = chemin_pdf.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(contenu_pdf)))
                self.send_header("Content-Disposition", 'inline; filename="hypothese_riemann.pdf"')
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(contenu_pdf)
                return

        elif chemin in ["/hypothese_riemann.png", "/riemann.png"]:
            chemin_png = Path(__file__).resolve().parent / "web_cloud" / "hypothese_riemann.png"
            if chemin_png.is_file():
                contenu_png = chemin_png.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(contenu_png)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "public, max-age=604800")
                self.end_headers()
                self.wfile.write(contenu_png)
                return

        # 0.4D Résultats JSON des équations de la quatrième dimension
        elif chemin in ["/quatrieme-dimension.json", "/quatrieme-dimension/resultats.json"]:
            chemin_json = Path(__file__).resolve().parent / "web_cloud" / "quatrieme_dimension_resultats.json"
            if chemin_json.is_file():
                contenu_json = chemin_json.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(contenu_json)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(contenu_json)
                return

        # 0.LQG Résultats JSON de la gravitation quantique à boucles
        elif chemin in [
            "/gravitation-quantique-boucles.json",
            "/gravitation-quantique-boucles/resultats.json",
        ]:
            chemin_json = Path(__file__).resolve().parent / "web_cloud" / "gravitation_quantique_boucles_resultats.json"
            if chemin_json.is_file():
                contenu_json = chemin_json.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(contenu_json)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(contenu_json)
                return

        # 0.ECO Résultats JSON du règlement des dettes et de la redistribution
        elif chemin in [
            "/reglement-dettes-redistribution.json",
            "/reglement-dettes-redistribution/resultats.json",
        ]:
            chemin_json = Path(__file__).resolve().parent / "web_cloud" / "reglement_dettes_redistribution_resultats.json"
            if chemin_json.is_file():
                contenu_json = chemin_json.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(contenu_json)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(contenu_json)
                return

        # 0.REA Résultats JSON de la rétro-ingénierie assistée par IA
        elif chemin in [
            "/retro-ingenierie-ia.json",
            "/retro-ingenierie-ia/resultats.json",
        ]:
            chemin_json = Path(__file__).resolve().parent / "web_cloud" / "retro_ingenierie_ia_resultats.json"
            if chemin_json.is_file():
                contenu_json = chemin_json.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(contenu_json)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(contenu_json)
                return

        # 0.TRM JSON du traducteur multimédia (lecture seule, artefact local)
        elif chemin in [
            "/traducteur-multimedia.json",
            "/traducteur-multimedia/resultats.json",
        ]:
            chemin_json = Path(__file__).resolve().parent / "web_cloud" / "traducteur_multimedia_resultats.json"
            if chemin_json.is_file():
                contenu_json = chemin_json.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(contenu_json)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(contenu_json)
                return

        # 0.TRM_PREUVES Manifeste, source et code du traducteur multimédia (vérification par un pair)
        elif chemin in [
            "/traducteur-multimedia/manifeste.json",
            "/traducteur-multimedia/source.json",
            "/traducteur-multimedia/code/traducteur_multimedia.py",
            "/traducteur-multimedia/code/generer_page_traducteur_multimedia.py",
        ]:
            nom = chemin.rsplit("/", 1)[-1]
            if nom == "manifeste.json":
                nom = "manifeste_sha256.json"
            elif nom == "source.json":
                nom = "source_video.json"
            chemin_preuve = Path(__file__).resolve().parent / "web_cloud" / "preuves_traducteur" / nom
            if chemin_preuve.is_file():
                contenu_preuve = chemin_preuve.read_bytes()
                type_contenu = (
                    "text/plain; charset=utf-8"
                    if nom.endswith(".py")
                    else "application/json; charset=utf-8"
                )
                self.send_response(200)
                self.send_header("Content-Type", type_contenu)
                self.send_header("Content-Length", str(len(contenu_preuve)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(contenu_preuve)
                return

        # 0.QUBIT Page du qubit logique [[7,1,3]] : équations, preuves, résultats
        elif chemin in PAGES_QUBIT:
            if self._servir_page_web_cloud(PAGES_QUBIT[chemin]):
                return
        elif chemin in PAGES_PUBLIQUES:
            if self._servir_page_web_cloud(PAGES_PUBLIQUES[chemin]):
                return

        # 0.COMPTES Pages publiques : inscription, connexion, espace, vérification, CGU
        elif chemin in PAGES_COMPTES:
            if self._servir_page_web_cloud(PAGES_COMPTES[chemin]):
                return

        # 0.LEGAL Mentions Légales & Identification d'Entreprise Sans Dol
        elif chemin in ["/mentions-legales", "/legal", "/mentions"]:
            chemin_legal = Path(__file__).resolve().parent / "web_cloud" / "mentions_legales.html"
            if chemin_legal.exists():
                with open(chemin_legal, "r", encoding="utf-8") as f:
                    legal_html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(legal_html.encode("utf-8"))
                return

        # 0.LEGAL_JSON Métadonnées officielles de conformité INPI/INSEE
        elif chemin in ["/api/v1/legal", "/api/v1/entreprise", "/api/v1/conformite"]:
            f_id = Path(__file__).resolve().parent / "memoire_aq" / "almizan_identite_legale_entreprise.json"
            if f_id.exists():
                with open(f_id, "r", encoding="utf-8") as f:
                    d_id = json.load(f)
                self._repondre_json({"succes": True, "entreprise_conforme": d_id})
                return

        # 0.CONTRAT_V2 Artefact public du contrat intelligent (lecture seule)
        elif chemin in ["/api/v1/contrat/v2/artefact", "/api/v1/contrat/v2/artifact"]:
            f_art = Path(__file__).resolve().parent / "contracts" / "AlMizanV2Souverain.artifact.json"
            f_src = Path(__file__).resolve().parent / "contracts" / "AlMizanV2Souverain.sol"
            if not f_art.is_file():
                self._repondre_json({"succes": False, "erreur": "ARTEFACT_ABSENT"}, 404)
                return
            try:
                with open(f_art, "r", encoding="utf-8") as f:
                    artefact = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._repondre_json({"succes": False, "erreur": "ARTEFACT_ILLISIBLE"}, 500)
                return
            a_jour = False
            if f_src.is_file():
                a_jour = hashlib.sha256(f_src.read_bytes()).hexdigest() == artefact.get("source_sha256")
            self._repondre_json({
                "succes": True,
                "statut": "source validée, non déployée" if a_jour else "artefact périmé",
                "artefact_a_jour": a_jour,
                "avertissement": (
                    "Contrat non déployé. Le déploiement éventuel est signé par votre portefeuille ; "
                    "ce site ne détient aucune clé privée."
                ),
                "artefact": artefact,
            })
            return

        # 0.FAVICON Icône de l'onglet (ICO si présente, sinon 204 sans corps)
        elif chemin == "/favicon.ico":
            if CHEMIN_FAVICON.exists():
                donnees_favicon = CHEMIN_FAVICON.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon")
                self.send_header("Content-Length", str(len(donnees_favicon)))
                self.send_header("Cache-Control", "public, max-age=604800")
                self.end_headers()
                self.wfile.write(donnees_favicon)
            else:
                self.send_response(204)
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
            return

        # 0.SEO Référencement Google (robots.txt & sitemap.xml)
        elif chemin == "/robots.txt":
            chemin_robots = Path(__file__).resolve().parent / "web_cloud" / "robots.txt"
            if chemin_robots.exists():
                with open(chemin_robots, "r", encoding="utf-8") as f:
                    data_txt = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(data_txt.encode("utf-8"))
                return

        elif chemin == "/sitemap.xml":
            chemin_sitemap = Path(__file__).resolve().parent / "web_cloud" / "sitemap.xml"
            if chemin_sitemap.exists():
                with open(chemin_sitemap, "r", encoding="utf-8") as f:
                    data_xml = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(data_xml.encode("utf-8"))
                return

        # 0.QUBIT_API Résultats du qubit logique [[7,1,3]] (lecture seule, artefact local)
        elif chemin in ["/api/v1/qubit_logique", "/api/v1/qubit-logique", "/api/v1/qubit"]:
            if not CHEMIN_RESUME_QUBIT.is_file():
                self._repondre_json({
                    "succes": False,
                    "erreur": "Résultats absents. Exécuter : py -3 qubit_logique_mizan.py --rapport",
                    "statut": "non généré",
                }, statut_code=404)
                return
            try:
                with open(CHEMIN_RESUME_QUBIT, "r", encoding="utf-8") as f_qubit:
                    resume_qubit = json.load(f_qubit)
            except (OSError, ValueError) as e:
                self._repondre_json({"succes": False, "erreur": f"Résultats illisibles : {e}"}, statut_code=500)
                return
            self._repondre_json({
                "succes": True,
                "qubit_logique": resume_qubit,
                "source": "resultats/qubit_logique/resume.json",
                "reproduction": "py -3 qubit_logique_mizan.py --verifier && py -3 qubit_logique_mizan.py --rapport",
            })
            return

        # 0.OFFRES Catalogue public des offres et services (spécifié, non activé)
        elif chemin in ["/api/v1/offres", "/api/v1/offres-services"]:
            self._repondre_json({
                "succes": True,
                "catalogue": offres_mizan.catalogue_public(),
                "source": "module_offres_mizan.py",
                "page": "/offres",
            })
            return

        # 0.STATUT État instantané et honnête des composants
        elif chemin in ["/api/v1/statut", "/api/v1/status", "/api/v1/composants"]:
            self._repondre_json(construire_etat_composants())
            return

        # 0.OEUVRE_API Registre universel : équations, résultats et limites
        elif chemin in ["/api/v1/oeuvre-universelle", "/api/v1/oeuvre_universelle"]:
            if not CHEMIN_RESUME_OEUVRE.is_file():
                self._repondre_json({
                    "succes": False,
                    "erreur": (
                        "Registre non généré. Exécuter : "
                        "py -3 oeuvre_universelle/generer_page_oeuvre.py"
                    ),
                }, statut_code=404)
                return
            try:
                with open(CHEMIN_RESUME_OEUVRE, "r", encoding="utf-8") as f_oeuvre:
                    donnees_oeuvre = json.load(f_oeuvre)
            except (OSError, ValueError) as e:
                self._repondre_json(
                    {"succes": False, "erreur": f"Registre illisible : {e}"},
                    statut_code=500,
                )
                return
            self._repondre_json({
                "succes": True,
                "oeuvre": donnees_oeuvre,
                "source": "resultats/oeuvre_universelle/resume.json",
                "reproduction": "py -3 oeuvre_universelle/generer_page_oeuvre.py",
            })
            return

        # 0.OEUVRE_MANIFESTE Manifeste SHA-256 / Merkle (lecture seule)
        elif chemin in [
            "/api/v1/oeuvre-universelle/manifeste",
            "/api/v1/oeuvre_universelle/manifeste",
        ]:
            if not CHEMIN_MANIFESTE_OEUVRE.is_file():
                self._repondre_json({
                    "succes": False,
                    "erreur": (
                        "Manifeste absent. Exécuter : "
                        "py -3 oeuvre_universelle/manifeste_anteriorite.py"
                    ),
                }, statut_code=404)
                return
            try:
                with open(CHEMIN_MANIFESTE_OEUVRE, "r", encoding="utf-8") as f_man:
                    manifeste = json.load(f_man)
            except (OSError, ValueError) as e:
                self._repondre_json(
                    {"succes": False, "erreur": f"Manifeste illisible : {e}"},
                    statut_code=500,
                )
                return
            self._repondre_json({"succes": True, "manifeste": manifeste})
            return

        # 0.COMPTES_API Lecture du compte, sessions, export, administration
        elif chemin.startswith("/api/v1/comptes/") or chemin.startswith("/api/v1/admin/"):
            self._traiter_get_comptes(chemin, parsed_url)
            return

        # 0.bis Statut de la démonstration multimodale — jamais de jeton en sortie
        elif chemin == "/api/v1/auth/statut_session":
            auth_header = self.headers.get("Authorization", "")
            token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
            demonstration_ouverte = SAS_BIOMETRIQUE_SOUVERAIN.est_session_souveraine_active(token)
            self._repondre_json({
                "succes": True,
                "est_souverain": False,
                "authentifiant": False,
                "mode": "DEMONSTRATION_NON_AUTHENTIFIANTE" if demonstration_ouverte else "VISITEUR_PUBLIC",
                "avertissement": "La démonstration multimodale ne vérifie aucun facteur et ne donne aucun droit d'accès.",
                "session": SAS_BIOMETRIQUE_SOUVERAIN.resume_public_session() if demonstration_ouverte else None,
            })
            return

        # 0.AGENT_CODE Statut et bilan d'Harmonisation du Code
        elif chemin in ["/api/v1/agent_code/statut", "/api/v1/agent_code", "/agent_code"]:
            bilan_agent = AGENT_CODE_AL_MIZAN.harmoniser_base_complete()
            self._repondre_json(bilan_agent)
            return

        # 0.MATERIEL_GPU Télémétrie de l'accélération matérielle (Option 1 & 2)
        elif chemin in ["/api/v1/materiel/gpu", "/api/v1/gpu", "/api/v1/materiel"]:
            contexte_gpu = GESTIONNAIRE_GPU.obtenir_contexte_execution()
            self._repondre_json({"succes": True, "infrastructure": contexte_gpu})
            return

        # 0.VOIX_STATUT Statut du moteur vocal hybride
        elif chemin in ["/api/v1/voix/statut", "/api/v1/voix"]:
            statut_voix = MOTEUR_VOIX_HYBRIDE.obtenir_statut_vocal_complet()
            self._repondre_json({"succes": True, "vocal": statut_voix})
            return

        # 0.VOIX_ACOUSTIQUE Télémétrie acoustique harmonique synchronisée sur l'Horloge Logique
        elif chemin in ["/api/v1/voix/acoustique", "/api/v1/acoustique", "/api/v1/prosodie"]:
            regles_acoustiques = MOTEUR_ACOUSTIQUE.exporter_regles_synthese_client()
            self._repondre_json({"succes": True, "acoustique": regles_acoustiques})
            return

        # 0.ECOUTE_SPECTRE Spectre d'écoute harmonique — valeurs de démonstration
        elif chemin in ["/api/v1/ecoute/spectre", "/api/v1/cochlee", "/api/v1/spectre"]:
            bilan_spectre = MOTEUR_SPECTRE_ECOUTE.analyser_flux_spectral()
            self._repondre_json({
                "succes": True,
                "nature": "demonstration",
                "avertissement": "Bandes par défaut (30/55/15) reprises du modèle : aucun micro n'est capté par cette route.",
                "spectre_ecoute": asdict(bilan_spectre),
            })
            return

        # 0.SYNCHRONISATION_TOTALE Unification complète (Machine ↔ Logique ↔ Voix ↔ Écoute ↔ Code)
        elif chemin in ["/api/v1/synchronisation/totale", "/api/v1/unification", "/api/v1/harmonie_totale"]:
            bilan_unification = ORCHESTRATEUR_SYNCHRO_TOTALE.obtenir_synthese_unification_json()
            self._repondre_json(bilan_unification)
            return

        # 0.ter Télémétrie de la Couche Intermédiaire de Synchronisation & Traduction
        elif chemin in ["/api/v1/synchronisation", "/api/v1/sync"]:
            metriques_sync = COUCHE_INTERMEDIAIRE_SYNC.obtenir_metriques_couche()
            self._repondre_json({"succes": True, "synchronisation": metriques_sync})
            return

        # 0.quater Audit Officiel des Transactions et Moyens de Paiement
        elif chemin in ["/api/v1/audit/paiements", "/api/v1/audit/transactions", "/audit/paiements"]:
            fichier_audit = Path(__file__).resolve().parent / "memoire_aq" / "almizan_audit_transactions_paiements.json"
            if fichier_audit.exists():
                try:
                    with open(fichier_audit, "r", encoding="utf-8") as f:
                        donnees_audit = json.load(f)
                    self._repondre_json({"succes": True, "audit": donnees_audit})
                    return
                except Exception as e:
                    self._repondre_json({"succes": False, "erreur": str(e)}, statut_code=500)
                    return
            else:
                self._repondre_json({"succes": False, "erreur": "Rapport d'audit non trouvé. Veuillez régénérer."}, statut_code=404)
                return

        # 0.quinties Économie Islamique Vivante (Anti-Riba, Zakat, Nisab)
        elif chemin in ["/api/v1/economie_islamique/statut", "/api/v1/islamic_economy", "/economie_islamique"]:
            bilan_islam = MOTEUR_ISLAMIQUE.obtenir_bilan_economie_islamique()
            self._repondre_json({"succes": True, "economie_islamique": bilan_islam})
            return

        # 0.sexies Inventaire hub local IMAM8MAHDI (acte A126)
        elif chemin in ["/api/v1/inventaire", "/inventaire", "/hub"]:
            bilan = INVENTAIRE_HUB.cartographier(persister=True)
            self._repondre_json({
                "succes": bilan.succes,
                "acte": "A126",
                "service": "Inventaire Hub Développement Local IMAM8MAHDI",
                "inventaire": asdict(bilan),
                "symbole": "🛡️🟢 HUB IMAM8MAHDI CARTOGRAPHIÉ",
            })
            return

        # 1. Santé du service VPS
        elif chemin in ["/api/v1/sante", "/sante", "/ping"]:
            self._repondre_json({
                "statut": "OPERATIONNEL",
                "service": "Passerelle REST Légère & Webhooks VPS Al-Mizan",
                "systeme": "ASTRO-Q°ODE / AL-MIZAN",
                "horodatage_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "invariants": {
                    "bride_mizan": BRIDE_MIZAN,
                    "killswitch_cryo_mk": KILLSWITCH_MK,
                    "horloge_universelle_mhz": 135.097021,
                    "partage_commercial": "50/50",
                    "taux_usure_riba": "0.0%",
                },
                "symbole": "🛡️🟢 LE JUSTE MILIEU VPS",
            })
            return

        # 2. Lecture du Tenseur d'état 12D et données physiques
        elif chemin == "/api/v1/etat":
            etat = AGENT_IA_AUTONOME.observer_systeme()
            self._repondre_json({
                "succes": True,
                "nature": "modele_simule",
                "avertissement": "Valeurs issues du modèle interne de l'agent ; ce ne sont pas des mesures d'instruments Cryo-CMOS certifiés.",
                "source": "AGENT_IA_AUTONOME.observer_systeme()",
                "horodatage_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "tenseur_12d": {
                    "temperature_cryo_mk": etat.temperature_cryo_mk,
                    "derive_thermique_mks": etat.derive_thermique_derivee,
                    "stabilite_horloge_dt_pct": etat.stabilite_horloge_dt_pct,
                    "fidelite_quantique_bell": etat.fidelite_quantique_bell,
                    "entropie_quantique": etat.entropie_von_neumann,
                    "debit_silicium_mops": etat.debit_silicium_die_mops,
                    "satisfaction_maslow": etat.score_satisfaction_maslow,
                    "ratio_or_argent": etat.reserve_or_argent_ratio,
                    "partage_5050_pct": etat.conformite_partage_5050_pct,
                    "taux_usure_riba_pct": etat.taux_usure_riba_pct,
                    "pression_cyber": etat.score_pression_entropique_cyber,
                    "harmonie_globale_mizan": etat.indice_harmonie_globale_mizan,
                },
                "securite_physique": {
                    "marge_killswitch_mk": KILLSWITCH_MK - etat.temperature_cryo_mk,
                    "killswitch_actif": etat.temperature_cryo_mk >= KILLSWITCH_MK,
                },
            })
            return

        # 3. Lecture du Connectome des 8 288 synapses et Boucle Infinie
        elif chemin == "/api/v1/synapses":
            statut_boucle = MOTEUR_BOUCLE_INFINIE.obtenir_statut_temps_reel()
            self._repondre_json({
                "succes": True,
                "connectome": {
                    "total_synapses_actives": statut_boucle["total_synapses_actives"],
                    "architecture": "L0 (28) -> L1 (64) -> L2 (64) -> L3 (32) -> L4 (7) + Feedback (128)",
                    "taux_apprentissage_eta": AGENT_IA_AUTONOME.matrice_synaptique.eta,
                    "bride_mizan": BRIDE_MIZAN,
                },
                "boucle_infinie_permanente": {
                    "active_24_7": statut_boucle["actif"],
                    "total_cycles_infinis": statut_boucle["total_cycles_infinis"],
                    "latence_synaptique_moyenne_ms": statut_boucle["latence_synaptique_moyenne_ms"],
                    "latence_bibliotheque_moyenne_ms": statut_boucle["latence_bibliotheque_moyenne_ms"],
                    "derniers_concepts": statut_boucle["derniers_concepts_interroges"],
                },
            })
            return

        # 4. Consultation de la Grande Bibliothèque Universelle (RAG < 0.1 ms)
        elif chemin == "/api/v1/bibliotheque":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            sujet = query_params.get("q", ["cryogénie"])[0]
            docs = MOTEUR_MEMOIRE_HYBRIDE.base_vectorielle.recherche_similarite_cosinus(sujet, top_k=2)
            resultats = [
                {
                    "titre": d[0].titre,
                    "score_similarite": d[1],
                    "extrait": d[0].contenu_texte[:200] + "...",
                }
                for d in docs
            ]
            self._repondre_json({
                "succes": True,
                "sujet_recherche": sujet,
                "traites_trouves": resultats,
                "total_traites_ram": len(MOTEUR_MEMOIRE_HYBRIDE.base_vectorielle.documents),
                "latence_acces_ram_ms": MOTEUR_MEMOIRE_HYBRIDE.base_vectorielle.derniere_latence_recherche_ms,
            })
            return

        # 5. Liste des webhooks et historique des événements
        elif chemin == "/api/v1/webhooks":
            with GESTIONNAIRE_WEBHOOKS.verrou:
                abos = [asdict(h) for h in GESTIONNAIRE_WEBHOOKS.abonnements.values()]
                evts = list(GESTIONNAIRE_WEBHOOKS.historique_evenements)[-10:]
            self._repondre_json({
                "succes": True,
                "total_webhooks_inscrits": len(abos),
                "abonnements": abos,
                "derniers_evenements_emis": evts,
            })
            return

        # 6. Bilan consolidé des 4 Démarches Unifiées
        elif chemin in ["/api/v1/unifie", "/unifie/donnees"]:
            from orchestrateur_unifie_4_demarches import ORCHESTRATEUR_UNIFIE
            fichier_bilan = Path(__file__).resolve().parent / "memoire_aq" / "almizan_bilan_unifie_4_demarches.json"
            if fichier_bilan.exists():
                with open(fichier_bilan, "r", encoding="utf-8") as f:
                    bilan = json.load(f)
            else:
                bilan = asdict(ORCHESTRATEUR_UNIFIE.executer_tout_d_une_fois())
            self._repondre_json({"succes": True, "bilan": bilan})
            return

        # 7. Dashboard Visuel Interactif des 4 Démarches ("Tout-en-un")
        elif chemin in ["/unifie", "/panneau"]:
            from module_authentification_google_oauth import GESTIONNAIRE_GOOGLE_OAUTH
            info_oauth = GESTIONNAIRE_GOOGLE_OAUTH.generer_url_connexion()
            url_oauth = info_oauth.get("url_autorisation", "#")

            html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Al-Mizan — Tableau de Bord Unifié des 4 Démarches</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #151d30;
            --accent-green: #10b981;
            --accent-blue: #3b82f6;
            --accent-gold: #f59e0b;
            --text-light: #f3f4f6;
            --text-muted: #9ca3af;
            --border-color: #273553;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-light);
            margin: 0;
            padding: 24px;
        }}
        .header {{
            text-align: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-color);
        }}
        .header h1 {{
            color: var(--accent-green);
            margin: 0 0 8px 0;
            font-size: 28px;
        }}
        .header p {{
            color: var(--text-muted);
            margin: 0;
        }}
        .btn-action-principale {{
            display: inline-block;
            margin-top: 16px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            font-size: 16px;
            font-weight: 700;
            padding: 14px 28px;
            border-radius: 8px;
            text-decoration: none;
            cursor: pointer;
            border: none;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
            transition: all 0.2s ease;
        }}
        .btn-action-principale:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-top: 24px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .card h2 {{
            font-size: 18px;
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .tag-status {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            background: rgba(16, 185, 129, 0.2);
            color: var(--accent-green);
        }}
        .code-box {{
            background: #090d16;
            border: 1px solid #1f293d;
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
            color: #60a5fa;
            margin-top: 10px;
        }}
        .btn-link {{
            display: inline-block;
            margin-top: 12px;
            background: #1e293b;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            border: 1px solid #334155;
        }}
        .btn-link:hover {{
            background: #334155;
        }}
        .btn-oauth {{
            background: #4285f4;
            border-color: #4285f4;
        }}
        .btn-oauth:hover {{
            background: #3367d6;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️🟢 AL-MIZAN — LE JUSTE MILIEU UNIFIÉ</h1>
        <p>Les 4 Démarches Fondamentales Englobées en un Tableau de Bord Unique</p>
        <button class="btn-action-principale" onclick="executerToutDUnCoup()">⚡ RÉ-EXÉCUTER LES 4 DÉMARCHES EN 1 CLIC</button>
        <div id="statut-exec" style="margin-top: 10px; font-weight: bold; color: #10b981;"></div>
    </div>

    <div class="grid">
        <!-- 1. IA VIVANTE -->
        <div class="card">
            <h2>🧠 1. Assistant Conversationnel <span class="tag-status">OPÉRATIONNEL</span></h2>
            <p style="color: var(--text-muted); font-size: 14px;">Modèle de génération Google Gemini si une clé est configurée, sinon synthétiseur local déterministe. Matrice logicielle de 8 288 poids et tenseur 12D simulé (aucune synapse biologique, aucun capteur physique).</p>
            <input type="text" id="input-prompt" value="Explique la justice du Mizan et l'harmonie des mondes." style="width: 100%; box-sizing: border-box; padding: 8px; border-radius: 6px; background: #090d16; border: 1px solid #1f293d; color: white; margin-top: 8px;">
            <button class="btn-link" onclick="testerDialogue()">Poser la question à l'IA</button>
            <div id="ia-reponse" class="code-box" style="white-space: pre-wrap;">Prêt pour dialogue en direct...</div>
        </div>

        <!-- 2. SERVEUR VPS -->
        <div class="card">
            <h2>🌐 2. Déploiement VPS Linux <span class="tag-status">PRÊT (Port 8095)</span></h2>
            <p style="color: var(--text-muted); font-size: 14px;">Archive autonome générée (al_mizan_vps_bundle.tar.gz) et service systemd configuré.</p>
            <p style="font-size: 13px;">Commande d'installation automatique :</p>
            <div class="code-box">tar -xzf al_mizan_vps_bundle.tar.gz -C /opt/al-mizan/ && sudo cp /opt/al-mizan/deploiement_vps/systemd/al-mizan-api-vps.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now al-mizan-api-vps</div>
            <a href="/api/v1/etat" class="btn-link" target="_blank">Consulter Tenseur 12D (/api/v1/etat)</a>
        </div>

        <!-- 3. WEBHOOKS HMAC -->
        <div class="card">
            <h2>🔔 3. Webhooks & Alertes Temps Réel <span class="tag-status">HMAC-SHA256</span></h2>
            <p style="color: var(--text-muted); font-size: 14px;">Diffusion asynchrone des alertes issues des paramètres simulés et des quittances 50/50 signées.</p>
            <input type="text" id="input-webhook" placeholder="URL Webhook (Discord, Telegram, n8n...)" style="width: 100%; box-sizing: border-box; padding: 8px; border-radius: 6px; background: #090d16; border: 1px solid #1f293d; color: white; margin-top: 8px;">
            <button class="btn-link" onclick="inscrireWebhook()">Enregistrer Webhook</button>
            <div id="webhook-statut" class="code-box">Webhooks actifs enregistrés sur le serveur.</div>
        </div>

        <!-- 4. GOOGLE OAUTH -->
        <div class="card">
            <h2>🔑 4. Google OAuth 2.0 <span class="tag-status">CLIENT CONFIGURÉ</span></h2>
            <p style="color: var(--text-muted); font-size: 14px;">Projet Google Cloud <code>laffaire-dallah</code> connecté avec client_secret.json.</p>
            <p style="font-size: 13px;">ID Client : <code>721418906887...apps.googleusercontent.com</code></p>
            <a href="{url_oauth}" class="btn-link btn-oauth" target="_blank">🔗 Se Connecter avec Google en 1 Clic</a>
        </div>
    </div>

    <script>
        function testerDialogue() {{
            const p = document.getElementById('input-prompt').value;
            const repBox = document.getElementById('ia-reponse');
            repBox.innerText = 'Génération en cours (Gemini si configuré, sinon synthétiseur local)...';
            fetch('/api/v1/interagir', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ message: p }})
            }})
            .then(r => r.json())
            .then(d => {{
                repBox.innerText = d.reponse_ia || JSON.stringify(d, null, 2);
            }})
            .catch(e => {{ repBox.innerText = 'Erreur : ' + e; }});
        }}

        function inscrireWebhook() {{
            const url = document.getElementById('input-webhook').value;
            if(!url) return alert('Veuillez renseigner une URL');
            fetch('/api/v1/webhooks/inscrire', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ url_cible: url }})
            }})
            .then(r => r.json())
            .then(d => {{
                document.getElementById('webhook-statut').innerText = 'Inscrit avec succès : ' + d.webhook.id_webhook;
            }});
        }}

        function executerToutDUnCoup() {{
            const st = document.getElementById('statut-exec');
            st.innerText = '⚡ Exécution des 4 démarches en cours...';
            fetch('/api/v1/unifie/executer', {{ method: 'POST' }})
            .then(r => r.json())
            .then(d => {{
                st.innerText = '✅ LES 4 DÉMARCHES ONT ÉTÉ ENGLOBÉES ET EXÉCUTÉES AVEC SUCCÈS !';
                if(d.bilan && d.bilan.demarche_1_ia_vivante) {{
                    document.getElementById('ia-reponse').innerText = d.bilan.demarche_1_ia_vivante.reponse_generee;
                }}
            }})
            .catch(e => {{ st.innerText = 'Erreur : ' + e; }});
        }}
    </script>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
            return

        else:
            if not chemin.startswith("/api/") and self._servir_page_web_cloud("page_404.html", statut_code=404):
                return
            self._repondre_json({"succes": False, "erreur": "Route GET introuvable"}, 404)


    def do_POST(self):
        """Endpoints REST de Commandes, Dialogue & Inscription Webhook."""
        longueur = int(self.headers.get("Content-Length", 0))
        brut = self.rfile.read(longueur) if longueur > 0 else b""
        try:
            corps = brut.decode("utf-8")
        except UnicodeDecodeError:
            # Corps gzip ou windows-1252 : décoder en remplacement, json.loads retombe sur {}
            corps = brut.decode("utf-8", "replace")
        try:
            data = json.loads(corps) if corps.strip() else {}
        except Exception:
            data = {}

        parsed_url = urllib.parse.urlparse(self.path)
        chemin = parsed_url.path

        # 0. COMPTES : inscription, connexion, 2FA, suppression, administration
        if chemin.startswith("/api/v1/comptes/") or chemin.startswith("/api/v1/admin/"):
            self._traiter_post_comptes(chemin, data)
            return

        # 0. ANALYSE HEURISTIQUE DE CYBERSÉCURITÉ (en-têtes HTTP/TLS, non certifiée)
        if chemin in ["/api/v1/cyber/auditer", "/api/v1/cyber/scan"]:
            url_cible = str(data.get("url") or data.get("cible") or data.get("domaine") or "").strip()
            if not url_cible:
                self._repondre_json({"succes": False, "erreur": "Le champ 'url' ou 'domaine' est requis."}, 400)
                return

            if "://" in url_cible and not url_cible.startswith(("http://", "https://")):
                self._repondre_json({
                    "succes": False,
                    "erreur": "Cible refusée : Schéma non autorisé (http ou https uniquement).",
                    "url_testee": url_cible,
                }, 400)
                return

            if not url_cible.startswith("http://") and not url_cible.startswith("https://"):
                url_cible = "https://" + url_cible

            # Garde anti-SSRF : cible publique uniquement, ports 80/443.
            cible_ok, erreur_cible, ip_cible = valider_cible_audit_publique(url_cible)
            if not cible_ok:
                self._repondre_json({
                    "succes": False,
                    "erreur": f"Cible refusée : {erreur_cible}",
                    "url_testee": url_cible,
                }, 400)
                return

            # Exécution du diagnostic technique réel
            import ssl
            # NB : `time` est déjà importé au niveau module. Un `import time` local ici rendait
            # `time` LOCAL à tout do_POST -> UnboundLocalError sur les autres routes POST.

            hote = urllib.parse.urlparse(url_cible).netloc.split(":")[0]
            rapport = {
                "url_auditee": url_cible,
                "hote": hote,
                "adresse_resolue": ip_cible,
                "nature_analyse": "Analyse heuristique des en-têtes HTTP/TLS, non intrusive et non certifiée.",
                "horodatage_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "statut_connexion": "INCONNU",
                "latence_ms": 0.0,
                "ssl_tls": {"actif": False, "details": None},
                "en_tetes_securite": {},
                "score_resilience_100": 0,
                "calcul_al_mizan_sans_dol": {},
                "recommandations": []
            }

            t0 = time.time()
            try:
                # 1. Test HTTP/HTTPS et analyse des headers (redirections refusées)
                ctx = ssl.create_default_context()

                req = urllib.request.Request(
                    url_cible,
                    headers={
                        "User-Agent": "Al-Mizan-CyberShield-Auditor/1.0 (+https://al-mizan.world)",
                        "Host": hote
                    }
                )
                ouvreur = urllib.request.build_opener(_SansRedirection)
                with ouvreur.open(req, timeout=6) as resp:
                    t1 = time.time()
                    rapport["latence_ms"] = round((t1 - t0) * 1000, 2)
                    rapport["statut_connexion"] = f"HTTP {resp.status}"

                    headers = {k.lower(): v for k, v in resp.getheaders()}
                    securite_headers = {
                        "strict-transport-security": "HSTS (Chiffrement forcé)",
                        "content-security-policy": "CSP (Anti-Injection & XSS)",
                        "x-frame-options": "Anti-Clickjacking",
                        "x-content-type-options": "Anti-Sniffing MIME",
                        "referrer-policy": "Politique de Référent",
                        "permissions-policy": "Permissions matérielles"
                    }

                    score = 20  # Base pour site joignable
                    if url_cible.startswith("https://"):
                        score += 30
                        rapport["ssl_tls"]["actif"] = True

                    for h_key, h_desc in securite_headers.items():
                        present = h_key in headers
                        rapport["en_tetes_securite"][h_desc] = {
                            "present": present,
                            "valeur": headers.get(h_key, "ABSENT")
                        }
                        if present:
                            score += 8
                        else:
                            rapport["recommandations"].append(f"Activer l'en-tête de sécurité {h_desc} ({h_key}).")

                    # 3. Vérification certificat TLS via IPv4
                    try:
                        sock_cible = ip_cible if ip_cible else hote
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
                            raw_sock.settimeout(4)
                            raw_sock.connect((sock_cible, 443))
                            with ctx.wrap_socket(raw_sock, server_hostname=hote) as s:
                                cert = s.getpeercert()
                                if cert:
                                    rapport["ssl_tls"]["details"] = {
                                        "sujet": dict(x[0] for x in cert.get("subject", [])),
                                        "emetteur": dict(x[0] for x in cert.get("issuer", [])),
                                        "expire_le": cert.get("notAfter"),
                                    }
                                else:
                                    rapport["ssl_tls"]["details"] = {"actif": True, "note": "Certificat TLS actif"}
                    except Exception as e_ssl:
                        rapport["ssl_tls"]["erreur"] = str(e_ssl)

                    # 3. Calcul Al-Mizan sans dol
                    score_final = min(score, 99)  # Jamais 100% sans dol
                    rapport["score_resilience_100"] = score_final
                    eta = score_final / 100.0
                    epsilon = 0.005  # 0.5% incompressible
                    r_res = (1.0 - eta) + epsilon
                    reduction_pct = round((1.0 - r_res) * 100, 2)

                    rapport["calcul_al_mizan_sans_dol"] = {
                        "formule": "R_res = R_0 * (1 - eta) + epsilon",
                        "efficacite_eta": round(eta, 4),
                        "marge_incompressible_epsilon": epsilon,
                        "risque_residuel_calcule": round(r_res, 4),
                        "taux_reduction_risque_pct": reduction_pct,
                        "note_honnetete": "Indicateur heuristique fondé sur la présence d'en-têtes ; ni audit certifié, ni garantie de sécurité."
                    }

                self._repondre_json({"succes": True, "audit": rapport})
                return

            except Exception as e_glob:
                self._repondre_json({
                    "succes": False,
                    "erreur": f"Impossible d'auditer la cible : {str(e_glob)}",
                    "url_testee": url_cible
                }, 500)
                return

        # 0.VOIX_TRANSCRIPTION (Module Hybride CPU/GPU)
        if chemin in ["/api/v1/voix/transcrire", "/api/v1/voix/stt"]:
            audio_b64 = str(data.get("audio_base64") or "").strip()
            if len(audio_b64) > 8_000_000:
                self._repondre_json({"succes": False, "erreur": "Flux audio trop volumineux (limite de 8 Mo encodés)."}, 413)
                return

            fmt = str(data.get("format", "webm"))
            raw_audio = b""
            audio_valide = False
            if audio_b64:
                try:
                    raw_audio = base64.b64decode(audio_b64, validate=True)
                    audio_valide = bool(raw_audio)
                except Exception:
                    audio_valide = False

            bilan_vocal = MOTEUR_VOIX_HYBRIDE.transcrire_audio_binaire(raw_audio, format_audio=fmt)
            self._repondre_json({
                "succes": True,
                "nature": "demonstration",
                "avertissement": "Aucun moteur de reconnaissance vocale n'est chargé : le texte renvoyé est un gabarit, pas une transcription.",
                "audio_recu": audio_valide,
                "transcription_reelle": bilan_vocal.transcription_reelle,
                "transcription": asdict(bilan_vocal),
            })
            return

        # 1. Dialogue & Question Vivante (Google Gemini / Al-Mizan)
        if chemin in ["/api/v1/interagir", "/api/v1/dialogue"]:
            message = str(data.get("message") or data.get("texte") or "").strip()
            if not message:
                self._repondre_json({"succes": False, "erreur": "Le champ 'message' est requis."}, 400)
                return

            canal = str(data.get("canal", "API_VPS_REST"))
            spectre_audio = data.get("spectre_audio")

            try:
                # Ingestion et alignement dans la couche intermédiaire synchrone
                id_trame_sync = COUCHE_INTERMEDIAIRE_SYNC.ingerer_asynchrone(
                    TypeTechnologieAsynchrone.INTELLIGENCE_LLM_GEMINI,
                    {"message": message, "canal": canal, "spectre_audio": spectre_audio},
                    priorite=NiveauPrioriteSynchrone.NORMALE_COGNITIVE,
                )

                reponse_ia = NOYAU_LOGIQUE_INTERACTIF.traiter_instruction_interactive(
                    message, canal_source=canal, spectre_audio=spectre_audio
                )

                # Notification par webhook
                GESTIONNAIRE_WEBHOOKS.emettre_evenement("INTERACTION_VIVANTE", {
                    "message_entree": message,
                    "reponse": reponse_ia.reponse_vocale_et_texte,
                    "canal": canal,
                })

                self._repondre_json({
                    "succes": True,
                    "id_interaction": reponse_ia.id_interaction,
                    "message_utilisateur": message,
                    "reponse_ia": reponse_ia.reponse_vocale_et_texte,
                    "prosodie_mizan": MOTEUR_ACOUSTIQUE.exporter_regles_synthese_client(),
                    "mode_esprit": MOTEUR_INTELLIGENCE_GENERATIVE.dernier_mode_generation,
                    "modele_configure": MOTEUR_INTELLIGENCE_GENERATIVE.modele_actif,
                    "actions_executees": reponse_ia.actions_proactives_appliquees,
                    "garde_fous_valides": reponse_ia.garde_fous_valides,
                    "symbole_securite": reponse_ia.symbole_securite,
                })
            except Exception as e_dialogue:
                self._repondre_json({
                    "succes": False,
                    "erreur": "Le traitement du dialogue a échoué.",
                    "detail": str(e_dialogue)[:200],
                }, 503)
            return

        # 2. Exécution d'une Commande Proactive (Sécurisée par Authentification)
        elif chemin in ["/api/v1/commande", "/api/v1/action"]:
            if not self._verifier_authentification():
                self._repondre_json({
                    "succes": False,
                    "erreur": "Authentification requise (Fournir 'Authorization: Bearer <CLE_VPS>' ou '?token=...')."
                }, 401)
                return

            action_nom = str(data.get("action", "")).strip().upper()
            justification = str(data.get("justification", "Commande déclenchée via API REST VPS."))

            try:
                # Validation du type d'action parmi les 7 actions proactives
                type_act = TypeActionProactive[action_nom] if action_nom in TypeActionProactive.__members__ else None
                if not type_act:
                    self._repondre_json({
                        "succes": False,
                        "erreur": f"Action inconnue. Valeurs valides : {list(TypeActionProactive.__members__.keys())}",
                    }, 400)
                    return

                # Ingestion prioritaire dans la couche intermédiaire synchrone (Priorité Critique)
                id_trame_cmd = COUCHE_INTERMEDIAIRE_SYNC.ingerer_asynchrone(
                    TypeTechnologieAsynchrone.COMMANDE_PROACTIVE,
                    {"action": action_nom, "justification": justification},
                    priorite=NiveauPrioriteSynchrone.CRITIQUE_SOUVERAIN,
                )

                # Enregistrement et diffusion de l'événement
                GESTIONNAIRE_WEBHOOKS.emettre_evenement("COMMANDE_EXEC", {
                    "action": action_nom,
                    "id_trame_sync": id_trame_cmd,
                    "justification": justification,
                    "statut": "ENREGISTREE",
                })

                self._repondre_json({
                    "succes": True,
                    "action_demandee": action_nom,
                    "justification": justification,
                    "nature": "enregistrement",
                    "avertissement": "La commande est enregistrée et diffusée ; aucun actionneur physique n'est piloté par cette route.",
                    "statut": "COMMANDE ENREGISTRÉE ET HORODATÉE",
                    "horodatage_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
            except Exception as e:
                self._repondre_json({"succes": False, "erreur": str(e)}, 500)
            return

        # 3. Inscription d'un nouveau Webhook
        elif chemin == "/api/v1/webhooks/inscrire":
            url_cible = str(data.get("url_cible", "")).strip()
            if not url_cible or not url_cible.startswith("http"):
                self._repondre_json({"succes": False, "erreur": "Une 'url_cible' HTTP/HTTPS valide est requise."}, 400)
                return

            evenements = data.get("evenements", ["TOUS"])
            hook = GESTIONNAIRE_WEBHOOKS.inscrire_webhook(url_cible, evenements)
            self._repondre_json({
                "succes": True,
                "webhook": asdict(hook),
                "message": f"Webhook inscrit avec succès. Les notifications seront signées HMAC-SHA256.",
            })
            return

        # 4. Réception d'un Webhook entrant externe
        elif chemin in ["/webhook/recevoir", "/api/v1/webhooks/entree"]:
            evenement_source = str(data.get("evenement", "NOTIFICATION_EXTERNE"))
            charge = data.get("payload", data)

            # Ingestion et alignement par la couche intermédiaire synchrone
            id_trame_hook = COUCHE_INTERMEDIAIRE_SYNC.ingerer_asynchrone(
                TypeTechnologieAsynchrone.WEBHOOK_EXTERNE_ENTRANT,
                {"evenement": evenement_source, "charge": charge},
                priorite=NiveauPrioriteSynchrone.NORMALE_COGNITIVE,
            )

            # Traitement interne de l'événement entrant
            GESTIONNAIRE_WEBHOOKS.emettre_evenement("WEBHOOK_ENTRANT_RECU", {
                "evenement": evenement_source,
                "id_trame_sync": id_trame_hook,
                "donnees": charge,
            })

            self._repondre_json({
                "succes": True,
                "statut": "REÇU_ET_TRAITÉ",
                "horodatage_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            return

        # 5. Déclenchement à la demande des 4 Démarches Unifiées
        elif chemin in ["/api/v1/unifie/executer", "/unifie/executer"]:
            from orchestrateur_unifie_4_demarches import ORCHESTRATEUR_UNIFIE
            prompt = str(data.get("prompt", "Explique l'harmonie universelle et la justice du Mizan."))
            url_wh = data.get("webhook", None)
            bilan = ORCHESTRATEUR_UNIFIE.executer_tout_d_une_fois(prompt_ia=prompt, url_webhook=url_wh)
            self._repondre_json({"succes": True, "bilan": asdict(bilan)})
            return

        # 6. Démonstrateur multimodal : génération du défi 3 s (sans valeur d'authentification)
        elif chemin in ["/api/v1/auth/sas_biometrique/challenge", "/sas/challenge"]:
            ip_client = self.client_address[0] if self.client_address else "127.0.0.1"
            defi = SAS_BIOMETRIQUE_SOUVERAIN.generer_defi_souverain(ip_source=ip_client)
            defi["nature"] = "demonstration"
            defi["avertissement"] = "Défi pédagogique : aucune caméra, aucun micro et aucune passkey ne sont vérifiés."
            self._repondre_json(defi)
            return

        # 7. Démonstrateur multimodal : cohérence des facteurs déclarés (aucun droit d'accès)
        elif chemin in ["/api/v1/auth/sas_biometrique/valider", "/sas/valider"]:
            ip_client = self.client_address[0] if self.client_address else "127.0.0.1"
            preuve = PreuveMultimodaleSoumise(
                id_defi=str(data.get("id_defi", "")),
                phrase_prononcee=str(data.get("phrase_prononcee", "")),
                spectre_audio_moyenne=data.get("spectre_audio_moyenne", [0.42] * 64),
                visage_detecte=bool(data.get("visage_detecte", False)),
                score_vivacite_liveness=float(data.get("score_vivacite_liveness", 0.0)),
                signature_materielle_passkey=str(data.get("signature_materielle_passkey", "")),
                ip_source=ip_client,
            )

            succes, message, session = SAS_BIOMETRIQUE_SOUVERAIN.evaluer_preuve_multimodale(preuve)
            if succes and session:
                GESTIONNAIRE_WEBHOOKS.emettre_evenement("DEMONSTRATION_MULTIMODALE_VALIDEE", {
                    "ip": ip_client,
                    "horodatage": session.horodatage_connexion_iso,
                    "authentifiant": False,
                })
                self._repondre_json({
                    "succes": True,
                    "nature": "demonstration",
                    "authentifiant": False,
                    "avertissement": "Facteurs déclarés par le client : aucune vérification caméra, micro ou WebAuthn ; aucun droit d'accès.",
                    "message": message,
                    "jeton_demonstration": session.jeton_autorisation_bearer,
                    "session": SAS_BIOMETRIQUE_SOUVERAIN.resume_public_session(),
                })
            else:
                GESTIONNAIRE_WEBHOOKS.emettre_evenement("DEMONSTRATION_MULTIMODALE_REFUSEE", {
                    "ip": ip_client,
                    "erreur": message,
                })
                self._repondre_json({"succes": False, "erreur": message}, 403)
            return

        # 8. Déconnexion de la Session Souveraine
        elif chemin in ["/api/v1/auth/deconnexion", "/sas/deconnexion"]:
            SAS_BIOMETRIQUE_SOUVERAIN.revoquer_session_souveraine()
            self._repondre_json({"succes": True, "statut": "SESSION_REVOQUEE_RETOUR_PUBLIC"})
            return

        # 9. Économie Islamique : Vérification Contrat & Filtrage Anti-Riba
        elif chemin == "/api/v1/economie_islamique/contrat/verifier":
            type_c = data.get("type_contrat", "MUDARABA")
            partie_a = data.get("partie_a", "Investisseur")
            partie_b = data.get("partie_b", "Entrepreneur")
            capital = float(data.get("capital", 1000.0))
            taux = float(data.get("taux_interet", 0.0))
            cle = data.get("cle_partage", "50/50")
            contrat = MOTEUR_ISLAMIQUE.verifier_et_filtrer_anti_riba(type_c, partie_a, partie_b, capital, taux, cle_partage=cle)
            self._repondre_json({"succes": True, "contrat": asdict(contrat)})
            return

        # 10. Économie Islamique : Prélèvement Légal de la Zakat (2.5%) vers la Caisse Civique
        elif chemin == "/api/v1/economie_islamique/zakat/prelever":
            compte = data.get("compte", "CITE_GALAXY_MOBILE")
            solde = float(data.get("solde", 7800000.0))
            succes, op, msg = MOTEUR_ISLAMIQUE.executer_prelevement_zakat_sur_solde(compte, solde)
            self._repondre_json({
                "succes": succes,
                "message": msg,
                "operation": asdict(op) if op else None,
                "nouveau_bilan": MOTEUR_ISLAMIQUE.obtenir_bilan_economie_islamique()
            })
            return

        else:
            self._repondre_json({"succes": False, "erreur": "Route POST introuvable"}, 404)


class ServeurPasserelleAPIVPS:
    """Conteneur d'exécution du serveur HTTP de la passerelle VPS."""

    def __init__(self, port: int = 8095, hote: str = "0.0.0.0"):
        self.port = int(port)
        self.hote = hote
        self.httpd: Optional[http.server.HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def demarrer(self, bloquant: bool = False):
        """Démarre le serveur API VPS en mode multi-thread pour éviter tout interblocage."""
        if not cle_api_vps_attendue():
            print(
                "[AVERTISSEMENT] MIZAN_VPS_API_KEY absente : les routes protégées répondent 401.",
                file=sys.stderr,
            )
        self.httpd = http.server.ThreadingHTTPServer((self.hote, self.port), GestionnaireRequetesPasserelleVPS)
        self.httpd.daemon_threads = True
        if bloquant:
            self.httpd.serve_forever()
        else:
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()

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


# Instance résidente
PASSERELLE_VPS = ServeurPasserelleAPIVPS(port=8095)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Passerelle API REST Légère & Webhooks VPS Al-Mizan")
    parser.add_argument("--test", action="store_true", help="Exécute les tests unitaires et s'arrête")
    parser.add_argument("--port", type=int, default=8095, help="Port d'écoute (défaut: 8095)")
    args = parser.parse_args()

    try:
        secret_webhooks_requis()
    except RuntimeError as erreur:
        raise SystemExit(f"[ERREUR] Démarrage refusé : {erreur}")

    print("=" * 80)
    print(f" DÉMARRAGE DE LA PASSERELLE API REST LÉGÈRE & WEBHOOKS VPS (PORT {args.port})")
    print("=" * 80)
    passerelle = ServeurPasserelleAPIVPS(port=args.port)

    if args.test:
        passerelle.demarrer(bloquant=False)
        time.sleep(0.5)

        print("\n[TEST] 1. Interrogation GET /api/v1/sante...")
        with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/api/v1/sante") as rep:
            print(rep.read().decode())

        print("\n[TEST] 2. Interrogation POST /api/v1/interagir...")
        req = urllib.request.Request(
            f"http://127.0.0.1:{args.port}/api/v1/interagir",
            data=json.dumps({"message": "Bonjour depuis le VPS !"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as rep:
            res = json.loads(rep.read().decode())
            print("Réponse reçue du VPS :", res.get("reponse_ia")[:140] + "...")

        print("\n[TEST] 3. Inscription Webhook POST /api/v1/webhooks/inscrire...")
        req_hook = urllib.request.Request(
            f"http://127.0.0.1:{args.port}/api/v1/webhooks/inscrire",
            data=json.dumps({"url_cible": f"http://127.0.0.1:9999/mon-webhook"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_hook) as rep:
            print(rep.read().decode())

        passerelle.arreter()
        print("\n[SUCCÈS CONFIRMÉ] La Passerelle API REST & Webhooks VPS est opérationnelle.")
    else:
        # MODE PRODUCTION PERMANENT 24/7 POUR SYSTEMD
        passerelle.demarrer(bloquant=True)
