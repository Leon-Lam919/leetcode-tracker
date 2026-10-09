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
    })
    expect(onSaved).toHaveBeenCalled()
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
