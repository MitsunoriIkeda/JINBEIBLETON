#!/bin/bash
set -e

# Dynamically fetch version from package.json
VERSION=$(node -p "require('./package.json').version")
RELEASE_FOLDER="JINBEIBLETON_v${VERSION}"
ZIP_NAME="JINBEIBLETON-arm64.zip"

echo "============================================="
echo "🏗️  JINBEIBLETON Release Builder (v${VERSION})"
echo "============================================="

echo "🔨 1/6 Clearing old build artifacts..."
rm -rf server/dist server/build dist-app/

echo "🐍 2/6 Copying host ffmpeg binary for bundling..."
mkdir -p server/bin
if [ -f /opt/homebrew/bin/ffmpeg ]; then
  cp /opt/homebrew/bin/ffmpeg server/bin/ffmpeg
elif [ -f /usr/local/bin/ffmpeg ]; then
  cp /usr/local/bin/ffmpeg server/bin/ffmpeg
else
  echo "❌ ffmpeg not found on host machine. Cannot bundle."
  exit 1
fi

echo "🐍 2.5/6 Building Python backend with PyInstaller..."
cd server
./venv/bin/pyinstaller --noconfirm jinbeibleton_server.spec
rm -rf bin/
cd ..

echo "⚛️ 3/6 Building React client..."
npm run build

echo "📦 4/6 Bundling Electron app..."
export CSC_IDENTITY_AUTO_DISCOVERY=false
npx electron-builder --mac --arm64

echo "🚚 5/6 Copying node_modules into unpacked ASAR..."
# Copy node_modules manually because electron-builder ignores them for node_bridge
cp -R server/node_bridge/node_modules dist-app/mac-arm64/JINBEIBLETON.app/Contents/Resources/app.asar.unpacked/server/node_bridge/

echo "🤐 6/6 Packaging distribution folder & zipping..."
cd dist-app
mkdir -p "${RELEASE_FOLDER}"

# Copy the app bundle
cp -R mac-arm64/JINBEIBLETON.app "${RELEASE_FOLDER}/"

# Copy helper files from parent directory
cd ..
cp README.md "dist-app/${RELEASE_FOLDER}/"
if [ -f README_SETUP.txt ]; then cp README_SETUP.txt "dist-app/${RELEASE_FOLDER}/"; fi
if [ -d midi-script ]; then cp -R midi-script "dist-app/${RELEASE_FOLDER}/"; fi
if [ -f install_remote_script.command ]; then cp install_remote_script.command "dist-app/${RELEASE_FOLDER}/"; fi

# Compress using ditto to preserve macOS metadata and avoid Gatekeeper issues
cd dist-app
echo "Creating ZIP: ${ZIP_NAME}..."
ditto -c -k --sequesterRsrc --keepParent "${RELEASE_FOLDER}" "${ZIP_NAME}"
cd ..

echo "============================================="
echo "🎉 Build Finished Successfully!"
echo "Package: dist-app/${ZIP_NAME}"
echo "Folder: dist-app/${RELEASE_FOLDER}"
echo "============================================="
