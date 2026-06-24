# pdf-trad

> **Outil pour traduire des PDFs scannés en conservant le layout original**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🎯 **Fonctionnalités**

- ✅ **Extraction OCR** : Convertit les PDFs scannés en texte avec `Tesseract` (pytesseract).
- ✅ **Détection de Layout** : Identifie les zones de texte (blocs, colonnes, en-têtes, pieds de page).
- ✅ **Traduction Automatique** : Traduit le texte de l'**anglais vers le français** via une **API OpenAI locale** (Llama, Mistral, etc.).
- ✅ **Conservation du Layout** : Génère un nouveau PDF avec le texte traduit **en conservant la mise en page originale** (positions, polices, tailles).
- ✅ **Interface CLI** : Outil en ligne de commande simple et efficace.

---

## 📋 **Prérequis**

### 1. **Système d'exploitation**
- Linux (recommandé)
- macOS
- Windows (avec WSL pour Tesseract)

### 2. **Dépendances système**

#### **Tesseract OCR**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev

# macOS (avec Homebrew)
brew install tesseract

# Windows (avec Chocolatey)
choco install tesseract
```

#### **Poppler (pour pdf2image)**
```bash
# Ubuntu/Debian
sudo apt install -y poppler-utils

# macOS
brew install poppler

# Windows (avec Chocolatey)
choco install poppler
```

### 3. **API OpenAI Locale**
Pour la traduction, vous avez besoin d'une **API OpenAI locale** (ex: Llama, Mistral).

#### **Option 1: llama-cpp** (recommandé)
```bash
# Installer llama-cpp
pip install llama-cpp-python

# Télécharger un modèle (ex: Llama 2 7B)
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/resolve/main/llama-2-7b-chat.ggmlv3.q4_0.bin

# Démarrer le serveur
python -m llama_cpp.server --model llama-2-7b-chat.ggmlv3.q4_0.bin --port 8000
```

#### **Option 2: text-generation-webui**
```bash
# Cloner le dépôt
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui

# Installer les dépendances
pip install -r requirements.txt

# Télécharger un modèle (ex: Mistral 7B)
python download-model.py --model mistralai/Mistral-7B-Instruct-v0.1

# Démarrer le serveur
python server.py --model mistral-7b-instruct-v0.1 --api
```

---

## 🚀 **Installation**

### **Avec Poetry (recommandé)**
```bash
# Cloner le dépôt
git clone https://github.com/EricDelannoy/pdf-trad.git
cd pdf-trad

# Installer les dépendances
poetry install

# Activer l'environnement virtuel
poetry shell
```

### **Avec pip**
```bash
# Cloner le dépôt
git clone https://github.com/EricDelannoy/pdf-trad.git
cd pdf-trad

# Installer les dépendances
pip install -e .
```

### **Avec Docker**
```bash
# Construire l'image
docker build -t pdf-trad .

# Exécuter le conteneur (avec montage du volume pour les PDFs)
docker run -it --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -p 8000:8000 \
  pdf-trad
```

---

## 💡 **Utilisation**

### **1. Traduire un PDF**
```bash
# Commande de base
pdf-trad translate input.pdf output.pdf

# Avec des options personnalisées
pdf-trad translate input.pdf output.pdf \
  --dpi 300 \
  --base-url http://localhost:8000/v1 \
  --model llama-2-7b-chat \
  --method pymupdf
```

### **2. Mode Débogage**
Affiche les informations de layout et d'OCR sans générer de PDF :
```bash
pdf-trad debug input.pdf
```

### **3. Traduire un dossier de PDFs**
```bash
pdf-trad batch ./input/ ./output/ --dpi 300
```

### **4. Options disponibles**
| Option | Description | Défaut |
|--------|-------------|--------|
| `--dpi` | Résolution pour la conversion PDF → image | `300` |
| `--lang` | Langue source du texte | `en` |
| `--base-url` | URL de l'API OpenAI locale | `http://localhost:8000/v1` |
| `--model` | Modèle OpenAI à utiliser | `llama-2-7b-chat` |
| `--method` | Méthode de reconstruction (`pymupdf` ou `reportlab`) | `pymupdf` |
| `--debug` | Affiche les informations de débogage | `False` |

---

## 📁 **Structure du Projet**

```
pdf-trad/
├── src/
│   └── pdf_trad/
│       ├── __init__.py          # Exports principaux
│       ├── ocr.py                # Extraction OCR (Tesseract)
│       ├── layout.py             # Détection de layout
│       ├── translation.py        # Traduction (API OpenAI locale)
│       ├── pdf_rebuilder.py      # Reconstruction du PDF
│       └── cli.py                # Interface en ligne de commande
├── tests/                       # Tests unitaires
├── examples/
│   ├── input/                   # PDFs d'exemple (à traduire)
│   └── output/                  # PDFs traduits (sortie)
├── docs/                        # Documentation technique
├── .github/
│   └── workflows/               # Workflows GitHub Actions
├── pyproject.toml               # Configuration du projet (Poetry)
├── README.md                    # Ce fichier
├── ROADMAP.md                   # Feuille de route du projet
├── LICENSE                      # Licence MIT
└── .gitignore
```

---

## 🔧 **Configuration**

### **Fichier `config.yaml`**
Créez un fichier `config.yaml` à la racine du projet pour personnaliser les paramètres :

```yaml
openai:
  base_url: "http://localhost:8000/v1"
  api_key: "dummy"  # Non utilisé en local
  model: "llama-2-7b-chat"
  temperature: 0.1
  max_tokens: 2048

translation:
  from_lang: "en"
  to_lang: "fr"
  cache_enabled: true  # Cache les traductions pour éviter de re-traduire
```

---

## 🧪 **Tests**

### **Exécuter les tests**
```bash
# Avec Poetry
poetry run pytest

# Avec coverage
poetry run pytest --cov=src/pdf_trad --cov-report=html
```

### **Exemple de test**
```python
# tests/test_ocr.py
def test_extract_text_from_image():
    from pdf_trad.ocr import extract_text_from_image
    import cv2
    import numpy as np
    
    # Créer une image de test
    image = np.zeros((100, 400, 3), dtype=np.uint8)
    cv2.putText(image, "Hello World", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Extraire le texte
    result = extract_text_from_image(image, lang="eng", preprocess=False)
    
    assert "Hello World" in result["text"]
```

---

## 📊 **Workflow Complet**

1. **Préparation** :
   - Installer Tesseract, Poppler et une API OpenAI locale.
   - Cloner le dépôt et installer les dépendances.

2. **Traduction** :
   ```bash
   pdf-trad translate input.pdf output.pdf --base-url http://localhost:8000/v1
   ```

3. **Vérification** :
   - Ouvrir `output.pdf` et vérifier que le texte est traduit et le layout conservé.

---

## 🐛 **Dépannage**

### **Problème: Tesseract non trouvé**
```bash
# Vérifier l'installation
which tesseract

# Réinstaller si nécessaire
sudo apt install --reinstall tesseract-ocr
```

### **Problème: Erreur de conversion PDF → image**
```bash
# Vérifier que Poppler est installé
which pdftoppm

# Installer Poppler
sudo apt install poppler-utils
```

### **Problème: API OpenAI locale non accessible**
```bash
# Vérifier que le serveur est en cours d'exécution
curl http://localhost:8000/v1/models

# Démarrer le serveur (ex: llama-cpp)
python -m llama_cpp.server --model llama-2-7b-chat.ggmlv3.q4_0.bin --port 8000
```

### **Problème: Texte mal détecté (OCR)**
- **Solution 1** : Augmenter la résolution (`--dpi 600`).
- **Solution 2** : Désactiver le prétraitement (`--no-preprocess`).
- **Solution 3** : Vérifier la qualité du PDF scanné.

---

## 📚 **Documentation Technique**

- [Feuille de Route (ROADMAP.md)](ROADMAP.md) : Étapes de développement et calendrier.
- [API des Modules](docs/API.md) : Documentation détaillée des fonctions.
- [Architecture](docs/ARCHITECTURE.md) : Schéma d'architecture du projet.

---

## 🤝 **Contribution**

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails.

### **Étapes pour contribuer**
1. Forker le dépôt.
2. Créer une branche (`git checkout -b feature/ma-fonctionnalité`).
3. Commiter vos changements (`git commit -m "Ajout de ma fonctionnalité"`).
4. Pousser vers la branche (`git push origin feature/ma-fonctionnalité`).
5. Ouvrir une Pull Request.

---

## 📜 **Licence**

Ce projet est sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 **Remerciements**

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) pour l'extraction de texte.
- [PyMuPDF](https://pymupdf.readthedocs.io/) pour la manipulation de PDFs.
- [OpenCV](https://opencv.org/) pour le traitement d'images.
- [Llama.cpp](https://github.com/ggerganov/llama.cpp) pour l'exécution locale de modèles de langage.
- [Click](https://click.palletsprojects.com/) pour l'interface CLI.

---

## 📧 **Contact**

Pour toute question ou suggestion, n'hésitez pas à ouvrir une **Issue** ou un **Discussion** sur GitHub :

👉 [https://github.com/EricDelannoy/pdf-trad](https://github.com/EricDelannoy/pdf-trad)
