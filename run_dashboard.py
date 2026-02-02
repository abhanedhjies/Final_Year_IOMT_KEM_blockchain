#!/usr/bin/env python3
"""
Wrapper script to run the IoT dashboard with proper Python path setup
"""
import sys
import os

# Add IoMT_Blockchain_Security to path
dashboard_dir = os.path.join(os.path.dirname(__file__), 'IoMT_Blockchain_Security')
sys.path.insert(0, dashboard_dir)

# Import and run
from iot_integrated_dashboard import main

if __name__ == '__main__':
    main()
