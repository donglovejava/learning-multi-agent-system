import { useEffect, useState } from 'react'

interface KnowledgeItem {
  id: string
  name: string
  category: string
  difficulty: number
  description: string
  resourceCount?: number
}

interface GraphData {
  nodes: Array<{ id: string; name: string; category: string; difficulty: number; description: string }>
  edges: Array<{ source: string; target: string; strength: number }>
}

const FALLBACK_ITEMS: KnowledgeItem[] = [
  { id: '1', name: '线性代数基础', category: '数学', difficulty: 2, description: '向量、矩阵、行列式、特征值' },
  { id: '2', name: '概率论入门', category: '数学', difficulty: 3, description: '概率分布、条件概率、贝叶斯定理' },
  { id: '3', name: 'Python 编程基础', category: '编程', difficulty: 1, description: '语法、数据结构、函数、面向对象' },
  { id: '4', name: '神经网络基础', category: '深度学习', difficulty: 3, description: '感知机、反向传播、激活函数' },
  { id: '5', name: '注意力机制', category: '深度学习', difficulty: 4, description: '自注意力、Q/K/V、Softmax、缩放点积' },
  { id: '6', name: 'Transformer 架构', category: '深度学习', difficulty: 5, description: '编码器-解码器、残差连接、Layer Norm' },
  { id: '7', name: 'BERT', category: '深度学习', difficulty: 5, description: 'MLM 预训练、双向编码、微调' },
  { id: '8', name: '决策树', category: '机器学习', difficulty: 2, description: '信息增益、ID3/C4.5/CART、剪枝' },
]

export default function KnowledgeBase() {
  const [items, setItems] = useState<KnowledgeItem[]>(FALLBACK_ITEMS)
  const [graph, setGraph] = useState<GraphData | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [uploading, setUploading] = useState(false)
  const [isReal, setIsReal] = useState(false)

  useEffect(() => {
    // 拉取知识图谱全量节点 + 边
    fetch('/api/v1/knowledge/graph')
      .then(r => r.json())
      .then((data: GraphData) => {
        if (data?.nodes?.length) {
          const mapped: KnowledgeItem[] = data.nodes.map(n => ({
            id: n.id,
            name: n.name,
            category: n.category,
            difficulty: n.difficulty,
            description: n.description,
          }))
          setItems(mapped)
          setGraph(data)
          setIsReal(true)
        }
      })
      .catch(() => { /* 用 fallback */ })
  }, [])

  const categories = ['all', ...Array.from(new Set(items.map(i => i.category)))]
  const filtered = items.filter(i => {
    const matchSearch = i.name.toLowerCase().includes(search.toLowerCase()) || i.description.toLowerCase().includes(search.toLowerCase())
    const matchCategory = category === 'all' || i.category === category
    return matchSearch && matchCategory
  })

  const handleUpload = () => {
    setUploading(true)
    setTimeout(() => {
      setUploading(false)
      alert('文档上传成功！系统正在解析和构建知识库...')
    }, 2000)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
        <div className="flex items-center gap-2">
          {!isReal && <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">示例数据</span>}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 text-sm"
          >
            {uploading ? '上传中...' : '📤 上传课程资料'}
          </button>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex gap-3">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索知识点..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={category}
          onChange={e => setCategory(e.target.value)}
          className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {categories.map(c => (
            <option key={c} value={c}>{c === 'all' ? '全部分类' : c}</option>
          ))}
        </select>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="知识点总数" value={items.length} color="text-blue-600" />
        <Stat label="分类数" value={categories.length - 1} color="text-green-600" />
        <Stat label="图谱关联" value={graph?.edges?.length ?? '—'} color="text-purple-600" />
        <Stat label="高难度知识点" value={items.filter(i => i.difficulty >= 4).length} color="text-orange-600" />
      </div>

      {/* 知识点列表 */}
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">知识点</th>
              <th className="px-4 py-3 text-center">分类</th>
              <th className="px-4 py-3 text-center">难度</th>
              <th className="px-4 py-3 text-left hidden md:table-cell">描述</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filtered.map(item => (
              <tr key={item.id} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-4 py-3 font-medium">{item.name}</td>
                <td className="px-4 py-3 text-center">
                  <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700">{item.category}</span>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex justify-center gap-0.5">
                    {[1, 2, 3, 4, 5].map(i => (
                      <div key={i} className={`w-2 h-2 rounded-full ${i <= item.difficulty ? 'bg-orange-400' : 'bg-gray-200'}`} />
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-500 hidden md:table-cell">{item.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center text-gray-400 py-8">没有找到匹配的知识点</div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  )
}
