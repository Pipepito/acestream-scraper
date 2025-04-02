import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple
import re

from app.models.acestream_channel import AcestreamChannel
from app.models.epg_source import EPGSource
from app.models.epg_string_mapping import EPGStringMapping
from app.repositories.epg_source_repository import EPGSourceRepository
from app.repositories.epg_string_mapping_repository import EPGStringMappingRepository
from app.repositories.channel_repository import ChannelRepository
from app.extensions import db

logger = logging.getLogger(__name__)

class EPGService:
    def __init__(self):
        self.epg_source_repo = EPGSourceRepository()
        self.epg_string_mapping_repo = EPGStringMappingRepository()
        self.channel_repo = ChannelRepository()
        self.epg_data = {}  # Cache of EPG data {tvg_id: {tvg_name, logo}}
        self.auto_mapping_threshold = 0.75  # Similarity threshold for auto-mapping
    
    def fetch_epg_data(self) -> Dict:
        """Fetch EPG data from all enabled sources."""
        self.epg_data = {}
        sources = self.epg_source_repo.get_enabled()
        
        for source in sources:
            try:
                logger.info(f"Fetching EPG data from {source.url}")
                response = requests.get(source.url, timeout=60)
                if response.status_code == 200:
                    self._parse_epg_xml(response.text, source.id)  # Pass source.id
                    # Update timestamp
                    source.last_updated = datetime.utcnow()
                    source.error_count = 0
                    source.last_error = None
                else:
                    error_msg = f"HTTP error {response.status_code}"
                    logger.warning(f"Error fetching EPG from {source.url}: {error_msg}")
                    source.error_count = source.error_count + 1 if source.error_count else 1
                    source.last_error = error_msg
            except Exception as e:
                logger.error(f"Error processing EPG from {source.url}: {str(e)}")
                source.error_count = source.error_count + 1 if source.error_count else 1
                source.last_error = str(e)
            
            # Save changes to the source
            self.epg_source_repo.update(source)
        
        logger.info(f"Loaded {len(self.epg_data)} channels from EPG sources")
        return self.epg_data
    
    def _parse_epg_xml(self, xml_content: str, source_id: int) -> None:
        try:
            root = ET.fromstring(xml_content)
            
            # Extract channel information
            for channel in root.findall(".//channel"):
                channel_id = channel.get("id")
                if not channel_id:
                    continue
                
                display_name_elem = channel.find("display-name")
                channel_name = display_name_elem.text if display_name_elem is not None else ""
                
                icon_elem = channel.find("icon")
                icon_url = icon_elem.get("src") if icon_elem is not None else ""
                
                self.epg_data[channel_id] = {
                    "tvg_id": channel_id,
                    "tvg_name": channel_name,
                    "logo": icon_url,
                    "source_id": source_id  # Store the source ID
                }
                
        except Exception as e:
            logger.error(f"Error parsing EPG XML: {str(e)}")
            raise
    
    def get_channel_epg_data(self, channel: AcestreamChannel) -> Dict:
        """
        Get EPG data for a specific channel with the following priority:
        1. Direct manual mapping in the channel table
        2. String pattern mapping in EPGStringMapping
        3. Automatic mapping by name similarity
        """
        # Ensure we have EPG data
        if not self.epg_data:
            self.fetch_epg_data()
        
        # 1. Check if it already has manual mapping in the table
        if channel.tvg_id and channel.tvg_id in self.epg_data:
            return self.epg_data[channel.tvg_id]
        
        # 2. Look for string pattern matches
        string_mappings = self.epg_string_mapping_repo.get_all()
        for mapping in string_mappings:
            if mapping.search_pattern.lower() in channel.name.lower() and mapping.epg_channel_id in self.epg_data:
                # Found a pattern match
                return self.epg_data[mapping.epg_channel_id]
        
        # 3. Try automatic mapping by similarity
        best_match = None
        best_score = 0
        
        for epg_id, epg_data in self.epg_data.items():
            score = SequenceMatcher(None, channel.name.lower(), epg_data["tvg_name"].lower()).ratio()
            if score > best_score and score >= self.auto_mapping_threshold:
                best_score = score
                best_match = epg_id
        
        if best_match:
            logger.info(f"Auto-mapped '{channel.name}' to '{self.epg_data[best_match]['tvg_name']}' (score: {best_score:.2f})")
            return self.epg_data[best_match]
        
        # If no match, return basic information
        return {
            "tvg_id": "",
            "tvg_name": channel.name,
            "logo": ""
        }
    
    def _update_channel_epg(self, channel: AcestreamChannel) -> Tuple[bool, bool, bool, bool]:
        """
        Update EPG data for a channel.
        
        Returns a tuple of (tvg_id_updated, tvg_name_updated, logo_updated, any_update)
        """
        string_mappings = self.epg_string_mapping_repo.get_all()
        
        # Detectar si el canal debe ser excluido (mantener esta parte sin cambios)
        channel_name_lower = channel.name.lower()
        for mapping in string_mappings:
            if mapping.search_pattern.startswith('!'):
                exclusion_pattern = mapping.search_pattern[1:].lower()
                if exclusion_pattern in channel_name_lower:
                    logger.info(f"Channel '{channel.name}' excluded by pattern '!{exclusion_pattern}'")
                    
                    # Limpiar los datos EPG si el canal tiene algún dato
                    changes_made = False
                    
                    if channel.tvg_id:
                        channel.tvg_id = None
                        changes_made = True
                    
                    if channel.tvg_name:
                        channel.tvg_name = None
                        changes_made = True
                    
                    if channel.logo:
                        channel.logo = None
                        changes_made = True
                    
                    if changes_made:
                        logger.info(f"Cleared EPG data from channel '{channel.name}' due to exclusion pattern")
                        return (True, True, True, True)
                    
                    return (False, False, False, False)
        
        # Mejorar la lógica de mapeo
        potential_mappings = []
        
        # Pre-procesar el nombre del canal para dividirlo en palabras para comparación más exacta
        channel_words = channel_name_lower.split()
        
        for mapping in string_mappings:
            if not mapping.search_pattern.startswith('!'):  # Solo procesar patrones regulares
                pattern_lower = mapping.search_pattern.lower()
                pattern_words = pattern_lower.split()
                
                # Solo considerar patrones que estén dentro del nombre del canal
                if pattern_lower in channel_name_lower:
                    # Base score - longitud del patrón multiplicado por 10 para darle más peso
                    pattern_score = len(pattern_lower) * 10
                    
                    # MAYOR PRIORIDAD: Coincidencia exacta con el nombre completo
                    if pattern_lower == channel_name_lower:
                        pattern_score += 10000  # Prioridad extremadamente alta
                    
                    # NUEVA PRIORIDAD MUY ALTA: El patrón coincide exactamente con el inicio del nombre
                    if channel_name_lower.startswith(pattern_lower):
                        pattern_score += 3000  # Mayor prioridad que tener números
                    
                    # ALTA PRIORIDAD: Coincidencia al inicio del nombre (más importante que tener números)
                    elif channel_name_lower.startswith(pattern_lower + ' '):
                        pattern_score += 2500  # Mayor prioridad que tener números
                    
                    # Bonus por coincidencia de palabras completas
                    matching_words = 0
                    for word in pattern_words:
                        if word in channel_words:
                            matching_words += 1
                    
                    if matching_words == len(pattern_words):
                        pattern_score += 1000 * matching_words
                        
                        # Bonus si las palabras están en el mismo orden
                        if ' '.join(pattern_words) in ' '.join(channel_words):
                            pattern_score += 500
                    
                    # Bonus para patrones con números (reducido para no sobrepasar coincidencias al inicio)
                    if any(char.isdigit() for char in pattern_lower):
                        pattern_score += 1500  # Reducido de 2000 a 1500
                    
                    # NUEVO: Bonus adicional si la primera palabra del patrón coincide con la primera palabra del canal
                    # Esto ayuda a priorizar patrones como "dazn laliga" para canales que comienzan con "DAZN"
                    if channel_words and pattern_words and channel_words[0] == pattern_words[0]:
                        pattern_score += 1800
                    
                    potential_mappings.append((mapping, pattern_score))
        
        # Ordenar por score, de mayor a menor
        potential_mappings.sort(key=lambda x: x[1], reverse=True)
        
        # Usar el mapeo con el score más alto si existe
        if potential_mappings:
            best_mapping, score = potential_mappings[0]
            
            if best_mapping.epg_channel_id in self.epg_data:
                epg_data = self.epg_data[best_mapping.epg_channel_id]
                updates = self._apply_epg_data(channel, epg_data)
                if any(updates):
                    logger.info(f"Channel '{channel.name}' matched pattern '{best_mapping.search_pattern}', applied EPG data from channel '{best_mapping.epg_channel_id}'")
                return updates
            else:
                logger.warning(f"EPG channel ID '{best_mapping.epg_channel_id}' not found for pattern '{best_mapping.search_pattern}'")
        
        # Si no se encontró ningún mapeo adecuado
        return (False, False, False, False)
    
    def _apply_epg_data(self, channel: AcestreamChannel, epg_data: Dict) -> Tuple[bool, bool, bool]:
        """
        Apply EPG data to the channel, always updating if the data exists in the EPG.
        This overrides the previous behavior of only updating if the channel data was empty.
        Returns a tuple of (tvg_id_updated, tvg_name_updated, logo_updated).
        """
        tvg_id_updated = False
        tvg_name_updated = False
        logo_updated = False
        
        # Update tvg_id if provided in EPG data (always update, not just when empty)
        if epg_data["tvg_id"]:
            # Only mark as updated if value actually changes
            tvg_id_updated = channel.tvg_id != epg_data["tvg_id"]
            channel.tvg_id = epg_data["tvg_id"]
        
        # Update tvg_name if provided in EPG data
        if epg_data["tvg_name"]:
            tvg_name_updated = channel.tvg_name != epg_data["tvg_name"]
            channel.tvg_name = epg_data["tvg_name"]
        
        # Update logo if provided in EPG data
        if epg_data["logo"]:
            logo_updated = channel.logo != epg_data["logo"]
            channel.logo = epg_data["logo"]
            
        return (tvg_id_updated, tvg_name_updated, logo_updated)
    
    def update_all_channels_epg(self, respect_existing: bool = False, clean_unmatched: bool = False) -> dict:
        """
        Updates EPG information for all channels that don't have EPG locked.
        
        Args:
            respect_existing: If True, don't modify channels that already have some EPG data
            clean_unmatched: If True, clear EPG data from channels with no match
        
        Returns:
            Stats about the update process.
        """
        stats = {
            "total": 0,
            "updated": 0,
            "locked": 0,
            "excluded": 0,
            "cleaned": 0,
            "skipped": 0,
            "errors": 0
        }
        
        # Verificar si hay reglas de mapeo definidas
        string_mappings = self.epg_string_mapping_repo.get_all()
        normal_rules = [m for m in string_mappings if not m.search_pattern.startswith('!')]
        has_mapping_rules = len(normal_rules) > 0
        
        logger.info(f"Updating EPG mappings. Has mapping rules: {has_mapping_rules}, Normal rules count: {len(normal_rules)}")
        
        channels = self.channel_repo.get_all()
        channels_with_epg = [c for c in channels if c.tvg_id or c.tvg_name or c.logo]
        
        logger.info(f"Processing {len(channels)} channels, {len(channels_with_epg)} have some EPG data")
        stats["total"] = len(channels)
        
        # Primero asegurarnos de cargar los datos EPG
        if not self.epg_data:
            self.fetch_epg_data()
        
        # Usar una transacción explícita para asegurar que los cambios se apliquen
        from sqlalchemy.orm import Session
        session = db.session
        
        try:
            for channel in channels:
                try:
                    # Cambiar epg_update_protected por epg_update_protected
                    if channel.epg_update_protected:
                        stats["locked"] += 1
                        continue
                    
                    # Si la opción respect_existing está activada y el canal ya tiene datos, saltarlo
                    if respect_existing and (channel.tvg_id or channel.tvg_name or channel.logo):
                        stats["skipped"] += 1
                        continue
                    
                    if not has_mapping_rules:
                        # Si no hay reglas de mapeo y el canal tiene datos, limpiarlo SOLO si clean_unmatched es true
                        if clean_unmatched and (channel.tvg_id or channel.tvg_name or channel.logo):
                            old_data = f"tvg_id={channel.tvg_id}, tvg_name={channel.tvg_name}, logo={'Yes' if channel.logo else 'No'}"
                            
                            # Realizar limpieza directamente
                            channel.tvg_id = None
                            channel.tvg_name = None
                            channel.logo = None
                            
                            # Actualizar el canal en la base de datos
                            try:
                                self.channel_repo.update(channel)
                                session.flush()
                                
                                stats["cleaned"] += 1
                                logger.info(f"CLEANED: Channel '{channel.name}' (previous: {old_data}) - no mapping rules exist")
                            except Exception as e:
                                logger.error(f"Failed to update channel {channel.name}: {str(e)}")
                                stats["errors"] += 1
                        continue
                    
                    # Si hay reglas, proceder con la aplicación de mapeos
                    was_updated, tvg_id_updated, tvg_name_updated, logo_updated = self._update_channel_epg(channel)
                    
                    if was_updated:
                        try:
                            self.channel_repo.update(channel)
                            session.flush()  # Asegurar que los cambios se apliquen
                            
                            if not channel.tvg_id and not channel.tvg_name and not channel.logo:
                                stats["cleaned"] += 1
                                stats["excluded"] += 1
                                logger.info(f"EXCLUDED: Channel '{channel.name}' matched exclusion rule")
                            else:
                                stats["updated"] += 1
                                logger.info(f"UPDATED: Channel '{channel.name}' with new EPG data")
                        except Exception as e:
                            logger.error(f"Failed to save updates for channel {channel.name}: {str(e)}")
                            stats["errors"] += 1
                        continue
                    
                    # Si no se actualizó el canal y no está excluido, limpiar sus datos
                    is_excluded = self._is_excluded_by_rule(channel)
                    
                    if not is_excluded and (channel.tvg_id or channel.tvg_name or channel.logo):
                        # CORRECCIÓN: Limpiar solo si clean_unmatched es verdadero
                        if clean_unmatched:
                            old_data = f"tvg_id={channel.tvg_id}, tvg_name={channel.tvg_name}, logo={'Yes' if channel.logo else 'No'}"
                            
                            # Limpiar datos
                            channel.tvg_id = None
                            channel.tvg_name = None
                            channel.logo = None
                            
                            try:
                                self.channel_repo.update(channel)
                                session.flush()
                                
                                stats["cleaned"] += 1
                                logger.info(f"CLEANED: Channel '{channel.name}' (previous: {old_data}) - no matching rule")
                            except Exception as e:
                                logger.error(f"Failed to clean channel {channel.name}: {str(e)}")
                                stats["errors"] += 1
                    elif is_excluded:
                        stats["excluded"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing channel {channel.name}: {str(e)}")
                    stats["errors"] += 1
            
            # Confirmar todos los cambios
            session.commit()
            logger.info(f"EPG update completed. Summary: Updated={stats['updated']}, Cleaned={stats['cleaned']}, Locked={stats['locked']}, Excluded={stats['excluded']}, Errors={stats['errors']}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed, rolling back: {str(e)}")
            stats["errors"] += 1
            raise
                
        return stats
    
    def _is_excluded_by_rule(self, channel: AcestreamChannel) -> bool:
        """Determinar si un canal está excluido por una regla de patrón."""
        channel_name_lower = channel.name.lower()
        string_mappings = self.epg_string_mapping_repo.get_all()
        
        for mapping in string_mappings:
            if mapping.search_pattern.startswith('!'):
                exclusion_pattern = mapping.search_pattern[1:].lower()
                if exclusion_pattern in channel_name_lower:
                    return True
        
        return False

    def auto_scan_channels(self, threshold: float = 0.8, clean_unmatched: bool = False, respect_existing: bool = False) -> dict:
        """
        Scan all unlocked channels and try to match them with EPG data.
        
        Args:
            threshold: Similarity threshold for matching (0.0-1.0)
            clean_unmatched: If True, clear EPG data from channels with no match
            respect_existing: If True, don't modify channels that already have some EPG data
        
        Returns:
            Statistics about the scan
        """
        # Ensure we have EPG data
        if not self.epg_data:
            self.fetch_epg_data()
        
        channels = self.channel_repo.get_all()
        
        total_processed = 0
        total_matched = 0
        total_cleaned = 0
        total_skipped = 0
        
        for channel in channels:
            if channel.epg_update_protected:
                continue
                
            # Skip channels excluded by rules
            if self._is_excluded_by_rule(channel):
                continue
            
            # Skip channels that already have EPG data if respect_existing is enabled
            if respect_existing and (channel.tvg_id or channel.tvg_name or channel.logo):
                total_skipped += 1
                continue
            
            # Skip channels with complete EPG data
            if channel.tvg_id and channel.tvg_name and channel.logo:
                continue
                
            total_processed += 1
            
            # Try to find best match by name similarity using normalized names
            best_match = None
            best_score = 0
            normalized_channel_name = self._normalize_channel_name(channel.name)
            
            for epg_id, epg_data in self.epg_data.items():
                normalized_epg_name = self._normalize_channel_name(epg_data["tvg_name"])
                
                # Usar nombres normalizados para la comparación
                score = SequenceMatcher(None, normalized_channel_name, normalized_epg_name).ratio()
                
                # Dar bonus si el inicio del nombre coincide exactamente
                if normalized_epg_name.startswith(normalized_channel_name) or normalized_channel_name.startswith(normalized_epg_name):
                    score += 0.1  # Bonus for matching prefix
                
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = epg_id
            
            if best_match:
                epg_data = self.epg_data[best_match]
                updates = self._apply_epg_data(channel, epg_data)
                if any(updates):
                    logger.info(f"Auto-mapped '{channel.name}' to '{epg_data['tvg_name']}' (score: {best_score:.2f}, normalized: '{normalized_channel_name}')")
                    self.channel_repo.update(channel)
                    total_matched += 1
            elif clean_unmatched and (channel.tvg_id or channel.tvg_name or channel.logo):
                # Clean EPG data if no match was found and clean_unmatched is enabled
                old_data = f"tvg_id={channel.tvg_id}, tvg_name={channel.tvg_name}, logo={'Yes' if channel.logo else 'No'}"
                channel.tvg_id = None
                channel.tvg_name = None
                channel.logo = None
                self.channel_repo.update(channel)
                total_cleaned += 1
                logger.info(f"Cleaned EPG data from channel '{channel.name}' (previous: {old_data}) - no match found")
        
        # Save all changes
        db.session.commit()
        
        return {
            'total': total_processed,
            'matched': total_matched,
            'cleaned': total_cleaned,
            'skipped': total_skipped
        }

    def _normalize_channel_name(self, channel_name: str) -> str:
        """
        Normaliza el nombre del canal eliminando indicadores de calidad y términos técnicos
        que no son relevantes para la comparación con EPG.
        """
        # Convertir a minúsculas
        name = channel_name.lower()
        
        # Eliminar todo lo que esté entre paréntesis
        name = re.sub(r'\([^)]*\)', '', name)
        
        # Eliminar términos técnicos comunes
        terms_to_remove = [
            '1080', '1080p', '720', '480', '4k', '8k',
            'hd', 'sd', 'uhd', 'fullhd', 'full hd', 
            'multiaudio', 'multi audio', 'multilenguaje', 'multi', 
            'p', 'i', 'h264', 'h265', 'hevc',
            'ace', 'acestream', 
            '+', '[]', '()', '{}',
        ]
        
        for term in terms_to_remove:
            # Reemplazar el término rodeado por espacios, al principio o al final
            name = re.sub(r'(^|\s)' + re.escape(term) + r'(\s|$)', ' ', name)
        
        # Eliminar múltiples espacios
        name = re.sub(r'\s+', ' ', name)
        
        # Eliminar espacios al principio y al final
        name = name.strip()
        
        return name