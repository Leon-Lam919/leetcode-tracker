import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SolveTable from '../components/SolveTable'

const base = {
  title_slug: 'two-sum',
  difficulty: 'Easy',
  url: 'https://leetcode.com/problems/two-sum/',
  solved_date: '2026-10-08',
  topics: [],
  confidence: null,
  needs_review: false,
  approach: null,
  code: null,
}

describe('SolveTable', () => {
  it('marks only solves that have a written solution', () => {
    const solves = [
      { ...base, id: 1, title: 'Two Sum', approach: 'hash map' },
      { ...base, id: 2, title: '3Sum' },
    ]
    render(<SolveTable solves={solves} onSelect={() => {}} />)
    expect(screen.getAllByTitle('Has a written solution')).toHaveLength(1)
  })
})
