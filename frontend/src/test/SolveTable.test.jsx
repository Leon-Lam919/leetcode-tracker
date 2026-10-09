import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
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

afterEach(() => vi.unstubAllGlobals())

describe('SolveTable inline rating', () => {
  it('rates an unrated row in place without opening the editor', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })
    vi.stubGlobal('fetch', fetchMock)
    const onSelect = vi.fn()
    const onRated = vi.fn()
    const user = userEvent.setup()
    const solves = [
      { ...base, id: 1, title: 'Two Sum' },
      { ...base, id: 2, title: '3Sum', confidence: 3 },
    ]

    render(<SolveTable solves={solves} onSelect={onSelect} onRated={onRated} />)
    expect(screen.getAllByRole('button', { name: /^Rate / })).toHaveLength(1)
    expect(screen.getByText('Clean')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Rate Two Sum' }))
    await user.click(screen.getByRole('button', { name: 'Good: Two Sum' }))

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/solves/1')
    expect(JSON.parse(options.body)).toEqual({ confidence: 2 })
    expect(onRated).toHaveBeenCalled()
    expect(onSelect).not.toHaveBeenCalled()
  })
})
