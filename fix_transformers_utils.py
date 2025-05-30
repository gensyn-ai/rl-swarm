import transformers.utils

# Eksik fonksiyonları ekle
if not hasattr(transformers.utils, 'is_rich_available'):
    def is_rich_available():
        try:
            import rich
            return True
        except ImportError:
            return False
    
    transformers.utils.is_rich_available = is_rich_available

print("Transformers utils patch uygulandı!")
