// Accepts "two-sum" or a pasted URL like
// "https://leetcode.com/problems/two-sum/description/?envType=daily" and returns "two-sum".
export function extractSlug(input) {
  const text = input.trim()
  const match = text.match(/\/problems\/([^/?#]+)/)
  const slug = match ? match[1] : text
  return slug.toLowerCase()
}
