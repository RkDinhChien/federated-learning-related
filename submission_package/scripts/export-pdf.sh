#!/bin/bash

# Script to export presentation materials to PDF
# Requires: pandoc, wkhtmltopdf, or markdown-pdf

echo "🎤 Exporting Presentation Materials to PDF..."

# Check if pandoc is installed
if command -v pandoc &> /dev/null; then
    echo "✅ Using pandoc for PDF export"
    
    # Export Presentation Script
    echo "📄 Exporting PRESENTATION_SCRIPT.md..."
    pandoc PRESENTATION_SCRIPT.md -o PRESENTATION_SCRIPT.pdf \
        --pdf-engine=xelatex \
        --variable mainfont="Arial" \
        --variable fontsize=11pt \
        --variable geometry:margin=1in \
        --toc \
        --highlight-style tango
    
    # Export Q&A Preparation
    echo "📝 Exporting QA_PREPARATION.md..."
    pandoc QA_PREPARATION.md -o QA_PREPARATION.pdf \
        --pdf-engine=xelatex \
        --variable mainfont="Arial" \
        --variable fontsize=11pt \
        --variable geometry:margin=1in \
        --toc \
        --highlight-style tango
    
    echo "✅ PDF files created successfully!"
    echo "   - PRESENTATION_SCRIPT.pdf"
    echo "   - QA_PREPARATION.pdf"
    
elif command -v npm &> /dev/null; then
    echo "⚠️  Pandoc not found. Using markdown-pdf (Node.js)..."
    
    # Check if markdown-pdf is installed
    if ! npm list -g markdown-pdf &> /dev/null; then
        echo "📦 Installing markdown-pdf..."
        npm install -g markdown-pdf
    fi
    
    # Export using markdown-pdf
    echo "📄 Exporting PRESENTATION_SCRIPT.md..."
    markdown-pdf PRESENTATION_SCRIPT.md -o PRESENTATION_SCRIPT.pdf
    
    echo "📝 Exporting QA_PREPARATION.md..."
    markdown-pdf QA_PREPARATION.md -o QA_PREPARATION.pdf
    
    echo "✅ PDF files created successfully!"
    
else
    echo "❌ Error: Neither pandoc nor npm found"
    echo ""
    echo "📥 Installation options:"
    echo ""
    echo "Option 1 - Install pandoc (recommended):"
    echo "  brew install pandoc basictex"
    echo ""
    echo "Option 2 - Use Node.js markdown-pdf:"
    echo "  npm install -g markdown-pdf"
    echo ""
    echo "Option 3 - Manual export:"
    echo "  1. Open markdown files in VS Code"
    echo "  2. Install 'Markdown PDF' extension"
    echo "  3. Right-click → 'Markdown PDF: Export (pdf)'"
    exit 1
fi

# Open PDFs if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "🚀 Opening PDFs..."
    open PRESENTATION_SCRIPT.pdf 2>/dev/null || true
    open QA_PREPARATION.pdf 2>/dev/null || true
fi

echo ""
echo "✨ Done! PDF files ready for presentation."
