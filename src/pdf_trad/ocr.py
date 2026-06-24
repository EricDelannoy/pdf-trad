"""
Module pour l'extraction de texte via OCR depuis des PDFs scannés.

Utilise Tesseract (pytesseract) pour extraire le texte et ses coordonnées,
avec un pré-traitement des images via OpenCV pour améliorer la qualité.
"""

from typing import List, Dict, Any, Optional
import tempfile
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path


class OCRError(Exception):
    """Exception levée en cas d'erreur lors de l'OCR."""
    pass


def preprocess_image(
    image: np.ndarray,
    dpi: int = 300,
    denoise: bool = True,
    deskew: bool = True,
    binarize: bool = True,
) -> np.ndarray:
    """
    Prétraite une image pour améliorer la qualité de l'OCR.
    
    Args:
        image: Image en niveaux de gris (numpy array).
        dpi: Résolution de l'image (utilisée pour ajuster les paramètres).
        denoise: Appliquer un débruitage (filtre morphologique).
        deskew: Corriger l'inclinaison du texte.
        binarize: Binariser l'image (seuillage adaptatif).
    
    Returns:
        Image prétraitée (numpy array).
    """
    # Convertir en niveaux de gris si nécessaire
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Redimensionner si la résolution est trop faible
    if dpi < 150:
        scale = 300 / dpi
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Débruitage
    if denoise:
        kernel = np.ones((1, 1), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        image = cv2.medianBlur(image, 3)
    
    # Binarisation (seuillage adaptatif)
    if binarize:
        image = cv2.adaptiveThreshold(
            image, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
    
    # Correction de l'inclinaison (déskew)
    if deskew:
        coords = np.column_stack(np.where(image > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return image


def extract_text_from_image(
    image: np.ndarray,
    lang: str = "eng",
    config: str = "--psm 6 --oem 3",
    preprocess: bool = True,
) -> Dict[str, Any]:
    """
    Extrait le texte et les coordonnées depuis une image via Tesseract.
    
    Args:
        image: Image à analyser (numpy array).
        lang: Langue du texte (ex: "eng", "fra").
        config: Options Tesseract (ex: "--psm 6" pour un bloc de texte).
        preprocess: Appliquer le prétraitement avant l'OCR.
    
    Returns:
        Dictionnaire avec :
        - "text": Texte extrait.
        - "words": Liste de mots avec leurs coordonnées.
        - "boxes": Coordonnées des mots (left, top, width, height).
    """
    if preprocess:
        image = preprocess_image(image)
    
    # Convertir en PIL Image pour pytesseract
    pil_image = Image.fromarray(image)
    
    # Extraire le texte et les données de position
    data = pytesseract.image_to_data(
        pil_image, 
        lang=lang, 
        config=config,
        output_type=pytesseract.Output.DICT
    )
    
    # Extraire les mots et leurs coordonnées
    words = []
    boxes = []
    for i in range(len(data["text"])):
        if data["text"][i].strip():
            word = {
                "text": data["text"][i],
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
                "conf": data["conf"][i],
            }
            words.append(word)
            boxes.append({
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })
    
    return {
        "text": " ".join(data["text"]),
        "words": words,
        "boxes": boxes,
    }


def extract_text_with_ocr(
    pdf_path: str,
    dpi: int = 300,
    lang: str = "eng",
    pages: Optional[List[int]] = None,
    preprocess: bool = True,
) -> List[Dict[str, Any]]:
    """
    Extrait le texte et les coordonnées depuis un PDF scanné.
    
    Args:
        pdf_path: Chemin vers le fichier PDF.
        dpi: Résolution pour la conversion PDF → image.
        lang: Langue du texte (ex: "eng").
        pages: Liste des numéros de pages à traiter (None = toutes).
        preprocess: Appliquer le prétraitement avant l'OCR.
    
    Returns:
        Liste de dictionnaires (un par page) avec :
        - "page": Numéro de la page.
        - "text": Texte extrait.
        - "words": Liste de mots avec coordonnées.
        - "boxes": Coordonnées des mots.
        - "image_size": Taille de l'image (largeur, hauteur).
    
    Raises:
        OCRError: Si le PDF ne peut pas être lu ou converti.
    """
    if not os.path.exists(pdf_path):
        raise OCRError(f"Fichier PDF introuvable: {pdf_path}")
    
    try:
        # Convertir le PDF en images
        images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1000)
        
        if pages is not None:
            images = [images[i-1] for i in pages if i <= len(images)]
    except Exception as e:
        raise OCRError(f"Erreur lors de la conversion PDF → images: {e}")
    
    results = []
    for idx, image in enumerate(images, start=1):
        if pages is not None and idx not in pages:
            continue
        
        # Convertir PIL Image en numpy array
        image_np = np.array(image)
        
        # Extraire le texte
        ocr_result = extract_text_from_image(
            image_np, 
            lang=lang, 
            preprocess=preprocess
        )
        
        results.append({
            "page": idx,
            "text": ocr_result["text"],
            "words": ocr_result["words"],
            "boxes": ocr_result["boxes"],
            "image_size": (image.width, image.height),
        })
    
    return results
