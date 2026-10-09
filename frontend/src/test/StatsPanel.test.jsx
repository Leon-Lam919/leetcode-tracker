import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import StatsPanel from '../components/StatsPanel'

describe('StatsPanel', () => {
  it('shows totals and only the top 5 topics', () => {
    const stats = {
      total_solved: 12,
      by_difficulty: { Easy: 7, Medium: 4, Hard: 1 },
      by_topic: { Array: 6, 'Hash Table': 5, String: 4, Stack: 3, Math: 2, Graph: 1 },
    }
    render(<StatsPanel stats={stats} />)

    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('Medium 4')).toBeInTheDocument()
    expect(screen.getByText('Math')).toBeInTheDocument()
    expect(screen.queryByText('Graph')).not.toBeInTheDocument()
  })
})
