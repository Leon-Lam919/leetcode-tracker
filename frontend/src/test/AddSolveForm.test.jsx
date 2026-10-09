import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import AddSolveForm from '../components/AddSolveForm'

function mockFetchCreated() {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 201,
    json: () => Promise.resolve({}),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const sentBody = (fetchMock) => JSON.parse(fetchMock.mock.calls[0][1].body)

afterEach(() => vi.unstubAllGlobals())

describe('AddSolveForm', () => {
  it('Enter submits with no rating', async () => {
    const fetchMock = mockFetchCreated()
    const onAdded = vi.fn()
    const user = userEvent.setup()

    render(<AddSolveForm onAdded={onAdded} />)
    await user.type(screen.getByLabelText('Add a solve by slug or URL'), 'two-sum{Enter}')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/solves')
    expect(sentBody(fetchMock)).toEqual({ title_slug: 'two-sum' })
    expect(onAdded).toHaveBeenCalled()
  })

  it('includes the rating and review flag when one is picked', async () => {
    const fetchMock = mockFetchCreated()
    const user = userEvent.setup()

    render(<AddSolveForm onAdded={() => {}} />)
    await user.type(screen.getByLabelText('Add a solve by slug or URL'), 'two-sum')
    await user.click(screen.getByRole('button', { name: 'Easy' }))
    await user.click(screen.getByLabelText('🔁 flag for review'))
    await user.click(screen.getByRole('button', { name: 'Add' }))

    expect(sentBody(fetchMock)).toEqual({
      title_slug: 'two-sum',
      confidence: 3,
      needs_review: true,
    })
  })

  it('clicking the picked rating again clears it', async () => {
    const fetchMock = mockFetchCreated()
    const user = userEvent.setup()

    render(<AddSolveForm onAdded={() => {}} />)
    await user.type(screen.getByLabelText('Add a solve by slug or URL'), 'two-sum')
    await user.click(screen.getByRole('button', { name: 'Good' }))
    expect(screen.getByRole('button', { name: 'Good' })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'Good' }))
    await user.click(screen.getByRole('button', { name: 'Add' }))

    expect(sentBody(fetchMock)).toEqual({ title_slug: 'two-sum' })
  })
})
