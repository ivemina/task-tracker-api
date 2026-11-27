import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL as string

type Health = { status: string }

function App() {
  const [status, setStatus] = useState<string>('checking...')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json() as Promise<Health>
      })
      .then((data) => setStatus(data.status))
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <main>
      <h1>Task Tracker</h1>
      {error ? <p>API error: {error}</p> : <p>API status: {status}</p>}
    </main>
  )
}

export default App