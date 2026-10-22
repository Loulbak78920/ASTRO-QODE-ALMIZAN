# Dockerfile pour Al-Mizan & ASTRO-Q°ODE sur VPS Ubuntu Linux
FROM ubuntu:24.04

LABEL maintainer="M. Ahmed EL BAHLOUL <elbahloulahmed505@gmail.com>"
LABEL description="Al-Mizan & ASTRO-Q°ODE Resident Node VPS - DOI 10.5281/zenodo.23554838"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/opt/al-mizan:/opt/al-mizan/runtime:/opt/al-mizan/outils_sans_usine"

# Installation des paquets système indispensables
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    ca-certificates \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Création du groupe et de l'utilisateur dédié
RUN groupadd -r almizan && useradd -r -g almizan -d /opt/al-mizan -s /bin/bash almizan

WORKDIR /opt/al-mizan

# Copie des fichiers système
COPY . /opt/al-mizan/

RUN chown -R almizan:almizan /opt/al-mizan

USER almizan

# Ports exposes :
# 5025: AWG SCPI | 5026: Cryo | 5030: Die Silicium | 8000: Dashboard | 8765: HTTP Porte | 8766: HTTPS Permanence
EXPOSE 5025 5026 5030 8000 8765 8766

CMD ["python3", "/opt/al-mizan/runtime/q0_fusion/daemon_synchron_mzn_resident.py", "--interval", "2.0"]
