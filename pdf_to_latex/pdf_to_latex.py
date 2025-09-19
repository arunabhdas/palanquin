#!/usr/bin/env python3
"""
PDF to LaTeX Converter

This script converts PDF documents to neatly formatted LaTeX.
It extracts text from PDFs and applies appropriate LaTeX formatting
for headings, bullet points, and other document structures.

Requirements:
    pip install pdfplumber

Usage:
    python pdf_to_latex.py input.pdf output.tex
"""

import re
import sys
import argparse
from pathlib import Path
try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is required. Install with: pip install pdfplumber")
    sys.exit(1)


class PDFToLaTeXConverter:
    def __init__(self):
        self.latex_special_chars = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '^': r'\textasciicircum{}',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '\\': r'\textbackslash{}',
        }
    
    def escape_latex(self, text):
        """Escape special LaTeX characters in text."""
        for char, replacement in self.latex_special_chars.items():
            text = text.replace(char, replacement)
        return text
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")
    
    def identify_structure(self, text):
        """Identify document structure and create structured content."""
        lines = text.split('\n')
        structured_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify different types of content
            if self.is_title(line, lines):
                structured_content.append(('title', line))
            elif self.is_section_heading(line):
                structured_content.append(('section', line))
            elif self.is_subsection_heading(line):
                structured_content.append(('subsection', line))
            elif self.is_primary_bullet(line):
                structured_content.append(('bullet1', self.clean_bullet_text(line)))
            elif self.is_secondary_bullet(line):
                structured_content.append(('bullet2', self.clean_bullet_text(line)))
            else:
                structured_content.append(('paragraph', line))
        
        return structured_content
    
    def is_title(self, line, all_lines):
        """Check if line is likely a document title."""
        # First non-empty line or lines that are short and standalone
        if len(line) < 50 and line.isupper():
            return True
        if "App" in line or "System" in line or "Project" in line:
            return True
        return False
    
    def is_section_heading(self, line):
        """Check if line is a section heading."""
        section_keywords = ['Summary', 'Features', 'Introduction', 'Overview', 
                           'Requirements', 'Implementation', 'Conclusion']
        return any(keyword.lower() in line.lower() for keyword in section_keywords) and len(line) < 50
    
    def is_subsection_heading(self, line):
        """Check if line is a subsection heading."""
        # Lines that end with certain patterns or are short standalone lines
        if line.endswith(':') and len(line) < 80:
            return True
        return False
    
    def is_primary_bullet(self, line):
        """Check if line is a primary bullet point."""
        return line.startswith('●') or line.startswith('•') or line.startswith('- ')
    
    def is_secondary_bullet(self, line):
        """Check if line is a secondary bullet point."""
        return line.startswith('○') or line.startswith('  ○') or line.startswith('    ○')
    
    def clean_bullet_text(self, line):
        """Remove bullet characters and clean up text."""
        # Remove various bullet characters and leading whitespace
        cleaned = re.sub(r'^[\s]*[●•○\-]\s*', '', line)
        return cleaned.strip()
    
    def convert_to_latex(self, structured_content):
        """Convert structured content to LaTeX format."""
        latex_content = []
        
        # LaTeX document header
        latex_content.append(r'\documentclass[11pt,a4paper]{article}')
        latex_content.append(r'\usepackage[utf8]{inputenc}')
        latex_content.append(r'\usepackage[T1]{fontenc}')
        latex_content.append(r'\usepackage{geometry}')
        latex_content.append(r'\usepackage{enumitem}')
        latex_content.append(r'\usepackage{parskip}')
        latex_content.append(r'\geometry{margin=1in}')
        latex_content.append('')
        latex_content.append(r'\begin{document}')
        latex_content.append('')
        
        in_itemize = False
        in_subitemize = False
        
        for content_type, content in structured_content:
            escaped_content = self.escape_latex(content)
            
            if content_type == 'title':
                latex_content.append(f'\\title{{{escaped_content}}}')
                latex_content.append(r'\maketitle')
                latex_content.append('')
            
            elif content_type == 'section':
                # Close any open lists
                if in_subitemize:
                    latex_content.append(r'\end{itemize}')
                    in_subitemize = False
                if in_itemize:
                    latex_content.append(r'\end{itemize}')
                    in_itemize = False
                
                latex_content.append(f'\\section{{{escaped_content}}}')
                latex_content.append('')
            
            elif content_type == 'subsection':
                # Close any open lists
                if in_subitemize:
                    latex_content.append(r'\end{itemize}')
                    in_subitemize = False
                if in_itemize:
                    latex_content.append(r'\end{itemize}')
                    in_itemize = False
                
                latex_content.append(f'\\subsection{{{escaped_content}}}')
                latex_content.append('')
            
            elif content_type == 'bullet1':
                # Close secondary itemize if open
                if in_subitemize:
                    latex_content.append(r'\end{itemize}')
                    in_subitemize = False
                
                # Start primary itemize if not open
                if not in_itemize:
                    latex_content.append(r'\begin{itemize}')
                    in_itemize = True
                
                latex_content.append(f'\\item {escaped_content}')
            
            elif content_type == 'bullet2':
                # Start secondary itemize if not open
                if not in_subitemize:
                    latex_content.append(r'\begin{itemize}')
                    in_subitemize = True
                
                latex_content.append(f'\\item {escaped_content}')
            
            elif content_type == 'paragraph':
                # Close any open lists
                if in_subitemize:
                    latex_content.append(r'\end{itemize}')
                    in_subitemize = False
                if in_itemize:
                    latex_content.append(r'\end{itemize}')
                    in_itemize = False
                
                latex_content.append(escaped_content)
                latex_content.append('')
        
        # Close any remaining open lists
        if in_subitemize:
            latex_content.append(r'\end{itemize}')
        if in_itemize:
            latex_content.append(r'\end{itemize}')
        
        # LaTeX document footer
        latex_content.append('')
        latex_content.append(r'\end{document}')
        
        return '\n'.join(latex_content)
    
    def convert_pdf_to_latex(self, pdf_path, output_path=None):
        """Main conversion function."""
        if output_path is None:
            output_path = Path(pdf_path).with_suffix('.tex')
        
        print(f"Reading PDF: {pdf_path}")
        text = self.extract_text_from_pdf(pdf_path)
        
        print("Analyzing document structure...")
        structured_content = self.identify_structure(text)
        
        print("Converting to LaTeX...")
        latex_content = self.convert_to_latex(structured_content)
        
        print(f"Writing LaTeX file: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print("Conversion complete!")
        return latex_content


def main():
    parser = argparse.ArgumentParser(description='Convert PDF to LaTeX format')
    parser.add_argument('input_pdf', help='Input PDF file path')
    parser.add_argument('-o', '--output', help='Output LaTeX file path (optional)')
    
    args = parser.parse_args()
    
    if not Path(args.input_pdf).exists():
        print(f"Error: Input file '{args.input_pdf}' not found")
        sys.exit(1)
    
    converter = PDFToLaTeXConverter()
    
    try:
        latex_content = converter.convert_pdf_to_latex(args.input_pdf, args.output)
        print("\nSample of generated LaTeX content:")
        print("-" * 50)
        print(latex_content[:500] + "..." if len(latex_content) > 500 else latex_content)
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
