import { BUTTONS } from '../ratings'

// Again / Good / Easy. `name` makes each button's accessible label unique ("Good: Two Sum").
// `selected` (optional) highlights one button, for forms where a click picks instead of saves.
export default function RatingButtons({ name, onRate, disabled = false, selected = null }) {
  return (
    <div className="flex gap-2">
      {BUTTONS.map(({ label, confidence, className }) => (
        <button
          key={label}
          type="button"
          disabled={disabled}
          onClick={() => onRate(confidence)}
          aria-label={name ? `${label}: ${name}` : label}
          aria-pressed={selected === null ? undefined : selected === confidence}
          className={`rounded px-3 py-1 text-sm font-semibold text-white disabled:opacity-50 ${className} ${
            selected !== null && selected !== confidence ? 'opacity-40' : ''
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
