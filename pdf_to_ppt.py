#!/usr/bin/env python3
"""
PDF to PowerPoint Converter
Converts PDF files to editable PowerPoint presentations
"""

import os
import sys
from pathlib import Path
try:
    from pdf2image import convert_from_path
    from pptx import Presentation
    from pptx.util import Inches
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required library - {e}")
    print("Please install required packages: pip install -r requirements.txt")
    sys.exit(1)


class PDFtoPPTConverter:
    """Convert PDF files to PowerPoint presentations"""

    def __init__(self, pdf_path, output_path=None, dpi=300):
        """
        Initialize the converter

        Args:
            pdf_path: Path to the PDF file
            output_path: Path for output PPT file (optional)
            dpi: Resolution for PDF conversion (default: 300)
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.pdf_path.with_suffix('.pptx')

        self.dpi = dpi

    def convert(self):
        """Convert PDF to PowerPoint"""
        print(f"Converting PDF: {self.pdf_path}")
        print(f"Output will be saved to: {self.output_path}")

        # Convert PDF pages to images
        print(f"Extracting pages from PDF (DPI: {self.dpi})...")
        try:
            images = convert_from_path(
                self.pdf_path,
                dpi=self.dpi,
                fmt='png'
            )
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            print("\nTroubleshooting:")
            print("- Make sure poppler is installed (see README)")
            print("- Try lowering DPI (e.g., --dpi 150)")
            sys.exit(1)

        print(f"Found {len(images)} pages")

        # Create PowerPoint presentation
        print("Creating PowerPoint presentation...")
        prs = Presentation()

        # Set slide size (16:9 aspect ratio)
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(5.625)

        # Add each page as a slide
        for i, image in enumerate(images, 1):
            print(f"Processing page {i}/{len(images)}...")

            # Add blank slide
            blank_slide_layout = prs.slide_layouts[6]  # Blank layout
            slide = prs.slides.add_slide(blank_slide_layout)

            # Save image temporarily
            temp_image_path = f"temp_page_{i}.png"
            image.save(temp_image_path, 'PNG')

            # Calculate image dimensions to fit slide
            img_width, img_height = image.size
            slide_width = prs.slide_width
            slide_height = prs.slide_height

            # Calculate scaling to fit slide while maintaining aspect ratio
            width_ratio = slide_width / img_width
            height_ratio = slide_height / img_height
            scale_ratio = min(width_ratio, height_ratio)

            # Calculate final dimensions
            final_width = int(img_width * scale_ratio)
            final_height = int(img_height * scale_ratio)

            # Center the image on the slide
            left = (slide_width - final_width) / 2
            top = (slide_height - final_height) / 2

            # Add image to slide
            slide.shapes.add_picture(
                temp_image_path,
                left,
                top,
                width=final_width,
                height=final_height
            )

            # Clean up temporary image
            os.remove(temp_image_path)

        # Save presentation
        print(f"Saving PowerPoint to: {self.output_path}")
        prs.save(str(self.output_path))
        print("✓ Conversion completed successfully!")
        print(f"\nYou can now edit the presentation in PowerPoint or compatible software.")

        return self.output_path


def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert PDF files to editable PowerPoint presentations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_to_ppt.py input.pdf
  python pdf_to_ppt.py input.pdf -o output.pptx
  python pdf_to_ppt.py input.pdf --dpi 150
  python pdf_to_ppt.py notebooklm_slides.pdf -o my_slides.pptx --dpi 200

Note:
  Higher DPI = better quality but larger file size and slower conversion
  Default DPI of 300 works well for most cases
        """
    )

    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file to convert'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output PowerPoint file path (default: same name as PDF with .pptx extension)',
        default=None
    )

    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='Resolution for PDF conversion (default: 300, recommended: 150-300)'
    )

    args = parser.parse_args()

    try:
        converter = PDFtoPPTConverter(
            args.pdf_file,
            args.output,
            args.dpi
        )
        converter.convert()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
