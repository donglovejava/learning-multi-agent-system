import { useEffect, useState } from 'react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'

const DIMENSIONS = ['知识基础', '学习风格', '学习动机', '元认知', '学习进度', '练习正确率']

interface ProfileData {
  major?: string
  learning_goal?: string
  knowledge_base?: number
  learning_style?: string
  motivation?: string
  metacognition?: number
  scaffold_level?: string
  version?: number
}

export default function Profile() {
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [studentId] = useState('demo-001')

  useEffect(() => {
    fetch(`/api/v1/profile/${studentId}`)
      .then(r => r.json())
      .then(data => {
        setProfile(data.dimensions || data)
        setLoading(false)
      })
      .catch(() => {
        // 后端未运行时用模拟数据
        setProfile({
          major: '计算机科学与技术',
          learning_goal: '考研',
          knowledge_base: 0.65,
          learning_style: 'visual',
          motivation: '内在',
          metacognition: 0.7,
          scaffold_level: 'medium',
          version: 1,
        })
        setLoading(false)
      })
  }, [studentId])

  const radarData = DIMENSIONS.map(dim => {
    const value = (() => {
      switch (dim) {
        case '知识基础': return (profile?.knowledge_base ?? 0.5) * 100
        case '元认知': return (profile?.metacognition ?? 0.5) * 100
        case '学习动机': return profile?.motivation === '内在' ? 80 : profile?.motivation === '外在' ? 60 : 50
        case '学习风格': return profile?.learning_style === 'visual' ? 85 : 60
        case '学习进度': return 45
        case '练习正确率': return 72
        default: return 50
      }
    })()
    return { dim, value: Math.round(value) }
  })

  if (loading) return <p className="text-gray-400">加载中...</p>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">学习画像</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 雷达图 */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="font-semibold text-lg mb-4">6 维度画像雷达图</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="dim" tick={{ fontSize: 12 }} />
              <PolarRadiusAxis domain={[0, 100]} />
              <Radar name="掌握度" dataKey="value" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.4} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* 画像信息 */}
        <div className="bg-white rounded-lg border shadow-sm p-6 space-y-4">
          <h3 className="font-semibold text-lg">基本信息</h3>
          <InfoRow label="专业" value={profile?.major || '未设置'} />
          <InfoRow label="学习目标" value={profile?.learning_goal || '未设置'} />
          <InfoRow label="学习风格" value={styleLabel(profile?.learning_style)} />
          <InfoRow label="学习动机" value={motivationLabel(profile?.motivation)} />
          <InfoRow label="脚手架级别" value={scaffoldLabel(profile?.scaffold_level)} />
          <InfoRow label="画像版本" value={`v${profile?.version ?? 1}`} />
        </div>
      </div>

      {/* 维度详情 */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h3 className="font-semibold text-lg mb-4">维度详情</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {radarData.map(d => (
            <div key={d.dim} className="border rounded-lg p-3">
              <div className="text-sm text-gray-500">{d.dim}</div>
              <div className="text-2xl font-bold text-blue-600">{d.value}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${d.value}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b pb-2">
      <span className="text-gray-500 text-sm">{label}</span>
      <span className="font-medium text-sm">{value}</span>
    </div>
  )
}

function styleLabel(s?: string) {
  const map: Record<string, string> = { visual: '视觉型', auditory: '听觉型', kinesthetic: '动觉型', reading: '读写型' }
  return map[s || ''] || s || '未评估'
}
function motivationLabel(s?: string) {
  const map: Record<string, string> = { intrinsic: '内在动机', extrinsic: '外在动机' }
  return map[s || ''] || s || '未评估'
}
function scaffoldLabel(s?: string) {
  const map: Record<string, string> = { high: '高支持（初学者）', medium: '中支持（进阶者）', low: '低支持（高级者）' }
  return map[s || ''] || s || '未设置'
}
