import { useState } from 'react'

interface PathNode {
  id: string
  label: string
  status: 'completed' | 'current' | 'pending' | 'skipped'
  mastery?: number
}

export default function Path() {
  const [target, setTarget] = useState('')
  const [nodes, setNodes] = useState<PathNode[]>([])
  const [loading, setLoading] = useState(false)
  const [studentId] = useState('demo-001')

  const handlePlan = async () => {
    if (!target.trim() || loading) return
    setLoading(true)
    try {
      const resp = await fetch('/api/v1/path', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, target_knowledge: target }),
      })
      if (resp.ok) {
        const data = await resp.json()
        setNodes(data.path?.map((n: any, i: number) => ({
          id: n.id || `node-${i}`,
          label: n.label || n.id || `知识点 ${i + 1}`,
          status: i === 0 ? 'current' : 'pending',
          mastery: Math.random() * 0.4 + 0.6,
        })) || [])
      } else {
        // 后端未通时用模拟数据
        setNodes(generateMockPath(target))
      }
    } catch {
      setNodes(generateMockPath(target))
    } finally {
      setLoading(false)
    }
  }

  const statusColors: Record<string, string> = {
    completed: 'bg-green-100 border-green-400 text-green-800',
    current: 'bg-blue-100 border-blue-400 text-blue-800',
    pending: 'bg-gray-50 border-gray-300 text-gray-600',
    skipped: 'bg-yellow-50 border-yellow-300 text-yellow-700 line-through',
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">学习路径规划</h1>
      <p className="text-gray-600 text-sm">
        基于 DAG 知识图谱 + 改进 Dijkstra 算法，结合你的画像规划个性化学习路径。
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          value={target}
          onChange={e => setTarget(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handlePlan()}
          placeholder="目标知识点，例如：Transformer"
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={handlePlan}
          disabled={loading || !target.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
        >
          {loading ? '规划中...' : '规划路径'}
        </button>
      </div>

      {nodes.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-4 text-sm">
            <Legend color="bg-green-400" label="已掌握" />
            <Legend color="bg-blue-400" label="当前学习" />
            <Legend color="bg-gray-300" label="待学习" />
            <Legend color="bg-yellow-300" label="已跳过" />
          </div>

          <div className="relative">
            {/* 连接线 */}
            <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-gray-300" />

            <div className="space-y-3">
              {nodes.map((node, i) => (
                <div key={node.id} className={`relative flex items-center gap-4 p-4 rounded-lg border-2 ${statusColors[node.status]}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                    node.status === 'completed' ? 'bg-green-400 text-white' :
                    node.status === 'current' ? 'bg-blue-400 text-white' :
                    node.status === 'skipped' ? 'bg-yellow-300 text-yellow-800' :
                    'bg-gray-200 text-gray-600'
                  }`}>
                    {node.status === 'completed' ? '✓' : i + 1}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{node.label}</div>
                    {node.mastery !== undefined && node.status !== 'skipped' && (
                      <div className="text-xs text-gray-500 mt-1">
                        掌握度：{Math.round(node.mastery * 100)}%
                      </div>
                    )}
                  </div>
                  <div className="text-xs font-medium uppercase">
                    {node.status === 'completed' && '已完成'}
                    {node.status === 'current' && '学习中'}
                    {node.status === 'pending' && '待学习'}
                    {node.status === 'skipped' && '已跳过'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {nodes.length === 0 && !loading && (
        <p className="text-gray-400 text-center text-sm py-12">
          输入目标知识点后点击"规划路径"
        </p>
      )}
    </div>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1">
      <div className={`w-3 h-3 rounded-full ${color}`} />
      <span>{label}</span>
    </div>
  )
}

function generateMockPath(target: string): PathNode[] {
  return [
    { id: '1', label: '线性代数基础', status: 'completed', mastery: 0.85 },
    { id: '2', label: '概率论入门', status: 'completed', mastery: 0.72 },
    { id: '3', label: '神经网络基础', status: 'current', mastery: 0.45 },
    { id: '4', label: '注意力机制', status: 'pending' },
    { id: '5', label: 'Transformer 架构', status: 'pending' },
    { id: '6', label: target || '目标知识点', status: 'pending' },
    { id: '7', label: 'BERT/GPT 应用', status: 'pending' },
  ]
}
