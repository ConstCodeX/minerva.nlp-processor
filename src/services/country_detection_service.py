"""
Servicio de detección de país - Maneja la identificación del país mencionado en un artículo
Responsabilidad única: Detectar el país del contexto
"""

from typing import Optional


class CountryDetectionService:
    """Servicio para detectar países mencionados en texto"""
    
    def __init__(self):
        # Mapa compacto de países clave con patrones
        self.country_patterns = {
            'Perú': ['perú', 'peru', 'peruano', 'lima', 'arequipa', 'cusco'],
            'Chile': ['chile', 'chileno', 'santiago', 'boric'],
            'Argentina': ['argentina', 'argentino', 'buenos aires', 'milei'],
            'México': ['méxico', 'mexicano', 'cdmx', 'amlo'],
            'Colombia': ['colombia', 'colombiano', 'bogotá', 'petro'],
            'Brasil': ['brasil', 'brasileño', 'brasilia', 'lula'],
            'Estados Unidos': ['estados unidos', 'eeuu', 'usa', 'biden', 'trump'],
            'España': ['españa', 'español', 'madrid', 'barcelona'],
            'China': ['china', 'chino', 'beijing', 'xi jinping'],
            'Rusia': ['rusia', 'ruso', 'moscú', 'putin'],
        }
    
    def detect(self, text: str) -> Optional[str]:
        """
        Detecta el país más mencionado en el texto
        
        Returns:
            Nombre del país o None si no se detecta
        """
        text_lower = text.lower()
        
        country_mentions = {}
        for country, patterns in self.country_patterns.items():
            count = sum(1 for pattern in patterns if pattern in text_lower)
            if count > 0:
                country_mentions[country] = count
        
        if country_mentions:
            return max(country_mentions, key=country_mentions.get)
        
        return None
