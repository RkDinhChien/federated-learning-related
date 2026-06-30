"""
Download CIFAR-10 from alternative source
"""
import os
import urllib.request
import tarfile

print("📥 Downloading CIFAR-10 from mirror...")

# Create data folder
os.makedirs('data', exist_ok=True)
os.chdir('data')

# Download from alternative source
url = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
filename = "cifar-10-python.tar.gz"

try:
    print(f"Downloading from: {url}")
    urllib.request.urlretrieve(url, filename)
    print(f"✅ Downloaded {filename}")
    
    # Extract
    print(f"📦 Extracting {filename}...")
    with tarfile.open(filename, 'r:gz') as tar:
        tar.extractall()
    print("✅ Extracted successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
