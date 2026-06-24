"""Tests pour le module layout."""

from pdf_trad.layout import (
    Word,
    TextLine,
    TextBlock,
    LayoutZone,
    PageLayout,
    group_words_into_lines,
    group_lines_into_blocks,
    detect_columns,
    detect_layout,
    LayoutError,
)


class TestWord:
    """Tests pour la classe Word."""

    def test_word_creation(self):
        """Test la création d'un objet Word."""
        word = Word(
            text="Hello",
            left=10,
            top=20,
            width=30,
            height=10,
            conf=90,
            page=1,
        )
        
        assert word.text == "Hello"
        assert word.left == 10
        assert word.top == 20
        assert word.width == 30
        assert word.height == 10
        assert word.conf == 90
        assert word.page == 1


class TestTextLine:
    """Tests pour la classe TextLine."""

    def test_text_line_creation(self):
        """Test la création d'une ligne de texte."""
        word1 = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        word2 = Word(text="World", left=45, top=20, width=30, height=10, conf=90)
        
        line = TextLine(words=[word1, word2])
        
        assert line.text == "Hello World"
        assert len(line.words) == 2
        assert line.bbox == (10, 20, 75, 30)

    def test_empty_text_line(self):
        """Test une ligne de texte vide."""
        line = TextLine()
        assert line.text == ""
        assert line.bbox == (0, 0, 0, 0)


class TestTextBlock:
    """Tests pour la classe TextBlock."""

    def test_text_block_creation(self):
        """Test la création d'un bloc de texte."""
        word1 = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        word2 = Word(text="World", left=45, top=20, width=30, height=10, conf=90)
        line1 = TextLine(words=[word1, word2])
        
        word3 = Word(text="Test", left=10, top=40, width=30, height=10, conf=90)
        line2 = TextLine(words=[word3])
        
        block = TextBlock(lines=[line1, line2])
        
        assert block.text == "Hello World\nTest"
        assert len(block.lines) == 2


class TestLayoutZone:
    """Tests pour la classe LayoutZone."""

    def test_layout_zone_creation(self):
        """Test la création d'une zone de layout."""
        word = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        line = TextLine(words=[word])
        block = TextBlock(lines=[line])
        
        zone = LayoutZone(blocks=[block], zone_type="text")
        
        assert zone.text == "Hello"
        assert zone.zone_type == "text"
        assert len(zone.blocks) == 1


class TestPageLayout:
    """Tests pour la classe PageLayout."""

    def test_page_layout_creation(self):
        """Test la création d'un layout de page."""
        word = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        line = TextLine(words=[word])
        block = TextBlock(lines=[line])
        zone = LayoutZone(blocks=[block])
        
        page_layout = PageLayout(
            page=1,
            zones=[zone],
            words=[word],
            lines=[line],
            blocks=[block],
            image_size=(800, 600),
        )
        
        assert page_layout.page == 1
        assert len(page_layout.zones) == 1
        assert page_layout.image_size == (800, 600)

    def test_get_text_by_zone_type(self):
        """Test la récupération de texte par type de zone."""
        word1 = Word(text="Header", left=10, top=10, width=30, height=10, conf=90)
        line1 = TextLine(words=[word1])
        block1 = TextBlock(lines=[line1])
        zone1 = LayoutZone(blocks=[block1], zone_type="header")
        
        word2 = Word(text="Body", left=10, top=100, width=30, height=10, conf=90)
        line2 = TextLine(words=[word2])
        block2 = TextBlock(lines=[line2])
        zone2 = LayoutZone(blocks=[block2], zone_type="text")
        
        page_layout = PageLayout(
            page=1,
            zones=[zone1, zone2],
        )
        
        header_texts = page_layout.get_text_by_zone_type("header")
        assert len(header_texts) == 1
        assert header_texts[0] == "Header"


class TestGroupWordsIntoLines:
    """Tests pour la fonction group_words_into_lines."""

    def test_group_words_same_line(self):
        """Test le regroupement de mots sur la même ligne."""
        word1 = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        word2 = Word(text="World", left=45, top=20, width=30, height=10, conf=90)
        
        lines = group_words_into_lines([word1, word2], vertical_tolerance=5, horizontal_gap=20)
        
        assert len(lines) == 1
        assert lines[0].text == "Hello World"

    def test_group_words_different_lines(self):
        """Test le regroupement de mots sur des lignes différentes."""
        word1 = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        word2 = Word(text="World", left=10, top=50, width=30, height=10, conf=90)
        
        lines = group_words_into_lines([word1, word2], vertical_tolerance=5, horizontal_gap=20)
        
        assert len(lines) == 2
        assert lines[0].text == "Hello"
        assert lines[1].text == "World"

    def test_empty_words(self):
        """Test avec une liste de mots vide."""
        lines = group_words_into_lines([], vertical_tolerance=5, horizontal_gap=20)
        assert lines == []


class TestGroupLinesIntoBlocks:
    """Tests pour la fonction group_lines_into_blocks."""

    def test_group_lines_same_block(self):
        """Test le regroupement de lignes dans le même bloc."""
        word1 = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        line1 = TextLine(words=[word1])
        
        word2 = Word(text="World", left=10, top=40, width=30, height=10, conf=90)
        line2 = TextLine(words=[word2])
        
        blocks = group_lines_into_blocks([line1, line2], horizontal_tolerance=20, vertical_gap=20)
        
        assert len(blocks) == 1
        assert blocks[0].text == "Hello\nWorld"

    def test_group_lines_different_blocks(self):
        """Test le regroupement de lignes dans des blocs différents."""
        word1 = Word(text="Hello", left=10, top=20, width=30, height=10, conf=90)
        line1 = TextLine(words=[word1])
        
        word2 = Word(text="World", left=100, top=20, width=30, height=10, conf=90)
        line2 = TextLine(words=[word2])
        
        blocks = group_lines_into_blocks([line1, line2], horizontal_tolerance=20, vertical_gap=20)
        
        assert len(blocks) == 2


class TestDetectColumns:
    """Tests pour la fonction detect_columns."""

    def test_detect_single_column(self):
        """Test la détection d'une seule colonne."""
        word1 = Word(text="Line1", left=10, top=20, width=30, height=10, conf=90)
        line1 = TextLine(words=[word1])
        block1 = TextBlock(lines=[line1])
        
        word2 = Word(text="Line2", left=10, top=40, width=30, height=10, conf=90)
        line2 = TextLine(words=[word2])
        block2 = TextBlock(lines=[line2])
        
        columns = detect_columns([block1, block2], min_column_width=100)
        
        assert len(columns) == 1
        assert len(columns[0]) == 2

    def test_detect_multiple_columns(self):
        """Test la détection de plusieurs colonnes."""
        word1 = Word(text="Col1", left=10, top=20, width=30, height=10, conf=90)
        line1 = TextLine(words=[word1])
        block1 = TextBlock(lines=[line1])
        
        word2 = Word(text="Col2", left=200, top=20, width=30, height=10, conf=90)
        line2 = TextLine(words=[word2])
        block2 = TextBlock(lines=[line2])
        
        columns = detect_columns([block1, block2], min_column_width=100)
        
        assert len(columns) == 2


class TestDetectLayout:
    """Tests pour la fonction detect_layout."""

    def test_empty_ocr_results(self):
        """Test avec des résultats OCR vides."""
        with pytest.raises(LayoutError):
            detect_layout([])

    def test_single_page_layout(self):
        """Test la détection de layout pour une seule page."""
        ocr_results = [
            {
                "page": 1,
                "text": "Hello World",
                "words": [
                    {"text": "Hello", "left": 10, "top": 20, "width": 30, "height": 10, "conf": 90},
                    {"text": "World", "left": 45, "top": 20, "width": 30, "height": 10, "conf": 90},
                ],
                "boxes": [
                    {"left": 10, "top": 20, "width": 30, "height": 10},
                    {"left": 45, "top": 20, "width": 30, "height": 10},
                ],
                "image_size": (800, 600),
            }
        ]
        
        page_layouts = detect_layout(ocr_results)
        
        assert len(page_layouts) == 1
        assert page_layouts[0].page == 1
        assert len(page_layouts[0].words) == 2


class TestLayoutError:
    """Tests pour la classe LayoutError."""

    def test_error_message(self):
        """Test le message d'erreur."""
        error = LayoutError("Test error message")
        assert str(error) == "Test error message"
