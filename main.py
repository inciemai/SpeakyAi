#!/usr/bin/env python3
"""
Main entry point for Speaky Bot application.
"""

from speaky_bot.app import create_app

def main():
    """Run the Speaky Bot web application."""
    app = create_app()
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    main() 