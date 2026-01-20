"""
MIRKWOOD Structuring Agent (Lite / Assumed Mode)

[UX Goal]
Telegram에서 "엄지손가락 몇 번"으로 구조화 시뮬레이션 완료.
사용자 입력 최소화:
  1) 상품 타입 (RCPS/CB/BW) - 버튼
  2) 주가, 총주식수 - 텍스트 (예: 5000 1000000)
  3) 투자금(억 원) - 텍스트 (예: 10)
  4) (옵션) 변동성만 직접 입력할지 선택

[Market Standard Defaults]
- 만기: 3년
- 변동성: 30%
- 무위험이자율: 3.5%
- 행사가: 현재 주가 (ATM)
- 채권 할인율: 8% (High Yield proxy)
- Refixing: 옵션가치 +10% 프리미엄 (휴리스틱)

NOTE: 본 모듈은 Quick Estimate 용도이며, TF/라티스 기반 OPM과는 별개입니다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


def _to_float(text: str) -> Optional[float]:
    if text is None:
        return None
    try:
        t = text.strip().replace(",", "").replace("_", "")
        return float(t)
    except Exception:
        return None


def _norm_cdf(x: float) -> float:
    # Standard normal CDF via erf (no scipy dependency)
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call_price(S: float, K: float, r: float, T: float, sigma: float) -> float:
    """Black-Scholes call option price (no dividends), per-share."""
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return 0.0
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    except Exception:
        return 0.0


def _fmt_uk(krw: float) -> str:
    """KRW -> 억 원 표시"""
    try:
        return f"{krw / 1e8:,.1f}억"
    except Exception:
        return "N/A"


@dataclass
class StructInputs:
    sec_type: str
    price_krw: float
    shares: float
    amount_uk: float  # 억 원
    sigma: float
    T: float = 3.0
    rf: float = 0.035
    bond_yield: float = 0.08
    refix_premium: float = 0.10


class StructuringAgent:
    TYPE, PRICE_SHARES, AMOUNT, VOL_CHECK, CUSTOM_VOL = range(5)

    def __init__(self):
        self.default_sigma = 0.30

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[
            InlineKeyboardButton("RCPS", callback_data="TYPE:RCPS"),
            InlineKeyboardButton("CB", callback_data="TYPE:CB"),
            InlineKeyboardButton("BW", callback_data="TYPE:BW"),
        ]]
        await update.message.reply_text(
            "🏗️ **구조화 시뮬레이션**을 시작합니다. 상품 타입을 선택하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return self.TYPE

    async def receive_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        data = (q.data or "").strip()

        if not data.startswith("TYPE:"):
            await q.edit_message_text("⚠️ 타입 선택을 다시 해주세요.")
            return self.TYPE

        sec_type = data.split(":", 1)[1].strip().upper()
        if sec_type not in {"RCPS", "CB", "BW"}:
            await q.edit_message_text("⚠️ 지원되지 않는 타입입니다. 다시 선택해 주세요.")
            return self.TYPE

        context.user_data["sec_type"] = sec_type
        await q.edit_message_text(
            f"✅ {sec_type} 선택.\n"
            "현재 **주가**와 **발행주식총수**를 띄어쓰기로 입력해주세요.\n"
            "(예: `5000 1000000`)",
            parse_mode="Markdown",
        )
        return self.PRICE_SHARES

    async def receive_price_shares(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (update.message.text or "").strip()
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("⚠️ 입력 형식: `주가 총주식수` (예: `5000 1000000`)", parse_mode="Markdown")
            return self.PRICE_SHARES

        price = _to_float(parts[0])
        shares = _to_float(parts[1])
        if price is None or shares is None or price <= 0 or shares <= 0:
            await update.message.reply_text("⚠️ 숫자만 입력해주세요. 예: `5000 1000000`", parse_mode="Markdown")
            return self.PRICE_SHARES

        context.user_data["price_krw"] = float(price)
        context.user_data["shares"] = float(shares)

        marketcap_krw = float(price) * float(shares)
        context.user_data["pre_money_krw"] = marketcap_krw

        await update.message.reply_text(
            f"📊 현재 시가총액: **{_fmt_uk(marketcap_krw)} 원**\n"
            "투자(발행) 금액은 얼마입니까? (억 원 단위, 숫자만)\n"
            "예: `10`",
            parse_mode="Markdown",
        )
        return self.AMOUNT

    async def receive_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        amount = _to_float((update.message.text or "").strip())
        if amount is None or amount <= 0:
            await update.message.reply_text("⚠️ 억 원 단위 숫자만 입력해주세요. 예: `10`", parse_mode="Markdown")
            return self.AMOUNT

        context.user_data["amount_uk"] = float(amount)

        keyboard = [[
            InlineKeyboardButton("표준 적용 (30%)", callback_data="VOL:STD"),
            InlineKeyboardButton("직접 입력", callback_data="VOL:CUSTOM"),
        ]]

        await update.message.reply_text(
            f"💰 발행금액 **{amount:,.1f}억 원** 확인.\n"
            "나머지 조건은 **시장 표준(만기 3년, 변동성 30%, ATM)**을 적용할까요?\n"
            "아니면 **변동성(Volatility)**을 직접 입력하시겠습니까?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return self.VOL_CHECK

    async def receive_vol_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        data = (q.data or "").strip()

        if data == "VOL:STD":
            context.user_data["sigma"] = self.default_sigma
            report = self._build_report(context)
            await q.edit_message_text(report, parse_mode=None)
            return -1

        if data == "VOL:CUSTOM":
            await q.edit_message_text("적용할 변동성을 % 단위로 입력하세요. (예: 45)")
            return self.CUSTOM_VOL

        await q.edit_message_text("⚠️ 선택을 다시 해주세요.")
        return self.VOL_CHECK

    async def receive_custom_vol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        vol = _to_float((update.message.text or "").strip())
        if vol is None or vol <= 0 or vol > 200:
            await update.message.reply_text("⚠️ 변동성(%) 숫자를 입력해주세요. 예: `45`", parse_mode="Markdown")
            return self.CUSTOM_VOL

        context.user_data["sigma"] = float(vol) / 100.0
        report = self._build_report(context)
        await update.message.reply_text(report, parse_mode=None)
        return -1

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text("🛑 구조화 시뮬레이션을 취소했습니다.")
        return -1

    def _build_report(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        sec_type = str(context.user_data.get("sec_type") or "N/A")
        price_krw = float(context.user_data.get("price_krw") or 0.0)
        shares = float(context.user_data.get("shares") or 0.0)
        amount_uk = float(context.user_data.get("amount_uk") or 0.0)
        sigma = float(context.user_data.get("sigma") or self.default_sigma)

        inp = StructInputs(
            sec_type=sec_type,
            price_krw=price_krw,
            shares=shares,
            amount_uk=amount_uk,
            sigma=sigma,
        )

        pre_money_krw = inp.price_krw * inp.shares
        amount_krw = inp.amount_uk * 1e8
        post_money_krw = pre_money_krw + amount_krw

        # Bond floor (HY proxy discount)
        bond_val_krw = amount_krw / ((1.0 + inp.bond_yield) ** inp.T)

        # Option value (ATM call, conversion shares ~= amount/price)
        K = inp.price_krw
        conv_shares = amount_krw / K if K > 0 else 0.0
        call_per_share = _bs_call_price(S=inp.price_krw, K=K, r=inp.rf, T=inp.T, sigma=inp.sigma)
        option_val_krw = call_per_share * conv_shares
        option_val_krw = option_val_krw * (1.0 + inp.refix_premium)

        total_val_krw = bond_val_krw + option_val_krw
        upside_pct = ((total_val_krw / amount_krw) - 1.0) * 100 if amount_krw > 0 else 0.0

        vol_pct = inp.sigma * 100.0

        return "\n".join([
            "🌲 MIRKWOOD Structuring Report",
            "--------------------------------",
            f"• 상품: {inp.sec_type} | 투자금: {inp.amount_uk:,.1f}억",
            f"• Pre-Money Val : {_fmt_uk(pre_money_krw)} 원",
            f"• Post-Money Val: {_fmt_uk(post_money_krw)} 원",
            "--------------------------------",
            "[이론적 가치 평가]",
            f"1. 채권 가치 (Bond Floor): {_fmt_uk(bond_val_krw)} 원",
            f"2. 옵션 가치 (w/ Refixing): {_fmt_uk(option_val_krw)} 원",
            f"👉 총 이론 가치: {_fmt_uk(total_val_krw)} 원 ({upside_pct:,.1f}% Premium)",
            "--------------------------------",
            f"*가정: 만기 3년, 변동성 {vol_pct:.1f}%, 무위험 3.5%, ATM, 리픽싱 +10%*",
            "*주의: 시장 표준 가정 기반 Quick Estimate*",
        ])

"""
MIRKWOOD Structuring Agent (Lite)

[Goal]
Telegram UX 최적화: "산더미 같은 변수 입력" 제거.
유저는 핵심 3가지만 입력:
  1) 상품 타입 (RCPS / CB / BW)
  2) 현재 주가 & 총주식수
  3) 투자(발행) 금액(억 원)

[Market Standard Assumptions]
- 변동성: 30% (KOSDAQ 평균 가정)
- 만기: 3년
- 무위험이자율: 3.5%
- 행사가: 현재 주가 (ATM)
- 리픽싱: 옵션가치 10% 프리미엄(휴리스틱)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


def _to_float(text: str) -> Optional[float]:
    if text is None:
        return None
    try:
        t = text.strip().replace(",", "").replace("_", "")
        return float(t)
    except Exception:
        return None


def _fmt_krw_ukr(value_krw: float) -> str:
    """KRW -> 억 원 string"""
    try:
        return f"{value_krw / 1e8:,.1f}억"
    except Exception:
        return "N/A"


def _norm_cdf(x: float) -> float:
    # Standard normal CDF using erf (no scipy dependency)
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call_price(S: float, K: float, r: float, T: float, sigma: float) -> float:
    """
    Black-Scholes call option price (no dividends).
    Returns price per share.
    """
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return 0.0
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    except Exception:
        return 0.0


@dataclass
class StructInputs:
    sec_type: str
    price_krw: float
    shares: float
    amount_uk: float  # 억 원
    sigma: float
    T: float = 3.0
    rf: float = 0.035
    bond_yield: float = 0.08
    refix_premium: float = 0.10


class StructuringAgent:
    # Conversation states
    TYPE, PRICE_SHARES, AMOUNT, VOL_CHECK, CUSTOM_VOL = range(5)

    def __init__(self):
        # Defaults (Market Standards)
        self.default_sigma = 0.30

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                InlineKeyboardButton("RCPS", callback_data="TYPE:RCPS"),
                InlineKeyboardButton("CB", callback_data="TYPE:CB"),
                InlineKeyboardButton("BW", callback_data="TYPE:BW"),
            ]
        ]
        await update.message.reply_text(
            "🏗️ **구조화 시뮬레이션**을 시작합니다.\n상품 타입을 선택하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return self.TYPE

    async def receive_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()

        data = q.data or ""
        if not data.startswith("TYPE:"):
            await q.edit_message_text("⚠️ 타입 선택을 다시 해주세요.")
            return self.TYPE

        sec_type = data.split(":", 1)[1].strip().upper()
        if sec_type not in {"RCPS", "CB", "BW"}:
            await q.edit_message_text("⚠️ 지원되지 않는 타입입니다. 다시 선택해 주세요.")
            return self.TYPE

        context.user_data["sec_type"] = sec_type
        await q.edit_message_text(
            f"✅ {sec_type} 선택.\n\n"
            "현재 **주가**와 **발행주식총수**를 띄어쓰기로 입력해주세요.\n"
            "(예: `5000 1000000` → 5천원, 100만주)",
            parse_mode="Markdown",
        )
        return self.PRICE_SHARES

    async def receive_price_shares(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (update.message.text or "").strip()
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("⚠️ 입력 형식이 잘못되었습니다. 예: `5000 1000000`", parse_mode="Markdown")
            return self.PRICE_SHARES

        price = _to_float(parts[0])
        shares = _to_float(parts[1])
        if price is None or shares is None or price <= 0 or shares <= 0:
            await update.message.reply_text("⚠️ 숫자만 입력해주세요. 예: `5000 1000000`", parse_mode="Markdown")
            return self.PRICE_SHARES

        context.user_data["price_krw"] = float(price)
        context.user_data["shares"] = float(shares)

        marketcap_krw = float(price) * float(shares)
        context.user_data["pre_money_krw"] = marketcap_krw

        await update.message.reply_text(
            f"📊 현재 시가총액: **{_fmt_krw_ukr(marketcap_krw)} 원**\n\n"
            "투자(발행) 금액은 얼마입니까?\n"
            "(억 원 단위, 숫자만 입력. 예: `10`)",
            parse_mode="Markdown",
        )
        return self.AMOUNT

    async def receive_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        amount = _to_float((update.message.text or "").strip())
        if amount is None or amount <= 0:
            await update.message.reply_text("⚠️ 억 원 단위 숫자만 입력해주세요. 예: `10`", parse_mode="Markdown")
            return self.AMOUNT

        context.user_data["amount_uk"] = float(amount)

        keyboard = [
            [
                InlineKeyboardButton("표준 적용 (30%)", callback_data="VOL:STD"),
                InlineKeyboardButton("직접 입력", callback_data="VOL:CUSTOM"),
            ]
        ]
        await update.message.reply_text(
            f"💰 발행금액 **{amount:,.1f}억 원** 확인.\n\n"
            "나머지 조건은 **시장 표준(만기 3년, 변동성 30%, ATM)**을 적용할까요?\n"
            "아니면 **변동성(Volatility)**을 직접 입력하시겠습니까?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return self.VOL_CHECK

    async def receive_vol_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        data = q.data or ""

        if data == "VOL:STD":
            context.user_data["sigma"] = self.default_sigma
            report = self._calculate_report(context)
            await q.edit_message_text(report, parse_mode=None)
            return -1  # ConversationHandler.END

        if data == "VOL:CUSTOM":
            await q.edit_message_text("적용할 변동성을 % 단위로 입력하세요. (예: 45)")
            return self.CUSTOM_VOL

        await q.edit_message_text("⚠️ 선택을 다시 해주세요.")
        return self.VOL_CHECK

    async def receive_custom_vol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        vol = _to_float((update.message.text or "").strip())
        if vol is None or vol <= 0 or vol > 200:
            await update.message.reply_text("⚠️ 변동성(%) 숫자를 입력해주세요. 예: `45`", parse_mode="Markdown")
            return self.CUSTOM_VOL

        context.user_data["sigma"] = float(vol) / 100.0
        report = self._calculate_report(context)
        await update.message.reply_text(report, parse_mode=None)
        return -1  # ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text("🛑 구조화 시뮬레이션을 취소했습니다.")
        return -1  # ConversationHandler.END

    # --------------------------
    # Core math & formatting
    # --------------------------
    def _calculate_report(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        sec_type = str(context.user_data.get("sec_type") or "N/A")
        price_krw = float(context.user_data.get("price_krw") or 0.0)
        shares = float(context.user_data.get("shares") or 0.0)
        amount_uk = float(context.user_data.get("amount_uk") or 0.0)
        sigma = float(context.user_data.get("sigma") or self.default_sigma)

        inp = StructInputs(
            sec_type=sec_type,
            price_krw=price_krw,
            shares=shares,
            amount_uk=amount_uk,
            sigma=sigma,
        )

        pre_money_krw = inp.price_krw * inp.shares
        amount_krw = inp.amount_uk * 1e8
        post_money_krw = pre_money_krw + amount_krw

        # 1) Bond floor (high-yield proxy)
        bond_val_krw = amount_krw / ((1.0 + inp.bond_yield) ** inp.T)

        # 2) Option value (conversion assumed at ATM)
        K = inp.price_krw
        call_per_share = _bs_call_price(
            S=inp.price_krw,
            K=K,
            r=inp.rf,
            T=inp.T,
            sigma=inp.sigma,
        )
        conv_shares = amount_krw / K if K > 0 else 0.0
        option_val_krw = call_per_share * conv_shares

        # 3) Refixing premium heuristic
        option_val_krw_refix = option_val_krw * (1.0 + inp.refix_premium)

        total_val_krw = bond_val_krw + option_val_krw_refix
        upside_pct = ((total_val_krw / amount_krw) - 1.0) * 100 if amount_krw > 0 else 0.0

        vol_pct = inp.sigma * 100

        lines = []
        lines.append("🌲 MIRKWOOD Structuring Report")
        lines.append("--------------------------------")
        lines.append(f"• 상품: {inp.sec_type} | 투자금: {inp.amount_uk:,.1f}억")
        lines.append(f"• Pre-Money Val : {_fmt_krw_ukr(pre_money_krw)} 원")
        lines.append(f"• Post-Money Val: {_fmt_krw_ukr(post_money_krw)} 원")
        lines.append("--------------------------------")
        lines.append("[이론적 가치 평가]")
        lines.append(f"1. 채권 가치 (Bond Floor): {_fmt_krw_ukr(bond_val_krw)} 원")
        lines.append(f"2. 옵션 가치 (w/ Refixing): {_fmt_krw_ukr(option_val_krw_refix)} 원")
        lines.append(f"👉 총 이론 가치: {_fmt_krw_ukr(total_val_krw)} 원 ({upside_pct:,.1f}% Premium)")
        lines.append("--------------------------------")
        lines.append(f"*가정: 만기 3년, 변동성 {vol_pct:.1f}%, 무위험 3.5%, ATM, 리픽싱 프리미엄 10%*")
        lines.append("*주의: 본 결과는 '시장 표준 가정' 기반의 Quick Estimate 입니다.*")

        return "\n".join(lines)

