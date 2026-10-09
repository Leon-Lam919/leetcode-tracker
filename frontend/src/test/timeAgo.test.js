import { describe, expect, it } from 'vitest'
import { timeAgo } from '../timeAgo'

const now = new Date('2026-10-08T14:00:00Z')

describe('timeAgo', () => {
  it.each([
    ['2026-10-08T13:59:30Z', 'just now'],
    ['2026-10-08T13:48:00Z', '12 min ago'],
    ['2026-10-08T11:00:00Z', '3 h ago'],
    ['2026-10-07T13:00:00Z', '1 day ago'],
    ['2026-10-05T14:00:00Z', '3 days ago'],
  ])('%s -> %s', (time, expected) => {
    expect(timeAgo(time, now)).toBe(expected)
  })
})
