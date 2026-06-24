"""Tests pour le module OCR."""

import os
import tempfile
import numpy as np
from PIL import Image
import pytest

from pdf_trad.ocr import (
    extract_text_from_image,
    preprocess_image,
    extract_text_with_ocr,
    OCRError,
)


class TestPreprocessImage:
    """Tests pour la fonction preprocess_image."""

    def test_preprocess_grayscale_image(self):
        """Test le prétraitement d'une image en niveaux de gris."""
        # Créer une image en niveaux de gris
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # Prétraiter l'image
        processed = preprocess_image(image, denoise=True, deskew=True, binarize=True)
        
        # Vérifier que l'image est toujours en niveaux de gris
        assert len(processed.shape) == 2
        assert processed.dtype == np.uint8

    def test_preprocess_color_image(self):
        """Test le prétraitement d'une image en couleur."""
        # Créer une image en couleur
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Prétraiter l'image
        processed = preprocess_image(image, denoise=True, deskew=True, binarize=True)
        
        # Vérifier que l'image est convertie en niveaux de gris
        assert len(processed.shape) == 2

    def test_preprocess_no_denoise(self):
        """Test le prétraitement sans débruitage."""
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        processed = preprocess_image(image, denoise=False, deskew=False, binarize=False)
        
        # Sans prétraitement, l'image devrait être similaire
        assert np.array_equal(image, processed)


class TestExtractTextFromImage:
    """Tests pour la fonction extract_text_from_image."""

    def test_extract_text_simple(self):
        """Test l'extraction de texte depuis une image simple."""
        # Créer une image avec du texte (simulée)
        # Note: Tesseract peut ne pas détecter le texte dans une image générée
        # Ce test vérifie que la fonction ne lève pas d'erreur
        image = np.zeros((100, 400, 3), dtype=np.uint8)
        
        # Extraire le texte (sans prétraitement pour éviter les erreurs)
        result = extract_text_from_image(image, lang="eng", preprocess=False)
        
        # Vérifier que le résultat est un dictionnaire
        assert isinstance(result, dict)
        assert "text" in result
        assert "words" in result
        assert "boxes" in result

    def test_extract_text_with_preprocess(self):
        """Test l'extraction de texte avec prétraitement."""
        image = np.zeros((100, 400, 3), dtype=np.uint8)
        
        # Extraire le texte avec prétraitement
        result = extract_text_from_image(image, lang="eng", preprocess=True)
        
        # Vérifier la structure du résultat
        assert isinstance(result, dict)


class TestExtractTextWithOCR:
    """Tests pour la fonction extract_text_with_ocr."""

    def test_nonexistent_file(self):
        """Test l'erreur pour un fichier inexistant."""
        with pytest.raises(OCRError):
            extract_text_with_ocr("nonexistent.pdf")

    def test_invalid_pdf(self):
        """Test l'erreur pour un fichier PDF invalide."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"Not a PDF file")
            temp_path = f.name
        
        try:
            with pytest.raises(OCRError):
                extract_text_with_ocr(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.skip(reason="Nécessite un PDF valide pour le test")
    def test_valid_pdf(self):
        """Test l'extraction OCR depuis un PDF valide."""
        # Ce test nécessite un PDF valide dans le dossier tests/
        # Il est marqué comme skip par défaut
        pass


class TestOCRError:
    """Tests pour la classe OCRError."""

    def test_error_message(self):
        """Test le message d'erreur."""
        error = OCRError("Test error message")
        assert str(error) == "Test error message"
