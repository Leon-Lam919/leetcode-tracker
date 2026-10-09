import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import NoteEditor from '../components/NoteEditor'

const solve = {
  id: 7,
  title: 'Two Sum',
  solved_date: '2026-10-08',
  time_spent_min: null,
  confidence: null,
  notes: '',
  needs_review: false,
  approach: null,
  code: null,
  language: 'python3',
  time_complexity: null,
  space_complexity: null,
}

function mockFetchOk() {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({ ...solve }),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const NO_SOLUTION = {
  approach: null,
  language: 'python3',
  code: null,
  time_complexity: null,
  space_complexity: null,
}

afterEach(() => vi.unstubAllGlobals())

describe('NoteEditor', () => {
  it('sends a PATCH with the edited fields', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ...solve }),
    })
    vi.stubGlobal('fetch', fetchMock)
    const onSaved = vi.fn()
    const user = userEvent.setup()

    render(<NoteEditor solve={solve} onSaved={onSaved} onClose={() => {}} />)
    await user.type(screen.getByLabelText('Time (min)'), '25')
    await user.selectOptions(screen.getByLabelText('Confidence'), '2')
    await user.type(screen.getByLabelText('Notes'), 'hash map')
    await user.click(screen.getByLabelText('Needs review'))
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/solves/7')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({
      time_spent_min: 25,
      confidence: 2,
      notes: 'hash map',
      needs_review: true,
      ...NO_SOLUTION,
    })
    expect(onSaved).toHaveBeenCalled()
  })

  it('sends the solution fields in the PATCH body', async () => {
    const fetchMock = mockFetchOk()
    const user = userEvent.setup()

    render(<NoteEditor solve={solve} onSaved={() => {}} onClose={() => {}} />)
    await user.type(screen.getByLabelText('Approach'), 'hash map, one pass')
    await user.selectOptions(screen.getByLabelText('Language'), 'java')
    await user.type(screen.getByLabelText('Time complexity'), 'O(n)')
    await user.type(screen.getByLabelText('Space complexity'), 'O(n)')
    const codeBox = screen.getByLabelText('Code')
    await user.click(codeBox)
    await user.keyboard('if x:{Enter}{Tab}return')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    const body = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(body).toMatchObject({
      approach: 'hash map, one pass',
      language: 'java',
      code: 'if x:\n    return', // Tab became 4 spaces
      time_complexity: 'O(n)',
      space_complexity: 'O(n)',
    })
  })

  it('shows the error message if saving fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Solve not found' }),
      }),
    )
    const user = userEvent.setup()

    render(<NoteEditor solve={solve} onSaved={() => {}} onClose={() => {}} />)
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Solve not found')
  })
})
