"""
Risk Manager Service
Calculates position sizes, validates trades, manages daily limits.
"""
from typing import Optional, Tuple
from loguru import logger


# Binance minimum order sizes (notional in USDT)
EXCHANGE_MINIMUMS = {
    "BTC/USDT": {"min_notional": 5.0, "min_qty": 0.00001},
    "ETH/USDT": {"min_notional": 5.0, "min_qty": 0.0001},
    "SOL/USDT": {"min_notional": 1.0, "min_qty": 0.01},
    "DEFAULT":  {"min_notional": 1.0, "min_qty": 0.001}
}

MAKER_FEE = 0.001   # 0.1% Binance spot fee
TAKER_FEE = 0.001


class RiskManager:
    def __init__(
        self,
        initial_balance: float,
        max_risk_per_trade: float = 0.02,
        daily_loss_limit: float = 0.05
    ):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.max_risk_per_trade = max_risk_per_trade
        self.daily_loss_limit = daily_loss_limit
        self.daily_pnl = 0.0
        self.daily_start_balance = initial_balance

    def update_balance(self, new_balance: float):
        self.current_balance = new_balance

    def update_daily_pnl(self, pnl: float):
        self.daily_pnl += pnl

    def reset_daily(self):
        self.daily_pnl = 0.0
        self.daily_start_balance = self.current_balance

    @property
    def is_daily_limit_breached(self) -> bool:
        daily_loss_pct = self.daily_pnl / self.daily_start_balance if self.daily_start_balance > 0 else 0
        return daily_loss_pct < -self.daily_loss_limit

    def max_loss_amount(self) -> float:
        """Maximum dollar amount we're willing to lose per trade."""
        return self.current_balance * self.max_risk_per_trade

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        symbol: str
    ) -> Tuple[float, float, str]:
        """
        Calculate position size using fixed fractional method.
        Returns: (quantity, notional_value, error_message)
        
        Formula: quantity = risk_amount / (entry - stop_loss)
        """
        if stop_loss_price >= entry_price:
            return 0.0, 0.0, "Stop loss must be below entry price for long trades"

        risk_per_unit = entry_price - stop_loss_price
        if risk_per_unit <= 0:
            return 0.0, 0.0, "Invalid risk per unit"

        risk_amount = self.max_loss_amount()
        raw_quantity = risk_amount / risk_per_unit

        notional = raw_quantity * entry_price

        # Check if notional is affordable (max 50% of balance per trade)
        max_notional = self.current_balance * 0.5
        if notional > max_notional:
            raw_quantity = max_notional / entry_price
            notional = max_notional

        # Check exchange minimums
        mins = EXCHANGE_MINIMUMS.get(symbol, EXCHANGE_MINIMUMS["DEFAULT"])
        if notional < mins["min_notional"]:
            return 0.0, 0.0, f"Notional {notional:.4f} below minimum {mins['min_notional']} USDT"

        if raw_quantity < mins["min_qty"]:
            return 0.0, 0.0, f"Quantity {raw_quantity:.8f} below minimum {mins['min_qty']}"

        # Round quantity appropriately
        if symbol.startswith("BTC"):
            quantity = round(raw_quantity, 5)
        elif symbol.startswith("ETH"):
            quantity = round(raw_quantity, 4)
        else:
            quantity = round(raw_quantity, 2)

        # Ensure we have enough balance
        required = (quantity * entry_price) * (1 + TAKER_FEE)
        if required > self.current_balance:
            return 0.0, 0.0, f"Insufficient balance: need {required:.4f}, have {self.current_balance:.4f}"

        logger.info(
            f"[Risk] {symbol} | Entry={entry_price} SL={stop_loss_price} | "
            f"Risk={risk_amount:.4f} USDT | Qty={quantity} | Notional={notional:.4f} USDT"
        )

        return quantity, quantity * entry_price, ""

    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        side: str = "buy",
        atr_multiplier: float = 1.5
    ) -> float:
        """Calculate ATR-based stop loss."""
        if side == "buy":
            return round(entry_price - (atr * atr_multiplier), 8)
        else:
            return round(entry_price + (atr * atr_multiplier), 8)

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        side: str = "buy",
        risk_reward: float = 2.0
    ) -> float:
        """Calculate take profit based on risk-reward ratio."""
        risk = abs(entry_price - stop_loss)
        if side == "buy":
            return round(entry_price + (risk * risk_reward), 8)
        else:
            return round(entry_price - (risk * risk_reward), 8)

    def validate_trade(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float
    ) -> Tuple[bool, str]:
        """Final validation before placing a trade."""

        if self.is_daily_limit_breached:
            return False, "Daily loss limit reached, bot paused"

        if self.current_balance < 2.0:
            return False, "Balance too low to trade safely"

        # Validate SL/TP
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        if risk == 0:
            return False, "Invalid stop loss (same as entry)"

        rr = reward / risk
        if rr < 1.5:
            return False, f"Risk/reward ratio {rr:.2f} too low (min 1.5)"

        loss_amount = quantity * abs(entry_price - stop_loss)
        loss_pct = loss_amount / self.current_balance
        if loss_pct > self.max_risk_per_trade * 1.5:
            return False, f"Trade risk {loss_pct:.2%} exceeds max {self.max_risk_per_trade:.2%}"

        return True, "OK"

    def calculate_fee(self, notional: float, is_maker: bool = False) -> float:
        fee_rate = MAKER_FEE if is_maker else TAKER_FEE
        return notional * fee_rate


# Singleton instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager(balance: float = 10.0) -> RiskManager:
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager(
            initial_balance=balance,
            max_risk_per_trade=0.02,
            daily_loss_limit=0.05
        )
    return _risk_manager
