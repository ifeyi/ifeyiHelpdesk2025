set -e # Exit on error

echo "Downloading dependencies for Article section..."

# Create directory structure
mkdir -p helpdesk_app/static/tinymce
mkdir -p helpdesk_app/static/pdf-js

# Create temporary directory for downloads
mkdir -p temp_downloads
cd temp_downloads

# Download TinyMCE
echo "Downloading TinyMCE editor..."
TINYMCE_VERSION="6.7.0"
wget https://download.tiny.cloud/tinymce/community/tinymce_${TINYMCE_VERSION}.zip
unzip tinymce_${TINYMCE_VERSION}.zip
cp -r tinymce/* ../helpdesk_app/static/tinymce/
echo "TinyMCE downloaded and installed."

# Download PDF.js for PDF preview (Optional)
echo "Downloading PDF.js..."
PDFJS_VERSION="3.6.172"
wget https://github.com/mozilla/pdf.js/releases/download/v${PDFJS_VERSION}/pdfjs-${PDFJS_VERSION}-dist.zip
unzip pdfjs-${PDFJS_VERSION}-dist.zip
cp -r build/* ../helpdesk_app/static/pdf-js/
echo "PDF.js downloaded and installed."

# Clean up
cd ..
rm -rf temp_downloads

# Create placeholders for custom JS files
touch helpdesk_app/static/helpdeskassets/helpdeskscripts/article-editor.js

echo "All article dependencies downloaded and organized!"
echo "Remember to update your templates to use these local versions."