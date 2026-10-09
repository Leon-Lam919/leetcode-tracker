import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import TodayBanner from '../components/TodayBanner'

const baseStats = { today_count: 0, daily_goal: 1, current_streak: 4, longest_streak: 9 }

describe('TodayBanner', () => {
  it('shows done when today has a solve', () => {
    render(<TodayBanner stats={{ ...baseStats, today_done: true, today_count: 1 }} />)
    expect(screen.getByText('✅ Done today')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument() // current streak
    expect(screen.getByText('9')).toBeInTheDocument() // best streak
  })

  it('shows not yet when today has no solve', () => {
    render(<TodayBanner stats={{ ...baseStats, today_done: false }} />)
    expect(screen.getByText('❌ Not yet today')).toBeInTheDocument()
    expect(screen.queryByText('✅ Done today')).not.toBeInTheDocument()
  })
})
