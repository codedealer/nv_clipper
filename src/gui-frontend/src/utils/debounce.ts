export function debounce<A extends unknown[]>(fn: (...args: A) => void, wait = 200) {
  let t: ReturnType<typeof setTimeout>
  return (...args: A): void => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), wait)
  }
}
