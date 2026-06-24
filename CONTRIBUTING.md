# Contribution à pdf-trad

Merci de votre intérêt pour contribuer à **pdf-trad** ! Ce guide vous explique comment participer au projet.

---

## 📌 **Code de Conduite**

En participant à ce projet, vous acceptez de respecter notre [Code de Conduite](CODE_OF_CONDUCT.md). Soyez bienveillant, respectueux et constructif.

---

## 🚀 **Comment Contribuer**

### **1. Signaler un Bug**

Si vous trouvez un bug, merci de :

1. Vérifier que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/EricDelannoy/pdf-trad/issues).
2. Créer une nouvelle Issue avec :
   - Un **titre clair et descriptif**.
   - Une **description détaillée** du problème (étapes pour reproduire, comportement attendu, comportement réel).
   - Un **exemple de PDF** (si possible) pour reproduire le bug.
   - Votre **environnement** (OS, version de Python, dépendances installées).

### **2. Proposer une Fonctionnalité**

Si vous avez une idée pour améliorer le projet :

1. Vérifier que la fonctionnalité n'a pas déjà été proposée dans les [Issues](https://github.com/EricDelannoy/pdf-trad/issues) ou les [Discussions](https://github.com/EricDelannoy/pdf-trad/discussions).
2. Créer une nouvelle Issue avec :
   - Un **titre clair** (ex: "[Feature Request] Ajout du support des tableaux").
   - Une **description détaillée** de la fonctionnalité.
   - Les **avantages** pour le projet.
   - Un **exemple d'utilisation** (si applicable).

### **3. Contribuer au Code**

#### **Étapes pour soumettre une Pull Request (PR)**

1. **Forker le dépôt** :
   - Cliquez sur le bouton "Fork" en haut à droite de la page du dépôt.
   - Clonez votre fork localement :
     ```bash
     git clone https://github.com/votre-utilisateur/pdf-trad.git
     cd pdf-trad
     ```

2. **Configurer l'environnement** :
   - Installez les dépendances avec Poetry :
     ```bash
     poetry install
     ```
   - Activez l'environnement virtuel :
     ```bash
     poetry shell
     ```

3. **Créer une branche** :
   - Créez une branche pour votre fonctionnalité ou correction :
     ```bash
     git checkout -b feature/ma-fonctionnalité
     # ou
     git checkout -b fix/mon-bug
     ```

4. **Faire vos modifications** :
   - Suivez les [conventions de codage](#-conventions-de-codage) ci-dessous.
   - Ajoutez des **tests** pour vos modifications (voir [Tests](#-tests)).
   - Mettez à jour la **documentation** si nécessaire.

5. **Commiter vos changements** :
   - Utilisez des messages de commit **clairs et descriptifs** :
     ```bash
     git commit -m "Ajout du support des tableaux dans la détection de layout"
     ```
   - Suivez les [conventions de commit](#-conventions-de-commit).

6. **Pousser vers votre fork** :
   ```bash
   git push origin feature/ma-fonctionnalité
   ```

7. **Ouvrir une Pull Request** :
   - Allez sur la page du dépôt original : [https://github.com/EricDelannoy/pdf-trad](https://github.com/EricDelannoy/pdf-trad).
   - Cliquez sur "New Pull Request".
   - Sélectionnez votre branche comme "compare" et la branche `main` comme "base".
   - Remplissez le **titre** et la **description** de la PR :
     - **Titre** : Court et descriptif (ex: "Ajout du support des tableaux").
     - **Description** :
       - Décrivez vos modifications.
       - Expliquez **pourquoi** ces modifications sont nécessaires.
       - Mentionnez les **Issues** liées (ex: "Fixes #123").
       - Ajoutez des **captures d'écran** si applicable.

8. **Attendre la revue** :
   - Un mainteneur examinera votre PR et pourra demander des modifications.
   - Répondez aux commentaires et mettez à jour votre PR si nécessaire.

---

## 📜 **Conventions de Codage**

### **1. Style de Code**

- **Python** : Suivez les [PEP 8](https://peps.python.org/pep-0008/) et utilisez [Black](https://github.com/psf/black) pour le formatage.
  - Exécutez Black avant de commiter :
    ```bash
    poetry run black src/ tests/
    ```
- **Imports** : Utilisez `isort` pour trier les imports.
  - Exécutez isort avant de commiter :
    ```bash
    poetry run isort src/ tests/
    ```
- **Noms de variables/fonctions** : Utilisez `snake_case` pour les variables et fonctions, `PascalCase` pour les classes.
- **Docstrings** : Utilisez le format [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) pour les docstrings.

### **2. Exemple de Code**

```python
"""Module pour la détection de layout dans les PDFs."""

from typing import List, Dict, Any


def detect_columns(
    blocks: List[Dict[str, Any]],
    min_width: int = 100,
) -> List[List[Dict[str, Any]]]:
    """
    Détecte les colonnes dans une page à partir des blocs de texte.
    
    Args:
        blocks: Liste de blocs de texte avec leurs coordonnées.
        min_width: Largeur minimale pour considérer un groupe comme une colonne.
    
    Returns:
        Liste de colonnes (chaque colonne est une liste de blocs).
    
    Raises:
        ValueError: Si les blocs n'ont pas de coordonnées valides.
    """
    if not blocks:
        return []
    
    # Trier les blocs par coordonnée X
    blocks_sorted = sorted(blocks, key=lambda b: b["left"])
    
    columns = []
    current_column = [blocks_sorted[0]]
    
    for block in blocks_sorted[1:]:
        if abs(block["left"] - current_column[-1]["left"]) <= min_width:
            current_column.append(block)
        else:
            columns.append(current_column)
            current_column = [block]
    
    if current_column:
        columns.append(current_column)
    
    return columns
```

---

## 🧪 **Tests**

### **1. Écrire des Tests**

- Utilisez `pytest` pour écrire des tests unitaires.
- Placez les tests dans le dossier `tests/`.
- Nommez les fichiers de test avec le préfixe `test_` (ex: `test_ocr.py`).

### **2. Exemple de Test**

```python
# tests/test_ocr.py
import numpy as np
from pdf_trad.ocr import extract_text_from_image


def test_extract_text_from_image():
    """Test l'extraction de texte depuis une image simple."""
    # Créer une image de test avec du texte
    image = np.zeros((100, 400, 3), dtype=np.uint8)
    cv2.putText(
        image,
        "Hello World",
        (50, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )
    
    # Extraire le texte
    result = extract_text_from_image(image, lang="eng", preprocess=False)
    
    # Vérifier que le texte est extrait
    assert "Hello World" in result["text"]
    assert len(result["words"]) > 0
```

### **3. Exécuter les Tests**

```bash
# Exécuter tous les tests
poetry run pytest

# Exécuter les tests avec couverture de code
poetry run pytest --cov=src/pdf_trad --cov-report=html

# Exécuter un test spécifique
poetry run pytest tests/test_ocr.py::test_extract_text_from_image
```

### **4. Couverture de Code**

- Le projet vise une **couverture de code > 90%**.
- Utilisez `pytest-cov` pour générer un rapport de couverture.

---

## 📝 **Conventions de Commit**

Utilisez des messages de commit **clairs et descriptifs**. Suivez les conventions suivantes :

| Type de Commit | Préfixe | Exemple |
|---------------|---------|---------|
| Fonctionnalité | `feat:` | `feat: ajout du support des tableaux` |
| Correction | `fix:` | `fix: correction de l'extraction OCR pour les PDFs basse résolution` |
| Documentation | `docs:` | `docs: mise à jour du README` |
| Refactorisation | `refactor:` | `refactor: simplification du module layout` |
| Test | `test:` | `test: ajout de tests pour le module translation` |
| Chore | `chore:` | `chore: mise à jour des dépendances` |
| Style | `style:` | `style: formatage du code avec Black` |

### **Exemples de Messages de Commit**

```bash
# Bon
git commit -m "feat: ajout du support des colonnes dans la détection de layout"
git commit -m "fix: correction de la traduction des textes vides"
git commit -m "docs: ajout de la section installation dans le README"

# À éviter
git commit -m "fix bug"
git commit -m "wip"
git commit -m "mises à jour"
```

---

## 📁 **Structure des Pull Requests**

### **1. Titre**
- Court et descriptif (max 50 caractères).
- Utilisez le préfixe correspondant (ex: `[feat]`, `[fix]`).

### **2. Description**
- **Contexte** : Expliquez pourquoi cette PR est nécessaire.
- **Modifications** : Décrivez les changements apportés.
- **Issues liées** : Mentionnez les Issues résolues (ex: `Fixes #123`).
- **Captures d'écran** : Ajoutez des captures si applicable.
- **Tests** : Décrivez comment tester vos modifications.

### **3. Exemple de PR**

```markdown
## Description

Ajout du support des **tableaux** dans la détection de layout. Cette fonctionnalité permet de détecter les tableaux dans les PDFs scannés et de les traduire en conservant leur structure.

## Modifications
- Ajout de la fonction `detect_tables()` dans `src/pdf_trad/layout.py`.
- Mise à jour de la fonction `classify_zones()` pour gérer les tableaux.
- Ajout de tests unitaires dans `tests/test_layout.py`.

## Issues liées
- Fixes #45 (Support des tableaux)

## Tests
- Exécutez `poetry run pytest tests/test_layout.py` pour vérifier les nouveaux tests.
- Testez avec un PDF contenant des tableaux :
  ```bash
  pdf-trad translate input_with_tables.pdf output.pdf --debug
  ```

## Captures d'écran
![Avant](https://example.com/before.png)
![Après](https://example.com/after.png)
```

---

## 🔧 **Outils de Développement**

### **1. Pré-commit Hooks**

Le projet utilise des **hooks Git** pour automatiser la vérification du code avant les commits.

#### **Installation**
```bash
# Installer les hooks
poetry run pre-commit install
```

#### **Hooks Configurés**
- **Black** : Formatage automatique du code.
- **isort** : Tri automatique des imports.
- **flake8** : Vérification de la conformité PEP 8.
- **mypy** : Vérification des types (optionnel).

### **2. Vérification Manuelle**

Avant de soumettre une PR, exécutez les commandes suivantes :

```bash
# Formatage du code
poetry run black src/ tests/

# Tri des imports
poetry run isort src/ tests/

# Vérification PEP 8
poetry run flake8 src/ tests/

# Exécution des tests
poetry run pytest

# Vérification des types (optionnel)
poetry run mypy src/
```

---

## 📄 **Documentation**

### **1. Mettre à Jour la Documentation**

- La documentation est dans le dossier `docs/`.
- Mettez à jour le `README.md` si votre modification affecte l'utilisation du projet.
- Ajoutez des **docstrings** à vos fonctions et classes.

### **2. Générer la Documentation**

Le projet utilise [mkdocs](https://www.mkdocs.org/) pour générer la documentation.

```bash
# Installer mkdocs
poetry add mkdocs

# Générer la documentation
poetry run mkdocs build

# Servir la documentation localement
poetry run mkdocs serve
```

---

## 🤝 **Revue de Code**

### **1. Critères de Revue**

Votre PR sera revue selon les critères suivants :

- ✅ **Fonctionnalité** : La modification fonctionne-t-elle comme attendu ?
- ✅ **Tests** : Les tests couvrent-ils les nouveaux cas d'utilisation ?
- ✅ **Code** : Le code suit-il les conventions du projet ?
- ✅ **Documentation** : La documentation est-elle à jour ?
- ✅ **Performances** : La modification a-t-elle un impact négatif sur les performances ?
- ✅ **Sécurité** : La modification introduit-elle des vulnérabilités ?

### **2. Répondre aux Commentaires**

- Répondez aux commentaires des mainteneurs.
- Mettez à jour votre PR si des modifications sont demandées.
- Utilisez des **commits supplémentaires** pour apporter des corrections.

---

## 🎉 **Reconnaissance**

Toutes les contributions sont **reconnues** ! Les contributeurs actifs peuvent être ajoutés à la section **Contributeurs** du `README.md`.

---

## 📧 **Contact**

Pour toute question sur la contribution, n'hésitez pas à :

- Ouvrir une **Issue** ou une **Discussion** sur GitHub.
- Contacter le mainteneur principal : [EricDelannoy](https://github.com/EricDelannoy).

---

Merci de contribuer à **pdf-trad** ! 🚀
