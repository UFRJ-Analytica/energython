import { useEffect, useState } from "react"

export function useTypewriter(text: string, charsPerSec = 200) {
  const [displayed, setDisplayed] = useState("")

  useEffect(() => {
    setDisplayed("")
    if (!text) return
    let i = 0
    const ms = 1000 / charsPerSec
    const timer = setInterval(() => {
      i++
      setDisplayed(text.slice(0, i))
      if (i >= text.length) clearInterval(timer)
    }, ms)
    return () => clearInterval(timer)
  }, [text, charsPerSec])

  return displayed
}
