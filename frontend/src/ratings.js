// The three rating buttons, shared by the review queue, the rate card, the add form,
// and the solve table. Same scale as a solve's confidence: 1 = again, 2 = good, 3 = easy.
export const BUTTONS = [
  { label: 'Again', confidence: 1, className: 'bg-red-600 hover:bg-red-700' },
  { label: 'Good', confidence: 2, className: 'bg-blue-600 hover:bg-blue-700' },
  { label: 'Easy', confidence: 3, className: 'bg-green-600 hover:bg-green-700' },
]

// Optional "how long did it take" chips. 60+ is saved as 60.
export const TIME_CHIPS = [
  { label: '15', minutes: 15 },
  { label: '30', minutes: 30 },
  { label: '45', minutes: 45 },
  { label: '60+', minutes: 60 },
]
