import { useEffect, useState } from 'react'
import { AudioDemo } from './components/AudioDemo'
import { PriceCheckUI } from './components/PriceCheckUI'
import { ConversationUIDemo } from './components/ConversationUIDemo'
import { VoiceCommandDemo } from './components/VoiceCommandDemo'
import { AudioFeedbackDemo } from './components/AudioFeedbackDemo'
import { OfflineIndicator } from './components/OfflineIndicator'

type View = 'home' | 'price-check' | 'conversation' | 'audio' | 'voice-commands' | 'audio-feedback'

function App() {
  const [currentView, setCurrentView] = useState<View>('home')
  const [language, setLanguage] = useState('en')

  useEffect(() => {
    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch((error) => {
        console.error('Service Worker registration failed:', error)
      })
    }
  }, [])

  const renderView = () => {
    switch (currentView) {
      case 'price-check':
        return <PriceCheckUI language={language} userLocation={{ state: 'Maharashtra' }} />
      case 'conversation':
        return <ConversationUIDemo />
      case 'audio':
        return <AudioDemo />
      case 'voice-commands':
        return <VoiceCommandDemo />
      case 'audio-feedback':
        return <AudioFeedbackDemo />
      default:
        return <HomeView onNavigate={setCurrentView} />
    }
  }

  return (
    <div className="app" style={styles.app}>
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.title}>🌾 Multilingual Mandi</h1>
          <p style={styles.subtitle}>Voice-first platform for multilingual agricultural trade</p>
        </div>
        <div style={styles.headerActions}>
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)}
            style={styles.languageSelect}
          >
            <option value="en">English</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="te">తెలుగు (Telugu)</option>
            <option value="ta">தமிழ் (Tamil)</option>
          </select>
          {currentView !== 'home' && (
            <button onClick={() => setCurrentView('home')} style={styles.homeButton}>
              🏠 Home
            </button>
          )}
        </div>
      </header>
      <OfflineIndicator />
      <main style={styles.main}>
        {renderView()}
      </main>
      <footer style={styles.footer}>
        <p>Built with ❤️ for Indian farmers and traders</p>
      </footer>
    </div>
  )
}

function HomeView({ onNavigate }: { onNavigate: (view: View) => void }) {
  return (
    <div style={styles.homeContainer}>
      <section style={styles.hero}>
        <h2 style={styles.heroTitle}>Breaking Language Barriers in Agricultural Trade</h2>
        <p style={styles.heroText}>
          Real-time voice translation, AI-powered price discovery, and culturally-aware 
          negotiation assistance for farmers and traders across India's 22 languages.
        </p>
      </section>

      <section style={styles.features}>
        <h3 style={styles.sectionTitle}>Core Features</h3>
        <div style={styles.featureGrid}>
          <FeatureCard
            icon="💰"
            title="Price Check"
            description="Get real-time market prices and compare quotes instantly"
            onClick={() => onNavigate('price-check')}
          />
          <FeatureCard
            icon="💬"
            title="Conversations"
            description="Voice-to-voice translation for seamless multilingual communication"
            onClick={() => onNavigate('conversation')}
          />
          <FeatureCard
            icon="🎤"
            title="Voice Commands"
            description="Navigate the app using voice commands in your language"
            onClick={() => onNavigate('voice-commands')}
          />
          <FeatureCard
            icon="🔊"
            title="Audio Feedback"
            description="Voice prompts and audio feedback for all actions"
            onClick={() => onNavigate('audio-feedback')}
          />
        </div>
      </section>

      <section style={styles.features}>
        <h3 style={styles.sectionTitle}>Technical Demos</h3>
        <div style={styles.featureGrid}>
          <FeatureCard
            icon="🎙️"
            title="Audio Processing"
            description="Test audio capture, compression, and playback features"
            onClick={() => onNavigate('audio')}
          />
        </div>
      </section>

      <section style={styles.stats}>
        <div style={styles.statCard}>
          <div style={styles.statNumber}>22</div>
          <div style={styles.statLabel}>Languages Supported</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statNumber}>50+</div>
          <div style={styles.statLabel}>Commodities Tracked</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statNumber}>2G/3G</div>
          <div style={styles.statLabel}>Network Optimized</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statNumber}>Offline</div>
          <div style={styles.statLabel}>PWA Support</div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ 
  icon, 
  title, 
  description, 
  onClick 
}: { 
  icon: string
  title: string
  description: string
  onClick: () => void 
}) {
  return (
    <div style={styles.featureCard} onClick={onClick}>
      <div style={styles.featureIcon}>{icon}</div>
      <h4 style={styles.featureTitle}>{title}</h4>
      <p style={styles.featureDescription}>{description}</p>
      <button style={styles.featureButton}>Try it →</button>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f5f5f5',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    backgroundColor: '#2e7d32',
    color: 'white',
    padding: '1rem 2rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '1rem',
  },
  headerContent: {
    flex: 1,
  },
  title: {
    margin: 0,
    fontSize: '1.8rem',
    fontWeight: 'bold',
  },
  subtitle: {
    margin: '0.5rem 0 0 0',
    fontSize: '0.95rem',
    opacity: 0.9,
  },
  headerActions: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
  },
  languageSelect: {
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    border: 'none',
    fontSize: '0.9rem',
    cursor: 'pointer',
  },
  homeButton: {
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    border: 'none',
    backgroundColor: 'white',
    color: '#2e7d32',
    fontSize: '0.9rem',
    cursor: 'pointer',
    fontWeight: '500',
  },
  main: {
    flex: 1,
    padding: '2rem',
    maxWidth: '1400px',
    margin: '0 auto',
    width: '100%',
  },
  footer: {
    backgroundColor: '#1b5e20',
    color: 'white',
    padding: '1rem',
    textAlign: 'center',
  },
  homeContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '3rem',
  },
  hero: {
    textAlign: 'center',
    padding: '2rem',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  heroTitle: {
    fontSize: '2rem',
    color: '#2e7d32',
    marginBottom: '1rem',
  },
  heroText: {
    fontSize: '1.1rem',
    color: '#666',
    lineHeight: '1.6',
    maxWidth: '800px',
    margin: '0 auto',
  },
  features: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    color: '#333',
    marginBottom: '0.5rem',
  },
  featureGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '1.5rem',
  },
  featureCard: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    ':hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    },
  },
  featureIcon: {
    fontSize: '3rem',
    marginBottom: '1rem',
  },
  featureTitle: {
    fontSize: '1.3rem',
    color: '#333',
    marginBottom: '0.5rem',
  },
  featureDescription: {
    fontSize: '0.95rem',
    color: '#666',
    lineHeight: '1.5',
    marginBottom: '1rem',
  },
  featureButton: {
    padding: '0.6rem 1.2rem',
    backgroundColor: '#2e7d32',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '0.9rem',
    cursor: 'pointer',
    fontWeight: '500',
  },
  stats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1.5rem',
  },
  statCard: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    textAlign: 'center',
  },
  statNumber: {
    fontSize: '2.5rem',
    fontWeight: 'bold',
    color: '#2e7d32',
    marginBottom: '0.5rem',
  },
  statLabel: {
    fontSize: '0.95rem',
    color: '#666',
  },
}

export default App
