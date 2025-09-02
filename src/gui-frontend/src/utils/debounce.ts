export function debounce<T extends (...args: any[]) => any>(fn: T, wait = 200) {
  let t: ReturnType<typeof setTimeout>
  return ((...args: Parameters<T>) => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), wait)
  }) as T
}
