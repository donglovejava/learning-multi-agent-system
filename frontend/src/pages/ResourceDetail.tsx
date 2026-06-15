import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

interface ResourceItem {
  id: number
  resource_type: string
  content: any
  scaffold_level?: string
  quality_score?: number
  review_status?: string
  created_at?: string
}

const TYPE_LABELS: Record<string, string> = {
  document: '📄 讲解文档',
  quiz: '📝 练习题',
  mindmap: '🧠 思维导图',
  code: '💻 代码案例',
  reading: '📚 拓展阅读',
  video: '🎬 教学视频',
}

const STATUS_COLORS: Record<string, string> = {
  passed: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  rejected: 'bg-red-100 text-red-700',
}

// 模拟数据（后端未通时使用）
const MOCK_RESOURCES: ResourceItem[] = [
  {
    id: 1, resource_type: 'document', scaffold_level: 'medium', review_status: 'passed',
    content: '# 注意力机制\n\n## 概述\n注意力机制是深度学习的核心技术...\n\n## 核心概念\n自注意力允许模型关注输入的不同部分...',
    created_at: '2026-06-15T10:30:00',
  },
  {
    id: 2, resource_type: 'quiz', review_status: 'passed',
    content: { questions: [
      { question: '注意力机制的主要作用？', options: ['A. 减少参数', 'B. 聚焦关键信息', 'C. 加速训练', 'D. 增加层数'], answer: 'B', explanation: '注意力机制让模型聚焦关键信息。', difficulty: 'easy' },
      { question: 'Q·K^T 计算的是什么？', options: ['A. 注意力分数', 'B. 损失函数', 'C. 梯度', 'D. 学习率'], answer: 'A', explanation: 'Q·K^T 计算注意力分数矩阵。', difficulty: 'medium' },
    ]},
    created_at: '2026-06-15T10:30:00',
  },
  {
    id: 3, resource_type: 'mindmap', review_status: 'passed',
    content: { data: { root: { id: 'attention', label: '注意力机制' }, children: [
      { id: 'self', label: '自注意力', children: [{ id: 'qkv', label: 'Q/K/V' }, { id: 'softmax', label: 'Softmax' }] },
      { id: 'multi', label: '多头注意力', children: [{ id: 'parallel', label: '并行计算' }] },
    ]}},
    created_at: '2026-06-15T10:30:00',
  },
  {
    id: 4, resource_type: 'code', review_status: 'passed',
    content: { language: 'python', code: 'import torch\nimport torch.nn as nn\n\nclass SelfAttention(nn.Module):\n    def __init__(self, embed_size, heads):\n        super().__init__()\n        self.heads = heads\n        self.to_qkv = nn.Linear(embed_size, embed_size * 3)\n        self.fc = nn.Linear(embed_size, embed_size)\n\n    def forward(self, x):\n        B, N, C = x.shape\n        qkv = self.to_qkv(x).reshape(B, N, 3, self.heads, C // self.heads)\n        q, k, v = qkv.unbind(2)\n        attn = (q @ k.transpose(-2, -1)) / (C ** 0.5)\n        attn = attn.softmax(dim=-1)\n        out = (attn @ v).transpose(1, 2).reshape(B, N, C)\n        return self.fc(out)', runnable: true },
    created_at: '2026-06-15T10:30:00',
  },
  {
    id: 5, resource_type: 'reading', review_status: 'passed',
    content: '## 延伸主题\n\n### 1. Transformer 架构演进\n从原始 Transformer 到 BERT、GPT 系列的发展脉络...\n\n### 2. 注意力机制的数学本质\n注意力本质上是一种可微分的软查找机制...\n\n### 3. 注意力在其他领域的应用\n计算机视觉中的 ViT、音频处理中的 Conformer...',
    created_at: '2026-06-15T10:30:00',
  },
]

export default function ResourceDetail() {
  const [resources, setResources] = useState<ResourceItem[]>(MOCK_RESOURCES)
  const [selected, setSelected] = useState<ResourceItem | null>(null)
  const [studentId] = useState('demo-001')

  useEffect(() => {
    fetch(`/api/v1/resources/${studentId}`)
      .then(r => r.json())
      .then(data => { if (Array.isArray(data)) setResources(data) })
      .catch(() => { /* 用模拟数据 */ })
  }, [studentId])

  const renderContent = (res: ResourceItem) => {
    switch (res.resource_type) {
      case 'document':
      case 'reading':
        return (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{typeof res.content === 'string' ? res.content : JSON.stringify(res.content)}</ReactMarkdown>
          </div>
        )
      case 'quiz':
        return (
          <div className="space-y-4">
            {res.content?.questions?.map((q: any, i: number) => (
              <div key={i} className="border rounded-lg p-4">
                <p className="font-medium">Q{i + 1}. [{q.difficulty === 'easy' ? '基础' : q.difficulty === 'medium' ? '中等' : '提高'}] {q.question}</p>
                <div className="mt-2 space-y-1">
                  {q.options?.map((opt: string, j: number) => (
                    <div key={j} className={`text-sm px-3 py-1 rounded ${opt.startsWith(q.answer) ? 'bg-green-100 font-medium' : 'bg-gray-50'}`}>{opt}</div>
                  ))}
                </div>
                <p className="mt-2 text-sm text-gray-600">💡 {q.explanation}</p>
              </div>
            ))}
          </div>
        )
      case 'mindmap':
        return <MindMapView data={res.content?.data} />
      case 'code':
        return (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm text-gray-500">语言：{res.content?.language || 'python'}</span>
              {res.content?.runnable && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">✓ 可运行</span>}
            </div>
            <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-x-auto"><code>{res.content?.code}</code></pre>
          </div>
        )
      default:
        return <pre className="text-sm">{JSON.stringify(res.content, null, 2)}</pre>
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">我的资源</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 资源列表 */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="font-semibold text-gray-700">已生成资源（{resources.length}）</h3>
          {resources.map(res => (
            <button
              key={res.id}
              onClick={() => setSelected(res)}
              className={`w-full text-left p-3 rounded-lg border transition ${
                selected?.id === res.id ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="font-medium text-sm">{TYPE_LABELS[res.resource_type] || res.resource_type}</div>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[res.review_status || 'pending']}`}>
                  {res.review_status === 'passed' ? '已通过' : res.review_status === 'rejected' ? '未通过' : '待审核'}
                </span>
                {res.scaffold_level && (
                  <span className="text-xs text-gray-400">
                    {res.scaffold_level === 'high' ? '高支持' : res.scaffold_level === 'low' ? '低支持' : '中支持'}
                  </span>
                )}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {res.created_at ? new Date(res.created_at).toLocaleString('zh-CN') : ''}
              </div>
            </button>
          ))}
        </div>

        {/* 资源详情 */}
        <div className="lg:col-span-2">
          {selected ? (
            <div className="bg-white rounded-lg border shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">{TYPE_LABELS[selected.resource_type] || selected.resource_type}</h2>
                {selected.quality_score && (
                  <span className="text-sm text-gray-500">质量分：{(selected.quality_score * 100).toFixed(0)}%</span>
                )}
              </div>
              {renderContent(selected)}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-12 text-center text-gray-400">
              选择一个资源查看详情
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MindMapView({ data }: { data?: any }) {
  if (!data) return <p className="text-gray-400">暂无数据</p>

  const renderNode = (node: any, depth: number = 0) => (
    <div key={node.id} style={{ marginLeft: depth * 20 }}>
      <div className={`inline-block px-3 py-1.5 rounded-lg text-sm font-medium ${
        depth === 0 ? 'bg-blue-600 text-white' :
        depth === 1 ? 'bg-blue-100 text-blue-800' :
        'bg-gray-100 text-gray-700'
      }`}>
        {node.label}
      </div>
      {node.children?.map((child: any) => renderNode(child, depth + 1))}
    </div>
  )

  return (
    <div className="space-y-2">
      {renderNode(data.root || data)}
      {data.children?.map((child: any) => renderNode(child, 1))}
    </div>
  )
}
