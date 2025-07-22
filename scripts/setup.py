#!/usr/bin/env python3
"""
Setup script for SignAware AI.
This script helps users set up the environment and initialize the database.
"""

import os
import sys
import shutil
import subprocess

def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        return False
    else:
        print("✅ Python version OK")
    
    # Check if uv is installed
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("✅ uv is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv is not installed. Please install it first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    # Check if Ollama is running
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if response.status_code == 200:
            print("✅ Ollama is running")
            
            # Check if deepseek-r1:8b is available
            models = response.json().get("models", [])
            deepseek_available = any("deepseek-r1" in model.get("name", "") for model in models)
            
            if deepseek_available:
                print("✅ Deepseek-R1:8B model is available")
            else:
                print("⚠️  Deepseek-R1:8B model not found. Please run:")
                print("   ollama pull deepseek-r1:8b")
        else:
            print("⚠️  Ollama is not responding correctly")
    except Exception:
        print("⚠️  Could not connect to Ollama. Make sure it's running:")
        print("   ollama serve")
    
    return True

def setup_environment():
    """Set up environment file."""
    print("\n📝 Setting up environment...")
    
    if not os.path.exists(".env"):
        if os.path.exists("env.template"):
            shutil.copy("env.template", ".env")
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your actual configuration:")
            print("   - Set your OpenAI API key")
            print("   - Configure your PostgreSQL database URL")
            print("   - Update other settings as needed")
        else:
            print("❌ env.template file not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run(["uv", "sync"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def init_database():
    """Initialize the database."""
    print("\n🗄️  Initializing database...")
    
    try:
        subprocess.run(["uv", "run", "python", "scripts/init_db.py"], check=True)
        print("✅ Database initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        print("   Make sure PostgreSQL is running and accessible")
        print("   Check your DATABASE_URL in the .env file")
        return False

def main():
    """Main setup function."""
    print("🚀 SignAware AI Setup Script")
    print("=" * 40)
    
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please address the issues above.")
        return 1
    
    if not setup_environment():
        print("\n❌ Environment setup failed.")
        return 1
    
    if not install_dependencies():
        print("\n❌ Dependency installation failed.")
        return 1
    
    print("\n" + "=" * 40)
    print("✨ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Edit your .env file with your actual configuration")
    print("   2. Make sure PostgreSQL is running")
    print("   3. Make sure Ollama is running with deepseek-r1:8b")
    print("   4. Initialize the database:")
    print("      uv run python scripts/init_db.py")
    print("   5. Start the application:")
    print("      uv run python run.py")
    print("   6. Test the APIs:")
    print("      uv run python scripts/test_api.py")
    print(f"   7. Visit http://localhost:8000/docs for API documentation")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 