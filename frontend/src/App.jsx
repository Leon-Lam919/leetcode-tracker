import { useState } from 'react'
import { getDueReviews, getHeatmap, getPatterns, getSolves, getStats } from './api'
import { useFetch } from './hooks/useFetch'
import AddSolveForm from './components/AddSolveForm'
import Filters from './components/Filters'
import Heatmap from './components/Heatmap'
import NoteEditor from './components/NoteEditor'
import PatternChecklist from './components/PatternChecklist'
import ReviewQueue from './components/ReviewQueue'
import SolveTable from './components/SolveTable'
import StatsPanel from './components/StatsPanel'
import Status from './components/Status'
import SyncButton from './components/SyncButton'
import TodayBanner from './components/TodayBanner'

const card = 'rounded-xl bg-white p-4 shadow-sm dark:bg-gray-800/60'
const NO_FILTERS = { difficulty: '', topic: '', needsReview: false }
const TABS = ['Today', 'Patterns']

export default function App() {
  // Bumping `version` makes every useFetch below load again (stats, heatmap, and solves).
  const [version, setVersion] = useState(0)
  const refresh = () => setVersion((v) => v + 1)

  const [filters, setFilters] = useState(NO_FILTERS)
  const [selected, setSelected] = useState(null) // solve being edited
  const [tab, setTab] = useState('Today')

  const stats = useFetch(getStats, version)
  const heatmap = useFetch(getHeatmap, version)
  const solves = useFetch(getSolves, version, filters)
  const reviews = useFetch(getDueReviews, version)
  const patterns = useFetch(getPatterns, version)

  const topics = Object.keys(stats.data?.by_topic ?? {}).sort()

  function handleSaved() {
    setSelected(null)
    refresh()
  }

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      <div className="mx-auto max-w-4xl space-y-4 p-4">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">LeetCode Tracker</h1>
          <SyncButton
            onSynced={refresh}
            lastSyncAt={stats.data?.last_sync_at}
            lastSyncResult={stats.data?.last_sync_result}
          />
        </header>

        <nav className="flex gap-2" aria-label="Sections">
          {TABS.map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => setTab(name)}
              aria-pressed={tab === name}
              className={`rounded-lg px-4 py-1 font-medium ${
                tab === name
                  ? 'bg-gray-800 text-white dark:bg-gray-200 dark:text-gray-900'
                  : 'bg-white text-gray-700 shadow-sm dark:bg-gray-800 dark:text-gray-200'
              }`}
            >
              {name}
            </button>
          ))}
        </nav>

        {tab === 'Patterns' && (
          <section className={card}>
            <Status {...patterns}>
              <PatternChecklist groups={patterns.data ?? []} />
            </Status>
          </section>
        )}

        {tab === 'Today' && (
          <>
            <Status {...stats}>
              <TodayBanner stats={stats.data} />
            </Status>

            <section className={card}>
              <Status {...reviews}>
                <ReviewQueue reviews={reviews.data ?? []} onReviewed={refresh} />
              </Status>
            </section>

            <div className="grid gap-4 md:grid-cols-2">
              <section className={card}>
                <h2 className="mb-2 font-semibold">Last 90 days</h2>
                <Status {...heatmap}>
                  <Heatmap days={heatmap.data ?? []} />
                </Status>
              </section>
              <section className={card}>
                <Status {...stats}>
                  <StatsPanel stats={stats.data} />
                </Status>
              </section>
            </div>

            <section className={card}>
              <AddSolveForm onAdded={refresh} />
            </section>

            {selected && (
              <NoteEditor
                key={selected.id} // fresh form state when a different row is picked
                solve={selected}
                onSaved={handleSaved}
                onClose={() => setSelected(null)}
              />
            )}

            <section className={`${card} space-y-3`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">Solves</h2>
                <Filters filters={filters} topics={topics} onChange={setFilters} />
              </div>
              <Status {...solves}>
                <SolveTable solves={solves.data ?? []} onSelect={setSelected} />
              </Status>
            </section>
          </>
        )}
      </div>
    </main>
  )
}
