import { useState } from 'react'
import { generateResources } from '../api/client'
import ReactMarkdown from 'react-markdown'

interface Resource {
  type: string
  content: any
  [key: string]: any
}

export default function Resources() {
  const [knowledge, setKnowledge] = useState('')
  const [resources, setResources] = useState<Resource[]>([])
  const [loading, setLoading] = useState(false)
  const [time, setTime] = useState(0)
  const [studentId] = useState('demo-001')

  const handleGenerate = async () => {
    if (!knowledge.trim() || loading) return
    setLoading(true)
    setResources([])

    try {
      const start = Date.now()
      const resp = await generateResources({
        student_id: studentId,
        knowledge_point: knowledge,
        resource_types: ['document', 'quiz', 'mindmap', 'code', 'reading'],
      })
      setResources(resp.resources)
      setTime(Date.now() - start)
    } catch (err) {
      alert(`生成失败：${err}`)
    } finally {
      setLoading(false)
    }
  }

  const renderResource = (res: Resource, idx: number) => {
    const typeLabels: Record<string, string> = {
      document: '讲解文档',
      quiz: '练习题',
      mindmap: '思维导图',
      code: '代码案例',
      reading: '拓展阅读',
    }
    const label = typeLabels[res.type] || res.type

    return (
      <div key={idx} className="bg-white rounded-lg border shadow-sm p-4">
        <h3 className="font-semibold text-lg mb-3 text-blue-700">{label}</h3>
        {res.type === 'document' || res.type === 'reading' ? (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{typeof res.content === 'string' ? res.content : JSON.stringify(res.content)}</ReactMarkdown>
          </div>
        ) : res.type === 'quiz' ? (
          <div className="space-y-3">
            {res.content?.questions?.map((q: any, i: number) => (
              <div key={i} className="border-b pb-2">
                <p className="font-medium text-sm">
                  Q{i + 1}. [{q.difficulty}] {q.question}
                </p>
                <div className="text-xs text-gray-600 mt-1">
                  答案：{q.answer} | 解析：{q.explanation}
                </div>
              </div>
            ))}
          </div>
        ) : res.type === 'code' ? (
          <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-x-auto">
            {res.content?.code || JSON.stringify(res.content)}
          </pre>
        ) : res.type === 'mindmap' ? (
          <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
            {JSON.stringify(res.content?.data, null, 2)}
          </pre>
        ) : (
          <pre className="text-xs">{JSON.stringify(res.content, null, 2)}</pre>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">资源生成</h1>
      <p className="text-gray-600 text-sm">
        输入知识点，一次请求并行生成 5 种学习资源。
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          value={knowledge}
          onChange={e => setKnowledge(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleGenerate()}
          placeholder="例如：Transformer 注意力机制"
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={handleGenerate}
          disabled={loading || !knowledge.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? '生成中...' : '生成资源'}
        </button>
      </div>

      {time > 0 && (
        <p className="text-sm text-gray-500">耗时：{(time / 1000).toFixed(1)} 秒</p>
      )}

      <div className="space-y-4">
        {resources.map((res, idx) => renderResource(res, idx))}
      </div>

      {resources.length === 0 && !loading && (
        <p className="text-gray-400 text-center text-sm py-12">
          输入知识点后点击"生成资源"
        </p>
      )}
    </div>
  )
}
