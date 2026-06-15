import { useState } from 'react'

interface KnowledgeItem {
  id: number
  name: string
  category: string
  difficulty: number
  description: string
  resourceCount: number
}

const MOCK_KNOWLEDGE: KnowledgeItem[] = [
  { id: 1, name: '线性代数基础', category: '数学', difficulty: 2, description: '向量、矩阵、行列式、特征值', resourceCount: 12 },
  { id: 2, name: '概率论入门', category: '数学', difficulty: 3, description: '概率分布、条件概率、贝叶斯定理', resourceCount: 8 },
  { id: 3, name: 'Python 编程基础', category: '编程', difficulty: 1, description: '语法、数据结构、函数、面向对象', resourceCount: 15 },
  { id: 4, name: '神经网络基础', category: 'AI', difficulty: 3, description: '感知机、反向传播、激活函数', resourceCount: 10 },
  { id: 5, name: '注意力机制', category: 'AI', difficulty: 4, description: '自注意力、多头注意力、位置编码', resourceCount: 6 },
  { id: 6, name: 'Transformer 架构', category: 'AI', difficulty: 5, description: '编码器-解码器、残差连接、Layer Norm', resourceCount: 4 },
  { id: 7, name: 'BERT 预训练', category: 'AI', difficulty: 5, description: 'MLM、NSP、微调策略', resourceCount: 3 },
  { id: 8, name: '数据结构', category: '编程', difficulty: 2, description: '链表、树、图、排序算法', resourceCount: 14 },
]

export default function KnowledgeBase() {
  const [items] = useState<KnowledgeItem[]>(MOCK_KNOWLEDGE)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [uploading, setUploading] = useState(false)

  const categories = ['all', ...new Set(items.map(i => i.category))]
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
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 text-sm"
        >
          {uploading ? '上传中...' : '📤 上传课程资料'}
        </button>
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
        <div className="bg-white rounded-lg border shadow-sm p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{items.length}</div>
          <div className="text-sm text-gray-500">知识点总数</div>
        </div>
        <div className="bg-white rounded-lg border shadow-sm p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{categories.length - 1}</div>
          <div className="text-sm text-gray-500">分类数</div>
        </div>
        <div className="bg-white rounded-lg border shadow-sm p-4 text-center">
          <div className="text-2xl font-bold text-purple-600">{items.reduce((a, i) => a + i.resourceCount, 0)}</div>
          <div className="text-sm text-gray-500">关联资源</div>
        </div>
        <div className="bg-white rounded-lg border shadow-sm p-4 text-center">
          <div className="text-2xl font-bold text-orange-600">{items.filter(i => i.difficulty >= 4).length}</div>
          <div className="text-sm text-gray-500">高难度知识点</div>
        </div>
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
              <th className="px-4 py-3 text-center">资源</th>
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
                <td className="px-4 py-3 text-center text-blue-600">{item.resourceCount}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center text-gray-400 py-8">没有找到匹配的知识点</div>
        )}
      </div>

      {/* 上传说明 */}
      <div className="bg-gray-50 rounded-lg border p-4">
        <h3 className="font-semibold text-gray-700 mb-2">📋 上传说明</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• 支持格式：PDF、Word、PPT、Markdown</li>
          <li>• 上传后系统自动解析文档，提取知识点</li>
          <li>• 自动生成练习题和讲解文档</li>
          <li>• 构建知识图谱，建立知识点关联关系</li>
        </ul>
      </div>
    </div>
  )
}
