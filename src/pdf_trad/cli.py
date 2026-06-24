"""
Interface en ligne de commande pour pdf-trad.

Permet de traduire des PDFs scannés via la ligne de commande.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click

from .ocr import extract_text_with_ocr
from .layout import detect_layout, PageLayout
from .translation import translate_text, translate_batch, get_translator
from .pdf_rebuilder import rebuild_pdf, apply_translations_to_layout


@click.group()
@click.version_option(version="0.1.0", message="pdf-trad version %(version)s")
def cli():
    """Outil pour traduire des PDFs scannés en conservant le layout."""
    pass


@cli.command()
@click.argument("input_pdf", type=click.Path(exists=True))
@click.argument("output_pdf", type=click.Path())
@click.option(
    "--dpi",
    default=300,
    help="Résolution pour la conversion PDF → image (défaut: 300).",
)
@click.option(
    "--lang",
    default="en",
    help="Langue source du texte (défaut: en).",
)
@click.option(
    "--base-url",
    default="http://localhost:8000/v1",
    help="URL de base de l'API OpenAI locale (défaut: http://localhost:8000/v1).",
)
@click.option(
    "--model",
    default="llama-2-7b-chat",
    help="Modèle OpenAI à utiliser (défaut: llama-2-7b-chat).",
)
@click.option(
    "--method",
    type=click.Choice(["pymupdf", "reportlab"]),
    default="pymupdf",
    help="Méthode de reconstruction du PDF (défaut: pymupdf).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Affiche les informations de débogage.",
)
def translate(
    input_pdf: str,
    output_pdf: str,
    dpi: int,
    lang: str,
    base_url: str,
    model: str,
    method: str,
    debug: bool,
):
    """
    Traduit un PDF scanné en français en conservant le layout.
    
    Exemple:
        pdf-trad translate input.pdf output.pdf --dpi 300 --base-url http://localhost:8000/v1
    """
    try:
        click.echo(f"Traitement du fichier: {input_pdf}")
        
        # Étape 1: Extraction OCR
        click.echo("1/4: Extraction OCR...")
        ocr_results = extract_text_with_ocr(
            pdf_path=input_pdf,
            dpi=dpi,
            lang=lang,
            preprocess=True,
        )
        
        if debug:
            for page_result in ocr_results:
                click.echo(f"  Page {page_result['page']}: {len(page_result['words'])} mots détectés")
        
        # Étape 2: Détection de layout
        click.echo("2/4: Détection de layout...")
        page_layouts = detect_layout(ocr_results)
        
        if debug:
            for page_layout in page_layouts:
                click.echo(f"  Page {page_layout.page}: {len(page_layout.zones)} zones détectées")
                for zone in page_layout.zones:
                    click.echo(f"    Zone ({zone.zone_type}): {len(zone.blocks)} blocs")
        
        # Étape 3: Traduction
        click.echo("3/4: Traduction...")
        
        # Extraire tout le texte à traduire
        texts_to_translate = []
        text_to_zone_map = {}  # texte original → (page, zone, block, line)
        
        for page_layout in page_layouts:
            for zone in page_layout.zones:
                for block in zone.blocks:
                    for line in block.lines:
                        if line.text.strip():
                            texts_to_translate.append(line.text)
                            text_to_zone_map[line.text] = (page_layout.page, zone, block, line)
        
        # Traduire tout le texte
        translations = translate_batch(
            texts=texts_to_translate,
            from_lang=lang,
            to_lang="fr",
            base_url=base_url,
            model=model,
        )
        
        # Créer un dictionnaire de traductions
        translation_dict = {}
        for original, translated in zip(texts_to_translate, translations):
            translation_dict[original] = translated
        
        if debug:
            for original, translated in translation_dict.items():
                click.echo(f"  '{original}' → '{translated}'")
        
        # Appliquer les traductions au layout
        translated_layouts = apply_translations_to_layout(page_layouts, translation_dict)
        
        # Étape 4: Reconstruction du PDF
        click.echo("4/4: Reconstruction du PDF...")
        rebuild_pdf(
            input_pdf_path=input_pdf,
            page_layouts=translated_layouts,
            output_path=output_pdf,
            method=method,
        )
        
        click.echo(f"✅ Traduction terminée! Fichier généré: {output_pdf}")
        
    except Exception as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_pdf", type=click.Path(exists=True))
@click.option(
    "--dpi",
    default=300,
    help="Résolution pour la conversion PDF → image (défaut: 300).",
)
@click.option(
    "--lang",
    default="en",
    help="Langue source du texte (défaut: en).",
)
@click.option(
    "--output-dir",
    default="debug_output",
    help="Dossier de sortie pour les images de débogage (défaut: debug_output).",
)
def debug(
    input_pdf: str,
    dpi: int,
    lang: str,
    output_dir: str,
):
    """
    Affiche les informations de débogage pour un PDF (OCR + layout).
    
    Exemple:
        pdf-trad debug input.pdf --show-layout
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Extraction OCR
        click.echo("Extraction OCR...")
        ocr_results = extract_text_with_ocr(
            pdf_path=input_pdf,
            dpi=dpi,
            lang=lang,
            preprocess=True,
        )
        
        for page_result in ocr_results:
            click.echo(f"\nPage {page_result['page']}:")
            click.echo(f"  Texte: {page_result['text'][:200]}...")
            click.echo(f"  Mots: {len(page_result['words'])}")
        
        # Détection de layout
        click.echo("\nDétection de layout...")
        page_layouts = detect_layout(ocr_results)
        
        for page_layout in page_layouts:
            click.echo(f"\nPage {page_layout.page}:")
            click.echo(f"  Taille: {page_layout.image_size}")
            click.echo(f"  Zones: {len(page_layout.zones)}")
            
            for zone in page_layout.zones:
                click.echo(f"    Zone ({zone.zone_type}):")
                click.echo(f"      BBox: {zone.bbox}")
                click.echo(f"      Blocs: {len(zone.blocks)}")
                
                for block in zone.blocks:
                    click.echo(f"        Bloc:")
                    click.echo(f"          BBox: {block.bbox}")
                    click.echo(f"          Lignes: {len(block.lines)}")
                    
                    for line in block.lines:
                        click.echo(f"            Ligne: '{line.text}'")
                        click.echo(f"              BBox: {line.bbox}")
        
    except Exception as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option(
    "--dpi",
    default=300,
    help="Résolution pour la conversion PDF → image (défaut: 300).",
)
@click.option(
    "--base-url",
    default="http://localhost:8000/v1",
    help="URL de base de l'API OpenAI locale.",
)
@click.option(
    "--model",
    default="llama-2-7b-chat",
    help="Modèle OpenAI à utiliser.",
)
def batch(
    input_dir: str,
    output_dir: str,
    dpi: int,
    base_url: str,
    model: str,
):
    """
    Traduit tous les PDFs d'un dossier.
    
    Exemple:
        pdf-trad batch ./input/ ./output/ --dpi 300
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        input_path = Path(input_dir)
        pdf_files = list(input_path.glob("*.pdf"))
        
        if not pdf_files:
            click.echo("Aucun fichier PDF trouvé dans le dossier d'entrée.")
            return
        
        click.echo(f"Traitement de {len(pdf_files)} fichiers PDF...")
        
        for pdf_file in pdf_files:
            output_file = Path(output_dir) / f"{pdf_file.stem}_fr{pdf_file.suffix}"
            
            click.echo(f"\nTraitement de: {pdf_file.name}")
            
            # Appeler la commande translate
            cli.main(
                args=[
                    "translate",
                    str(pdf_file),
                    str(output_file),
                    "--dpi", str(dpi),
                    "--base-url", base_url,
                    "--model", model,
                ],
                standalone_mode=False,
            )
        
        click.echo(f"\n✅ Tous les fichiers ont été traités! Dossier de sortie: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        sys.exit(1)


def main():
    """Point d'entrée principal pour l'interface CLI."""
    cli()


if __name__ == "__main__":
    main()
