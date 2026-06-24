# Dockerfile pour pdf-trad
# Utilise une image Python officielle avec les dépendances système nécessaires

FROM python:3.10-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    # PDF
    poppler-utils \
    # Autres
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer Poetry
RUN pip install poetry==1.7.0

# Copier les fichiers du projet
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Installer les dépendances Python
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root

# Copier le reste du projet
COPY . .

# Installer le package en mode éditable
RUN poetry install --no-interaction

# Créer un utilisateur non-root pour exécuter l'application
RUN useradd -m -u 1000 pdftrad
USER pdftrad

# Définir le point d'entrée
ENTRYPOINT ["poetry", "run", "pdf-trad"]
CMD ["--help"]

# Exposer le port pour l'API OpenAI locale (optionnel)
EXPOSE 8000
