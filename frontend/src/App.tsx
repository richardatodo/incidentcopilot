import { Activity, ShieldCheck } from 'lucide-react'

function App() {
  return (
    <main className="min-h-screen bg-[#0f1115] text-gray-100">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-8">
        <header className="flex items-center justify-between border-b border-gray-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800 p-2">
              <Activity className="h-6 w-6 text-gray-300" />
            </div>

            <div>
              <h1 className="text-xl font-semibold">IncidentCopilot</h1>
              <p className="text-sm text-gray-400">
                AI DevOps Incident Investigation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-400">
            <ShieldCheck className="h-4 w-4" />
            Local environment
          </div>
        </header>

        <section className="flex flex-1 items-center justify-center">
          <div className="max-w-2xl text-center">
            <p className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-500">
              Milestone 1
            </p>

            <h2 className="text-4xl font-bold tracking-tight">
              Incident investigation foundation
            </h2>

            <p className="mt-4 text-lg leading-8 text-gray-400">
              The local development foundation for IncidentCopilot is ready.
              Incident ingestion, correlation, RAG, AI diagnosis, and the full
              dashboard will be implemented in later milestones.
            </p>

            <div className="mt-8 inline-flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 px-4 py-3 text-sm text-gray-300">
              <Activity className="h-4 w-4" />
              Development environment ready
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}

export default App
