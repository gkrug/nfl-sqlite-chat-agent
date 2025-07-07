#!/usr/bin/env python3
"""
Setup script for NFL Stat Agent
Helps users install dependencies and configure the environment.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required packages."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_database():
    """Check if the database file exists."""
    db_path = Path("data/pbp_db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"✅ Database found: {size_mb:.1f} MB")
        return True
    else:
        print("❌ Database not found at data/pbp_db")
        print("Please ensure you have the NFL database file")
        return False

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file...")
    env_content = """# Together AI API Key - Get yours at https://together.ai/
TOGETHER_API_KEY=your_together_ai_api_key_here

# Database Configuration
DB_PATH=data/pbp_db
SCHEMA_FILE=schema_context.txt

# Optional: Logging Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_path, "w") as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please edit .env and add your Together AI API key")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    """Main setup function."""
    print("🏈 NFL Stat Agent Setup")
    print("=" * 30)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check database
    if not check_database():
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    print("\n" + "=" * 30)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your Together AI API key")
    print("2. Run: python test_agent.py (to test the agent)")
    print("3. Run: streamlit run app.py (to start the web interface)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 