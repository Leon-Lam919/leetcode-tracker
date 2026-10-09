import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import SyncButton from '../components/SyncButton'

afterEach(() => vi.useRealTimers())

describe('SyncButton', () => {
  it('shows when the last sync ran', () => {
    vi.useFakeTimers({ now: new Date('2026-10-08T14:00:00Z') })
    render(
      <SyncButton
        onSynced={() => {}}
        lastSyncAt="2026-10-08T13:48:00Z"
        lastSyncResult="added 1, skipped 19"
      />,
    )
    expect(screen.getByText('Synced 12 min ago')).toHaveAttribute('title', 'added 1, skipped 19')
  })

  it('shows nothing before the first sync', () => {
    render(<SyncButton onSynced={() => {}} lastSyncAt={null} />)
    expect(screen.queryByText(/Synced/)).not.toBeInTheDocument()
  })
})
