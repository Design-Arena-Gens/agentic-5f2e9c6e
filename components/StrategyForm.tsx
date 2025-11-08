"use client";

import React from 'react';
import { z } from 'zod';
import { Input, Label, Section, Select, TextArea } from './Field';

const StrategySchema = z.object({
  symbols: z.string().default('EURUSD,GBPUSD'),
  timeframe: z.enum(['M1','M5','M15','M30','H1','H4','D1']).default('M15'),
  riskPerTradePct: z.coerce.number().min(0).max(10).default(1),
  maxOpenPositions: z.coerce.number().int().min(1).max(20).default(3),
  emaFast: z.coerce.number().int().min(2).max(200).default(50),
  emaSlow: z.coerce.number().int().min(5).max(400).default(200),
  rsiPeriod: z.coerce.number().int().min(2).max(50).default(14),
  atrPeriod: z.coerce.number().int().min(5).max(100).default(14),
  atrStopMultiplier: z.coerce.number().min(0.1).max(10).default(2.0),
  takeProfitRMultiple: z.coerce.number().min(0.1).max(10).default(2.0),
  trailingStopATR: z.coerce.number().min(0).max(10).default(1.5),
  dailyLossLimitPct: z.coerce.number().min(0).max(50).default(5),
  maxDrawdownPct: z.coerce.number().min(0).max(90).default(20),
  liveTrading: z.enum(['false','true']).default('false'),
  magicNumber: z.coerce.number().int().min(1).max(999999).default(424242),
});

export type StrategyConfig = z.infer<typeof StrategySchema>;

function toBase64(json: unknown) {
  return typeof window === 'undefined'
    ? ''
    : btoa(unescape(encodeURIComponent(JSON.stringify(json))));
}

export default function StrategyForm() {
  const [form, setForm] = React.useState<StrategyConfig>({
    symbols: 'EURUSD,GBPUSD',
    timeframe: 'M15',
    riskPerTradePct: 1,
    maxOpenPositions: 3,
    emaFast: 50,
    emaSlow: 200,
    rsiPeriod: 14,
    atrPeriod: 14,
    atrStopMultiplier: 2,
    takeProfitRMultiple: 2,
    trailingStopATR: 1.5,
    dailyLossLimitPct: 5,
    maxDrawdownPct: 20,
    liveTrading: 'false',
    magicNumber: 424242,
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target as { name: keyof StrategyConfig; value: string };
    setForm((prev) => ({ ...prev, [name]: value } as StrategyConfig));
  };

  const parsed = StrategySchema.safeParse(form);
  const b64 = parsed.success ? toBase64(parsed.data) : '';
  const pythonCmd = parsed.success
    ? `python mt5_connector/connector.py --config-b64 '${b64}'`
    : '';

  return (
    <div className="space-y-6">
      <Section title="Symbols & Timeframe">
        <div>
          <Label htmlFor="symbols">Symbols (comma-separated)</Label>
          <Input id="symbols" name="symbols" value={form.symbols} onChange={handleChange} />
        </div>
        <div>
          <Label htmlFor="timeframe">Timeframe</Label>
          <Select id="timeframe" name="timeframe" value={form.timeframe} onChange={handleChange}>
            {['M1','M5','M15','M30','H1','H4','D1'].map((tf) => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </Select>
        </div>
      </Section>

      <Section title="Risk & Limits">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="riskPerTradePct">Risk per trade (%)</Label>
            <Input id="riskPerTradePct" name="riskPerTradePct" type="number" step="0.1" value={form.riskPerTradePct} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="maxOpenPositions">Max open positions</Label>
            <Input id="maxOpenPositions" name="maxOpenPositions" type="number" value={form.maxOpenPositions} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="dailyLossLimitPct">Daily loss limit (%)</Label>
            <Input id="dailyLossLimitPct" name="dailyLossLimitPct" type="number" step="0.1" value={form.dailyLossLimitPct} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="maxDrawdownPct">Max drawdown (%)</Label>
            <Input id="maxDrawdownPct" name="maxDrawdownPct" type="number" step="0.1" value={form.maxDrawdownPct} onChange={handleChange} />
          </div>
        </div>
      </Section>

      <Section title="Indicators & Exits">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="emaFast">EMA fast</Label>
            <Input id="emaFast" name="emaFast" type="number" value={form.emaFast} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="emaSlow">EMA slow</Label>
            <Input id="emaSlow" name="emaSlow" type="number" value={form.emaSlow} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="rsiPeriod">RSI period</Label>
            <Input id="rsiPeriod" name="rsiPeriod" type="number" value={form.rsiPeriod} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="atrPeriod">ATR period</Label>
            <Input id="atrPeriod" name="atrPeriod" type="number" value={form.atrPeriod} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="atrStopMultiplier">ATR stop multiplier</Label>
            <Input id="atrStopMultiplier" name="atrStopMultiplier" type="number" step="0.1" value={form.atrStopMultiplier} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="takeProfitRMultiple">Take-profit R multiple</Label>
            <Input id="takeProfitRMultiple" name="takeProfitRMultiple" type="number" step="0.1" value={form.takeProfitRMultiple} onChange={handleChange} />
          </div>
          <div>
            <Label htmlFor="trailingStopATR">Trailing stop (ATR x)</Label>
            <Input id="trailingStopATR" name="trailingStopATR" type="number" step="0.1" value={form.trailingStopATR} onChange={handleChange} />
          </div>
        </div>
      </Section>

      <Section title="Execution">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="liveTrading">Live trading</Label>
            <Select id="liveTrading" name="liveTrading" value={form.liveTrading} onChange={handleChange}>
              <option value="false">Disabled (dry run)</option>
              <option value="true">Enabled</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="magicNumber">Magic number</Label>
            <Input id="magicNumber" name="magicNumber" type="number" value={form.magicNumber} onChange={handleChange} />
          </div>
        </div>
      </Section>

      <Section title="Connector Command">
        <div>
          <Label htmlFor="b64">Base64 config</Label>
          <TextArea id="b64" readOnly rows={3} value={b64} />
        </div>
        <div>
          <Label htmlFor="cmd">Run this command on your MT5 machine</Label>
          <TextArea id="cmd" readOnly rows={2} value={pythonCmd} />
        </div>
      </Section>
    </div>
  );
}
