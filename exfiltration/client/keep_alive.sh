#!/bin/bash

echo "🐳 DoH Exfiltration Client Container Ready"
echo "📁 Available tools:"
echo "  - python quick_test_json.py --help"
echo "  - python config_generator.py --help"
echo "  - python test_evasion_suite.py --help"
echo ""
echo "💡 Usage examples:"
echo "  python quick_test_json.py --scenario stealth /app/test_data/myfile.txt"
echo "  python config_generator.py --list"
echo ""
echo "🔧 Container will stay alive. Use 'docker exec' to interact."
echo ""

# Keep container alive
tail -f /dev/null