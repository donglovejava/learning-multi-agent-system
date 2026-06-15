import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Resources from './pages/Resources'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-3 flex gap-6">
          <Link to="/" className="text-gray-700 hover:text-blue-600 font-medium">首页</Link>
          <Link to="/chat" className="text-gray-700 hover:text-blue-600 font-medium">对话</Link>
          <Link to="/resources" className="text-gray-700 hover:text-blue-600 font-medium">资源</Link>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/resources" element={<Resources />} />
        </Routes>
      </main>
    </div>
  )
}
