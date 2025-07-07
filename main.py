#!/usr/bin/env python3
"""
Main entry point for Speaky Bot application.
"""

import os
from speaky_bot.app import create_app

def main():
    """Run the Speaky Bot web application."""
    app = create_app()
    
    # Get configuration from environment variables for deployment compatibility
    host = os.environ.get('HOST', '0.0.0.0')  # Bind to all interfaces for deployment
    port = int(os.environ.get('PORT', 5000))  # Use PORT env var or default to 5000
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'  # Disable debug in production
    
    print(f"Starting Speaky Bot on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main() 