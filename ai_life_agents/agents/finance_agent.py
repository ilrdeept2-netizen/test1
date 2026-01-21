"""
AgentFinance - 재정/자산 관리 에이전트
Matt Schlicht의 AgentWealth 컨셉을 한국 상황에 맞게 구현

기능:
- 청구서 관리 및 자동 납부
- 카드/대출 최적화
- 적립식 투자 (DCA)
- 지출 분석 및 절약
- 한국 금융 서비스 연동 (토스, 카카오페이 등)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio

from ..base_agent import BaseAgent, Task, Message, Priority


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    INVESTMENT = "investment"


@dataclass
class Account:
    """금융 계좌"""
    id: str
    name: str
    bank: str
    account_type: str  # checking, savings, investment, credit
    balance: Decimal = Decimal("0")
    currency: str = "KRW"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Transaction:
    """거래 내역"""
    id: str
    account_id: str
    amount: Decimal
    transaction_type: TransactionType
    category: str
    merchant: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class Bill:
    """청구서"""
    id: str
    name: str
    amount: Decimal
    due_date: datetime
    recurring: bool = True
    auto_pay: bool = False
    category: str = ""
    status: str = "pending"  # pending, paid, overdue


@dataclass
class Investment:
    """투자 포지션"""
    id: str
    asset_type: str  # stock, etf, crypto, fund
    symbol: str
    name: str
    quantity: Decimal
    avg_price: Decimal
    current_price: Decimal = Decimal("0")

    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.current_price

    @property
    def profit_loss(self) -> Decimal:
        return (self.current_price - self.avg_price) * self.quantity

    @property
    def profit_loss_pct(self) -> float:
        if self.avg_price == 0:
            return 0
        return float((self.current_price - self.avg_price) / self.avg_price * 100)


class AgentFinance(BaseAgent):
    """
    재정 관리 에이전트

    한국 맞춤 기능:
    - 토스/카카오뱅크 계좌 연동
    - 국민연금/건강보험료 추적
    - 연말정산 최적화
    - 주식/ETF/펀드 적립식 투자
    - 통신비/보험료 최저가 비교
    """

    def __init__(self, agent_id: str = "finance"):
        super().__init__(
            agent_id=agent_id,
            name="AgentFinance",
            description="재정 및 자산 관리 에이전트"
        )

        # 데이터 저장소
        self.accounts: Dict[str, Account] = {}
        self.transactions: List[Transaction] = []
        self.bills: Dict[str, Bill] = {}
        self.investments: Dict[str, Investment] = {}

        # 설정
        self.config = {
            "auto_pay_enabled": True,
            "dca_enabled": True,
            "spending_alerts": True,
            "savings_goal": Decimal("10000000"),  # 1000만원
            "monthly_budget": Decimal("3000000"),  # 300만원
            "emergency_fund_months": 6
        }

        # DCA (적립식 투자) 설정
        self.dca_plans: List[Dict[str, Any]] = []

        # 지출 카테고리
        self.categories = {
            "housing": "주거",
            "food": "식비",
            "transport": "교통",
            "utilities": "공과금",
            "insurance": "보험",
            "healthcare": "의료",
            "education": "교육",
            "entertainment": "여가",
            "shopping": "쇼핑",
            "savings": "저축",
            "investment": "투자",
            "other": "기타"
        }

    async def initialize(self) -> bool:
        """초기화"""
        self.logger.info("재정 에이전트 초기화 중...")

        # 이벤트 핸들러 등록
        self.on("income_received", self._on_income_received)
        self.on("large_expense", self._on_large_expense)
        self.on("bill_due_soon", self._on_bill_due)

        # 자동 작업 스케줄링
        await self._schedule_recurring_tasks()

        return True

    def get_capabilities(self) -> List[str]:
        """기능 목록"""
        return [
            "account_management",      # 계좌 관리
            "bill_payment",           # 청구서 납부
            "expense_tracking",       # 지출 추적
            "budget_management",      # 예산 관리
            "investment_dca",         # 적립식 투자
            "savings_optimization",   # 저축 최적화
            "card_optimization",      # 카드 최적화
            "tax_preparation",        # 연말정산 준비
            "insurance_comparison",   # 보험 비교
            "loan_optimization"       # 대출 최적화
        ]

    async def process_task(self, task: Task) -> Any:
        """작업 처리"""
        task_handlers = {
            "pay_bill": self._pay_bill,
            "analyze_spending": self._analyze_spending,
            "execute_dca": self._execute_dca,
            "optimize_cards": self._optimize_cards,
            "find_savings": self._find_savings,
            "negotiate_bill": self._negotiate_bill,
            "monthly_report": self._generate_monthly_report,
            "check_subscriptions": self._check_subscriptions
        }

        handler = task_handlers.get(task.name)
        if handler:
            return await handler(task.metadata)
        else:
            self.logger.warning(f"알 수 없는 작업: {task.name}")
            return None

    async def handle_request(self, message: Message) -> Optional[Message]:
        """요청 처리"""
        handlers = {
            "get_balance": self._handle_get_balance,
            "get_spending_summary": self._handle_get_spending,
            "monthly_report": self._handle_monthly_report,
            "budget_check": self._handle_budget_check,
            "emergency_fund_status": self._handle_emergency_fund
        }

        handler = handlers.get(message.subject)
        if handler:
            result = await handler(message.content)
            return Message(
                sender=self.agent_id,
                receiver=message.sender,
                message_type="response",
                subject=f"{message.subject}_response",
                content=result
            )
        return None

    # ========== 계좌 관리 ==========

    def add_account(self, account: Account) -> None:
        """계좌 추가"""
        self.accounts[account.id] = account
        self.logger.info(f"계좌 추가: {account.name} ({account.bank})")

    def get_total_balance(self) -> Decimal:
        """총 잔액 조회"""
        return sum(
            acc.balance for acc in self.accounts.values()
            if acc.account_type != "credit"
        )

    def get_net_worth(self) -> Decimal:
        """순자산 계산"""
        # 예금 + 투자 - 부채
        deposits = sum(
            acc.balance for acc in self.accounts.values()
            if acc.account_type in ["checking", "savings"]
        )
        investments = sum(
            inv.market_value for inv in self.investments.values()
        )
        debts = sum(
            abs(acc.balance) for acc in self.accounts.values()
            if acc.account_type == "credit" and acc.balance < 0
        )
        return deposits + investments - debts

    # ========== 청구서 관리 ==========

    def add_bill(self, bill: Bill) -> None:
        """청구서 추가"""
        self.bills[bill.id] = bill
        self.logger.info(f"청구서 추가: {bill.name} - {bill.amount:,}원")

    async def _pay_bill(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """청구서 납부"""
        bill_id = metadata.get("bill_id")
        bill = self.bills.get(bill_id)

        if not bill:
            return {"success": False, "error": "청구서를 찾을 수 없습니다"}

        # 납부 처리 (실제로는 뱅킹 API 호출)
        self.logger.info(f"청구서 납부: {bill.name} - {bill.amount:,}원")
        bill.status = "paid"

        # 거래 기록
        transaction = Transaction(
            id=f"tx_{datetime.now().timestamp()}",
            account_id=metadata.get("account_id", "main"),
            amount=bill.amount,
            transaction_type=TransactionType.EXPENSE,
            category=bill.category,
            description=f"{bill.name} 납부"
        )
        self.transactions.append(transaction)

        # 건강 에이전트에 보험료 납부 알림 (예시)
        if bill.category == "insurance":
            await self.send_message(
                "health",
                "insurance_paid",
                {"bill_name": bill.name, "amount": float(bill.amount)}
            )

        return {"success": True, "bill": bill.name, "amount": float(bill.amount)}

    async def _negotiate_bill(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        청구서 협상 (통신비, 보험료 등)

        실제로는 AI가 고객센터에 연락하여 할인 협상을 진행
        """
        bill_type = metadata.get("bill_type")
        current_amount = metadata.get("current_amount", 0)

        # 협상 시뮬레이션
        negotiation_results = {
            "통신비": {"success": True, "discount": 0.15, "reason": "장기고객 할인"},
            "보험료": {"success": True, "discount": 0.10, "reason": "무사고 할인"},
            "인터넷": {"success": True, "discount": 0.20, "reason": "결합 할인"}
        }

        result = negotiation_results.get(bill_type, {"success": False})

        if result["success"]:
            savings = current_amount * result["discount"]
            self.logger.info(
                f"협상 성공: {bill_type} - {result['reason']}으로 "
                f"월 {savings:,.0f}원 절약"
            )

        return result

    # ========== 지출 분석 ==========

    async def _analyze_spending(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """지출 분석"""
        period = metadata.get("period", 30)  # 기본 30일
        start_date = datetime.now() - timedelta(days=period)

        # 기간 내 지출 필터링
        expenses = [
            t for t in self.transactions
            if t.transaction_type == TransactionType.EXPENSE
            and t.timestamp >= start_date
        ]

        # 카테고리별 집계
        by_category = {}
        for expense in expenses:
            cat = expense.category
            if cat not in by_category:
                by_category[cat] = Decimal("0")
            by_category[cat] += expense.amount

        total = sum(by_category.values())

        # 예산 대비 분석
        budget = self.config["monthly_budget"]
        budget_usage = float(total / budget * 100) if budget else 0

        analysis = {
            "period_days": period,
            "total_spending": float(total),
            "by_category": {k: float(v) for k, v in by_category.items()},
            "budget": float(budget),
            "budget_usage_pct": budget_usage,
            "daily_average": float(total / period) if period else 0,
            "top_expenses": self._get_top_expenses(expenses, 5)
        }

        # 예산 초과 시 알림
        if budget_usage > 80:
            await self.emit_event("budget_warning", {
                "usage_pct": budget_usage,
                "remaining": float(budget - total)
            })

        return analysis

    def _get_top_expenses(self, expenses: List[Transaction],
                         limit: int) -> List[Dict[str, Any]]:
        """상위 지출 조회"""
        sorted_expenses = sorted(expenses, key=lambda x: x.amount, reverse=True)
        return [
            {
                "merchant": e.merchant,
                "amount": float(e.amount),
                "category": e.category,
                "date": e.timestamp.isoformat()
            }
            for e in sorted_expenses[:limit]
        ]

    # ========== 적립식 투자 (DCA) ==========

    def setup_dca(self, asset_symbol: str, amount: Decimal,
                  frequency: str = "monthly", day: int = 25) -> None:
        """
        적립식 투자 설정

        예시:
        - S&P500 ETF 월 50만원
        - 삼성전자 월 30만원
        - 비트코인 주 10만원
        """
        plan = {
            "id": f"dca_{len(self.dca_plans)}",
            "asset_symbol": asset_symbol,
            "amount": amount,
            "frequency": frequency,
            "day": day,
            "enabled": True,
            "created_at": datetime.now()
        }
        self.dca_plans.append(plan)
        self.logger.info(
            f"DCA 설정: {asset_symbol} - {amount:,}원 ({frequency})"
        )

    async def _execute_dca(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """적립식 투자 실행"""
        results = []

        for plan in self.dca_plans:
            if not plan["enabled"]:
                continue

            # 매수 실행 (실제로는 증권사 API 호출)
            self.logger.info(
                f"DCA 매수: {plan['asset_symbol']} - {plan['amount']:,}원"
            )

            # 포지션 업데이트
            result = {
                "asset": plan["asset_symbol"],
                "amount": float(plan["amount"]),
                "executed_at": datetime.now().isoformat(),
                "success": True
            }
            results.append(result)

        return {"dca_executions": results}

    # ========== 카드 최적화 ==========

    async def _optimize_cards(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        카드 최적화

        - 카드 혜택 분석
        - 최적 카드 추천
        - 연회비 대비 혜택 계산
        - 포인트/캐시백 극대화
        """
        spending_patterns = await self._analyze_spending({"period": 90})

        recommendations = []

        # 지출 패턴에 따른 카드 추천 (예시)
        by_category = spending_patterns.get("by_category", {})

        if by_category.get("food", 0) > 500000:
            recommendations.append({
                "card": "배민 신한카드",
                "reason": "식비 지출이 많아 배달앱 할인 카드 추천",
                "expected_savings": by_category["food"] * 0.05
            })

        if by_category.get("transport", 0) > 200000:
            recommendations.append({
                "card": "현대 M포인트 카드",
                "reason": "교통비가 많아 주유/대중교통 할인 카드 추천",
                "expected_savings": by_category["transport"] * 0.07
            })

        return {
            "current_spending": spending_patterns,
            "recommendations": recommendations,
            "total_potential_savings": sum(r["expected_savings"] for r in recommendations)
        }

    # ========== 절약 기회 찾기 ==========

    async def _find_savings(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """절약 기회 탐색"""
        opportunities = []

        # 1. 구독 서비스 중복 체크
        subscriptions = await self._check_subscriptions({})
        if subscriptions.get("duplicates"):
            opportunities.append({
                "type": "subscription_duplicate",
                "description": "중복 구독 서비스 발견",
                "potential_savings": subscriptions["duplicate_cost"]
            })

        # 2. 미사용 구독 체크
        if subscriptions.get("unused"):
            opportunities.append({
                "type": "subscription_unused",
                "description": "미사용 구독 서비스",
                "potential_savings": subscriptions["unused_cost"]
            })

        # 3. 보험료 비교
        opportunities.append({
            "type": "insurance_comparison",
            "description": "보험료 비교 견적 가능",
            "action": "negotiate_bill"
        })

        # 4. 통신비 최적화
        opportunities.append({
            "type": "telecom_optimization",
            "description": "알뜰폰 요금제 비교",
            "potential_savings": 30000  # 월 3만원 예상
        })

        return {
            "opportunities": opportunities,
            "total_potential_monthly_savings": sum(
                o.get("potential_savings", 0) for o in opportunities
            )
        }

    async def _check_subscriptions(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """구독 서비스 체크"""
        # 실제로는 카드 명세서 분석
        subscriptions = [
            {"name": "넷플릭스", "amount": 17000, "last_used": "2024-01-15"},
            {"name": "유튜브 프리미엄", "amount": 14900, "last_used": "2024-01-20"},
            {"name": "멜론", "amount": 10900, "last_used": "2023-11-01"},  # 미사용
            {"name": "애플뮤직", "amount": 10900, "last_used": "2024-01-18"},  # 멜론과 중복
        ]

        return {
            "subscriptions": subscriptions,
            "total_monthly": sum(s["amount"] for s in subscriptions),
            "duplicates": ["멜론", "애플뮤직"],
            "duplicate_cost": 10900,
            "unused": ["멜론"],
            "unused_cost": 10900
        }

    # ========== 리포트 생성 ==========

    async def _generate_monthly_report(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """월간 재정 리포트"""
        spending = await self._analyze_spending({"period": 30})

        report = {
            "summary": f"이번 달 총 지출: {spending['total_spending']:,.0f}원",
            "period": "monthly",
            "total_spending": spending["total_spending"],
            "budget_usage": spending["budget_usage_pct"],
            "net_worth": float(self.get_net_worth()),
            "spending_by_category": spending["by_category"],
            "investment_performance": self._get_investment_performance(),
            "upcoming_bills": self._get_upcoming_bills(),
            "recommendations": []
        }

        # 권장 사항 추가
        if spending["budget_usage_pct"] > 100:
            report["recommendations"].append(
                "예산을 초과했습니다. 다음 달 지출을 줄여보세요."
            )

        return report

    def _get_investment_performance(self) -> Dict[str, Any]:
        """투자 성과"""
        total_value = sum(inv.market_value for inv in self.investments.values())
        total_cost = sum(
            inv.avg_price * inv.quantity for inv in self.investments.values()
        )
        total_pl = total_value - total_cost

        return {
            "total_value": float(total_value),
            "total_profit_loss": float(total_pl),
            "profit_loss_pct": float(total_pl / total_cost * 100) if total_cost else 0
        }

    def _get_upcoming_bills(self, days: int = 7) -> List[Dict[str, Any]]:
        """예정된 청구서"""
        upcoming = []
        cutoff = datetime.now() + timedelta(days=days)

        for bill in self.bills.values():
            if bill.status == "pending" and bill.due_date <= cutoff:
                upcoming.append({
                    "name": bill.name,
                    "amount": float(bill.amount),
                    "due_date": bill.due_date.isoformat(),
                    "auto_pay": bill.auto_pay
                })

        return sorted(upcoming, key=lambda x: x["due_date"])

    # ========== 이벤트 핸들러 ==========

    async def _on_income_received(self, event) -> None:
        """급여/수입 발생 시"""
        amount = event.data.get("amount", 0)
        self.logger.info(f"수입 발생: {amount:,}원")

        # 자동 저축/투자 실행
        if self.config["dca_enabled"]:
            await self._execute_dca({})

    async def _on_large_expense(self, event) -> None:
        """큰 지출 발생 시"""
        amount = event.data.get("amount", 0)
        merchant = event.data.get("merchant", "")

        self.logger.warning(f"큰 지출 감지: {merchant}에서 {amount:,}원")

        # 사용자에게 알림 (실제로는 푸시 알림)

    async def _on_bill_due(self, event) -> None:
        """청구서 납부일 임박"""
        bill_name = event.data.get("bill_name")
        due_date = event.data.get("due_date")

        self.logger.info(f"청구서 알림: {bill_name} - {due_date}까지 납부")

    # ========== 핸들러 함수 ==========

    async def _handle_get_balance(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """잔액 조회 요청 처리"""
        return {
            "total_balance": float(self.get_total_balance()),
            "net_worth": float(self.get_net_worth()),
            "accounts": len(self.accounts)
        }

    async def _handle_get_spending(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """지출 요약 요청 처리"""
        return await self._analyze_spending(content)

    async def _handle_monthly_report(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """월간 리포트 요청 처리"""
        return await self._generate_monthly_report(content)

    async def _handle_budget_check(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """예산 체크 요청 처리"""
        spending = await self._analyze_spending({"period": 30})
        return {
            "budget": float(self.config["monthly_budget"]),
            "spent": spending["total_spending"],
            "remaining": float(self.config["monthly_budget"]) - spending["total_spending"],
            "usage_pct": spending["budget_usage_pct"]
        }

    async def _handle_emergency_fund(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """비상금 현황 요청 처리"""
        monthly_expenses = self.config["monthly_budget"]
        target_months = self.config["emergency_fund_months"]
        target_amount = monthly_expenses * target_months

        savings = sum(
            acc.balance for acc in self.accounts.values()
            if acc.account_type == "savings"
        )

        return {
            "current_savings": float(savings),
            "target_amount": float(target_amount),
            "progress_pct": float(savings / target_amount * 100) if target_amount else 0,
            "months_covered": float(savings / monthly_expenses) if monthly_expenses else 0
        }

    async def _schedule_recurring_tasks(self) -> None:
        """반복 작업 스케줄링"""
        # 매일 청구서 체크
        await self.add_task(
            "check_bills",
            "청구서 납부일 체크",
            Priority.NORMAL
        )

        # 매월 25일 DCA 실행
        if datetime.now().day == 25 and self.config["dca_enabled"]:
            await self.add_task(
                "execute_dca",
                "적립식 투자 실행",
                Priority.HIGH
            )
