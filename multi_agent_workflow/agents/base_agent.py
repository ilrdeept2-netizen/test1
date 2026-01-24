"""
기본 에이전트 클래스

모든 특화 에이전트의 기반이 되는 추상 클래스입니다.
Claude Agent SDK와 통합하여 에이전트 기능을 제공합니다.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
from enum import Enum

# Claude Agent SDK 임포트 (설치 필요)
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"


@dataclass
class AgentMessage:
    """에이전트 간 메시지"""
    sender: str
    receiver: str
    content: Any
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """에이전트 실행 결과"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    기본 에이전트 추상 클래스

    모든 특화 에이전트는 이 클래스를 상속받아 구현합니다.
    """

    def __init__(
        self,
        name: str,
        model: str = "claude-opus-4-5-20251101",
        system_prompt: str = "",
        tools: Optional[List[str]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or ["read", "write", "bash"]
        self.max_tokens = max_tokens
        self.temperature = temperature

        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"agent.{name}")
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.results: List[AgentResult] = []

        # Anthropic 클라이언트 초기화
        self._client = None
        if Anthropic:
            try:
                self._client = Anthropic()
            except Exception as e:
                self.logger.warning(f"Anthropic 클라이언트 초기화 실패: {e}")

    @property
    def is_ready(self) -> bool:
        """에이전트가 작업 준비가 되었는지 확인"""
        return self.status == AgentStatus.IDLE

    @abstractmethod
    async def process(self, input_data: Any) -> AgentResult:
        """
        에이전트의 주요 처리 로직

        Args:
            input_data: 입력 데이터

        Returns:
            AgentResult: 처리 결과
        """
        pass

    async def query(self, prompt: str) -> AsyncIterator[str]:
        """
        Claude API에 쿼리를 보내고 스트리밍 응답을 받습니다.

        Args:
            prompt: 사용자 프롬프트

        Yields:
            str: 응답 청크
        """
        if not self._client:
            yield "Error: Anthropic 클라이언트가 초기화되지 않았습니다."
            return

        self.status = AgentStatus.RUNNING

        try:
            messages = [{"role": "user", "content": prompt}]

            with self._client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

            self.status = AgentStatus.COMPLETED

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"쿼리 실행 중 오류: {e}")
            yield f"Error: {str(e)}"

    async def send_message(self, receiver: str, content: Any, **kwargs) -> None:
        """
        다른 에이전트에게 메시지를 보냅니다.

        Args:
            receiver: 수신 에이전트 이름
            content: 메시지 내용
            **kwargs: 추가 메타데이터
        """
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            content=content,
            metadata=kwargs,
        )
        await self.message_queue.put(message)
        self.logger.debug(f"메시지 전송: {self.name} -> {receiver}")

    async def receive_message(self, timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        메시지를 수신합니다.

        Args:
            timeout: 대기 시간(초)

        Returns:
            AgentMessage or None
        """
        try:
            message = await asyncio.wait_for(
                self.message_queue.get(),
                timeout=timeout
            )
            self.logger.debug(f"메시지 수신: {message.sender} -> {self.name}")
            return message
        except asyncio.TimeoutError:
            return None

    async def execute_tool(self, tool_name: str, **params) -> Any:
        """
        도구를 실행합니다.

        Args:
            tool_name: 도구 이름
            **params: 도구 파라미터

        Returns:
            도구 실행 결과
        """
        if tool_name not in self.tools:
            raise PermissionError(f"도구 '{tool_name}'에 대한 권한이 없습니다.")

        self.logger.info(f"도구 실행: {tool_name}")

        # 도구별 실행 로직 (실제 구현 시 Claude Agent SDK 도구 사용)
        tool_handlers = {
            "read": self._tool_read,
            "write": self._tool_write,
            "edit": self._tool_edit,
            "bash": self._tool_bash,
            "grep": self._tool_grep,
            "glob": self._tool_glob,
        }

        handler = tool_handlers.get(tool_name)
        if handler:
            return await handler(**params)
        else:
            raise NotImplementedError(f"도구 '{tool_name}'이 구현되지 않았습니다.")

    async def _tool_read(self, file_path: str) -> str:
        """파일 읽기 도구"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    async def _tool_write(self, file_path: str, content: str) -> str:
        """파일 쓰기 도구"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File written successfully: {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    async def _tool_edit(self, file_path: str, old_str: str, new_str: str) -> str:
        """파일 편집 도구"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace(old_str, new_str)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File edited successfully: {file_path}"
        except Exception as e:
            return f"Error editing file: {e}"

    async def _tool_bash(self, command: str) -> str:
        """Bash 명령 실행 도구"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return stdout.decode() if stdout else stderr.decode()
        except Exception as e:
            return f"Error executing command: {e}"

    async def _tool_grep(self, pattern: str, path: str = ".") -> str:
        """패턴 검색 도구"""
        return await self._tool_bash(f"grep -r '{pattern}' {path}")

    async def _tool_glob(self, pattern: str, path: str = ".") -> str:
        """파일 패턴 매칭 도구"""
        import glob
        matches = glob.glob(f"{path}/{pattern}", recursive=True)
        return "\n".join(matches)

    def reset(self) -> None:
        """에이전트 상태를 초기화합니다."""
        self.status = AgentStatus.IDLE
        self.results.clear()
        self.message_queue = asyncio.Queue()
        self.logger.info(f"에이전트 '{self.name}' 초기화됨")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', status={self.status.value})>"
