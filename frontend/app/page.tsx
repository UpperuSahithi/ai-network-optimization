import BackendStatus from "./BackendStatus";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 px-6 py-16 text-slate-900">
      <div className="mx-auto max-w-xl">
        <BackendStatus />

        <h1 className="text-3xl font-semibold tracking-tight">
          AI Network Optimization
        </h1>
        <p className="mt-2 text-lg text-slate-600">
          Reinforcement Learning Based Network Optimization
        </p>

        <section className="mt-10 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-medium">Network Configuration</h2>

          <div className="mt-6 flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm font-medium">
              Number of Nodes
              <input
                type="number"
                name="numberOfNodes"
                min={1}
                defaultValue={10}
                className="rounded-md border border-slate-300 px-3 py-2 text-base font-normal"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium">
              Traffic Load
              <input
                type="number"
                name="trafficLoad"
                min={0}
                defaultValue={50}
                className="rounded-md border border-slate-300 px-3 py-2 text-base font-normal"
              />
            </label>
          </div>

          <button
            type="button"
            className="mt-6 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white"
          >
            Run Simulation
          </button>
        </section>
      </div>
    </main>
  );
}
