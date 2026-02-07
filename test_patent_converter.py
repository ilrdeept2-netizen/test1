#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
특허 명세서 변환기 테스트
"""

import os
import sys
import json
from pathlib import Path
from collections import OrderedDict

from docx import Document
from patent_format_converter import (
    PatentFormatConverter,
    HLTGenerator,
    detect_section,
    parse_claims,
    WordReader,
    SECTION_DEFINITIONS,
)


def create_test_patent_document(output_path='test_patent.docx'):
    """테스트용 특허 명세서 Word 문서 생성"""

    doc = Document()

    doc.add_paragraph('【발명의 명칭】')
    doc.add_paragraph('인공지능 기반 문서 자동 변환 시스템')

    doc.add_paragraph('【기술분야】')
    doc.add_paragraph('본 발명은 문서 처리 기술에 관한 것으로, 특히 다양한 형식의 문서를 특허 명세서 형식으로 자동 변환하는 시스템에 관한 것이다.')

    doc.add_paragraph('【발명의 배경이 되는 기술】')
    doc.add_paragraph('종래에는 특허 명세서를 작성할 때 수동으로 복사하여 붙여넣기 하는 방식을 사용하였다.')
    doc.add_paragraph('이러한 방식은 시간이 많이 소요되고 오류가 발생하기 쉬운 문제점이 있었다.')

    doc.add_paragraph('【해결하려는 과제】')
    doc.add_paragraph('본 발명은 상기와 같은 문제점을 해결하기 위한 것으로, 문서 변환을 자동화하여 작업 효율을 높이는 것을 목적으로 한다.')

    doc.add_paragraph('【과제의 해결 수단】')
    doc.add_paragraph('상기 목적을 달성하기 위한 본 발명은 다음과 같은 구성을 포함한다.')
    doc.add_paragraph('문서 읽기 모듈, 섹션 인식 모듈, HLT 변환 모듈을 포함하는 문서 변환 시스템.')

    doc.add_paragraph('【발명의 효과】')
    doc.add_paragraph('본 발명에 따르면 특허 명세서 작성 시간을 대폭 단축할 수 있다.')
    doc.add_paragraph('또한 수동 작업에서 발생하는 오류를 방지할 수 있다.')

    doc.add_paragraph('【도면의 간단한 설명】')
    doc.add_paragraph('도 1은 본 발명의 실시예에 따른 문서 변환 시스템의 블록도이다.')
    doc.add_paragraph('도 2는 본 발명의 실시예에 따른 변환 과정을 나타낸 흐름도이다.')

    doc.add_paragraph('【발명을 실시하기 위한 구체적인 내용】')
    doc.add_paragraph('이하, 첨부된 도면을 참조하여 본 발명의 바람직한 실시예를 상세히 설명한다.')
    doc.add_paragraph('본 시스템은 Word, HWP 파일을 입력받아 HLT 형식으로 변환한다.')
    doc.add_paragraph('변환 과정에서 문서의 구조를 자동으로 인식하고 해당하는 섹션으로 분류한다.')

    doc.add_paragraph('【부호의 설명】')
    doc.add_paragraph('100: 문서 읽기 모듈')
    doc.add_paragraph('200: 섹션 인식 모듈')
    doc.add_paragraph('300: HLT 변환 모듈')

    doc.add_paragraph('【특허청구범위】')
    doc.add_paragraph('【청구항 1】')
    doc.add_paragraph('문서 파일을 읽는 문서 읽기부; 상기 문서의 섹션을 인식하는 섹션 인식부; 및 인식된 섹션을 HLT 형식으로 변환하는 변환부를 포함하는 특허 문서 변환 시스템.')
    doc.add_paragraph('【청구항 2】')
    doc.add_paragraph('제1항에 있어서, 상기 문서 파일은 Word, HWP 형식 중 하나인 것을 특징으로 하는 특허 문서 변환 시스템.')
    doc.add_paragraph('【청구항 3】')
    doc.add_paragraph('제1항에 있어서, 상기 변환부는 한국특허청 표준 XML 형식으로 출력하는 것을 특징으로 하는 특허 문서 변환 시스템.')

    doc.add_paragraph('【요약서】')
    doc.add_paragraph('본 발명은 다양한 형식의 문서를 특허 명세서 형식(HLT)으로 자동 변환하는 시스템에 관한 것이다.')

    doc.save(output_path)
    print(f"  테스트 문서 생성: {output_path}")
    return output_path


def test_section_detection():
    """섹션 헤더 감지 테스트"""
    print("\n[테스트 1] 섹션 헤더 감지")
    print("-" * 50)

    test_cases = [
        ('【발명의 명칭】', 'invention-title'),
        ('【기술분야】', 'technical-field'),
        ('【발명의 배경이 되는 기술】', 'background-art'),
        ('【배경기술】', 'background-art'),
        ('【해결하려는 과제】', 'technical-problem'),
        ('【해결하고자 하는 과제】', 'technical-problem'),
        ('【과제의 해결 수단】', 'technical-solution'),
        ('【발명의 효과】', 'advantageous-effects'),
        ('【도면의 간단한 설명】', 'description-of-drawings'),
        ('【발명을 실시하기 위한 구체적인 내용】', 'detailed-description'),
        ('【실시예】', 'detailed-description'),
        ('【부호의 설명】', 'reference-signs'),
        ('【특허청구범위】', 'claims'),
        ('【청구항 1】', 'claim-item'),
        ('【요약서】', 'abstract'),
        ('【요약】', 'abstract'),
        ('【대표도면】', 'representative-drawing'),
        ('일반 텍스트입니다', None),
        ('[발명의 명칭]', 'invention-title'),
    ]

    passed = 0
    failed = 0
    for text, expected in test_cases:
        result = detect_section(text)
        ok = result == expected
        status = 'OK' if ok else 'FAIL'
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  {status}: '{text}' -> {result} (expected: {expected})")

    print(f"  결과: {passed} passed, {failed} failed / {len(test_cases)} total")
    return failed == 0


def test_claims_parsing():
    """청구항 파싱 테스트"""
    print("\n[테스트 2] 청구항 파싱")
    print("-" * 50)

    # 케이스 1: 【청구항 N】 형식
    lines1 = [
        '문서 파일을 읽는 문서 읽기부.',
        '제1항에 있어서, 상기 문서 파일은 Word 형식인 것.',
    ]
    # 이 경우 번호가 없으므로 하나의 청구항으로 파싱됨

    # 케이스 2: "청구항 N:" 형식
    lines2 = [
        '청구항 1: 문서 파일을 읽는 문서 읽기부.',
        '청구항 2: 제1항에 있어서, Word 형식.',
        '청구항 3: 제1항에 있어서, XML 출력.',
    ]
    claims2 = parse_claims(lines2)

    ok = len(claims2) == 3 and claims2[0]['num'] == 1 and claims2[2]['num'] == 3
    print(f"  '청구항 N:' 형식: {'OK' if ok else 'FAIL'} ({len(claims2)} claims)")

    # 케이스 3: 번호만 있는 형식
    lines3 = [
        '1. 문서 파일을 읽는 문서 읽기부.',
        '2. 제1항에 있어서, Word 형식.',
    ]
    claims3 = parse_claims(lines3)
    ok3 = len(claims3) == 2
    print(f"  '1.' 형식: {'OK' if ok3 else 'FAIL'} ({len(claims3)} claims)")

    return ok and ok3


def test_word_conversion():
    """Word -> HLT 변환 테스트"""
    print("\n[테스트 3] Word -> HLT 변환")
    print("-" * 50)

    input_file = create_test_patent_document()
    output_file = 'test_patent.hlt'

    converter = PatentFormatConverter(input_file, output_file)

    # 섹션 추출 테스트
    sections = converter.extract_sections()
    print(f"  감지된 섹션: {len(sections)}개")
    for sid, content in sections.items():
        print(f"    [{sid}] {len(content)}개 단락")

    expected_sections = [
        'invention-title', 'technical-field', 'background-art',
        'technical-problem', 'technical-solution', 'advantageous-effects',
        'description-of-drawings', 'detailed-description', 'reference-signs',
        'claims', 'abstract',
    ]

    missing = [s for s in expected_sections if s not in sections]
    if missing:
        print(f"  누락된 섹션: {missing}")

    # 변환 테스트
    result_path = converter.convert()
    exists = os.path.exists(result_path)
    size = os.path.getsize(result_path) if exists else 0
    print(f"  HLT 파일 생성: {'OK' if exists else 'FAIL'} ({size} bytes)")

    # XML 유효성 확인
    if exists:
        from lxml import etree
        try:
            tree = etree.parse(result_path)
            root = tree.getroot()
            tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            print(f"  XML 유효성: OK (root: {tag})")
        except Exception as e:
            print(f"  XML 유효성: FAIL ({e})")
            return False

    return exists and len(missing) == 0


def test_hlt_generator_from_dict():
    """HLTGenerator에 직접 dict를 전달하여 HLT 생성 테스트"""
    print("\n[테스트 4] HLTGenerator 직접 호출")
    print("-" * 50)

    sections = OrderedDict([
        ('invention-title', ['테스트 발명']),
        ('technical-field', ['테스트 기술분야 내용']),
        ('claims', [
            '청구항 1: 제1 구성요소를 포함하는 장치.',
            '청구항 2: 제1항에 있어서, 추가 구성요소를 포함하는 장치.',
        ]),
        ('abstract', ['본 발명은 테스트 발명이다.']),
    ])

    generator = HLTGenerator()
    output_path = '/tmp/test_direct.hlt'
    generator.generate(sections, output_path)

    exists = os.path.exists(output_path)
    print(f"  파일 생성: {'OK' if exists else 'FAIL'}")

    if exists:
        from lxml import etree
        tree = etree.parse(output_path)
        root = tree.getroot()
        ns = {'ns': 'http://www.kipo.go.kr/kipo'}

        claims = root.findall('.//ns:claim', ns)
        print(f"  청구항 수: {len(claims)}")
        ok = len(claims) == 2
        print(f"  결과: {'OK' if ok else 'FAIL'}")

        os.unlink(output_path)
        return ok

    return False


def main():
    print("=" * 60)
    print("특허 명세서 변환기 테스트")
    print("=" * 60)

    results = []
    results.append(('섹션 헤더 감지', test_section_detection()))
    results.append(('청구항 파싱', test_claims_parsing()))
    results.append(('Word -> HLT 변환', test_word_conversion()))
    results.append(('HLTGenerator 직접 호출', test_hlt_generator_from_dict()))

    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    all_passed = True
    for name, ok in results:
        status = 'PASS' if ok else 'FAIL'
        print(f"  [{status}] {name}")
        if not ok:
            all_passed = False

    print()
    if all_passed:
        print("모든 테스트 통과")
    else:
        print("일부 테스트 실패")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
