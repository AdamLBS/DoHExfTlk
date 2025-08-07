#!/usr/bin/env python3
"""
DoH Exfiltration Server - Version Simplifiée

Simple serveur pour capturer et reconstruire les données exfiltrées via DoH.
Se concentre uniquement sur la capture et reconstruction, sans détection complexe.
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from traffic_interceptor import DoHTrafficInterceptor

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,  # Activer le debug
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force la reconfiguration du logging
)
logger = logging.getLogger(__name__)

class SimpleExfiltrationServer:
    """Serveur simple pour capturer l'exfiltration DoH"""
    
    def __init__(self, output_dir="/app/captured", interface=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.interface = interface or os.environ.get('INTERFACE', 'eth0')
        
        # Sessions de reconstruction
        self.sessions = {}
        self.session_lock = threading.Lock()
        
        logger.info(f"Serveur d'exfiltration démarré")
        logger.info(f"Interface: {self.interface}")
        logger.info(f"Répertoire de sortie: {self.output_dir}")
    
    def handle_dns_query(self, query_data):
        """Traite une requête DNS capturée"""
        try:
            domain = query_data.get('domain', '')
            query_name = query_data.get('query_name', '')
            
            # Détecter les requêtes d'exfiltration (domaines suspects)
            if any(keyword in domain.lower() for keyword in ['exfill', 'data', 'leak']):
                logger.info(f"🎯 Requête d'exfiltration détectée: {query_name}")
                
                # Extraire les données potentielles
                self._extract_exfiltration_data(query_data)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête: {e}")
    
    def _extract_exfiltration_data(self, query_data):
        """Extrait et stocke les données d'exfiltration"""
        try:
            query_name = query_data.get('query_name', '')
            timestamp = query_data.get('timestamp', time.time())
            
            # Analyser le format: session_id-index-total-chunk.random.domain
            logger.debug(f"🔍 Analyzing query name: {query_name}")
            parts = query_name.split('.')
            if len(parts) >= 2:
                data_segment = parts[0]  # Premier segment avant le premier point
                
                # Parser le format: session_id-index-total-chunk
                import re
                # Pattern correct pour le format réel: timestamp-index-total-chunk
                # Le chunk peut contenir des caractères base64 (lettres, chiffres, +, /, =, -, _)
                pattern = re.compile(r"(\d+)-(\d+)-(\d+)-(.+)")
                
                # Debug : afficher les tentatives de matching
                logger.debug(f"🔍 Tentative de parsing: '{data_segment}'")
                match = pattern.match(data_segment)
                
                if match:
                    session_id = match.group(1)  # timestamp uniquement
                    index = int(match.group(2))
                    total = int(match.group(3))
                    chunk = match.group(4)  # Données base64
                    
                    logger.debug(f"✅ Match réussi: session={session_id}, index={index}, total={total}, chunk={chunk[:10]}...")
                    
                    with self.session_lock:
                        if session_id not in self.sessions:
                            self.sessions[session_id] = {
                                'start_time': timestamp,
                                'total_chunks': total,
                                'chunks': {},  # Utiliser un dict pour l'indexation
                                'queries': []
                            }
                        
                        # Stocker le chunk avec son index
                        self.sessions[session_id]['chunks'][index] = chunk
                        self.sessions[session_id]['queries'].append(query_data)
                    
                    logger.info(f"📦 Segment de données capturé: {session_id}-{index:04d}-{total:04d}-{chunk[:20]}...")
                    
                    # Vérifier si on a tous les chunks
                    session = self.sessions[session_id]
                    if len(session['chunks']) >= session['total_chunks']:
                        logger.info(f"🔧 Reconstruction complète pour session {session_id} ({session['total_chunks']} chunks)")
                        self._try_reconstruct_session(session_id)
                else:
                    # Debug détaillé pour comprendre pourquoi ça ne marche pas
                    logger.warning(f"⚠️ Format de chunk non reconnu 2: {data_segment}")
                    logger.debug(f"🔧 Pattern utilisé: {pattern.pattern}")
                    
                    # Tentative de debug avec un pattern plus simple
                    simple_pattern = re.compile(r"(\d+)-(\d+)-(\d+)-(.+)")
                    simple_match = simple_pattern.match(data_segment)
                    if simple_match:
                        logger.debug(f"✅ Simple pattern match: {simple_match.groups()}")
                    else:
                        logger.debug(f"❌ Même le simple pattern ne fonctionne pas")
                        
                        # Afficher les caractères un par un pour diagnostiquer
                        chars_debug = [f"{c}({ord(c)})" for c in data_segment[:50]]
                        logger.debug(f"🔤 Caractères: {' '.join(chars_debug)}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction: {e}")
            import traceback
            traceback.print_exc()
    
    def _try_reconstruct_session(self, session_id):
        """Tente de reconstruire les données d'une session"""
        try:
            session = self.sessions[session_id]
            chunks = session['chunks']
            total_chunks = session['total_chunks']
            
            # Vérifier que tous les chunks sont présents
            if len(chunks) == total_chunks:
                logger.info(f"🔧 Reconstruction complète pour session {session_id} ({total_chunks} chunks)")
                
                # Ordonner les chunks par index
                ordered_chunks = []
                for i in range(total_chunks):
                    if i in chunks:
                        ordered_chunks.append(chunks[i])
                    else:
                        logger.error(f"❌ Chunk manquant: {i}")
                        return
                
                # Reconstruire les données
                reconstructed_data = self._decode_chunks(ordered_chunks)
                
                if reconstructed_data:
                    # Sauvegarder les données reconstruites
                    output_file = self.output_dir / f"exfiltrated_{session_id}_{int(time.time())}.bin"
                    with open(output_file, 'wb') as f:
                        f.write(reconstructed_data)
                    
                    # Analyser le type de fichier et afficher l'aperçu approprié
                    file_info = self._analyze_file_content(reconstructed_data)
                    
                    logger.info(f"✅ Données reconstruites sauvées: {output_file}")
                    logger.info(f"📊 Taille: {len(reconstructed_data)} bytes")
                    logger.info(f"� Type détecté: {file_info['type']}")
                    
                    # Afficher l'aperçu selon le type
                    self._display_file_preview(reconstructed_data, file_info)
                    
                    # Nettoyer la session
                    del self.sessions[session_id]
            else:
                logger.info(f"⏳ Session {session_id}: {len(chunks)}/{total_chunks} chunks reçus")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la reconstruction: {e}")
            import traceback
            traceback.print_exc()
    
    def _decode_chunks(self, ordered_chunks):
        """Décode les chunks ordonnés en données originales"""
        import base64
        
        # Concaténer tous les chunks dans l'ordre
        combined_data = ''.join(ordered_chunks)
        logger.info(f"🔢 Données combinées: {len(combined_data)} caractères")
        
        # Essayer le décodage base64 URL-safe en premier (utilisé par le client)
        try:
            # Ajouter le padding nécessaire pour base64
            padding_needed = 4 - (len(combined_data) % 4)
            if padding_needed != 4:
                combined_data += '=' * padding_needed
            
            decoded = base64.urlsafe_b64decode(combined_data)
            logger.info(f"✅ Décodage réussi avec base64 URL-safe")
            return decoded
        except Exception as e:
            logger.warning(f"⚠️ Échec base64 URL-safe: {e}")
        
        # Essayer base64 standard
        try:
            decoded = base64.b64decode(combined_data + '=' * (4 - len(combined_data) % 4))
            logger.info(f"✅ Décodage réussi avec base64 standard")
            return decoded
        except Exception as e:
            logger.warning(f"⚠️ Échec base64 standard: {e}")
        
        # Essayer base32
        try:
            padding_needed = 8 - (len(combined_data) % 8)
            if padding_needed != 8:
                combined_data += '=' * padding_needed
            decoded = base64.b32decode(combined_data)
            logger.info(f"✅ Décodage réussi avec base32")
            return decoded
        except Exception as e:
            logger.warning(f"⚠️ Échec base32: {e}")
        
        # Essayer hex
        try:
            decoded = bytes.fromhex(combined_data)
            logger.info(f"✅ Décodage réussi avec hex")
            return decoded
        except Exception as e:
            logger.warning(f"⚠️ Échec hex: {e}")
        
        # Si aucun décodage ne fonctionne, traiter comme données brutes
        logger.warning("⚠️ Aucun décodage réussi, sauvegarde des données brutes")
        return combined_data.encode('utf-8', errors='ignore')
    
    def _analyze_file_content(self, data):
        """Analyse le contenu du fichier pour déterminer son type"""
        if not data:
            return {'type': 'empty', 'encoding': None}
        
        # Vérifier les signatures de fichiers (magic numbers)
        signatures = {
            b'\x89PNG\r\n\x1a\n': {'type': 'PNG Image', 'ext': '.png'},
            b'\xff\xd8\xff': {'type': 'JPEG Image', 'ext': '.jpg'},
            b'GIF8': {'type': 'GIF Image', 'ext': '.gif'},
            b'%PDF': {'type': 'PDF Document', 'ext': '.pdf'},
            b'PK\x03\x04': {'type': 'ZIP Archive', 'ext': '.zip'},
            b'PK\x05\x06': {'type': 'ZIP Archive (empty)', 'ext': '.zip'},
            b'\x50\x4b\x03\x04': {'type': 'ZIP/Office Document', 'ext': '.zip'},
            b'\x1f\x8b\x08': {'type': 'GZIP Archive', 'ext': '.gz'},
            b'BZ': {'type': 'BZIP2 Archive', 'ext': '.bz2'},
            b'\x37\x7a\xbc\xaf\x27\x1c': {'type': '7ZIP Archive', 'ext': '.7z'},
            b'Rar!\x1a\x07\x00': {'type': 'RAR Archive', 'ext': '.rar'},
            b'\x00\x00\x01\x00': {'type': 'Windows Icon', 'ext': '.ico'},
            b'RIFF': {'type': 'RIFF (Audio/Video)', 'ext': '.wav/.avi'},
            b'\x49\x44\x33': {'type': 'MP3 Audio', 'ext': '.mp3'},
            b'\x66\x74\x79\x70': {'type': 'MP4 Video', 'ext': '.mp4'},
            b'\x00\x00\x00\x0c\x6a\x50\x20\x20': {'type': 'JPEG 2000', 'ext': '.jp2'},
            b'\x89\x50\x4e\x47': {'type': 'PNG Image', 'ext': '.png'},
            b'\x42\x4d': {'type': 'BMP Image', 'ext': '.bmp'},
            b'\x52\x61\x72\x21': {'type': 'RAR Archive', 'ext': '.rar'},
            b'\x7f\x45\x4c\x46': {'type': 'ELF Executable', 'ext': ''},
            b'MZ': {'type': 'Windows Executable', 'ext': '.exe'},
            b'\xca\xfe\xba\xbe': {'type': 'Java Class', 'ext': '.class'},
            b'\xd0\xcf\x11\xe0': {'type': 'Microsoft Office', 'ext': '.doc/.xls'},
        }
        
        # Vérifier les signatures
        for signature, info in signatures.items():
            if data.startswith(signature):
                return {
                    'type': info['type'],
                    'extension': info['ext'],
                    'encoding': 'binary'
                }
        
        # Essayer de détecter du texte
        try:
            # Tenter UTF-8
            text_content = data.decode('utf-8')
            # Vérifier si c'est du texte lisible (pas trop de caractères de contrôle)
            printable_ratio = sum(c.isprintable() or c.isspace() for c in text_content) / len(text_content)
            
            if printable_ratio > 0.8:  # 80% de caractères imprimables
                # Détecter le type de texte
                lower_content = text_content.lower()
                if any(marker in lower_content for marker in ['<html', '<!doctype', '<xml']):
                    return {'type': 'HTML/XML Document', 'encoding': 'utf-8', 'extension': '.html'}
                elif any(marker in lower_content for marker in ['{', '}', '":', '[']):
                    return {'type': 'JSON Data', 'encoding': 'utf-8', 'extension': '.json'}
                elif any(marker in lower_content for marker in ['def ', 'import ', 'class ', 'print(']):
                    return {'type': 'Python Code', 'encoding': 'utf-8', 'extension': '.py'}
                elif any(marker in lower_content for marker in ['function', 'var ', 'const ', 'let ']):
                    return {'type': 'JavaScript Code', 'encoding': 'utf-8', 'extension': '.js'}
                elif any(marker in lower_content for marker in ['#!/bin/', '#include', 'int main']):
                    return {'type': 'Source Code', 'encoding': 'utf-8', 'extension': '.c/.sh'}
                else:
                    return {'type': 'Plain Text', 'encoding': 'utf-8', 'extension': '.txt'}
        except UnicodeDecodeError:
            pass
        
        # Essayer d'autres encodages
        for encoding in ['latin-1', 'cp1252', 'ascii']:
            try:
                text_content = data.decode(encoding)
                printable_ratio = sum(c.isprintable() or c.isspace() for c in text_content) / len(text_content)
                if printable_ratio > 0.8:
                    return {'type': f'Text ({encoding})', 'encoding': encoding, 'extension': '.txt'}
            except:
                continue
        
        # Par défaut, considérer comme binaire
        return {'type': 'Binary Data', 'encoding': 'binary', 'extension': '.bin'}
    
    def _display_file_preview(self, data, file_info):
        """Affiche un aperçu approprié selon le type de fichier"""
        try:
            if file_info['encoding'] == 'binary':
                # Affichage hexadécimal pour les fichiers binaires
                hex_preview = data[:64].hex()
                formatted_hex = ' '.join(hex_preview[i:i+2] for i in range(0, len(hex_preview), 2))
                logger.info(f"📄 Aperçu hexadécimal: {formatted_hex}...")
                
                # Essayer d'afficher des caractères ASCII visibles
                ascii_preview = ''
                for byte in data[:64]:
                    if 32 <= byte <= 126:  # Caractères ASCII imprimables
                        ascii_preview += chr(byte)
                    else:
                        ascii_preview += '.'
                
                if ascii_preview.strip('.'):
                    logger.info(f"📄 Aperçu ASCII: {ascii_preview}")
                
            else:
                # Affichage texte pour les fichiers texte
                text_content = data.decode(file_info['encoding'], errors='ignore')
                
                # Limiter l'aperçu et nettoyer
                preview_lines = text_content[:500].split('\n')[:10]
                clean_preview = '\n'.join(line.strip() for line in preview_lines if line.strip())
                
                logger.info(f"📄 Aperçu texte:")
                for i, line in enumerate(clean_preview.split('\n')[:5]):
                    if line:
                        logger.info(f"   {i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
                
                # Statistiques pour les fichiers texte
                lines_count = len(text_content.split('\n'))
                words_count = len(text_content.split())
                logger.info(f"📊 Statistiques: {lines_count} lignes, {words_count} mots")
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur affichage aperçu: {e}")
            # Aperçu basique en cas d'erreur
            basic_preview = str(data[:100])[:100]
            logger.info(f"📄 Aperçu basique: {basic_preview}...")
    
    def start(self):
        """Démarre le serveur de capture"""
        logger.info("🚀 Démarrage de la capture...")
        
        try:
            # Créer l'intercepteur de trafic
            interceptor = DoHTrafficInterceptor(
                interface=self.interface,
                output_dir=str(self.output_dir)
            )
            
            # Configurer le callback pour traiter les requêtes
            interceptor.dns_callback = self.handle_dns_query
            
            # Démarrer la capture
            interceptor.start_capture()
            
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt du serveur...")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            sys.exit(1)

def main():
    """Point d'entrée principal"""
    
    # Configuration depuis les variables d'environnement
    output_dir = os.environ.get('OUTPUT_DIR', '/app/captured')
    interface = os.environ.get('INTERFACE')
    
    # Créer et démarrer le serveur
    server = SimpleExfiltrationServer(
        output_dir=output_dir,
        interface=interface
    )
    
    server.start()

if __name__ == "__main__":
    main()
