#!/usr/bin/env python
"""
Quantitative Investing Web Application Runner
Run this script to start the Flask development server
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from web import create_app


def main():
    """Main entry point for the application"""
    # Get configuration from environment
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

    # Create the Flask application
    app = create_app(config_name)

    # Print startup information
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Quantitative Investing Web Application                     ║
║                                                              ║
║   Configuration: {config_name:<42} ║
║   Host: {host:<51} ║
║   Port: {port:<51} ║
║   Debug: {str(debug):<50} ║
║                                                              ║
║   Access the application at:                                 ║
║   http://{host}:{port:<46} ║
║                                                              ║
║   Press Ctrl+C to stop the server                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Run the application
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
