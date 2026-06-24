"""
Module pour la détection de layout dans les PDFs scannés.

Identifie les zones de texte (blocs, colonnes, tableaux) à partir des résultats OCR,
et organise les mots en structures logiques pour la traduction.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import math

import numpy as np
from pydantic import BaseModel


@dataclass
class Word:
    """Représente un mot avec ses coordonnées et métadonnées."""
    text: str
    left: int
    top: int
    width: int
    height: int
    conf: int
    page: int = 1


@dataclass
class TextLine:
    """Représente une ligne de texte (groupe de mots alignés horizontalement)."""
    words: List[Word] = field(default_factory=list)
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (left, top, right, bottom)
    text: str = ""
    avg_height: float = 0.0
    
    def __post_init__(self):
        if self.words:
            self.text = " ".join(w.text for w in self.words)
            lefts = [w.left for w in self.words]
            tops = [w.top for w in self.words]
            rights = [w.left + w.width for w in self.words]
            bottoms = [w.top + w.height for w in self.words]
            self.bbox = (
                min(lefts),
                min(tops),
                max(rights),
                max(bottoms),
            )
            self.avg_height = np.mean([w.height for w in self.words])


@dataclass
class TextBlock:
    """Représente un bloc de texte (groupe de lignes alignées verticalement)."""
    lines: List[TextLine] = field(default_factory=list)
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
    text: str = ""
    
    def __post_init__(self):
        if self.lines:
            self.text = "\n".join(line.text for line in self.lines)
            lefts = [line.bbox[0] for line in self.lines]
            tops = [line.bbox[1] for line in self.lines]
            rights = [line.bbox[2] for line in self.lines]
            bottoms = [line.bbox[3] for line in self.lines]
            self.bbox = (
                min(lefts),
                min(tops),
                max(rights),
                max(bottoms),
            )


@dataclass
class LayoutZone:
    """Représente une zone de layout (bloc, colonne, tableau, etc.)."""
    blocks: List[TextBlock] = field(default_factory=list)
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
    zone_type: str = "text"  # "text", "column", "table", "header", "footer"
    text: str = ""
    
    def __post_init__(self):
        if self.blocks:
            self.text = "\n\n".join(block.text for block in self.blocks)
            lefts = [block.bbox[0] for block in self.blocks]
            tops = [block.bbox[1] for block in self.blocks]
            rights = [block.bbox[2] for block in self.blocks]
            bottoms = [block.bbox[3] for block in self.blocks]
            self.bbox = (
                min(lefts),
                min(tops),
                max(rights),
                max(bottoms),
            )


@dataclass
class PageLayout:
    """Représente le layout complet d'une page."""
    page: int
    zones: List[LayoutZone] = field(default_factory=list)
    words: List[Word] = field(default_factory=list)
    lines: List[TextLine] = field(default_factory=list)
    blocks: List[TextBlock] = field(default_factory=list)
    image_size: Tuple[int, int] = (0, 0)
    
    def get_text_by_zone_type(self, zone_type: str) -> List[str]:
        """Récupère tout le texte d'un type de zone spécifique."""
        return [zone.text for zone in self.zones if zone.zone_type == zone_type]


class LayoutError(Exception):
    """Exception levée en cas d'erreur lors de la détection de layout."""
    pass


def group_words_into_lines(
    words: List[Word],
    vertical_tolerance: int = 5,
    horizontal_gap: int = 10,
) -> List[TextLine]:
    """
    Regroupe les mots en lignes de texte.
    
    Les mots sont considérés comme étant sur la même ligne si :
    - Leur coordonnée `top` est à ± `vertical_tolerance` pixels.
    - Ils sont suffisamment proches horizontalement (écart < `horizontal_gap`).
    
    Args:
        words: Liste de mots avec coordonnées.
        vertical_tolerance: Tolérance verticale pour regrouper les mots en lignes.
        horizontal_gap: Écart horizontal maximal entre deux mots d'une même ligne.
    
    Returns:
        Liste de lignes de texte.
    """
    if not words:
        return []
    
    # Trier les mots par `top` puis par `left`
    words_sorted = sorted(words, key=lambda w: (w.top, w.left))
    
    lines = []
    current_line = [words_sorted[0]]
    
    for i in range(1, len(words_sorted)):
        prev_word = current_line[-1]
        curr_word = words_sorted[i]
        
        # Vérifier si le mot actuel est sur la même ligne
        top_diff = abs(curr_word.top - prev_word.top)
        left_diff = curr_word.left - (prev_word.left + prev_word.width)
        
        if top_diff <= vertical_tolerance and left_diff <= horizontal_gap:
            current_line.append(curr_word)
        else:
            lines.append(TextLine(words=current_line))
            current_line = [curr_word]
    
    if current_line:
        lines.append(TextLine(words=current_line))
    
    return lines


def group_lines_into_blocks(
    lines: List[TextLine],
    horizontal_tolerance: int = 20,
    vertical_gap: int = 20,
) -> List[TextBlock]:
    """
    Regroupe les lignes en blocs de texte.
    
    Les lignes sont considérées comme faisant partie du même bloc si :
    - Leur coordonnée `left` est à ± `horizontal_tolerance` pixels.
    - L'écart vertical entre les lignes est < `vertical_gap`.
    
    Args:
        lines: Liste de lignes de texte.
        horizontal_tolerance: Tolérance horizontale pour regrouper les lignes en blocs.
        vertical_gap: Écart vertical maximal entre deux lignes d'un même bloc.
    
    Returns:
        Liste de blocs de texte.
    """
    if not lines:
        return []
    
    # Trier les lignes par `top` puis par `left`
    lines_sorted = sorted(lines, key=lambda l: (l.bbox[1], l.bbox[0]))
    
    blocks = []
    current_block = [lines_sorted[0]]
    
    for i in range(1, len(lines_sorted)):
        prev_line = current_block[-1]
        curr_line = lines_sorted[i]
        
        # Vérifier si la ligne actuelle fait partie du même bloc
        left_diff = abs(curr_line.bbox[0] - prev_line.bbox[0])
        top_diff = curr_line.bbox[1] - prev_line.bbox[3]
        
        if left_diff <= horizontal_tolerance and top_diff <= vertical_gap:
            current_block.append(curr_line)
        else:
            blocks.append(TextBlock(lines=current_block))
            current_block = [curr_line]
    
    if current_block:
        blocks.append(TextBlock(lines=current_block))
    
    return blocks


def detect_columns(
    blocks: List[TextBlock],
    min_column_width: int = 100,
) -> List[List[TextBlock]]:
    """
    Détecte les colonnes dans une page à partir des blocs de texte.
    
    Args:
        blocks: Liste de blocs de texte.
        min_column_width: Largeur minimale pour considérer un groupe comme une colonne.
    
    Returns:
        Liste de colonnes (chaque colonne est une liste de blocs).
    """
    if not blocks:
        return []
    
    # Trier les blocs par `left` puis par `top`
    blocks_sorted = sorted(blocks, key=lambda b: (b.bbox[0], b.bbox[1]))
    
    # Regrouper les blocs par colonne (même `left` ± tolérance)
    columns = []
    current_column = [blocks_sorted[0]]
    
    for i in range(1, len(blocks_sorted)):
        prev_block = current_column[-1]
        curr_block = blocks_sorted[i]
        
        # Vérifier si le bloc fait partie de la même colonne
        left_diff = abs(curr_block.bbox[0] - prev_block.bbox[0])
        
        if left_diff <= min_column_width // 2:
            current_column.append(curr_block)
        else:
            columns.append(current_column)
            current_column = [curr_block]
    
    if current_column:
        columns.append(current_column)
    
    return columns


def detect_tables(
    blocks: List[TextBlock],
    lines: List[TextLine],
    min_table_rows: int = 2,
    min_table_cols: int = 2,
) -> List[LayoutZone]:
    """
    Détecte les tableaux dans une page (simplifié).
    
    Args:
        blocks: Liste de blocs de texte.
        lines: Liste de lignes de texte.
        min_table_rows: Nombre minimal de lignes pour considérer un tableau.
        min_table_cols: Nombre minimal de colonnes pour considérer un tableau.
    
    Returns:
        Liste de zones de type "table".
    """
    # TODO: Implémentation avancée avec détection de grilles
    # Pour l'instant, retourne une liste vide
    return []


def classify_zones(
    blocks: List[TextBlock],
    columns: List[List[TextBlock]],
    page_height: int,
) -> List[LayoutZone]:
    """
    Classifie les blocs en zones de layout (en-tête, pied de page, corps, etc.).
    
    Args:
        blocks: Liste de tous les blocs.
        columns: Liste de colonnes détectées.
        page_height: Hauteur de la page.
    
    Returns:
        Liste de zones classifiées.
    """
    zones = []
    
    # Classifier les blocs en fonction de leur position
    header_blocks = []
    footer_blocks = []
    body_blocks = []
    
    for block in blocks:
        # En-tête : blocs en haut de la page (10% de la hauteur)
        if block.bbox[1] < page_height * 0.1:
            header_blocks.append(block)
        # Pied de page : blocs en bas de la page (10% de la hauteur)
        elif block.bbox[3] > page_height * 0.9:
            footer_blocks.append(block)
        else:
            body_blocks.append(block)
    
    # Créer les zones
    if header_blocks:
        zones.append(LayoutZone(
            blocks=header_blocks,
            zone_type="header",
        ))
    
    if footer_blocks:
        zones.append(LayoutZone(
            blocks=footer_blocks,
            zone_type="footer",
        ))
    
    # Ajouter les colonnes du corps
    for col_idx, column in enumerate(columns):
        col_blocks = [b for b in body_blocks if b in column]
        if col_blocks:
            zones.append(LayoutZone(
                blocks=col_blocks,
                zone_type="column",
            ))
    
    # Ajouter les blocs restants (non classés)
    remaining_blocks = [b for b in body_blocks if not any(b in col for col in columns)]
    if remaining_blocks:
        zones.append(LayoutZone(
            blocks=remaining_blocks,
            zone_type="text",
        ))
    
    return zones


def detect_layout(
    ocr_results: List[Dict[str, Any]],
    vertical_tolerance: int = 5,
    horizontal_gap: int = 10,
    horizontal_tolerance: int = 20,
    vertical_gap: int = 20,
) -> List[PageLayout]:
    """
    Détecte le layout complet à partir des résultats OCR.
    
    Args:
        ocr_results: Résultats de l'OCR (sortie de `extract_text_with_ocr`).
        vertical_tolerance: Tolérance verticale pour regrouper les mots en lignes.
        horizontal_gap: Écart horizontal maximal entre deux mots d'une même ligne.
        horizontal_tolerance: Tolérance horizontale pour regrouper les lignes en blocs.
        vertical_gap: Écart vertical maximal entre deux lignes d'un même bloc.
    
    Returns:
        Liste de `PageLayout` (un par page).
    
    Raises:
        LayoutError: Si les résultats OCR sont invalides.
    """
    if not ocr_results:
        raise LayoutError("Aucun résultat OCR fourni")
    
    page_layouts = []
    
    for page_result in ocr_results:
        page_num = page_result.get("page", 1)
        words_data = page_result.get("words", [])
        image_size = page_result.get("image_size", (0, 0))
        
        # Convertir les mots en objets Word
        words = [
            Word(
                text=w["text"],
                left=w["left"],
                top=w["top"],
                width=w["width"],
                height=w["height"],
                conf=w["conf"],
                page=page_num,
            )
            for w in words_data
        ]
        
        # Regrouper les mots en lignes
        lines = group_words_into_lines(
            words,
            vertical_tolerance=vertical_tolerance,
            horizontal_gap=horizontal_gap,
        )
        
        # Regrouper les lignes en blocs
        blocks = group_lines_into_blocks(
            lines,
            horizontal_tolerance=horizontal_tolerance,
            vertical_gap=vertical_gap,
        )
        
        # Détecter les colonnes
        columns = detect_columns(blocks)
        
        # Classifier les zones
        zones = classify_zones(blocks, columns, image_size[1])
        
        # Créer le layout de la page
        page_layout = PageLayout(
            page=page_num,
            zones=zones,
            words=words,
            lines=lines,
            blocks=blocks,
            image_size=image_size,
        )
        
        page_layouts.append(page_layout)
    
    return page_layouts
