#!/usr/bin/env python3
"""
Simple run script for SignAware AI application.
"""

import uvicorn
from app.config import get_settings

def main():
    settings = get_settings()
    
    print("🚀 Starting SignAware AI...")
    print(f"   Host: {settings.host}")
    print(f"   Port: {settings.port}")
    print(f"   Debug: {settings.debug}")
    print(f"   Docs: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        access_log=True,
    )

if __name__ == "__main__":
    main() 