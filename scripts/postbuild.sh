#!/bin/bash
set -e
echo ">>> postbuild.sh started"
echo ">>> Current directory: $(pwd)"
echo ">>> Python: $(which python)"
echo ">>> Pip: $(which pip)"

# Fix opencv for headless server (Azure App Service has no libGL.so.1)
# docling pulls opencv-python (full) which requires GUI libs
# Replace it with headless version
pip uninstall -y opencv-python opencv-python-headless
pip install --no-cache-dir opencv-python-headless==4.11.0.86

echo ">>> Verifying opencv-python-headless..."
python -c "import cv2; print('cv2 version:', cv2.__version__)"
echo "✅ opencv-python-headless installed successfully"
