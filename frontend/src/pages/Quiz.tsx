import { useState } from 'react'

interface Question {
  id: string
  question: string
  options: string[]
  answer: string
  explanation: string
  difficulty: string
  points: number
}

const MOCK_QUESTIONS: Question[] = [
  {
    id: 'q1',
    question: '注意力机制的主要作用是什么？',
    options: ['A. 减少模型参数量', 'B. 让模型聚焦于关键信息', 'C. 加速训练过程', 'D. 增加网络层数'],
    answer: 'B',
    explanation: '注意力机制允许模型在处理序列数据时，对不同位置的输入赋予不同的权重，从而聚焦于关键信息。',
    difficulty: 'easy',
    points: 10,
  },
  {
    id: 'q2',
    question: '在自注意力机制中，Query、Key、Value 通过什么方式计算注意力分数？',
    options: ['A. 点积运算', 'B. 余弦相似度', 'C. 欧氏距离', 'D. 曼哈顿距离'],
    answer: 'A',
    explanation: '自注意力通过 Q·K^T 的点积运算计算注意力分数，再经 Softmax 归一化。',
    difficulty: 'medium',
    points: 10,
  },
  {
    id: 'q3',
    question: '多头注意力机制相比单头注意力的主要优势是？',
    options: ['A. 计算更快', 'B. 参数更少', 'C. 能捕捉不同子空间的信息', 'D. 更容易训练'],
    answer: 'C',
    explanation: '多头注意力将输入映射到多个不同的子空间，使模型能同时关注不同位置的不同信息。',
    difficulty: 'hard',
    points: 10,
  },
]

export default function Quiz() {
  const [questions] = useState<Question[]>(MOCK_QUESTIONS)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitted, setSubmitted] = useState(false)
  const [currentQ, setCurrentQ] = useState(0)

  const handleSubmit = () => setSubmitted(true)
  const handleReset = () => {
    setAnswers({})
    setSubmitted(false)
    setCurrentQ(0)
  }

  const score = questions.reduce((acc, q) => acc + (answers[q.id] === q.answer ? q.points : 0), 0)
  const totalPoints = questions.reduce((acc, q) => acc + q.points, 0)

  const q = questions[currentQ]
  const isCorrect = submitted && answers[q.id] === q.answer

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">练习答题</h1>
        {submitted && (
          <div className="text-lg font-semibold">
            得分：<span className={score >= totalPoints * 0.8 ? 'text-green-600' : score >= totalPoints * 0.6 ? 'text-yellow-600' : 'text-red-600'}>
              {score} / {totalPoints}
            </span>
          </div>
        )}
      </div>

      {/* 进度条 */}
      <div className="flex gap-1">
        {questions.map((_, i) => (
          <div
            key={i}
            className={`h-2 flex-1 rounded-full cursor-pointer ${
              i === currentQ ? 'bg-blue-500' :
              submitted ? (answers[questions[i].id] === questions[i].answer ? 'bg-green-400' : 'bg-red-400') :
              answers[questions[i].id] ? 'bg-blue-300' : 'bg-gray-200'
            }`}
            onClick={() => setCurrentQ(i)}
          />
        ))}
      </div>

      {/* 题目卡片 */}
      <div className="bg-white rounded-lg border shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">第 {currentQ + 1} / {questions.length} 题</span>
          <span className={`text-xs px-2 py-1 rounded ${
            q.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
            q.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          }`}>
            {q.difficulty === 'easy' ? '基础' : q.difficulty === 'medium' ? '中等' : '提高'} · {q.points} 分
          </span>
        </div>

        <h3 className="text-lg font-medium">{q.question}</h3>

        <div className="space-y-2">
          {q.options.map((opt, i) => {
            const letter = opt[0]
            const selected = answers[q.id] === letter
            const showResult = submitted
            const correct = letter === q.answer
            return (
              <button
                key={i}
                onClick={() => !submitted && setAnswers(prev => ({ ...prev, [q.id]: letter }))}
                disabled={submitted}
                className={`w-full text-left px-4 py-3 rounded-lg border-2 transition ${
                  showResult
                    ? correct ? 'border-green-400 bg-green-50' : selected ? 'border-red-400 bg-red-50' : 'border-gray-200'
                    : selected ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {opt}
                {showResult && correct && <span className="ml-2 text-green-600">✓</span>}
                {showResult && selected && !correct && <span className="ml-2 text-red-600">✗</span>}
              </button>
            )
          })}
        </div>

        {/* 解析 */}
        {submitted && (
          <div className={`p-4 rounded-lg ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
            <div className="font-medium text-sm mb-1">{isCorrect ? '回答正确！' : '回答错误'}</div>
            <div className="text-sm text-gray-700">{q.explanation}</div>
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-3">
        <button
          onClick={() => setCurrentQ(i => Math.max(0, i - 1))}
          disabled={currentQ === 0}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          上一题
        </button>
        {currentQ < questions.length - 1 ? (
          <button
            onClick={() => setCurrentQ(i => i + 1)}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            下一题
          </button>
        ) : !submitted ? (
          <button
            onClick={handleSubmit}
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            提交答案
          </button>
        ) : (
          <button
            onClick={handleReset}
            className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            重新答题
          </button>
        )}
      </div>
    </div>
  )
}
