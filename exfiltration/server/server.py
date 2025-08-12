#!/usr/bin/env python3
import os
import sys
import time
import logging
import threading
from pathlib import Path
from traffic_interceptor import DoHTrafficInterceptor

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class SimpleExfiltrationServer:
    """Simple server to capture DoH exfiltration"""
    
    def __init__(self, output_dir="/app/captured", interface=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        os.chown(self.output_dir, 1000, 1000)
        self.interface = interface or os.environ.get('INTERFACE', 'eth0')
        
        # Reconstruction sessions
        self.sessions = {}
        self.session_lock = threading.Lock()
        
        logger.info(f"Exfiltration server started")
        logger.info(f"Interface: {self.interface}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def handle_dns_query(self, query_data):
        """Process a captured DNS query"""
        try:
            domain = query_data.get('domain', '')
            query_name = query_data.get('query_name', '')
            
            # Detect exfiltration queries (suspicious domains)
            if any(keyword in domain.lower() for keyword in ['exfill', 'data', 'leak']):
                logger.info(f"Exfiltration query detected: {query_name}")
                
                # Extract potential data
                self._extract_exfiltration_data(query_data)
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
    
    def _extract_exfiltration_data(self, query_data):
        """Extract and store exfiltration data"""
        try:
            query_name = query_data.get('query_name', '')
            timestamp = query_data.get('timestamp', time.time())
            
            # Analyze format: session_id-index-total-chunk.random.domain
            logger.debug(f"Analyzing query name: {query_name}")
            parts = query_name.split('.')
            if len(parts) >= 2:
                data_segment = parts[0]  # First segment before the first dot
                
                # Parse format: session_id-index-total-chunk
                import re
                # Correct pattern for real format: timestamp-index-total-chunk
                # The chunk can contain base64 characters (letters, numbers, +, /, =, -, _)
                pattern = re.compile(r"(\d+)-(\d+)-(\d+)-(.+)")
                
                # Debug: show matching attempts
                logger.debug(f"Parsing attempt: '{data_segment}'")
                match = pattern.match(data_segment)
                
                if match:
                    session_id = match.group(1)  # timestamp only
                    index = int(match.group(2))
                    total = int(match.group(3))
                    chunk = match.group(4)  # base64 data
                    
                    logger.debug(f"Match successful: session={session_id}, index={index}, total={total}, chunk={chunk[:10]}...")
                    
                    with self.session_lock:
                        if session_id not in self.sessions:
                            self.sessions[session_id] = {
                                'start_time': timestamp,
                                'total_chunks': total,
                                'chunks': {},  # Use dict for indexing
                                'queries': []
                            }
                        
                        # Store chunk with its index
                        self.sessions[session_id]['chunks'][index] = chunk
                        self.sessions[session_id]['queries'].append(query_data)
                    
                    logger.info(f"Data segment captured: {session_id}-{index:04d}-{total:04d}-{chunk[:20]}...")
                    
                    # Check if we have all chunks
                    session = self.sessions[session_id]
                    if len(session['chunks']) >= session['total_chunks']:
                        logger.info(f"Complete reconstruction for session {session_id} ({session['total_chunks']} chunks)")
                        self._try_reconstruct_session(session_id)
                else:
                    # Detailed debug to understand why it doesn't work
                    logger.warning(f"Unrecognized chunk format 2: {data_segment}")
                    logger.debug(f"Pattern used: {pattern.pattern}")
                    
                    # Debug attempt with simpler pattern
                    simple_pattern = re.compile(r"(\d+)-(\d+)-(\d+)-(.+)")
                    simple_match = simple_pattern.match(data_segment)
                    if simple_match:
                        logger.debug(f"Simple pattern match: {simple_match.groups()}")
                    else:
                        logger.debug(f"Even simple pattern doesn't work")
                        
                        # Display characters one by one for diagnosis
                        chars_debug = [f"{c}({ord(c)})" for c in data_segment[:50]]
                        logger.debug(f"Characters: {' '.join(chars_debug)}")
                
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            import traceback
            traceback.print_exc()
    
    def _try_reconstruct_session(self, session_id):
        """Attempt to reconstruct session data"""
        try:
            session = self.sessions[session_id]
            chunks = session['chunks']
            total_chunks = session['total_chunks']
            
            # Check that all chunks are present
            if len(chunks) == total_chunks:
                logger.info(f"Complete reconstruction for session {session_id} ({total_chunks} chunks)")
                
                # Order chunks by index
                ordered_chunks = []
                for i in range(total_chunks):
                    if i in chunks:
                        ordered_chunks.append(chunks[i])
                    else:
                        logger.error(f"Missing chunk: {i}")
                        return
                
                # Reconstruct data
                reconstructed_data = self._decode_chunks(ordered_chunks)
                
                if reconstructed_data:
                    # Save reconstructed data
                    output_file = self.output_dir / f"exfiltrated_{session_id}_{int(time.time())}.bin"
                    with open(output_file, 'wb') as f:
                        f.write(reconstructed_data)
                    
                    # Analyze file type and display appropriate preview
                    file_info = self._analyze_file_content(reconstructed_data)
                    
                    logger.info(f"Reconstructed data saved: {output_file}")
                    logger.info(f"Size: {len(reconstructed_data)} bytes")
                    logger.info(f"Detected type: {file_info['type']}")
                    # rename file with appropriate extension
                    logger.info(f"Encoding: {file_info.get('encoding', 'unknown')}")
                    logger.info(f"Suggested extension: {file_info.get('extension', '.bin')}")
                    logger.info(f"File info: {file_info}")
                    if 'extension' in file_info:
                        new_file_name = output_file.with_suffix(file_info['extension'])
                        output_file.rename(new_file_name)
                        logger.info(f"File renamed: {new_file_name}")
                                        
                    # Clean up session
                    del self.sessions[session_id]
            else:
                logger.info(f"Session {session_id}: {len(chunks)}/{total_chunks} chunks received")
                    
        except Exception as e:
            logger.error(f"Error during reconstruction: {e}")
            import traceback
            traceback.print_exc()
    
    def _decode_chunks(self, ordered_chunks):
        """Decode ordered chunks into original data"""
        import base64
        
        # Concatenate all chunks in order
        combined_data = ''.join(ordered_chunks)
        logger.info(f"Combined data: {len(combined_data)} characters")
        
        # Try URL-safe base64 decoding first (used by client)
        try:
            # Add necessary padding for base64
            padding_needed = 4 - (len(combined_data) % 4)
            if padding_needed != 4:
                combined_data += '=' * padding_needed
            
            decoded = base64.urlsafe_b64decode(combined_data)
            logger.info(f"Successful decoding with URL-safe base64")
            return decoded
        except Exception as e:
            logger.warning(f"URL-safe base64 failed: {e}")
        
        # Try standard base64
        try:
            decoded = base64.b64decode(combined_data + '=' * (4 - len(combined_data) % 4))
            logger.info(f"Successful decoding with standard base64")
            return decoded
        except Exception as e:
            logger.warning(f"Standard base64 failed: {e}")
        
        # Try base32
        try:
            padding_needed = 8 - (len(combined_data) % 8)
            if padding_needed != 8:
                combined_data += '=' * padding_needed
            decoded = base64.b32decode(combined_data)
            logger.info(f"Successful decoding with base32")
            return decoded
        except Exception as e:
            logger.warning(f"Base32 failed: {e}")
        
        # Try hex
        try:
            decoded = bytes.fromhex(combined_data)
            logger.info(f"Successful decoding with hex")
            return decoded
        except Exception as e:
            logger.warning(f"Hex failed: {e}")
        
        # If no decoding works, treat as raw data
        logger.warning("No decoding succeeded, saving raw data")
        return combined_data.encode('utf-8', errors='ignore')
    
    def _analyze_file_content(self, data):
        """Analyze file content to determine its type"""
        if not data:
            return {'type': 'empty', 'encoding': None}
        
        # Check file signatures (magic numbers)
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
        
        # Check signatures
        for signature, info in signatures.items():
            if data.startswith(signature):
                return {
                    'type': info['type'],
                    'extension': info['ext'],
                    'encoding': 'binary'
                }
        
        # Default to binary
        return {'type': 'Binary Data', 'encoding': 'binary', 'extension': '.bin'}
    
    def start(self):
        """Start capture server"""
        logger.info("Starting capture...")
        
        try:
            # Create traffic interceptor
            interceptor = DoHTrafficInterceptor(
                interface=self.interface,
                output_dir=str(self.output_dir)
            )
            
            # Configure callback to process queries
            interceptor.dns_callback = self.handle_dns_query
            
            # Start capture
            interceptor.start_capture()
            
        except KeyboardInterrupt:
            logger.info("Stopping server...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    
    # Configuration from environment variables
    output_dir = os.environ.get('OUTPUT_DIR', '/app/captured')
    os.chown(output_dir, 1000, 1000)
    interface = os.environ.get('INTERFACE')
    
    # Create and start server
    server = SimpleExfiltrationServer(
        output_dir=output_dir,
        interface=interface
    )
    
    server.start()

if __name__ == "__main__":
    main()
