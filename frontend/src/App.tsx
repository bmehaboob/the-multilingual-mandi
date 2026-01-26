import { useEffect } from 'react'
import { AudioDemo } from './components/AudioDemo'

function App() {
  useEffect(() => {
    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch((error) => {
        console.error('Service Worker registration failed:', error)
      })
    }
  }, [])

  return (
    <div className="app">
      <header>
        <h1>Multilingual Mandi</h1>
        <p>Voice-first platform for multilingual agricultural trade</p>
      </header>
      <main>
        <AudioDemo />
      </main>
    </div>
  )
}

export default App
