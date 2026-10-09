import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import RateSolveCard from '../components/RateSolveCard'

const solve = (id, title) => ({
  id,
  title,
  title_slug: title.toLowerCase().replace(/ /g, '-'),
  difficulty: 'Easy',
  url: `https://leetcode.com/problems/${id}/`,
  confidence: null,
  needs_review: false,
})
const twoSum = solve(7, 'Two Sum')
const threeSum = solve(8, '3Sum')

function mockFetchOk() {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('RateSolveCard', () => {
  it('renders nothing when there are no unrated solves', () => {
    const { container } = render(<RateSolveCard solves={[]} onRated={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('lists unrated solves with a count and links', () => {
    render(<RateSolveCard solves={[twoSum, threeSum]} onRated={() => {}} />)
    expect(screen.getByText("✍️ Rate today's solves (2)")).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Two Sum' })).toHaveAttribute('href', twoSum.url)
  })

  it('one click on Good saves confidence and the review flag', async () => {
    const fetchMock = mockFetchOk()
    const onRated = vi.fn()
    const user = userEvent.setup()

    render(<RateSolveCard solves={[twoSum, threeSum]} onRated={onRated} />)
    await user.click(screen.getByRole('button', { name: 'Good: Two Sum' }))

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/solves/7')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ confidence: 2, needs_review: false })
    expect(onRated).toHaveBeenCalled()
    expect(screen.queryByRole('link', { name: 'Two Sum' })).not.toBeInTheDocument()
    expect(screen.getByText("✍️ Rate today's solves (1)")).toBeInTheDocument()
  })

  it('includes the time chip and the review flag when picked', async () => {
    const fetchMock = mockFetchOk()
    const user = userEvent.setup()

    render(<RateSolveCard solves={[twoSum]} onRated={() => {}} />)
    await user.click(screen.getByRole('button', { name: '30 min' }))
    await user.click(screen.getByRole('button', { name: '🔁 flag for review' }))
    await user.click(screen.getByRole('button', { name: 'Again: Two Sum' }))

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      confidence: 1,
      needs_review: true,
      time_spent_min: 30,
    })
  })

  it('Skip hides the row without saving', async () => {
    const fetchMock = mockFetchOk()
    const user = userEvent.setup()

    render(<RateSolveCard solves={[twoSum, threeSum]} onRated={() => {}} />)
    await user.click(screen.getAllByRole('button', { name: 'Skip' })[0])

    expect(screen.queryByRole('link', { name: 'Two Sum' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: '3Sum' })).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows the error and keeps the row if saving fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Solve not found' }),
      }),
    )
    const user = userEvent.setup()

    render(<RateSolveCard solves={[twoSum]} onRated={() => {}} />)
    await user.click(screen.getByRole('button', { name: 'Easy: Two Sum' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Solve not found')
    expect(screen.getByRole('link', { name: 'Two Sum' })).toBeInTheDocument()
  })
})
