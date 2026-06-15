import { useState } from 'react'

interface QuizResult {
  totalQuestions: number
  correctAnswers: number
  score: number
  timeSpent: number
  questions: Array<{
    question: string
    userAnswer: string
    correctAnswer: string
    isCorrect: boolean
    explanation: string
    difficulty: string
  }>
}

const MOCK_RESULT: QuizResult = {
  totalQuestions: 10,
  correctAnswers: 8,
  score: 80,
  timeSpent: 420,
  questions: [
    { question: '注意力机制的主要作用？', userAnswer: 'B', correctAnswer: 'B', isCorrect: true, explanation: '注意力机制让模型聚焦关键信息。', difficulty: 'easy' },
    { question: 'Q·K^T 计算的是什么？', userAnswer: 'A', correctAnswer: 'A', isCorrect: true, explanation: 'Q·K^T 计算注意力分数矩阵。', difficulty: 'medium' },
    { question: '多头注意力的优势？', userAnswer: 'C', correctAnswer: 'C', isCorrect: true, explanation: '多头注意力能捕捉不同子空间的信息。', difficulty: 'hard' },
    { question: 'Softmax 的作用？', userAnswer: 'B', correctAnswer: 'A', isCorrect: false, explanation: 'Softmax 将分数转换为概率分布。', difficulty: 'medium' },
    { question: '位置编码的目的是？', userAnswer: 'C', correctAnswer: 'C', isCorrect: true, explanation: '位置编码让模型理解序列顺序。', difficulty: 'easy' },
    { question: 'Layer Normalization 在哪？', userAnswer: 'A', correctAnswer: 'B', isCorrect: false, explanation: 'Layer Norm 在子层之后应用。', difficulty: 'hard' },
    { question: 'Transformer 的编码器层数？', userAnswer: 'C', correctAnswer: 'C', isCorrect: true, explanation: '原始 Transformer 有 6 层编码器。', difficulty: 'easy' },
    { question: '自注意力的计算复杂度？', userAnswer: 'B', correctAnswer: 'B', isCorrect: true, explanation: '自注意力复杂度为 O(n²)。', difficulty: 'medium' },
    { question: '残差连接的作用？', userAnswer: 'A', correctAnswer: 'A', isCorrect: true, explanation: '残差连接缓解梯度消失问题。', difficulty: 'medium' },
    { question: 'BERT 使用哪种注意力？', userAnswer: 'C', correctAnswer: 'C', isCorrect: true, explanation: 'BERT 使用双向自注意力。', difficulty: 'hard' },
  ],
}

export default function QuizResult() {
  const [result] = useState<QuizResult>(MOCK_RESULT)
  const [showAnalysis, setShowAnalysis] = useState(false)

  const accuracy = (result.correctAnswers / result.totalQuestions * 100).toFixed(0)
  const avgTime = Math.round(result.timeSpent / result.totalQuestions)
  const level = result.score >= 90 ? '优秀' : result.score >= 75 ? '良好' : result.score >= 60 ? '及格' : '需努力'
  const levelColor = result.score >= 90 ? 'text-green-600' : result.score >= 75 ? 'text-blue-600' : result.score >= 60 ? 'text-yellow-600' : 'text-red-600'

  const difficultyStats = result.questions.reduce((acc, q) => {
    acc[q.difficulty] = acc[q.difficulty] || { total: 0, correct: 0 }
    acc[q.difficulty].total++
    if (q.isCorrect) acc[q.difficulty].correct++
    return acc
  }, {} as Record<string, { total: number; correct: number }>)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">练习结果</h1>
        <button
          onClick={() => setShowAnalysis(!showAnalysis)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          {showAnalysis ? '收起分析' : '详细分析'}
        </button>
      </div>

      {/* 成绩概览 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="得分" value={`${result.score}`} suffix="分" color={levelColor} />
        <StatCard label="正确率" value={accuracy} suffix="%" color="text-blue-600" />
        <StatCard label="用时" value={`${Math.floor(result.timeSpent / 60)}`} suffix="分" color="text-purple-600" />
        <StatCard label="等级" value={level} color={levelColor} />
      </div>

      {/* 难度分析 */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h3 className="font-semibold text-lg mb-4">难度分析</h3>
        <div className="space-y-3">
          {['easy', 'medium', 'hard'].map(diff => {
            const stats = difficultyStats[diff]
            if (!stats) return null
            const pct = Math.round(stats.correct / stats.total * 100)
            return (
              <div key={diff}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{diff === 'easy' ? '基础' : diff === 'medium' ? '中等' : '提高'}</span>
                  <span className="text-gray-500">{stats.correct}/{stats.total} ({pct}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 详细分析 */}
      {showAnalysis && (
        <div className="bg-white rounded-lg border shadow-sm p-6 space-y-4">
          <h3 className="font-semibold text-lg">逐题分析</h3>
          {result.questions.map((q, i) => (
            <div key={i} className={`border rounded-lg p-4 ${q.isCorrect ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
              <div className="flex items-start gap-3">
                <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                  q.isCorrect ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                }`}>
                  {q.isCorrect ? '✓' : '✗'}
                </span>
                <div className="flex-1">
                  <p className="font-medium text-sm">Q{i + 1}. {q.question}</p>
                  <div className="mt-2 text-sm">
                    <span className="text-gray-500">你的答案：</span>
                    <span className={q.isCorrect ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>{q.userAnswer}</span>
                    {!q.isCorrect && (
                      <>
                        <span className="text-gray-500 ml-3">正确答案：</span>
                        <span className="text-green-600 font-medium">{q.correctAnswer}</span>
                      </>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-gray-600">💡 {q.explanation}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  q.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                  q.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {q.difficulty === 'easy' ? '基础' : q.difficulty === 'medium' ? '中等' : '提高'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 行动建议 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">💡 学习建议</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          {result.score < 80 && <li>• 建议重新学习相关知识点，重点关注错题</li>}
          {difficultyStats.hard && difficultyStats.hard.correct < difficultyStats.hard.total * 0.5 && (
            <li>• 提高题正确率较低，建议先巩固基础再挑战难题</li>
          )}
          {avgTime > 60 && <li>• 答题速度较慢，建议多做练习提高熟练度</li>}
          {result.score >= 90 && <li>• 表现优秀！可以尝试更高级的主题</li>}
        </ul>
      </div>
    </div>
  )
}

function StatCard({ label, value, suffix, color }: { label: string; value: string | number; suffix?: string; color: string }) {
  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 text-center">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className={`text-3xl font-bold ${color}`}>
        {value}{suffix && <span className="text-lg ml-1">{suffix}</span>}
      </div>
    </div>
  )
}
