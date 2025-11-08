import StrategyForm from '@/components/StrategyForm';

export default function Page() {
  return (
    <main className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">AI Forex Trading Bot</h1>
        <a
          href="https://agentic-5f2e9c6e.vercel.app"
          className="text-sm text-indigo-400 hover:text-indigo-300"
        >
          Production URL
        </a>
      </header>
      <p className="text-slate-300">
        Configure your strategy and generate the Python connector command for MetaTrader 5.
      </p>
      <StrategyForm />
    </main>
  );
}
