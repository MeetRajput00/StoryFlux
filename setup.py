#!/usr/bin/env python3
"""
Quick Setup Script for YouTube Automation Pipeline
Helps with initial configuration and testing
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python_version():
    """Check if Python version is adequate"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print("✅ Python version is compatible")

def install_dependencies():
    """Install required packages"""
    print_header("Installing Dependencies")
    
    response = input("Install required Python packages? (y/n): ").lower()
    if response == 'y':
        print("\nInstalling packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print("Try manually: pip install -r requirements.txt")
    else:
        print("⏭️  Skipped dependency installation")

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    print_header("Checking ffmpeg")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ ffmpeg is installed")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("⚠️  ffmpeg not found")
    print("\nffmpeg is required for video processing. Install it:")
    print("  macOS:   brew install ffmpeg")
    print("  Linux:   sudo apt-get install ffmpeg")
    print("  Windows: Download from https://ffmpeg.org/download.html")
    return False

def setup_env_file():
    """Create .env file from template"""
    print_header("Environment Configuration")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return
    
    if not os.path.exists('.env.example'):
        print("❌ .env.example not found")
        return
    
    response = input("Create .env file from template? (y/n): ").lower()
    if response == 'y':
        with open('.env.example', 'r') as src:
            with open('.env', 'w') as dst:
                dst.write(src.read())
        print("✅ .env file created")
        print("\n⚠️  Remember to add your API keys to .env file!")
    else:
        print("⏭️  Skipped .env creation")

def check_credentials():
    """Check for YouTube API credentials"""
    print_header("YouTube API Credentials")
    
    if os.path.exists('client_secrets.json'):
        print("✅ client_secrets.json found")
        return True
    
    print("❌ client_secrets.json not found")
    print("\nTo get YouTube API credentials:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project")
    print("3. Enable YouTube Data API v3")
    print("4. Create OAuth 2.0 credentials (Desktop app)")
    print("5. Download and save as 'client_secrets.json'")
    return False

def test_imports():
    """Test if all required modules can be imported"""
    print_header("Testing Module Imports")
    
    modules = [
        ('yaml', 'PyYAML'),
        ('dotenv', 'python-dotenv'),
        ('moviepy', 'moviepy'),
        ('gtts', 'gTTS'),
        ('PIL', 'Pillow'),
        ('google.oauth2', 'google-auth-oauthlib'),
        ('googleapiclient', 'google-api-python-client'),
    ]
    
    all_ok = True
    for module_name, package_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - Not installed")
            all_ok = False
    
    return all_ok

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")
    
    dirs = ['content', 'output/audio', 'output/videos', 'assets', 'logs']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✅ {d}")

def main():
    """Main setup function"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         🎥 YOUTUBE PIPELINE SETUP WIZARD 🎥            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run setup checks
    check_python_version()
    install_dependencies()
    check_ffmpeg()
    test_imports()
    create_directories()
    setup_env_file()
    has_credentials = check_credentials()
    
    # Final summary
    print_header("Setup Summary")
    
    if has_credentials:
        print("\n🎉 Setup complete! You're ready to create videos.")
        print("\nNext steps:")
        print("1. Edit config.yaml to customize your channel")
        print("2. Add API keys to .env file (optional but recommended)")
        print("3. Run: python main.py --no-upload  (to test without uploading)")
        print("4. Run: python main.py  (to create and upload your first video)")
    else:
        print("\n⚠️  Setup incomplete")
        print("\nRequired:")
        print("1. Get YouTube API credentials (client_secrets.json)")
        print("2. Place it in the project root directory")
        print("\nOptional (but recommended):")
        print("1. Get Hugging Face token for better content")
        print("2. Get Pexels API key for stock videos")
        print("3. Add these to .env file")
        print("\nThen run: python main.py")
    
    print("\n" + "="*60)
    print("For detailed instructions, see README.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
