import os
import subprocess
import shutil
import zipfile
import sys
import tempfile

def install_playwright():
    print("Installing Playwright and its browsers...")
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

def ensure_playwright_cache():
    playwright_cache = os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright")
    if not os.path.exists(playwright_cache):
        install_playwright()
    return playwright_cache

def run_pyinstaller():
    # Ensure you're in the correct directory
    os.chdir(r"C:\Users\brend\start over socials")
    
    # Ensure Playwright and its cache are set up
    playwright_cache = ensure_playwright_cache()
    
    # Update the spec file with the correct Playwright cache path
    spec_file = "InstagramVideoProcessor.spec"
    with open(spec_file, "r") as f:
        spec_content = f.read()
    
    # Replace or add the datas line to include Playwright cache
    if "datas = [" in spec_content:
        spec_content = spec_content.replace(
            "datas = [",
            f"datas = [(r'{playwright_cache}', 'playwright'), "
        )
    else:
        spec_content = f"datas = [(r'{playwright_cache}', 'playwright')]\n" + spec_content
    
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller
    result = subprocess.run(["pyinstaller", spec_file], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("PyInstaller failed. Error:")
        print(result.stderr)
        return False
    
    print("PyInstaller completed successfully.")
    return True

def create_zip():
    exe_path = r"C:\Users\brend\start over socials\dist\InstagramVideoProcessor.exe"
    zip_path = r"C:\Users\brend\start over socials\static\InstagramVideoProcessor.zip"
    
    # Ensure the static directory exists
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    
    # Create a zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the exe to the zip
        zipf.write(exe_path, os.path.basename(exe_path))
        
        # Add the run_app.bat file if it exists
        bat_file = os.path.join(os.path.dirname(exe_path), "run_app.bat")
        if os.path.exists(bat_file):
            zipf.write(bat_file, os.path.basename(bat_file))
        
    print(f"Zip file created at {zip_path}")

if __name__ == "__main__":
    if run_pyinstaller():
        create_zip()
    else:
        print("Failed to build the application. Zip file not created.")