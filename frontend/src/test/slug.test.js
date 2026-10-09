import { describe, expect, it } from 'vitest'
import { extractSlug } from '../slug'

describe('extractSlug', () => {
  it('pulls the slug out of a LeetCode URL', () => {
    expect(extractSlug('https://leetcode.com/problems/two-sum/')).toBe('two-sum')
  })

  it('ignores extra path parts and query strings', () => {
    expect(
      extractSlug('https://leetcode.com/problems/valid-anagram/description/?envType=daily'),
    ).toBe('valid-anagram')
  })

  it('accepts a URL without a trailing slash', () => {
    expect(extractSlug('leetcode.com/problems/3sum')).toBe('3sum')
  })

  it('returns a plain slug unchanged (trimmed, lowercased)', () => {
    expect(extractSlug('  Two-Sum ')).toBe('two-sum')
  })
})
