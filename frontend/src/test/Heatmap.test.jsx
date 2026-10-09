import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Heatmap from '../components/Heatmap'

// 90 days ending 2026-10-08, like /api/heatmap returns (oldest first).
function makeDays() {
  const end = Date.UTC(2026, 9, 8)
  return Array.from({ length: 90 }, (_, i) => {
    const date = new Date(end - (89 - i) * 86_400_000).toISOString().slice(0, 10)
    return { date, count: i % 3 }
  })
}

describe('Heatmap', () => {
  it('renders 90 cells with today marked', () => {
    render(<Heatmap days={makeDays()} />)

    const cells = screen.getAllByTestId('heatmap-cell')
    expect(cells).toHaveLength(90)

    const todayCells = cells.filter((cell) => cell.dataset.today)
    expect(todayCells).toHaveLength(1)
    expect(todayCells[0]).toHaveAttribute('title', '2026-10-08: 2 solves')
  })

  it('shows the date and count in the tooltip', () => {
    render(<Heatmap days={[{ date: '2026-10-08', count: 1 }]} />)
    expect(screen.getByTitle('2026-10-08: 1 solve')).toBeInTheDocument()
  })
})
