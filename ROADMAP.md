# Feuille de Route - pdf-trad

> **Objectif** : Outil pour identifier les zones de texte dans un PDF scanné, les traduire en français (via API OpenAI locale), et générer un nouveau PDF avec le texte traduit **en conservant le layout original**.

---

## 🎯 Contexte
- **Problématique** : Les PDFs scannés (images) contiennent du texte non sélectable. Les outils classiques (Adobe Acrobat, Online OCR) ne préservent pas la mise en page complexe (colonnes, tableaux, zones positionnées).
- **Solution** : 
  1. Extraire le texte + sa position via **OCR** (Tesseract).
  2. Identifier les **zones de texte** (blocs logiques) et leur hiérarchie.
  3. Traduire le texte (anglais → français) via **API OpenAI locale**.
  4. Reconstruire un PDF avec le texte traduit **en conservant le layout** (polices, tailles, couleurs, positions).

---

## 📌 Étapes Clés

### ✅ Phase 0 : Initialisation (1 semaine)
- [x] Créer la structure du dépôt (dossiers, fichiers de base).
- [x] Ajouter `ROADMAP.md`, `README.md`, `LICENSE` (MIT).
- [x] Configurer `pyproject.toml` (Poetry) et dépendances initiales.
- [x] Configurer GitHub Actions pour les tests et la CI.
- [ ] Mettre en place un template pour les issues/PRs.

**Livrables** :
- Dépôt GitHub structuré et prêt pour le développement.
- Environnement Python configuré (Poetry).

---

### 🔍 Phase 1 : Extraction OCR (2-3 semaines)
**Objectif** : Extraire le texte et ses **coordonnées précises** depuis un PDF scanné.

- [ ] Implémenter `src/pdf_trad/ocr.py` :
  - Conversion PDF → Images (1 page = 1 image) via `pdf2image`.
  - Pré-traitement des images (`OpenCV`) :
    - Binarisation (seuillage adaptatif).
    - Débruitage (filtres morphologiques).
    - Correction de l'inclinaison (déskew).
  - Extraction OCR avec `pytesseract` :
    - Mode **`--psm 6`** (bloc de texte uniforme) ou **`--psm 11`** (texte sparse).
    - Récupération des **coordonnées des mots** (`left`, `top`, `width`, `height`).
    - Détection de la langue (anglais par défaut).
- [ ] Gérer les erreurs :
  - PDFs corrompus ou protégés.
  - Images de mauvaise qualité (résolution < 150 DPI).
- [ ] Tests unitaires pour `ocr.py` (PDFs d'exemple dans `examples/`).

**Dépendances** :
```toml
pytesseract==0.3.10
pdf2image==1.16.3
opencv-python==4.8.0
Pillow==10.0.0
pymupdf==1.23.5  # Pour la reconstruction plus tard
```

**Livrables** :
- Module `ocr.py` fonctionnel.
- Script de test `tests/test_ocr.py`.
- Exemples de PDFs scannés dans `examples/input/`.

---

### 🧩 Phase 2 : Détection de Layout (3-4 semaines)
**Objectif** : Identifier les **zones de texte logiques** (paragraphes, colonnes, tableaux) et leur hiérarchie.

- [ ] Implémenter `src/pdf_trad/layout.py` :
  - Regrouper les mots OCR en **lignes** (même `top` ± tolérance).
  - Regrouper les lignes en **blocs** (même `left` ou alignement vertical).
  - Détecter les **colonnes** (blocs alignés verticalement).
  - Détecter les **tableaux** (grilles de lignes/colonnes) via `OpenCV` (contours) ou `pdfplumber`.
  - Conserver les **métadonnées** pour chaque zone :
    - Coordonnées (`x`, `y`, `width`, `height`).
    - Style (police, taille, couleur, gras/italique).
    - Ordre de lecture (pour la traduction cohérente).
- [ ] Intégrer avec `ocr.py` :
  - Prendre en entrée les résultats bruts de Tesseract.
  - Retourner une structure JSON/objet Python avec les zones organisées.
- [ ] Tests unitaires pour `layout.py`.

**Dépendances** :
```toml
layoutparser==0.3.4  # Pour la détection de layout avancée
pdfplumber==0.10.3   # Alternative pour les tableaux
scikit-image==0.21.0  # Traitement d'image avancé
```

**Livrables** :
- Module `layout.py` fonctionnel.
- Structure de données pour représenter le layout (ex: `LayoutZone`, `TextBlock`).
- Visualisation du layout (option `--debug` pour afficher les zones détectées).

---

### 🌍 Phase 3 : Traduction (2 semaines)
**Objectif** : Traduire le texte extrait (anglais → français) via **API OpenAI locale**.

- [ ] Implémenter `src/pdf_trad/translation.py` :
  - Intégration avec l'API OpenAI locale (ex: `llama-cpp` ou serveur local).
  - Configuration :
    - Modèle : `llama2-7b` ou `mistral-7b` (fine-tuné pour la traduction si possible).
    - Prompt système : `"Tu es un traducteur professionnel. Traduis ce texte de l'anglais vers le français en conservant le style et la structure. Ne modifie pas les balises ou les placeholders."`
    - Gestion des **blocs de texte** (pas de traduction ligne par ligne).
  - Optimisations :
    - Cache des traductions (éviter de re-traduire le même texte).
    - Batch processing (envoyer plusieurs blocs en une seule requête si possible).
    - Gestion des erreurs (timeout, modèle non disponible).
- [ ] Pré-traitement du texte :
  - Nettoyage (suppression des artefacts OCR comme `"lIke"` au lieu de `"like"`).
  - Détection des **non-texte** (numéros de page, en-têtes/pieds de page) à exclure.
- [ ] Post-traitement :
  - Ajustement des **sauts de ligne** et **espaces** pour correspondre au layout.
  - Vérification de la longueur du texte traduit (si > 20% plus long, réduire la taille de police).

**Dépendances** :
```toml
openai==1.3.0       # Pour l'API locale (compatible avec les serveurs OpenAI)
llama-cpp-python==0.2.0  # Alternative pour exécuter Llama localement
requests==2.31.0    # Pour les requêtes HTTP si API REST
```

**Livrables** :
- Module `translation.py` fonctionnel.
- Configuration pour l'API OpenAI locale (fichier `config.yaml` ou variables d'environnement).
- Tests avec des exemples de texte anglais → français.

---

### 📄 Phase 4 : Reconstruction du PDF (3-4 semaines)
**Objectif** : Générer un nouveau PDF avec le texte traduit **en conservant le layout original**.

- [ ] Implémenter `src/pdf_trad/pdf_rebuilder.py` :
  - **Approche 1** (modification directe) :
    - Utiliser `PyMuPDF` pour **éditer le texte en place** si le PDF original contient des polices embarquées.
    - Remplacer le texte par la traduction en gardant les mêmes `x`, `y`, `font`, `size`, `color`.
  - **Approche 2** (génération depuis zéro) :
    - Créer un PDF vierge avec `reportlab` ou `fpdf2`.
    - Dessiner chaque zone de texte aux coordonnées originales.
    - Gérer les **polices** :
      - Si la police originale est disponible, l'utiliser.
      - Sinon, utiliser une police par défaut (ex: `Arial`, `Helvetica`).
    - Gérer les **images** (logos, graphiques) : les copier depuis l'original.
  - **Gestion des cas complexes** :
    - Texte traduit plus long que l'original → réduire la taille de police ou ajuster les marges.
    - Texte avec **alignement** (gauche, centré, droite, justifié).
    - Texte **vertical** ou **roté**.
- [ ] Intégration avec les autres modules :
  - Prendre en entrée les résultats de `layout.py` + `translation.py`.
  - Générer un PDF de sortie dans `examples/output/`.

**Dépendances** :
```toml
pymupdf==1.23.5    # Pour la modification directe
reportlab==4.0.4   # Pour la génération depuis zéro
fpdf2==2.7.6       # Alternative légère à reportlab
```

**Livrables** :
- Module `pdf_rebuilder.py` fonctionnel.
- PDFs de test dans `examples/output/` (comparaison avant/après).
- Script pour valider visuellement la conservation du layout.

---

### 🧪 Phase 5 : Tests & Validation (2 semaines)
**Objectif** : Garantir la qualité et la robustesse de l'outil.

- [ ] **Tests unitaires** :
  - Couverture à 90%+ pour `ocr.py`, `layout.py`, `translation.py`, `pdf_rebuilder.py`.
  - Utiliser `pytest` + `pytest-cov`.
- [ ] **Tests d'intégration** :
  - Workflow complet : PDF scanné → OCR → Layout → Traduction → PDF traduit.
  - Validation sur des PDFs **complexes** (multi-colonnes, tableaux, images).
- [ ] **Validation manuelle** :
  - Comparaison visuelle des PDFs originaux vs. traduits.
  - Vérification de la **fidélité du layout** (outils comme `diff-pdf`).
- [ ] **Benchmark** :
  - Mesurer les performances (temps de traitement par page).
  - Optimiser les goulots d'étranglement (ex: OCR, appels API).

**Livrables** :
- Suite de tests complète dans `tests/`.
- Rapport de couverture (via GitHub Actions).
- Jeu de données de test (PDFs + résultats attendus).

---

### 🖥️ Phase 6 : CLI & Documentation (1 semaine)
**Objectif** : Rendre l'outil utilisable par les utilisateurs finaux.

- [ ] Implémenter `src/pdf_trad/cli.py` :
  - Interface en ligne de commande avec `click` ou `argparse`.
  - Commandes :
    ```bash
    pdf-trad translate input.pdf output.pdf --model-path ./models/llama-2-7b --language en-fr
    pdf-trad debug input.pdf --show-layout  # Affiche les zones détectées
    pdf-trad batch ./input/ ./output/       # Traite un dossier de PDFs
    ```
  - Options :
    - `--dpi` : Résolution pour la conversion PDF → image (défaut: 300).
    - `--force-ocr` : Forcer l'OCR même si le PDF contient déjà du texte.
    - `--skip-images` : Ignorer les images (ne traiter que le texte).
- [ ] **Documentation** :
  - `README.md` : Guide d'installation et d'utilisation.
  - `docs/` : Documentation technique (architecture, API des modules).
  - Exemples d'utilisation dans `examples/`.

**Dépendances** :
```toml
click==8.1.7  # Pour la CLI
```

**Livrables** :
- CLI fonctionnelle et documentée.
- `README.md` complet avec :
  - Instructions d'installation (Poetry, Docker).
  - Exemples de commandes.
  - Capture d'écran du workflow.

---

### 🚀 Phase 7 : Déploiement (1 semaine)
**Objectif** : Publier l'outil pour une utilisation facile.

- [ ] **Publication PyPI** :
  - Configurer `pyproject.toml` pour la publication.
  - Générer un package `pdf-trad` installable via `pip`.
- [ ] **Image Docker** :
  - Créer un `Dockerfile` avec toutes les dépendances (Tesseract, OpenCV, Python).
  - Publier sur Docker Hub/GitHub Container Registry.
- [ ] **GitHub Actions** :
  - Workflow pour publier automatiquement sur PyPI/Docker Hub.
  - Workflow pour exécuter les tests à chaque push/PR.
- [ ] **Release GitHub** :
  - Créer une release `v1.0.0` avec les binaires et la documentation.

**Livrables** :
- Package PyPI : `pip install pdf-trad`.
- Image Docker : `docker pull ericdelannoy/pdf-trad`.
- Workflows GitHub Actions configurés.

---

## 📅 Calendrier Prévisionnel
| **Phase**               | **Durée**   | **Date de Début** | **Date de Fin**   | **Responsable** |
|--------------------------|-------------|-------------------|-------------------|-----------------|
| Phase 0 : Initialisation | 1 semaine    | 2026-06-24        | 2026-07-01        | Eric            |
| Phase 1 : Extraction OCR  | 3 semaines   | 2026-07-01        | 2026-07-22        | Eric            |
| Phase 2 : Détection Layout| 4 semaines   | 2026-07-22        | 2026-08-19        | Eric            |
| Phase 3 : Traduction      | 2 semaines   | 2026-08-19        | 2026-09-02        | Eric            |
| Phase 4 : Reconstruction  | 4 semaines   | 2026-09-02        | 2026-09-30        | Eric            |
| Phase 5 : Tests           | 2 semaines   | 2026-09-30        | 2026-10-14        | Eric            |
| Phase 6 : CLI & Docs      | 1 semaine    | 2026-10-14        | 2026-10-21        | Eric            |
| Phase 7 : Déploiement     | 1 semaine    | 2026-10-21        | 2026-10-28        | Eric            |

**Date de livraison estimée** : **28 octobre 2026** (version 1.0.0).

---

## 🔧 Configuration Technique

### Environnement de Développement
- **Langage** : Python 3.10+.
- **Gestionnaire de dépendances** : Poetry.
- **OCR** : Tesseract 5.3+ (installé via `apt` ou `brew`).
- **API OpenAI locale** : 
  - Modèle : `llama-2-7b-chat` ou `mistral-7b-instruct` (fine-tuné pour la traduction).
  - Serveur : `llama-cpp` ou `text-generation-webui`.
  - Exemple de configuration :
    ```yaml
    # config.yaml
    openai:
      base_url: "http://localhost:8000/v1"  # URL du serveur local
      api_key: "dummy"  # Non utilisé en local
      model: "llama-2-7b-chat"
      temperature: 0.1
      max_tokens: 2048
    ```

### Dépendances Principales
| **Catégorie**       | **Librairie**          | **Version** | **Usage**                          |
|----------------------|------------------------|-------------|------------------------------------|
| OCR                  | pytesseract           | 0.3.10      | Extraction de texte depuis images.|
| PDF                  | pymupdf                | 1.23.5      | Lecture/écriture de PDFs.          |
|                      | pdf2image             | 1.16.3      | Conversion PDF → images.           |
| Image Processing     | opencv-python         | 4.8.0       | Pré-traitement des images.         |
|                      | Pillow                | 10.0.0      | Manipulation d'images.             |
| Layout Detection     | layoutparser          | 0.3.4       | Détection de zones de texte.       |
|                      | pdfplumber            | 0.10.3      | Extraction de tableaux.            |
| Traduction           | openai                | 1.3.0       | Appels à l'API OpenAI locale.      |
|                      | llama-cpp-python      | 0.2.0       | Exécution locale de Llama.         |
| CLI                  | click                 | 8.1.7       | Interface en ligne de commande.    |
| Tests                | pytest                | 7.4.0       | Tests unitaires.                   |
|                      | pytest-cov            | 4.1.0       | Couverture de code.                |

---

## 📊 Métriques de Succès
- **Précision OCR** : > 95% sur des PDFs scannés à 300 DPI.
- **Conservation du Layout** : 100% des zones de texte positionnées correctement (tolérance : ±2 pixels).
- **Qualité de Traduction** : Score BLEU > 80 (anglais → français).
- **Performances** : < 5 secondes par page (OCR + traduction + reconstruction).
- **Couverture de Tests** : > 90%.

---

## 🚨 Risques et Atténuation

| **Risque**                          | **Impact** | **Probabilité** | **Atténuation**                                                                 |
|--------------------------------------|------------|-----------------|---------------------------------------------------------------------------------|
| Mauvaise qualité OCR                 | Élevé      | Moyenne         | Pré-traitement avancé des images + validation manuelle des résultats.         |
| Layout complexe non détecté          | Élevé      | Moyenne         | Utiliser `layoutparser` + règles personnalisées pour les cas spécifiques.       |
| API OpenAI locale lente              | Moyen      | Faible          | Optimiser les requêtes (batch) + cache des traductions.                          |
| Polices manquantes dans le PDF final  | Moyen      | Moyenne         | Embarquer des polices par défaut (ex: DejaVu Sans).                              |
| Texte traduit trop long               | Faible     | Moyenne         | Réduire la taille de police ou ajuster les marges dynamiquement.               |
| Problèmes de compatibilité PDF        | Faible     | Faible          | Utiliser `PyMuPDF` (compatible avec la plupart des PDFs).                        |

---

## 📚 Ressources Utiles
- **OCR** :
  - [Tesseract Documentation](https://github.com/tesseract-ocr/tesseract)
  - [pytesseract Tutorial](https://pytesseract.readthedocs.io/en/latest/)
- **PDF Processing** :
  - [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/)
  - [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)
- **Layout Detection** :
  - [LayoutParser](https://layout-parser.readthedocs.io/en/latest/)
- **Traduction** :
  - [OpenAI API (Local)](https://github.com/openai/openai-python)
  - [llama-cpp](https://github.com/abetlen/llama-cpp-python)
- **Reconstruction PDF** :
  - [ReportLab Documentation](https://docs.reportlab.com/)

---

## 💬 Contribution
Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails.

---

## 📜 Licence
Ce projet est sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.
