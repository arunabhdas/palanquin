#!/bin/bash
# PDF/LaTeX Converter Setup Script
# This script sets up the complete environment for PDF ↔ LaTeX conversion

set -e  # Exit on any error

echo "🚀 Setting up PDF/LaTeX Converter Environment"
echo "============================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Reload PATH
    source ~/.bashrc 2>/dev/null || source ~/.bash_profile 2>/dev/null || true
    echo "✅ UV installed"
else
    echo "✅ UV already installed"
fi

# Create project directory
PROJECT_DIR="pdf-latex-converter"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir "$PROJECT_DIR"
    echo "✅ Created project directory: $PROJECT_DIR"
else
    echo "✅ Project directory exists: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
# PDF to LaTeX to PDF Converter Dependencies
pdfplumber>=0.9.0
EOF
    echo "✅ Created requirements.txt"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
source .venv/bin/activate
uv pip install -r requirements.txt
echo "✅ Dependencies installed"

# Check for LaTeX installation
echo "🔍 Checking LaTeX installation..."
LATEX_ENGINES=("pdflatex" "xelatex" "lualatex")
FOUND_ENGINE=""

for engine in "${LATEX_ENGINES[@]}"; do
    if command -v "$engine" &> /dev/null; then
        FOUND_ENGINE="$engine"
        echo "✅ Found LaTeX engine: $engine"
        break
    fi
done

if [ -z "$FOUND_ENGINE" ]; then
    echo "❌ No LaTeX engine found!"
    echo "Please install a LaTeX distribution:"
    echo "  Ubuntu/Debian: sudo apt-get install texlive-full"
    echo "  macOS: brew install --cask mactex"
    echo "  Windows: Download MiKTeX or TeX Live"
    echo ""
    echo "Python environment is ready, but you'll need LaTeX for PDF generation."
else
    echo "✅ LaTeX is ready to use"
fi

# Test the setup
echo "🧪 Testing the setup..."
python -c "import pdfplumber; print('✅ pdfplumber import successful')" 2>/dev/null || echo "❌ pdfplumber import failed"

# Create a simple test
echo "📝 Creating test files..."

# Create a simple test PDF content (we'll create a LaTeX file and compile it as a test)
if [ -n "$FOUND_ENGINE" ]; then
    cat > test.tex << 'EOF'
\documentclass{article}
\begin{document}
\title{Test Document}
\maketitle
\section{Introduction}
This is a test document to verify our setup works correctly.
\begin{itemize}
\item First item
\item Second item
\end{itemize}
\end{document}
EOF

    echo "🔨 Compiling test PDF..."
    $FOUND_ENGINE -interaction=nonstopmode test.tex > /dev/null 2>&1
    
    if [ -f "test.pdf" ]; then
        echo "✅ Test PDF created successfully"
        # Clean up test files
        rm -f test.tex test.pdf test.aux test.log
    else
        echo "❌ Test PDF creation failed"
    fi
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "Project location: $(pwd)"
echo "To use the converters:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. Run conversions:"
echo "     python pdf_to_latex.py input.pdf"
echo "     python tex_to_pdf.py output.tex"
echo ""
echo "Or use UV run (recommended):"
echo "  uv run python pdf_to_latex.py input.pdf"
echo "  uv run python tex_to_pdf.py output.tex"
echo ""

if [ -n "$FOUND_ENGINE" ]; then
    echo "✅ Ready to convert PDFs and LaTeX files!"
else
    echo "⚠️  Install LaTeX to enable PDF generation"
fi
