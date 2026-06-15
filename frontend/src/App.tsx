import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Resources from './pages/Resources'
import Profile from './pages/Profile'
import Path from './pages/Path'
import Quiz from './pages/Quiz'
import Assessment from './pages/Assessment'

const NAV_ITEMS = [
  { to: '/', label: '首页' },
  { to: '/chat', label: '对话' },
  { to: '/resources', label: '资源' },
  { to: '/profile', label: '画像' },
  { to: '/path', label: '路径' },
  { to: '/quiz', label: '练习' },
  { to: '/assessment', label: '评估' },
]

export default function App() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex gap-1 overflow-x-auto">
          {NAV_ITEMS.map(item => (
            <Link
              key={item.to}
              to={item.to}
              className={`px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition ${
                location.pathname === item.to
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/path" element={<Path />} />
          <Route path="/quiz" element={<Quiz />} />
          <Route path="/assessment" element={<Assessment />} />
        </Routes>
      </main>
    </div>
  )
}
