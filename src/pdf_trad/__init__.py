"""
pdf-trad: Outil pour traduire des PDFs scannés en conservant le layout original.

Ce package permet d'extraire le texte d'un PDF scanné via OCR, de détecter les zones de texte,
de les traduire en français (via une API OpenAI locale), et de générer un nouveau PDF
avec le texte traduit tout en conservant la mise en page d'origine.
"""

__version__ = "0.1.0"
__author__ = "EricDelannoy"

from .ocr import extract_text_with_ocr
from .layout import detect_layout
from .translation import translate_text
from .pdf_rebuilder import rebuild_pdf

__all__ = ["extract_text_with_ocr", "detect_layout", "translate_text", "rebuild_pdf"]
