"""
Module pour la traduction de texte via une API OpenAI locale.

Utilise l'API OpenAI (compatible avec les serveurs locaux comme llama-cpp)
pour traduire le texte de l'anglais vers le français.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

import yaml
from openai import OpenAI


class TranslationError(Exception):
    """Exception levée en cas d'erreur lors de la traduction."""
    pass


class TranslationCache:
    """Cache pour éviter de re-traduire le même texte."""
    
    def __init__(self, cache_dir: str = ".translation_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, str] = {}
        self._load_cache()
    
    def _get_cache_path(self, text: str) -> Path:
        """Génère un chemin de fichier unique pour le texte."""
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{text_hash}.json"
    
    def _load_cache(self):
        """Charge le cache depuis les fichiers."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cache[data["text"]] = data["translation"]
            except (json.JSONDecodeError, KeyError):
                continue
    
    def get(self, text: str) -> Optional[str]:
        """Récupère une traduction depuis le cache."""
        return self.cache.get(text)
    
    def set(self, text: str, translation: str):
        """Stocke une traduction dans le cache."""
        self.cache[text] = translation
        cache_path = self._get_cache_path(text)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"text": text, "translation": translation}, f, ensure_ascii=False)
    
    def clear(self):
        """Efface le cache."""
        self.cache.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


class OpenAITranslator:
    """Client pour l'API OpenAI locale (compatible avec llama-cpp)."""
    
    DEFAULT_SYSTEM_PROMPT = (
        "Tu es un traducteur professionnel. "
        "Traduis ce texte de l'anglais vers le français en conservant le style, "
        "la structure et la mise en forme. "
        "Ne modifie pas les balises, les placeholders ou les éléments non textuels. "
        "Sois précis et naturel."
    )
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "dummy",
        model: str = "llama-2-7b-chat",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
        cache_enabled: bool = True,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.cache_enabled = cache_enabled
        self.cache = TranslationCache() if cache_enabled else None
        
        # Initialiser le client OpenAI
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
    
    def translate(
        self,
        text: str,
        from_lang: str = "en",
        to_lang: str = "fr",
        use_cache: bool = True,
    ) -> str:
        """
        Traduit un texte de l'anglais vers le français.
        
        Args:
            text: Texte à traduire.
            from_lang: Langue source (non utilisée pour l'instant, toujours "en").
            to_lang: Langue cible (non utilisée pour l'instant, toujours "fr").
            use_cache: Utiliser le cache pour éviter de re-traduire.
        
        Returns:
            Texte traduit.
        
        Raises:
            TranslationError: Si la traduction échoue.
        """
        if not text.strip():
            return text
        
        # Vérifier le cache
        if use_cache and self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Translate this to French:\n\n{text}"},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=["\n\n"],
            )
            
            translation = response.choices[0].message.content.strip()
            
            # Stocker dans le cache
            if use_cache and self.cache:
                self.cache.set(text, translation)
            
            return translation
            
        except Exception as e:
            raise TranslationError(f"Erreur lors de la traduction: {e}")
    
    def batch_translate(
        self,
        texts: List[str],
        from_lang: str = "en",
        to_lang: str = "fr",
    ) -> List[str]:
        """
        Traduit une liste de textes en une seule requête (si possible).
        
        Args:
            texts: Liste de textes à traduire.
            from_lang: Langue source.
            to_lang: Langue cible.
        
        Returns:
            Liste de textes traduits.
        """
        translations = []
        for text in texts:
            translations.append(self.translate(text, from_lang, to_lang))
        return translations


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Charge la configuration depuis un fichier YAML.
    
    Args:
        config_path: Chemin vers le fichier de configuration.
    
    Returns:
        Dictionnaire de configuration.
    """
    config = {
        "openai": {
            "base_url": "http://localhost:8000/v1",
            "api_key": "dummy",
            "model": "llama-2-7b-chat",
            "temperature": 0.1,
            "max_tokens": 2048,
        },
        "translation": {
            "from_lang": "en",
            "to_lang": "fr",
            "cache_enabled": True,
        },
    }
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)
    
    return config


# Instance globale du traducteur (initialisée à la première utilisation)
_translator: Optional[OpenAITranslator] = None


def get_translator(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
) -> OpenAITranslator:
    """
    Récupère ou initialise le traducteur OpenAI.
    
    Args:
        base_url: URL de base de l'API OpenAI (remplace la config).
        api_key: Clé API (remplace la config).
        model: Modèle à utiliser (remplace la config).
        config_path: Chemin vers le fichier de configuration.
    
    Returns:
        Instance de OpenAITranslator.
    """
    global _translator
    
    if _translator is None:
        config = load_config(config_path)
        openai_config = config.get("openai", {})
        translation_config = config.get("translation", {})
        
        _translator = OpenAITranslator(
            base_url=base_url or openai_config.get("base_url", "http://localhost:8000/v1"),
            api_key=api_key or openai_config.get("api_key", "dummy"),
            model=model or openai_config.get("model", "llama-2-7b-chat"),
            temperature=openai_config.get("temperature", 0.1),
            max_tokens=openai_config.get("max_tokens", 2048),
            cache_enabled=translation_config.get("cache_enabled", True),
        )
    
    return _translator


def translate_text(
    text: str,
    from_lang: str = "en",
    to_lang: str = "fr",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
) -> str:
    """
    Traduit un texte de l'anglais vers le français via l'API OpenAI locale.
    
    Args:
        text: Texte à traduire.
        from_lang: Langue source (par défaut "en").
        to_lang: Langue cible (par défaut "fr").
        base_url: URL de base de l'API OpenAI (remplace la config).
        api_key: Clé API (remplace la config).
        model: Modèle à utiliser (remplace la config).
        config_path: Chemin vers le fichier de configuration.
    
    Returns:
        Texte traduit.
    
    Raises:
        TranslationError: Si la traduction échoue.
    """
    translator = get_translator(base_url, api_key, model, config_path)
    return translator.translate(text, from_lang, to_lang)


def translate_batch(
    texts: List[str],
    from_lang: str = "en",
    to_lang: str = "fr",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
) -> List[str]:
    """
    Traduit une liste de textes en une seule passe.
    
    Args:
        texts: Liste de textes à traduire.
        from_lang: Langue source.
        to_lang: Langue cible.
        base_url: URL de base de l'API OpenAI.
        api_key: Clé API.
        model: Modèle à utiliser.
        config_path: Chemin vers le fichier de configuration.
    
    Returns:
        Liste de textes traduits.
    """
    translator = get_translator(base_url, api_key, model, config_path)
    return translator.batch_translate(texts, from_lang, to_lang)
