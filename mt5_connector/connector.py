#!/usr/bin/env python3
import argparse
import base64
import json
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    import MetaTrader5 as mt5
except Exception as exc:
    mt5 = None  # type: ignore


def decode_config_b64(b64: str) -> dict:
    return json.loads(base64.b64decode(b64.encode()).decode())


def ema(values: List[float], period: int) -> List[float]:
    k = 2 / (period + 1)
    emas: List[float] = []
    prev: Optional[float] = None
    for v in values:
        prev = v if prev is None else (v - prev) * k + prev
        emas.append(prev)
    return emas


def rsi(closes: List[float], period: int) -> List[float]:
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    def sma(arr: List[float], p: int, idx: int) -> float:
        start = max(0, idx - p + 1)
        window = arr[start: idx + 1]
        return sum(window) / (len(window) or 1)
    rsis: List[float] = []
    for i in range(len(closes)):
        avg_gain = sma(gains, period, i)
        avg_loss = sma(losses, period, i)
        rs = (avg_gain / avg_loss) if avg_loss != 0 else 0.0
        val = 100 - (100 / (1 + rs)) if rs != 0 else 50.0
        rsis.append(val)
    return rsis


def true_range(h: float, l: float, pc: float) -> float:
    return max(h - l, abs(h - pc), abs(l - pc))


def atr(highs: List[float], lows: List[float], closes: List[float], period: int) -> List[float]:
    trs: List[float] = []
    for i in range(len(highs)):
        prev_close = closes[i - 1] if i > 0 else closes[i]
        trs.append(true_range(highs[i], lows[i], prev_close))
    # simple moving average for ATR for stability
    at: List[float] = []
    for i in range(len(trs)):
        start = max(0, i - period + 1)
        window = trs[start:i+1]
        at.append(sum(window) / len(window))
    return at


def timeframe_to_mt5(tf: str) -> int:
    mapping = {
        'M1': getattr(mt5, 'TIMEFRAME_M1', 1),
        'M5': getattr(mt5, 'TIMEFRAME_M5', 5),
        'M15': getattr(mt5, 'TIMEFRAME_M15', 15),
        'M30': getattr(mt5, 'TIMEFRAME_M30', 30),
        'H1': getattr(mt5, 'TIMEFRAME_H1', 60),
        'H4': getattr(mt5, 'TIMEFRAME_H4', 240),
        'D1': getattr(mt5, 'TIMEFRAME_D1', 1440),
    }
    return mapping.get(tf, getattr(mt5, 'TIMEFRAME_M15', 15))


@dataclass
class Config:
    symbols: List[str]
    timeframe: str
    riskPerTradePct: float
    maxOpenPositions: int
    emaFast: int
    emaSlow: int
    rsiPeriod: int
    atrPeriod: int
    atrStopMultiplier: float
    takeProfitRMultiple: float
    trailingStopATR: float
    dailyLossLimitPct: float
    maxDrawdownPct: float
    liveTrading: bool
    magicNumber: int


class PositionSizer:
    def __init__(self, balance: float, risk_pct: float):
        self.balance = balance
        self.risk_pct = risk_pct

    def lot_size(self, symbol: str, stop_pips: float) -> float:
        # Conservative fixed fraction position sizing
        # Assumes pip value ~ $10 per standard lot for majors; adjust via mt5.symbol_info if available
        if stop_pips <= 0:
            return 0.01
        risk_amount = self.balance * (self.risk_pct / 100.0)
        pip_value_per_lot = 10.0
        lots = max(0.01, min(5.0, risk_amount / (stop_pips * pip_value_per_lot)))
        return round(lots, 2)


def fetch_rates(symbol: str, tf: str, bars: int = 800):
    rates = mt5.copy_rates_from_pos(symbol, timeframe_to_mt5(tf), 0, bars)
    if rates is None:
        raise RuntimeError(f"Failed to fetch rates for {symbol}")
    closes = [float(r['close']) for r in rates]
    highs = [float(r['high']) for r in rates]
    lows = [float(r['low']) for r in rates]
    return rates, closes, highs, lows


def decide_signal(closes: List[float], highs: List[float], lows: List[float], cfg: Config) -> Tuple[str, Optional[float], Optional[float]]:
    efast = ema(closes, cfg.emaFast)
    eslow = ema(closes, cfg.emaSlow)
    rs = rsi(closes, cfg.rsiPeriod)
    at = atr(highs, lows, closes, cfg.atrPeriod)
    i = len(closes) - 1
    bias_up = efast[i] > eslow[i]
    bias_dn = efast[i] < eslow[i]
    oversold = rs[i] < 30
    overbought = rs[i] > 70

    if bias_up and oversold:
        stop = closes[i] - at[i] * cfg.atrStopMultiplier
        tp = closes[i] + (closes[i] - stop) * cfg.takeProfitRMultiple
        return ("BUY", stop, tp)
    if bias_dn and overbought:
        stop = closes[i] + at[i] * cfg.atrStopMultiplier
        tp = closes[i] - (stop - closes[i]) * cfg.takeProfitRMultiple
        return ("SELL", stop, tp)
    return ("HOLD", None, None)


def ensure_initialized():
    if mt5 is None:
        raise SystemExit("MetaTrader5 package not available. Install with: pip install MetaTrader5")
    if not mt5.initialize():
        raise SystemExit("Failed to initialize MT5 terminal. Ensure MT5 is installed and logged in.")


def place_order(symbol: str, action: str, lots: float, stop: float, tp: float, magic: int) -> bool:
    price = mt5.symbol_info_tick(symbol).ask if action == 'BUY' else mt5.symbol_info_tick(symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lots,
        'type': order_type,
        'price': price,
        'sl': stop,
        'tp': tp,
        'deviation': 20,
        'magic': magic,
        'comment': 'agentic-connector',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN,
    }
    result = mt5.order_send(request)
    return result is not None and result.retcode == mt5.TRADE_RETCODE_DONE


def manage_positions(symbol: str, cfg: Config, at_last: float):
    # Simple trailing stop using ATR multiple
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return
    tick = mt5.symbol_info_tick(symbol)
    for p in positions:
        if int(p.magic) != cfg.magicNumber:
            continue
        if p.type == mt5.POSITION_TYPE_BUY:
            new_sl = max(p.sl, tick.bid - cfg.trailingStopATR * at_last)
        else:
            new_sl = min(p.sl, tick.ask + cfg.trailingStopATR * at_last)
        if new_sl != p.sl:
            mt5.order_send({
                'action': mt5.TRADE_ACTION_SLTP,
                'position': p.ticket,
                'sl': new_sl,
                'tp': p.tp,
            })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-b64', type=str, required=True, help='Base64 JSON strategy config')
    parser.add_argument('--poll-seconds', type=int, default=30)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    cfg_dict = decode_config_b64(args.config_b64)
    cfg = Config(
        symbols=[s.strip().upper() for s in cfg_dict['symbols'].split(',') if s.strip()],
        timeframe=cfg_dict['timeframe'],
        riskPerTradePct=float(cfg_dict['riskPerTradePct']),
        maxOpenPositions=int(cfg_dict['maxOpenPositions']),
        emaFast=int(cfg_dict['emaFast']),
        emaSlow=int(cfg_dict['emaSlow']),
        rsiPeriod=int(cfg_dict['rsiPeriod']),
        atrPeriod=int(cfg_dict['atrPeriod']),
        atrStopMultiplier=float(cfg_dict['atrStopMultiplier']),
        takeProfitRMultiple=float(cfg_dict['takeProfitRMultiple']),
        trailingStopATR=float(cfg_dict['trailingStopATR']),
        dailyLossLimitPct=float(cfg_dict['dailyLossLimitPct']),
        maxDrawdownPct=float(cfg_dict['maxDrawdownPct']),
        liveTrading=(cfg_dict['liveTrading'] == 'true') and (not args.dry_run),
        magicNumber=int(cfg_dict['magicNumber']),
    )

    ensure_initialized()

    account_info = mt5.account_info()
    if account_info is None:
        raise SystemExit("Account info unavailable. Ensure you are logged in.")
    sizer = PositionSizer(balance=account_info.balance, risk_pct=cfg.riskPerTradePct)

    while True:
        for symbol in cfg.symbols:
            try:
                rates, closes, highs, lows = fetch_rates(symbol, cfg.timeframe)
                sig, stop, tp = decide_signal(closes, highs, lows, cfg)
                at_last = atr(highs, lows, closes, cfg.atrPeriod)[-1]
                manage_positions(symbol, cfg, at_last)

                if sig in ("BUY", "SELL") and stop is not None and tp is not None:
                    # simple check for number of open positions
                    positions = mt5.positions_get(symbol=symbol) or []
                    own_positions = [p for p in positions if int(p.magic) == cfg.magicNumber]
                    if len(own_positions) >= cfg.maxOpenPositions:
                        continue

                    stop_pips = abs(closes[-1] - stop) * 10000.0
                    lots = sizer.lot_size(symbol, stop_pips)
                    if cfg.liveTrading:
                        ok = place_order(symbol, sig, lots, stop, tp, cfg.magicNumber)
                        print(f"{symbol} {sig} lots={lots} sl={stop:.5f} tp={tp:.5f} -> {'OK' if ok else 'FAIL'}")
                    else:
                        print(f"DRYRUN {symbol} {sig} lots={lots} sl={stop:.5f} tp={tp:.5f}")
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        time.sleep(max(5, args.poll_seconds))


if __name__ == '__main__':
    main()
