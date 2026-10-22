#!/bin/bash
# ==============================================================================
# SCRIPT DE DÉPLOIEMENT AUTOMATISÉ VPS UBUNTU — AL-MIZAN & ASTRO-Q°ODE
# Auteur : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI)
# DOI Zenodo Officiel : 10.5281/zenodo.23554838
# ==============================================================================
set -euo pipefail

echo "================================================================================"
echo "    DÉPLOIEMENT DU NOEUD RÉSIDENT AL-MIZAN & ASTRO-Q°ODE SUR VPS UBUNTU"
echo "    DOI Zenodo : 10.5281/zenodo.23554838 · Clé Dorée : 0xc9550dd0a57c609494dbc44450df48d798ebfb0b"
echo "================================================================================"

INSTALL_DIR="/opt/al-mizan"
USER_NAME="almizan"

if [[ $EUID -ne 0 ]]; then
   echo "[ERREUR] Ce script doit être exécuté en tant que root (sudo)."
   exit 1
fi

echo "[1/6] Mise à jour des dépôts et paquets essentiels..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl ufw

echo "[2/6] Création de l'utilisateur dédié $USER_NAME..."
if ! id "$USER_NAME" &>/dev/null; then
    useradd -r -m -d "$INSTALL_DIR" -s /bin/bash "$USER_NAME"
fi

echo "[3/6] Déploiement des sources et permissions..."
mkdir -p "$INSTALL_DIR"
chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR"

echo "[4/6] Configuration des services systemd..."
cp systemd/al-mizan-synchron-mzn.service /etc/systemd/system/
cp systemd/al-mizan-permanence.service /etc/systemd/system/
systemctl daemon-reload

echo "[5/6] Activation et démarrage des services résidents..."
systemctl enable al-mizan-synchron-mzn.service
systemctl enable al-mizan-permanence.service
systemctl restart al-mizan-synchron-mzn.service
systemctl restart al-mizan-permanence.service

echo "[6/6] Configuration du Pare-feu (UFW)..."
ufw allow 8766/tcp comment 'Al-Mizan HTTPS Permanence'
ufw allow 8765/tcp comment 'Al-Mizan HTTP Porte'
ufw allow 8000/tcp comment 'Al-Mizan Dashboard'
ufw allow 5030/tcp comment 'Al-Mizan Die Silicium'

echo "================================================================================"
echo "[SUCCÈS] Nœud résident Al-Mizan déployé et actif en arrière-plan continu !"
echo "Vérifiez le statut : systemctl status al-mizan-synchron-mzn"
echo "Journal en direct  : journalctl -u al-mizan-synchron-mzn -f"
echo "================================================================================"
