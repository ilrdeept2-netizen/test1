#!/usr/bin/env python3
"""
Example usage of PDF to PowerPoint converter
PDF를 PowerPoint로 변환하는 예제 코드
"""

from pdf_to_ppt import PDFtoPPTConverter


def example_basic_conversion():
    """기본 변환 예제 (Basic conversion example)"""
    print("=== 예제 1: 기본 변환 (Example 1: Basic Conversion) ===")

    converter = PDFtoPPTConverter(
        pdf_path='input.pdf',  # 입력 PDF 파일 (Input PDF file)
        output_path='output.pptx',  # 출력 PPT 파일 (Output PPT file)
        dpi=200  # 해상도 (Resolution)
    )

    try:
        output_file = converter.convert()
        print(f"✓ 변환 완료: {output_file}")
        print(f"✓ Conversion completed: {output_file}")
    except FileNotFoundError:
        print("ℹ️  이 예제를 실행하려면 'input.pdf' 파일이 필요합니다.")
        print("ℹ️  To run this example, you need an 'input.pdf' file.")


def example_high_quality_conversion():
    """고품질 변환 예제 (High quality conversion example)"""
    print("\n=== 예제 2: 고품질 변환 (Example 2: High Quality Conversion) ===")

    converter = PDFtoPPTConverter(
        pdf_path='notebooklm_slides.pdf',
        output_path='high_quality_slides.pptx',
        dpi=300  # 고해상도 (High resolution)
    )

    try:
        output_file = converter.convert()
        print(f"✓ 고품질 변환 완료: {output_file}")
        print(f"✓ High quality conversion completed: {output_file}")
    except FileNotFoundError:
        print("ℹ️  이 예제를 실행하려면 'notebooklm_slides.pdf' 파일이 필요합니다.")
        print("ℹ️  To run this example, you need a 'notebooklm_slides.pdf' file.")


def example_quick_conversion():
    """빠른 변환 예제 (Quick conversion example)"""
    print("\n=== 예제 3: 빠른 변환 (Example 3: Quick Conversion) ===")

    converter = PDFtoPPTConverter(
        pdf_path='large_document.pdf',
        output_path='quick_output.pptx',
        dpi=100  # 낮은 해상도로 빠르게 (Low resolution for speed)
    )

    try:
        output_file = converter.convert()
        print(f"✓ 빠른 변환 완료: {output_file}")
        print(f"✓ Quick conversion completed: {output_file}")
    except FileNotFoundError:
        print("ℹ️  이 예제를 실행하려면 'large_document.pdf' 파일이 필요합니다.")
        print("ℹ️  To run this example, you need a 'large_document.pdf' file.")


def example_batch_conversion():
    """배치 변환 예제 (Batch conversion example)"""
    print("\n=== 예제 4: 배치 변환 (Example 4: Batch Conversion) ===")

    import os
    from pathlib import Path

    # 현재 디렉토리의 모든 PDF 파일 찾기
    # Find all PDF files in current directory
    pdf_files = list(Path('.').glob('*.pdf'))

    if not pdf_files:
        print("ℹ️  현재 디렉토리에 PDF 파일이 없습니다.")
        print("ℹ️  No PDF files found in current directory.")
        return

    print(f"발견된 PDF 파일: {len(pdf_files)}개")
    print(f"Found {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        print(f"\n변환 중 (Converting): {pdf_file.name}")

        try:
            converter = PDFtoPPTConverter(
                pdf_path=str(pdf_file),
                dpi=200
            )
            output_file = converter.convert()
            print(f"✓ 완료 (Completed): {output_file}")
        except Exception as e:
            print(f"✗ 오류 (Error): {e}")


def main():
    """메인 함수 (Main function)"""
    print("PDF to PowerPoint Converter - 사용 예제 (Usage Examples)")
    print("=" * 70)

    # 예제 실행 (Run examples)
    # 참고: 실제 PDF 파일이 있어야 동작합니다
    # Note: These require actual PDF files to work

    example_basic_conversion()
    example_high_quality_conversion()
    example_quick_conversion()
    example_batch_conversion()

    print("\n" + "=" * 70)
    print("모든 예제 완료 (All examples completed)")
    print("\n사용 팁 (Usage Tips):")
    print("1. DPI 200-300: 대부분의 경우 충분 (Sufficient for most cases)")
    print("2. DPI 100-150: 빠른 테스트용 (Fast testing)")
    print("3. DPI 300-400: 인쇄 품질 (Print quality)")


if __name__ == '__main__':
    main()
