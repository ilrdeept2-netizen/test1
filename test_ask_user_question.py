"""
=============================================================================
AskUserQuestion 도구 상세 설명 및 테스트
=============================================================================

## AskUserQuestion이란?

Claude Agent SDK에서 제공하는 내장 도구로, 에이전트 실행 중
사용자에게 구조화된 질문을 던지고 답변을 수집할 수 있게 해준다.

주로 Planning Mode에서 Claude가 코드베이스를 탐색한 뒤,
구현 방향을 결정하기 위해 사용자에게 선택지를 제시할 때 사용된다.

-----------------------------------------------------------------------------
## 동작 흐름
-----------------------------------------------------------------------------

  1. Claude가 실행 중 명확하지 않은 부분을 발견
  2. AskUserQuestion 도구를 호출 (questions 배열 전달)
  3. canUseTool 콜백이 트리거됨
  4. 앱이 사용자에게 질문/옵션을 표시
  5. 사용자가 선택하면 answers를 updatedInput에 담아 반환
  6. Claude가 답변을 받아 작업 계속 진행

-----------------------------------------------------------------------------
## Input Schema
-----------------------------------------------------------------------------

  {
    "questions": [
      {
        "question": str,       # 질문 전문 (자세한 설명 포함)
        "header": str,         # 짧은 라벨 (최대 12자)
        "options": [
          {
            "label": str,      # 옵션 텍스트 (1~5 단어)
            "description": str # 옵션 설명
          }
        ],
        "multiSelect": bool    # 복수 선택 허용 여부
      }
    ],
    "answers": dict | None     # 사용자 답변 (권한 시스템이 채움)
  }

-----------------------------------------------------------------------------
## Output Schema
-----------------------------------------------------------------------------

  {
    "questions": [...],                    # 원본 질문 그대로
    "answers": { "질문텍스트": "선택라벨" } # 질문 -> 선택된 라벨 매핑
  }

-----------------------------------------------------------------------------
## 제약 사항
-----------------------------------------------------------------------------

  - Task 도구로 생성된 서브에이전트에서는 사용 불가
  - 호출당 질문 1~4개, 옵션 2~4개
  - canUseTool 콜백 구현 필수
  - tools 배열에 "AskUserQuestion"을 명시적으로 포함해야 함

-----------------------------------------------------------------------------
## 핵심 함수: parse_response / handle_ask_user_question
-----------------------------------------------------------------------------

아래에 구현과 테스트를 포함한다.
"""

import unittest


# ---------------------------------------------------------------------------
# 구현부: 사용자 응답 파싱 함수
# ---------------------------------------------------------------------------

def parse_response(response: str, options: list[dict]) -> str:
    """사용자의 입력을 옵션 번호 또는 자유 텍스트로 파싱한다.

    Args:
        response: 사용자가 입력한 문자열 (예: "1", "1,3", "직접 입력")
        options: 옵션 딕셔너리 리스트. 각 항목은 {"label": str, "description": str}

    Returns:
        선택된 옵션의 label을 콤마로 연결한 문자열.
        번호 파싱에 실패하면 원본 response를 그대로 반환.

    Examples:
        >>> opts = [{"label": "React"}, {"label": "Vue"}, {"label": "Svelte"}]
        >>> parse_response("1", opts)
        'React'
        >>> parse_response("1, 3", opts)
        'React, Svelte'
        >>> parse_response("Angular", opts)
        'Angular'
    """
    try:
        indices = [int(s.strip()) - 1 for s in response.split(",")]
        labels = [
            options[i]["label"]
            for i in indices
            if 0 <= i < len(options)
        ]
        return ", ".join(labels) if labels else response
    except ValueError:
        return response


def build_ask_user_question_input(
    question: str,
    header: str,
    options: list[dict],
    multi_select: bool = False,
) -> dict:
    """AskUserQuestion 도구의 입력 데이터를 생성한다.

    Args:
        question: 질문 전문
        header: 짧은 라벨 (12자 이내 권장)
        options: [{"label": str, "description": str}, ...]
        multi_select: 복수 선택 허용 여부

    Returns:
        AskUserQuestion 입력 형식에 맞는 딕셔너리
    """
    return {
        "questions": [
            {
                "question": question,
                "header": header,
                "options": options,
                "multiSelect": multi_select,
            }
        ],
        "answers": None,
    }


def simulate_handle_ask_user_question(
    input_data: dict,
    simulated_responses: list[str],
) -> dict:
    """AskUserQuestion 핸들러를 시뮬레이션한다 (실제 stdin 대신 미리 정의된 응답 사용).

    Args:
        input_data: AskUserQuestion 입력 데이터
        simulated_responses: 각 질문에 대한 시뮬레이션 응답 리스트

    Returns:
        {"behavior": "allow", "updatedInput": {"questions": [...], "answers": {...}}}
    """
    answers = {}
    questions = input_data.get("questions", [])

    for i, q in enumerate(questions):
        response = simulated_responses[i] if i < len(simulated_responses) else ""
        answers[q["question"]] = parse_response(response, q["options"])

    return {
        "behavior": "allow",
        "updatedInput": {
            "questions": questions,
            "answers": answers,
        },
    }


# ---------------------------------------------------------------------------
# 테스트
# ---------------------------------------------------------------------------

class TestAskUserQuestion(unittest.TestCase):
    """AskUserQuestion 도구의 전체 흐름을 검증하는 테스트.

    이 테스트는 다음을 확인한다:
      1. 입력 데이터 생성 (build_ask_user_question_input)
      2. 사용자 응답 파싱 (parse_response)
      3. 핸들러 시뮬레이션 (simulate_handle_ask_user_question)
      4. 단일 선택 / 복수 선택 / 자유 텍스트 입력 시나리오
    """

    def setUp(self):
        """테스트에 사용할 공통 옵션 데이터를 준비한다."""
        self.tech_stack_options = [
            {"label": "React Native", "description": "크로스 플랫폼, JS 기반"},
            {"label": "Flutter", "description": "크로스 플랫폼, Dart 기반"},
            {"label": "Swift", "description": "iOS 네이티브"},
            {"label": "Kotlin", "description": "Android 네이티브"},
        ]

    def test_full_ask_user_question_flow(self):
        """AskUserQuestion 전체 흐름 테스트:
        입력 생성 -> 사용자 응답 -> 핸들러 처리 -> 결과 검증

        시나리오: 모바일 앱 기술 스택을 묻는 질문에 사용자가 "2"(Flutter)를 선택
        """
        # 1단계: 입력 데이터 생성
        input_data = build_ask_user_question_input(
            question="모바일 앱 개발에 어떤 기술 스택을 사용하시겠습니까?",
            header="기술스택",
            options=self.tech_stack_options,
            multi_select=False,
        )

        # 입력 구조 검증
        self.assertEqual(len(input_data["questions"]), 1)
        self.assertEqual(len(input_data["questions"][0]["options"]), 4)
        self.assertFalse(input_data["questions"][0]["multiSelect"])
        self.assertIsNone(input_data["answers"])

        # 2단계: 사용자가 "2" (Flutter) 선택을 시뮬레이션
        result = simulate_handle_ask_user_question(input_data, ["2"])

        # 3단계: 결과 검증
        self.assertEqual(result["behavior"], "allow")

        answers = result["updatedInput"]["answers"]
        question_text = "모바일 앱 개발에 어떤 기술 스택을 사용하시겠습니까?"
        self.assertIn(question_text, answers)
        self.assertEqual(answers[question_text], "Flutter")

        # questions가 그대로 유지되는지 확인
        self.assertEqual(
            result["updatedInput"]["questions"],
            input_data["questions"],
        )

        # 4단계: 복수 선택 시나리오 ("1,3" -> React Native, Swift)
        input_data_multi = build_ask_user_question_input(
            question="지원할 플랫폼을 모두 선택하세요",
            header="플랫폼",
            options=self.tech_stack_options,
            multi_select=True,
        )
        result_multi = simulate_handle_ask_user_question(input_data_multi, ["1,3"])
        multi_answer = result_multi["updatedInput"]["answers"]["지원할 플랫폼을 모두 선택하세요"]
        self.assertEqual(multi_answer, "React Native, Swift")

        # 5단계: 자유 텍스트 입력 시나리오
        result_free = simulate_handle_ask_user_question(input_data, ["Xamarin"])
        free_answer = result_free["updatedInput"]["answers"][question_text]
        self.assertEqual(free_answer, "Xamarin")  # 옵션에 없으므로 그대로 반환


if __name__ == "__main__":
    unittest.run_main()
