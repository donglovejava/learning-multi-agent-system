import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const DIMENSIONS = [
  { key: '知识掌握度', weight: 20, threshold: 60 },
  { key: '学习进度', weight: 15, threshold: 50 },
  { key: '学习时长', weight: 10, threshold: 50 },
  { key: '资源使用率', weight: 10, threshold: 40 },
  { key: '练习正确率', weight: 15, threshold: 50 },
  { key: '学习频率', weight: 5, threshold: 43 },
  { key: '知识遗忘率', weight: 10, threshold: 70 },
  { key: '深度学习能力', weight: 5, threshold: 40 },
  { key: '学习主动性', weight: 5, threshold: 20 },
  { key: '学习持续性', weight: 5, threshold: 60 },
]

const MOCK_SCORES: Record<string, number> = {
  '知识掌握度': 72,
  '学习进度': 45,
  '学习时长': 68,
  '资源使用率': 55,
  '练习正确率': 65,
  '学习频率': 40,
  '知识遗忘率': 75,
  '深度学习能力': 58,
  '学习主动性': 30,
  '学习持续性': 62,
}

export default function Assessment() {
  const totalScore = DIMENSIONS.reduce((acc, d) => acc + (MOCK_SCORES[d.key] || 0) * d.weight / 100, 0)
  const level = totalScore > 80 ? '优秀' : totalScore > 60 ? '良好' : '需改进'
  const warnings = DIMENSIONS.filter(d => (MOCK_SCORES[d.key] || 0) < d.threshold)

  const chartData = DIMENSIONS.map(d => ({
    name: d.key,
    score: MOCK_SCORES[d.key] || 0,
    threshold: d.threshold,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">学习效果评估</h1>
        <div className={`px-4 py-2 rounded-lg font-semibold ${
          level === '优秀' ? 'bg-green-100 text-green-800' :
          level === '良好' ? 'bg-blue-100 text-blue-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          综合等级：{level}（{Math.round(totalScore)} 分）
        </div>
      </div>

      {/* 柱状图 */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h3 className="font-semibold text-lg mb-4">10 维度评估得分</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="score" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={index} fill={entry.score < entry.threshold ? '#ef4444' : '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 预警列表 */}
      {warnings.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="font-semibold text-red-900 mb-2">⚠️ 学习预警（{warnings.length} 项）</h3>
          <ul className="space-y-1">
            {warnings.map(w => (
              <li key={w.key} className="text-sm text-red-800">
                • <strong>{w.key}</strong>：当前 {MOCK_SCORES[w.key]}%，低于阈值 {w.threshold}%
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 维度详情表 */}
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">维度</th>
              <th className="px-4 py-3 text-center">权重</th>
              <th className="px-4 py-3 text-center">得分</th>
              <th className="px-4 py-3 text-center">阈值</th>
              <th className="px-4 py-3 text-center">状态</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {DIMENSIONS.map(d => {
              const score = MOCK_SCORES[d.key] || 0
              const passed = score >= d.threshold
              return (
                <tr key={d.key} className={passed ? '' : 'bg-red-50'}>
                  <td className="px-4 py-3 font-medium">{d.key}</td>
                  <td className="px-4 py-3 text-center text-gray-500">{d.weight}%</td>
                  <td className="px-4 py-3 text-center font-semibold">{score}%</td>
                  <td className="px-4 py-3 text-center text-gray-500">{d.threshold}%</td>
                  <td className="px-4 py-3 text-center">
                    {passed ? <span className="text-green-600">✓ 正常</span> : <span className="text-red-600"> 预警</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
