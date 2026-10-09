const selectClass =
  'rounded border border-gray-300 bg-white p-1 text-sm dark:border-gray-600 dark:bg-gray-800'

// filters: { difficulty: '', topic: '', needsReview: false }
export default function Filters({ filters, topics, onChange }) {
  function update(field, value) {
    onChange({ ...filters, [field]: value })
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        aria-label="Difficulty filter"
        value={filters.difficulty}
        onChange={(event) => update('difficulty', event.target.value)}
        className={selectClass}
      >
        <option value="">All difficulties</option>
        <option>Easy</option>
        <option>Medium</option>
        <option>Hard</option>
      </select>

      <select
        aria-label="Topic filter"
        value={filters.topic}
        onChange={(event) => update('topic', event.target.value)}
        className={selectClass}
      >
        <option value="">All topics</option>
        {topics.map((topic) => (
          <option key={topic}>{topic}</option>
        ))}
      </select>

      <label className="flex items-center gap-1 text-sm">
        <input
          type="checkbox"
          checked={filters.needsReview}
          onChange={(event) => update('needsReview', event.target.checked)}
        />
        Needs review
      </label>
    </div>
  )
}
