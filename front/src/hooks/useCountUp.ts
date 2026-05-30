import { useEffect, useState } from "react"

export function useCountUp(target: number, duration = 1400) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!target) return setValue(0)
    const start = performance.now()
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setValue(Math.round(eased * target))
      if (p < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target, duration])

  return value
}
