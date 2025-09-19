#!/usr/bin/env python3
"""
LaTeX to PDF Converter

This script converts LaTeX (.tex) files to PDF format using various LaTeX engines.
It handles multiple compilation passes, error reporting, and cleanup.

Requirements:
    - LaTeX distribution (TeX Live, MiKTeX, etc.)
    - pdflatex, xelatex, or lualatex command available in PATH

Usage:
    python tex_to_pdf.py input.tex
    python tex_to_pdf.py input.tex -o output.pdf
    python tex_to_pdf.py input.tex --engine xelatex
"""

import os
import sys
import argparse
import subprocess
import shutil
import tempfile
from pathlib import Path
import re


class LaTeXToPDFConverter:
    def __init__(self, engine='pdflatex', cleanup=True, verbose=False):
        self.engine = engine
        self.cleanup = cleanup
        self.verbose = verbose
        self.supported_engines = ['pdflatex', 'xelatex', 'lualatex']
        
        # Check if LaTeX engine is available
        self._check_latex_installation()
    
    def _check_latex_installation(self):
        """Check if the specified LaTeX engine is installed."""
        if not shutil.which(self.engine):
            available_engines = [eng for eng in self.supported_engines if shutil.which(eng)]
            if available_engines:
                print(f"Warning: {self.engine} not found. Available engines: {', '.join(available_engines)}")
                self.engine = available_engines[0]
                print(f"Using {self.engine} instead.")
            else:
                raise Exception(
                    f"No LaTeX engine found. Please install a LaTeX distribution.\n"
                    f"For Ubuntu/Debian: sudo apt-get install texlive-full\n"
                    f"For macOS: brew install --cask mactex\n"
                    f"For Windows: Download MiKTeX or TeX Live"
                )
    
    def _run_latex_command(self, tex_file, output_dir, pass_number=1):
        """Run LaTeX compilation command."""
        cmd = [
            self.engine,
            '-interaction=nonstopmode',  # Don't stop on errors
            '-halt-on-error',           # But halt on errors
            f'-output-directory={output_dir}',
            str(tex_file)
        ]
        
        if self.verbose:
            print(f"Pass {pass_number}: Running {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=tex_file.parent
            )
            
            return result
        except subprocess.TimeoutExpired:
            raise Exception("LaTeX compilation timed out (5 minutes)")
        except Exception as e:
            raise Exception(f"Failed to run {self.engine}: {e}")
    
    def _parse_latex_errors(self, log_content):
        """Parse LaTeX log file for errors and warnings."""
        errors = []
        warnings = []
        
        lines = log_content.split('\n')
        for i, line in enumerate(lines):
            # Look for error patterns
            if line.startswith('!') or 'Error:' in line:
                error_context = []
                # Get some context around the error
                start = max(0, i-2)
                end = min(len(lines), i+3)
                for j in range(start, end):
                    error_context.append(lines[j])
                errors.append('\n'.join(error_context))
            
            # Look for warning patterns
            elif 'Warning:' in line or line.startswith('LaTeX Warning:'):
                warnings.append(line.strip())
        
        return errors, warnings
    
    def _needs_multiple_passes(self, log_content):
        """Check if document needs multiple compilation passes."""
        indicators = [
            'Rerun to get cross-references right',
            'Label(s) may have changed',
            'Rerun LaTeX',
            'Table widths have changed'
        ]
        
        return any(indicator in log_content for indicator in indicators)
    
    def convert_to_pdf(self, tex_file, output_pdf=None, max_passes=3):
        """Convert LaTeX file to PDF."""
        tex_path = Path(tex_file)
        
        if not tex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {tex_file}")
        
        if not tex_path.suffix.lower() == '.tex':
            raise ValueError("Input file must have .tex extension")
        
        # Determine output path
        if output_pdf is None:
            output_pdf = tex_path.with_suffix('.pdf')
        else:
            output_pdf = Path(output_pdf)
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy .tex file to temp directory
            temp_tex = temp_path / tex_path.name
            shutil.copy2(tex_path, temp_tex)
            
            # Copy any additional files (images, style files, etc.) from source directory
            self._copy_additional_files(tex_path.parent, temp_path)
            
            log_file = temp_path / tex_path.with_suffix('.log').name
            pdf_file = temp_path / tex_path.with_suffix('.pdf').name
            
            # Multiple compilation passes
            for pass_num in range(1, max_passes + 1):
                if self.verbose:
                    print(f"\n--- Compilation Pass {pass_num} ---")
                
                result = self._run_latex_command(temp_tex, temp_path, pass_num)
                
                # Read log file if it exists
                log_content = ""
                if log_file.exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content = f.read()
                    except Exception:
                        pass
                
                # Check for errors
                if result.returncode != 0:
                    errors, warnings = self._parse_latex_errors(log_content)
                    error_msg = "LaTeX compilation failed!\n\n"
                    
                    if errors:
                        error_msg += "ERRORS:\n" + "\n\n".join(errors) + "\n\n"
                    
                    if result.stderr:
                        error_msg += f"STDERR:\n{result.stderr}\n\n"
                    
                    if log_content:
                        error_msg += "For full details, check the log output above."
                    
                    raise Exception(error_msg)
                
                # Check if we need another pass
                if pass_num < max_passes and self._needs_multiple_passes(log_content):
                    if self.verbose:
                        print("Additional pass needed for cross-references...")
                    continue
                else:
                    break
            
            # Check if PDF was created
            if not pdf_file.exists():
                raise Exception("PDF file was not created, but no obvious errors were found")
            
            # Copy PDF to final location
            shutil.copy2(pdf_file, output_pdf)
            
            # Show warnings if verbose
            if self.verbose and log_content:
                errors, warnings = self._parse_latex_errors(log_content)
                if warnings:
                    print("\nWARNINGS:")
                    for warning in warnings[:10]:  # Show first 10 warnings
                        print(f"  {warning}")
                    if len(warnings) > 10:
                        print(f"  ... and {len(warnings) - 10} more warnings")
        
        return output_pdf
    
    def _copy_additional_files(self, source_dir, dest_dir):
        """Copy additional files that might be needed for compilation."""
        extensions_to_copy = ['.bib', '.cls', '.sty', '.bst', '.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg']
        
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions_to_copy:
                try:
                    shutil.copy2(file_path, dest_dir)
                    if self.verbose:
                        print(f"Copied: {file_path.name}")
                except Exception:
                    pass  # Ignore errors copying additional files


def main():
    parser = argparse.ArgumentParser(description='Convert LaTeX files to PDF')
    parser.add_argument('input_tex', help='Input LaTeX file (.tex)')
    parser.add_argument('-o', '--output', help='Output PDF file path (optional)')
    parser.add_argument('--engine', choices=['pdflatex', 'xelatex', 'lualatex'], 
                       default='pdflatex', help='LaTeX engine to use')
    parser.add_argument('--no-cleanup', action='store_true', 
                       help='Keep temporary files for debugging')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--max-passes', type=int, default=3,
                       help='Maximum number of compilation passes')
    
    args = parser.parse_args()
    
    if not Path(args.input_tex).exists():
        print(f"Error: Input file '{args.input_tex}' not found")
        sys.exit(1)
    
    converter = LaTeXToPDFConverter(
        engine=args.engine,
        cleanup=not args.no_cleanup,
        verbose=args.verbose
    )
    
    try:
        print(f"Converting {args.input_tex} to PDF using {args.engine}...")
        
        output_pdf = converter.convert_to_pdf(
            args.input_tex,
            args.output,
            args.max_passes
        )
        
        print(f"✓ PDF created successfully: {output_pdf}")
        print(f"  File size: {output_pdf.stat().st_size / 1024:.1f} KB")
        
        # Basic validation
        if output_pdf.stat().st_size < 1000:
            print("Warning: PDF file is very small, please check the content")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
