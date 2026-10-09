import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import PatternChecklist from '../components/PatternChecklist'

function problem(slug, solved) {
  return {
    slug,
    title: slug,
    difficulty: 'Medium',
    url: `https://leetcode.com/problems/${slug}/`,
    solved,
    needs_review: false,
  }
}

const groups = [
  {
    pattern: 'Arrays & Hashing',
    total: 2,
    solved: 1,
    problems: [problem('two-sum', true), problem('group-anagrams', false)],
  },
  {
    pattern: 'Two Pointers',
    total: 5,
    solved: 3,
    problems: ['a', 'b', 'c', 'd', 'e'].map((slug, i) => problem(slug, i < 3)),
  },
]

describe('PatternChecklist', () => {
  it('shows per-pattern and overall progress', () => {
    render(<PatternChecklist groups={groups} />)

    expect(screen.getByText('Two Pointers 3/5')).toBeInTheDocument()
    expect(screen.getByText('Arrays & Hashing 1/2')).toBeInTheDocument()
    expect(screen.getByText('4 / 7')).toBeInTheDocument()

    const bar = screen.getByRole('progressbar', { name: 'Two Pointers' })
    expect(bar).toHaveAttribute('aria-valuenow', '3')
    expect(bar).toHaveAttribute('aria-valuemax', '5')
    expect(bar.firstChild).toHaveStyle({ width: '60%' })
  })

  it('marks solved problems and links unsolved ones to LeetCode', () => {
    render(<PatternChecklist groups={groups} />)
    expect(screen.getAllByLabelText('solved')).toHaveLength(4)
    expect(screen.getByRole('link', { name: 'group-anagrams' })).toHaveAttribute(
      'href',
      'https://leetcode.com/problems/group-anagrams/',
    )
  })
})
