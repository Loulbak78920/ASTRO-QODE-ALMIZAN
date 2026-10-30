# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""Tests HTTP des pages publiques, du catalogue, du statut et des devis."""

from __future__ import annotations

import email
import email.policy
import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import passerelle_api_vps_mizan as passerelle
from module_comptes_utilisateurs_mizan import GestionnaireComptes
try:
    from test_comptes_http_mizan import ClientHTTP
except ImportError:  # import en paquet tests.*
    from tests.test_comptes_http_mizan import ClientHTTP

MOT_DE_PASSE = "Cheval-Noir-2026"
EMAIL = "cheval.noir@exemple.test"
HANDLE = "chevalnoir"
NOM = "Cheval Noir"


class TestSitePublicHTTP(unittest.TestCase):
    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp(prefix="mizan_site_"))
        self.db = self.dossier / "comptes.sqlite3"
        self.outbox = self.dossier / "outbox"
        self._env = {
            "MIZAN_GARDE_SECRET": "secret-site-mizan-0123456789abcdef",
            "MIZAN_OUTBOX_MODE": "1",
            "MIZAN_OUTBOX_DIR": str(self.outbox),
            "MIZAN_BASE_URL": "http://127.0.0.1",
        }
        self._ancien = {cle: os.environ.get(cle) for cle in self._env}
        os.environ.update(self._env)
        passerelle.GESTIONNAIRE_COMPTES = GestionnaireComptes(self.db)
        self._log_original = passerelle.GestionnaireRequetesPasserelleVPS.log_message
        passerelle.GestionnaireRequetesPasserelleVPS.log_message = lambda *a, **k: None
        self.serveur = passerelle.ServeurPasserelleAPIVPS(port=0, hote="127.0.0.1")
        self.serveur.demarrer(bloquant=False)
        self.port = self.serveur.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.client = ClientHTTP(self.base)

    def tearDown(self):
        passerelle.GestionnaireRequetesPasserelleVPS.log_message = self._log_original
        self.serveur.arreter()
        if self.serveur.httpd:
            self.serveur.httpd.server_close()
        for cle, valeur in self._ancien.items():
            if valeur is None:
                os.environ.pop(cle, None)
            else:
                os.environ[cle] = valeur
        shutil.rmtree(self.dossier, ignore_errors=True)

    # ------------------------------------------------------------------ outils
    def _dernier_courriel(self) -> str:
        fichiers = sorted(self.outbox.glob("*.eml"), key=lambda p: (p.stat().st_mtime, p.name))
        self.assertTrue(fichiers, "aucun email dans l'outbox")
        message = email.message_from_bytes(fichiers[-1].read_bytes(), policy=email.policy.default)
        return message.get_content()

    def _inscrire_et_connecter(self, email_=EMAIL, handle=HANDLE, nom=NOM, type_="particulier"):
        statut, donnees, _ = self.client.json("POST", "/api/v1/comptes/inscription", {
            "email": email_,
            "mot_de_passe": MOT_DE_PASSE,
            "nom_affichage": nom,
            "handle": handle,
            "type_compte": type_,
        })
        self.assertEqual(statut, 201, donnees)
        jeton = re.search(r"token=([A-Za-z0-9_\-]+)", self._dernier_courriel())
        self.assertIsNotNone(jeton)
        statut, donnees, _ = self.client.json("POST", "/api/v1/comptes/verification", {"token": jeton.group(1)})
        self.assertEqual(statut, 200, donnees)
        statut, donnees, _ = self.client.json("POST", "/api/v1/comptes/connexion", {
            "email": email_, "mot_de_passe": MOT_DE_PASSE,
        })
        self.assertEqual(statut, 200, donnees)
        return donnees["utilisateur"]

    def _devis(self, offre="particulier-essentiel", besoins="Besoin réel de test décrit en plus de vingt caractères.", volume=3):
        return self.client.json("POST", "/api/v1/comptes/devis", {
            "offre_code": offre, "besoins": besoins, "volume_utilisateurs": volume,
        })

    # ------------------------------------------------------------------ pages
    def test_01_pages_publiques_et_404(self):
        pages = {
            "/offres": "Offres et tarifs",
            "/tarifs": "Offres et tarifs",
            "/services": "Catalogue",
            "/statut": "État du service",
            "/etat-du-service": "État du service",
            "/securite": "divulgation responsable",
            "/accessibilite": "Déclaration d'accessibilité",
            "/contact": "Contact",
            "/developpeurs": "API et intégration",
            "/api-docs": "API et intégration",
            "/qubit-logique": "qubit",
            "/observateur-triniter": "Observateur Triniter",
            "/oeuvre-universelle": "Œuvre universelle",
            "/oeuvre-universelle/en": "The Universal Work",
            "/oeuvre-universelle/ar": "العمل الكوني",
            "/riemann": "Hypothèse de Riemann",
            "/riemann/en": "Riemann hypothesis",
            "/riemann/ar": "فرضية ريمان",
            "/quatrieme-dimension": "La quatrième dimension",
            "/quatrieme-dimension/en": "The fourth dimension",
            "/quatrieme-dimension/ar": "البعد الرابع",
            "/gravitation-quantique-boucles": "Gravitation quantique à boucles",
            "/gravitation-quantique-boucles/en": "Loop quantum gravity",
            "/gravitation-quantique-boucles/ar": "الجاذبية الكمومية الحلقية",
            "/reglement-dettes-redistribution": "Règlement des dettes et redistribution",
            "/reglement-dettes-redistribution/en": "Debt settlement and redistribution",
            "/reglement-dettes-redistribution/ar": "تسوية الديون وإعادة التوزيع",
            "/traducteur-multimedia": "Traducteur multimédia",
            "/traducteur-multimedia/en": "Multimedia translator",
            "/traducteur-multimedia/ar": "مترجم الوسائط المتعددة",
            "/retro-ingenierie-ia": "Rétro-ingénierie assistée par IA",
            "/retro-ingenierie-ia/en": "AI-assisted reverse engineering",
            "/retro-ingenierie-ia/ar": "الهندسة العكسية",
        }
        for chemin, marqueur in pages.items():
            statut, entetes, corps = self.client.requete("GET", chemin)
            self.assertEqual(statut, 200, chemin)
            self.assertIn("text/html", entetes.get("Content-Type", ""), chemin)
            self.assertIn(marqueur, corps, chemin)
            if chemin.endswith("/en"):
                self.assertIn('lang="en"', corps, chemin)
            elif chemin.endswith("/ar"):
                self.assertIn('lang="ar"', corps, chemin)
                self.assertIn('dir="rtl"', corps, chemin)
            else:
                self.assertIn('lang="fr"', corps, chemin)

        statut, entetes, corps = self.client.requete("GET", "/quatrieme-dimension.json")
        self.assertEqual(statut, 200)
        self.assertIn("application/json", entetes.get("Content-Type", ""))
        self.assertIn('"equations"', corps)

        statut, entetes, corps = self.client.requete("GET", "/gravitation-quantique-boucles.json")
        self.assertEqual(statut, 200)
        self.assertIn("application/json", entetes.get("Content-Type", ""))
        self.assertIn('"equations"', corps)
        self.assertIn('"controles"', corps)

        statut, entetes, corps = self.client.requete("GET", "/reglement-dettes-redistribution.json")
        self.assertEqual(statut, 200)
        self.assertIn("application/json", entetes.get("Content-Type", ""))
        self.assertIn('"equations"', corps)
        self.assertIn('"controles"', corps)

        statut, entetes, corps = self.client.requete("GET", "/traducteur-multimedia.json")
        self.assertEqual(statut, 200)
        self.assertIn("application/json", entetes.get("Content-Type", ""))
        self.assertIn('"trajectoire"', corps)
        self.assertIn('"anteriorite"', corps)

        statut, entetes, corps = self.client.requete("GET", "/retro-ingenierie-ia.json")
        self.assertEqual(statut, 200)
        self.assertIn("application/json", entetes.get("Content-Type", ""))
        self.assertIn('"equations"', corps)
        self.assertIn('"controles"', corps)
        self.assertIn('"o0i2kRvzv5s"', corps)

        # Preuves publiées : un pair doit pouvoir hacher exactement ce que le site sert.
        racine = Path(__file__).resolve().parent.parent
        copies = racine / "web_cloud" / "preuves_traducteur"
        preuves = {
            "/traducteur-multimedia/manifeste.json": ("manifeste_sha256.json", "application/json"),
            "/traducteur-multimedia/source.json": ("source_video.json", "application/json"),
            "/traducteur-multimedia/code/traducteur_multimedia.py": ("traducteur_multimedia.py", "text/plain"),
            "/traducteur-multimedia/code/generer_page_traducteur_multimedia.py": ("generer_page_traducteur_multimedia.py", "text/plain"),
        }
        for chemin, (nom, type_attendu) in preuves.items():
            statut, entetes, corps = self.client.requete("GET", chemin)
            self.assertEqual(statut, 200, chemin)
            self.assertIn(type_attendu, entetes.get("Content-Type", ""), chemin)
            self.assertEqual(corps.encode("utf-8"), (copies / nom).read_bytes(), chemin)

        for chemin, nom_page in (
            ("/traducteur-multimedia", "traducteur_multimedia.html"),
            ("/traducteur-multimedia/en", "traducteur_multimedia_en.html"),
            ("/traducteur-multimedia/ar", "traducteur_multimedia_ar.html"),
        ):
            statut, _, corps = self.client.requete("GET", chemin)
            self.assertEqual(statut, 200, chemin)
            self.assertEqual(corps.encode("utf-8"), (racine / "web_cloud" / nom_page).read_bytes(), chemin)
            self.assertIn(b"\n", (racine / "web_cloud" / nom_page).read_bytes())
            self.assertNotIn(b"\r\n", (racine / "web_cloud" / nom_page).read_bytes(), chemin)

        statut, entetes, corps = self.client.requete("GET", "/page-qui-nexiste-pas")
        self.assertEqual(statut, 404)
        self.assertIn("text/html", entetes.get("Content-Type", ""))
        self.assertIn("Cette page n'existe pas", corps)
        self.assertIn('href="/offres"', corps)

        statut, donnees, _ = self.client.json("GET", "/api/v1/inconnue")
        self.assertEqual(statut, 404)
        self.assertFalse(donnees.get("succes", True))

    def test_02_sitemap_et_robots(self):
        statut, entetes, corps = self.client.requete("GET", "/sitemap.xml")
        self.assertEqual(statut, 200)
        self.assertIn("application/xml", entetes.get("Content-Type", ""))
        for chemin in ("/offres", "/services", "/statut", "/securite", "/accessibilite", "/contact", "/developpeurs", "/observateur-triniter", "/oeuvre-universelle", "/oeuvre-universelle/en", "/oeuvre-universelle/ar", "/riemann", "/riemann/en", "/riemann/ar", "/quatrieme-dimension", "/quatrieme-dimension/en", "/quatrieme-dimension/ar", "/gravitation-quantique-boucles", "/gravitation-quantique-boucles/en", "/gravitation-quantique-boucles/ar", "/reglement-dettes-redistribution", "/reglement-dettes-redistribution/en", "/reglement-dettes-redistribution/ar", "/traducteur-multimedia", "/traducteur-multimedia/en", "/traducteur-multimedia/ar", "/retro-ingenierie-ia", "/retro-ingenierie-ia/en", "/retro-ingenierie-ia/ar"):
            self.assertIn(f"<loc>https://www.al-mizan.world{chemin}</loc>", corps, chemin)

        statut, _, robots = self.client.requete("GET", "/robots.txt")
        self.assertEqual(statut, 200)
        self.assertIn("Sitemap: https://www.al-mizan.world/sitemap.xml", robots)
        self.assertIn("Disallow: /api/", robots)

    # ------------------------------------------------------------------ API publiques
    def test_03_catalogue_et_statut(self):
        statut, donnees, _ = self.client.json("GET", "/api/v1/offres")
        self.assertEqual(statut, 200)
        catalogue = donnees["catalogue"]
        self.assertEqual(catalogue["version"], "2026.10.27")
        self.assertEqual(len(catalogue["offres"]), 8)
        self.assertEqual(len(catalogue["services"]), 12)
        self.assertIn("aucun paiement", catalogue["statut_tarifs"].lower())
        self.assertIn("particulier", catalogue["segments"])
        for offre in catalogue["offres"]:
            self.assertIn(offre["segment"], catalogue["segments"], offre["code"])
            if catalogue["segments"][offre["segment"]]["eligible_gratuit"]:
                self.assertTrue(offre["gratuit"], offre["code"])

        statut, donnees, _ = self.client.json("GET", "/api/v1/statut")
        self.assertEqual(statut, 200)
        self.assertTrue(donnees["succes"])
        self.assertIn("opérationnel", donnees["statut_global"])
        codes = {composant["code"] for composant in donnees["composants"]}
        self.assertLessEqual({"passerelle", "comptes", "qubit", "messagerie", "webhooks", "paiements", "quotas"}, codes)
        self.assertEqual(donnees["disponibilite"]["mesure"], "non instrumentée")
        paiements = next(c for c in donnees["composants"] if c["code"] == "paiements")
        self.assertEqual(paiements["statut"], "spécifié")

        statut, donnees, _ = self.client.json("GET", "/api/v1/sante")
        self.assertEqual(statut, 200)
        self.assertEqual(donnees["statut"], "OPERATIONNEL")

    # ------------------------------------------------------------------ devis
    def test_04_devis_utilisateur(self):
        self._inscrire_et_connecter()

        statut, donnees, _ = self.client.json("GET", "/api/v1/comptes/devis")
        self.assertEqual(statut, 200)
        self.assertEqual(donnees["devis"], [])

        statut, donnees, _ = self._devis()
        self.assertEqual(statut, 201, donnees)
        devis = donnees["devis"]
        self.assertTrue(devis["reference"].startswith("DEV-"))
        self.assertEqual(devis["statut"], "recu")
        self.assertEqual(devis["offre_code"], "particulier-essentiel")
        self.assertEqual(devis["volume_utilisateurs"], 3)
        self.assertEqual(devis["montant_indicatif_centimes"], 900)
        self.assertIsNone(devis["montant_propose_centimes"])

        # Segment incompatible et besoin trop court
        statut, donnees, _ = self._devis(offre="entreprise-equipe")
        self.assertEqual(statut, 403)
        self.assertEqual(donnees["code"], "SEGMENT_INCOMPATIBLE")
        statut, donnees, _ = self._devis(besoins="trop court")
        self.assertEqual(statut, 400)
        self.assertEqual(donnees["code"], "BESOIN_INVALIDE")
        statut, donnees, _ = self._devis(offre="offre-inexistante")
        self.assertEqual(statut, 400)
        self.assertEqual(donnees["code"], "OFFRE_INCONNUE")

        # CSRF et session
        statut, donnees, _ = self.client.json(
            "POST", "/api/v1/comptes/devis",
            {"offre_code": "particulier-essentiel", "besoins": "Besoin suffisamment long pour être accepté par la validation."},
            csrf=False,
        )
        self.assertEqual(statut, 403)
        self.assertEqual(donnees["code"], "CSRF_REFUSE")

        statut, donnees, _ = self.client.json("POST", "/api/v1/comptes/devis/annuler", {"devis_id": devis["id"]})
        self.assertEqual(statut, 200, donnees)
        self.assertEqual(donnees["devis"]["statut"], "annule")
        statut, donnees, _ = self.client.json("POST", "/api/v1/comptes/devis/annuler", {"devis_id": devis["id"]})
        self.assertEqual(statut, 409)
        self.assertEqual(donnees["code"], "DEVIS_NON_ANNULABLE")

    def test_05_devis_admin_et_export(self):
        utilisateur = self._inscrire_et_connecter()
        statut, donnees, _ = self._devis()
        self.assertEqual(statut, 201, donnees)
        reference = donnees["devis"]["reference"]

        statut, donnees, _ = self.client.json("GET", "/api/v1/admin/devis")
        self.assertEqual(statut, 403)

        admin = passerelle.GESTIONNAIRE_COMPTES.creer_admin(
            "admin@mizan.test", "Sceptre-Or-2026", "Administration", "archonte"
        )
        self.assertEqual(admin["type_compte"], "admin")
        admin_client = ClientHTTP(self.base)
        statut, donnees, _ = admin_client.json("POST", "/api/v1/comptes/connexion", {
            "email": "admin@mizan.test", "mot_de_passe": "Sceptre-Or-2026",
        })
        self.assertEqual(statut, 200, donnees)

        statut, donnees, _ = admin_client.json("GET", "/api/v1/admin/devis")
        self.assertEqual(statut, 200)
        entree = next(d for d in donnees["devis"] if d["reference"] == reference)
        self.assertEqual(entree["email"], EMAIL)
        self.assertEqual(entree["type_compte"], "particulier")

        statut, donnees, _ = admin_client.json("POST", "/api/v1/admin/devis/statut", {
            "devis_id": entree["id"], "statut": "en_revue", "note": "Dossier reçu.",
        })
        self.assertEqual(statut, 200, donnees)
        self.assertEqual(donnees["devis"]["statut"], "en_revue")

        statut, donnees, _ = admin_client.json("POST", "/api/v1/admin/devis/statut", {
            "devis_id": entree["id"], "statut": "devis_envoye", "note": "Proposition transmise.",
            "montant_propose_centimes": 12000,
        })
        self.assertEqual(statut, 200, donnees)
        self.assertEqual(donnees["devis"]["montant_propose_centimes"], 12000)
        self.assertEqual(donnees["devis"]["note_admin"], "Proposition transmise.")

        statut, donnees, _ = admin_client.json("POST", "/api/v1/admin/devis/statut", {
            "devis_id": entree["id"], "statut": "invalide",
        })
        self.assertEqual(statut, 400)
        self.assertEqual(donnees["code"], "STATUT_INVALIDE")

        statut, donnees, _ = self.client.json("GET", "/api/v1/comptes/devis")
        self.assertEqual(statut, 200)
        devis = donnees["devis"][0]
        self.assertEqual(devis["statut"], "devis_envoye")
        self.assertEqual(devis["montant_propose_centimes"], 12000)
        self.assertEqual(devis["note_admin"], "Proposition transmise.")

        statut, donnees, _ = self.client.json("GET", "/api/v1/comptes/export")
        self.assertEqual(statut, 200)
        self.assertEqual(donnees["export"]["profil"]["id"], utilisateur["id"])
        self.assertEqual(len(donnees["export"]["devis"]), 1)
        self.assertEqual(donnees["export"]["devis"][0]["reference"], reference)

    def test_06_devis_sans_session(self):
        anonyme = ClientHTTP(self.base)
        statut, donnees, _ = anonyme.json("GET", "/api/v1/comptes/devis")
        self.assertEqual(statut, 401)
        statut, donnees, _ = anonyme.json("POST", "/api/v1/comptes/devis", {
            "offre_code": "particulier-essentiel",
            "besoins": "Besoin anonyme suffisamment long pour dépasser vingt caractères.",
        })
        self.assertEqual(statut, 401)

    def test_07_oeuvre_universelle_api(self):
        statut, donnees, _ = self.client.json("GET", "/api/v1/oeuvre-universelle")
        self.assertEqual(statut, 200, donnees)
        self.assertTrue(donnees["succes"])
        oeuvre = donnees["oeuvre"]
        self.assertEqual(oeuvre["statistiques"]["nb_problemes"], 20)
        self.assertEqual(len(oeuvre["problemes"]), 20)
        mat = [p for p in oeuvre["problemes"] if p["code"] == "MAT-01"]
        self.assertEqual(len(mat), 1)
        self.assertFalse(mat[0]["calcul"]["resultat"]["hypothese_demontree"])
        self.assertFalse(mat[0]["calcul"]["resultat"]["preuve_fournie"])
        self.assertEqual(len(oeuvre["reseau"]["modules"]), 10)
        self.assertEqual(oeuvre["portefeuilles"]["custody"], "aucune")
        self.assertFalse(oeuvre["portefeuilles"]["cle_privee_stockee"])
        self.assertFalse(oeuvre["manifeste"]["causalite_mondiale_prouvee"])
        self.assertFalse(oeuvre["manifeste"]["preuve_anteorite_legale"])
        self.assertRegex(oeuvre["manifeste"]["racine_merkle_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("reproduction", donnees)

        statut, donnees, _ = self.client.json("GET", "/api/v1/oeuvre-universelle/manifeste")
        self.assertEqual(statut, 200, donnees)
        manifeste = donnees["manifeste"]
        self.assertTrue(manifeste["preuve_integrite"])
        self.assertFalse(manifeste["preuve_anteorite_legale"])
        self.assertFalse(manifeste["causalite_mondiale_prouvee"])
        self.assertGreater(manifeste["nb_fichiers"], 0)

        statut, donnees, _ = self.client.json("GET", "/api/v1/oeuvre_universelle")
        self.assertEqual(statut, 200)
        self.assertTrue(donnees["succes"])

    def test_08_hypothese_riemann(self):
        statut, entetes, corps = self.client.requete("GET", "/riemann")
        self.assertEqual(statut, 200)
        self.assertIn("text/html", entetes.get("Content-Type", ""))
        self.assertIn("Hypothèse de Riemann", corps)
        self.assertIn("non démontrée", corps)
        self.assertIn("/hypothese-riemann.pdf", corps)

        for route, marqueur in (
            ("/riemann/en", "Riemann hypothesis"),
            ("/riemann/ar", "فرضية ريمان"),
            ("/hypothese-riemann/en", "Riemann hypothesis"),
            ("/hypothese-riemann/ar", "فرضية ريمان"),
            ("/oeuvre-universelle/riemann", "Hypothèse de Riemann"),
            ("/oeuvre-universelle/riemann/en", "Riemann hypothesis"),
            ("/oeuvre-universelle/riemann/ar", "فرضية ريمان"),
        ):
            statut, entetes, page = self.client.requete("GET", route)
            self.assertEqual(statut, 200, route)
            self.assertIn("charset=utf-8", entetes.get("Content-Type", "").lower(), route)
            self.assertIn(marqueur, page, route)

        web = Path(__file__).resolve().parent.parent / "web_cloud"
        pdf_local = web / "hypothese_riemann.pdf"
        self.assertTrue(pdf_local.is_file())
        statut, entetes, _ = self.client.requete("GET", "/hypothese-riemann.pdf")
        self.assertEqual(statut, 200)
        self.assertEqual(entetes.get("Content-Type"), "application/pdf")
        self.assertEqual(int(entetes.get("Content-Length", "0")), pdf_local.stat().st_size)
        self.assertEqual(pdf_local.read_bytes()[:4], b"%PDF")

        statut, entetes, _ = self.client.requete("GET", "/hypothese_riemann.png")
        self.assertEqual(statut, 200)
        self.assertEqual(entetes.get("Content-Type"), "image/png")


if __name__ == "__main__":
    unittest.main()
