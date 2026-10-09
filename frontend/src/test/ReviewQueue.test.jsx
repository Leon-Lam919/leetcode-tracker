import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ReviewQueue from '../components/ReviewQueue'

const twoSum = {
  problem_id: 4,
  title: 'Two Sum',
  title_slug: 'two-sum',
  difficulty: 'Easy',
  url: 'https://leetcode.com/problems/two-sum/',
  next_review_date: '2026-10-07',
  days_overdue: 1,
  last_confidence: null,
  approach: 'hash map, one pass',
}

afterEach(() => vi.unstubAllGlobals())

describe('ReviewQueue', () => {
  it('shows the empty state', () => {
    render(<ReviewQueue reviews={[]} onReviewed={() => {}} />)
    expect(screen.getByText('Nothing to review today 🎉')).toBeInTheDocument()
  })

  it('lists due problems with a link and the approach', () => {
    render(<ReviewQueue reviews={[twoSum]} onReviewed={() => {}} />)
    expect(screen.getByText('🔁 1 to review today')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Two Sum' })).toHaveAttribute('href', twoSum.url)
    expect(screen.getByText(/1 day overdue · hash map, one pass/)).toBeInTheDocument()
  })

  it.each([
    ['Again', 1],
    ['Good', 2],
    ['Easy', 3],
  ])('%s posts confidence %i', async (label, confidence) => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })
    vi.stubGlobal('fetch', fetchMock)
    const onReviewed = vi.fn()
    const user = userEvent.setup()

    render(<ReviewQueue reviews={[twoSum]} onReviewed={onReviewed} />)
    await user.click(screen.getByRole('button', { name: `${label}: Two Sum` }))

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/reviews/4')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ confidence })
    expect(onReviewed).toHaveBeenCalled()
  })
})
