"""
Module pour la reconstruction de PDFs avec du texte traduit.

Génère un nouveau PDF en conservant le layout original (positions, polices, styles)
et en remplaçant le texte par sa traduction.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Frame, PageTemplate
from reportlab.pdfgen import canvas

from .layout import PageLayout, LayoutZone, TextBlock, TextLine, Word


class PDFRebuildError(Exception):
    """Exception levée en cas d'erreur lors de la reconstruction du PDF."""
    pass


def get_default_font():
    """Retourne une police par défaut pour le PDF."""
    return "Helvetica"


def get_font_size_from_height(height: float) -> float:
    """
    Estime la taille de police à partir de la hauteur du texte.
    
    Args:
        height: Hauteur du texte en pixels.
    
    Returns:
        Taille de police en points.
    """
    # Conversion approximative : 1 pixel ≈ 0.75 points à 300 DPI
    return height * 0.75


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convertit RGB en code hexadécimal."""
    return f"#{r:02x}{g:02x}{b:02x}"


def rebuild_pdf_with_reportlab(
    page_layouts: List[PageLayout],
    output_path: str,
    page_size: Tuple[int, int] = (595, 842),  # A4 en points (72 DPI)
) -> None:
    """
    Reconstruit un PDF en utilisant ReportLab (génération depuis zéro).
    
    Args:
        page_layouts: Liste de layouts de pages.
        output_path: Chemin vers le fichier PDF de sortie.
        page_size: Taille de la page en points (défaut: A4).
    
    Raises:
        PDFRebuildError: Si la reconstruction échoue.
    """
    try:
        # Créer un document PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=page_size,
            rightMargin=0,
            leftMargin=0,
            topMargin=0,
            bottomMargin=0,
        )
        
        # Créer une liste de flux (flowables)
        story = []
        
        for page_layout in page_layouts:
            # Créer une page
            canvas = canvas.Canvas(output_path)
            canvas.setPageSize(page_size)
            
            # Dessiner chaque zone de texte
            for zone in page_layout.zones:
                for block in zone.blocks:
                    for line in block.lines:
                        # Position du texte (conversion pixels → points)
                        # Supposons 300 DPI : 1 inch = 300 pixels = 72 points
                        dpi = 300
                        points_per_pixel = 72 / dpi
                        
                        x = line.bbox[0] * points_per_pixel
                        y = page_size[1] - (line.bbox[3] * points_per_pixel)  # Inverser l'axe Y
                        
                        # Taille de police
                        font_size = get_font_size_from_height(line.avg_height)
                        
                        # Dessiner le texte
                        canvas.setFont(get_default_font(), font_size)
                        canvas.setFillColor(colors.black)
                        canvas.drawString(x, y, line.text)
            
            canvas.save()
        
        # Construire le document
        doc.build(story)
        
    except Exception as e:
        raise PDFRebuildError(f"Erreur lors de la reconstruction avec ReportLab: {e}")


def rebuild_pdf_with_pymupdf(
    input_pdf_path: str,
    page_layouts: List[PageLayout],
    output_path: str,
) -> None:
    """
    Reconstruit un PDF en modifiant directement le PDF original avec PyMuPDF.
    
    Cette approche conserve mieux le layout original (polices, images, etc.).
    
    Args:
        input_pdf_path: Chemin vers le PDF original (pour copier les images/métadonnées).
        page_layouts: Liste de layouts de pages avec les traductions.
        output_path: Chemin vers le fichier PDF de sortie.
    
    Raises:
        PDFRebuildError: Si la reconstruction échoue.
    """
    try:
        # Ouvrir le PDF original pour copier les métadonnées
        original_doc = fitz.open(input_pdf_path)
        
        # Créer un nouveau PDF
        new_doc = fitz.open()
        
        for page_idx, page_layout in enumerate(page_layouts):
            if page_idx >= len(original_doc):
                break
            
            # Copier la page originale
            original_page = original_doc.load_page(page_idx)
            new_page = new_doc.new_page(
                width=original_page.rect.width,
                height=original_page.rect.height,
            )
            
            # Copier les images et autres éléments non-textuels
            # (PyMuPDF ne permet pas de copier directement les images, 
            # donc on les redessine si nécessaire)
            
            # Dessiner le texte traduit
            for zone in page_layout.zones:
                for block in zone.blocks:
                    for line in block.lines:
                        # Position du texte
                        x = line.bbox[0]
                        y = line.bbox[1]
                        
                        # Taille de police (estimée)
                        font_size = get_font_size_from_height(line.avg_height)
                        
                        # Dessiner le texte
                        new_page.insert_text(
                            point=(x, y),
                            text=line.text,
                            fontsize=font_size,
                            fontname=get_default_font(),
                            color=(0, 0, 0),  # Noir
                        )
            
            # TODO: Copier les images depuis la page originale
            # Cela nécessite une implémentation plus avancée
        
        # Sauvegarder le nouveau PDF
        new_doc.save(output_path)
        new_doc.close()
        original_doc.close()
        
    except Exception as e:
        raise PDFRebuildError(f"Erreur lors de la reconstruction avec PyMuPDF: {e}")


def rebuild_pdf(
    input_pdf_path: str,
    page_layouts: List[PageLayout],
    output_path: str,
    method: str = "pymupdf",
) -> None:
    """
    Reconstruit un PDF avec le texte traduit en conservant le layout.
    
    Args:
        input_pdf_path: Chemin vers le PDF original.
        page_layouts: Liste de layouts de pages (avec texte traduit).
        output_path: Chemin vers le fichier PDF de sortie.
        method: Méthode de reconstruction ("pymupdf" ou "reportlab").
    
    Raises:
        PDFRebuildError: Si la reconstruction échoue.
    """
    if method == "pymupdf":
        rebuild_pdf_with_pymupdf(input_pdf_path, page_layouts, output_path)
    elif method == "reportlab":
        # Convertir la taille de la page en points
        # Supposons que la première page a une taille définie
        if page_layouts:
            page_width, page_height = page_layouts[0].image_size
            # Conversion pixels → points (300 DPI : 1 inch = 300 pixels = 72 points)
            dpi = 300
            page_size = (page_width * 72 / dpi, page_height * 72 / dpi)
            rebuild_pdf_with_reportlab(page_layouts, output_path, page_size)
        else:
            rebuild_pdf_with_reportlab(page_layouts, output_path)
    else:
        raise PDFRebuildError(f"Méthode inconnue: {method}. Utilisez 'pymupdf' ou 'reportlab'.")


def apply_translations_to_layout(
    page_layouts: List[PageLayout],
    translations: Dict[str, str],
) -> List[PageLayout]:
    """
    Applique les traductions à un layout de page.
    
    Args:
        page_layouts: Liste de layouts de pages.
        translations: Dictionnaire de traductions (texte original → texte traduit).
    
    Returns:
        Nouvelle liste de layouts avec les textes traduits.
    """
    translated_layouts = []
    
    for page_layout in page_layouts:
        # Créer une copie du layout
        translated_zones = []
        
        for zone in page_layout.zones:
            translated_blocks = []
            
            for block in zone.blocks:
                translated_lines = []
                
                for line in block.lines:
                    # Traduire le texte de la ligne
                    translated_text = translations.get(line.text, line.text)
                    
                    # Créer une nouvelle ligne avec le texte traduit
                    translated_line = TextLine(
                        words=line.words,
                        bbox=line.bbox,
                        text=translated_text,
                        avg_height=line.avg_height,
                    )
                    translated_lines.append(translated_line)
                
                # Créer un nouveau bloc avec les lignes traduites
                translated_block = TextBlock(
                    lines=translated_lines,
                    bbox=block.bbox,
                    text="\n".join(l.text for l in translated_lines),
                )
                translated_blocks.append(translated_block)
            
            # Créer une nouvelle zone avec les blocs traduits
            translated_zone = LayoutZone(
                blocks=translated_blocks,
                bbox=zone.bbox,
                zone_type=zone.zone_type,
                text="\n\n".join(b.text for b in translated_blocks),
            )
            translated_zones.append(translated_zone)
        
        # Créer un nouveau layout de page
        translated_page_layout = PageLayout(
            page=page_layout.page,
            zones=translated_zones,
            words=page_layout.words,
            lines=page_layout.lines,
            blocks=page_layout.blocks,
            image_size=page_layout.image_size,
        )
        translated_layouts.append(translated_page_layout)
    
    return translated_layouts
