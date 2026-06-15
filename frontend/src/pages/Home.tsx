import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">学习多智能体系统</h1>
      <p className="text-gray-600">
        基于大模型的个性化资源生成与学习多智能体系统。11 个 AI 智能体协同工作，
        通过对话了解学生，30 秒内生成 6 种个性化学习资料。
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="font-semibold text-lg mb-2">对话交互</h3>
          <p className="text-gray-600 text-sm mb-4">
            与 AI 对话构建学习画像，系统了解你的专业、目标、基础、风格。
          </p>
          <Link to="/chat" className="text-blue-600 hover:underline text-sm">
            开始对话 →
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="font-semibold text-lg mb-2">资源生成</h3>
          <p className="text-gray-600 text-sm mb-4">
            一次请求并行生成讲解文档、练习题、思维导图、代码案例、拓展阅读。
          </p>
          <Link to="/resources" className="text-blue-600 hover:underline text-sm">
            生成资源 →
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="font-semibold text-lg mb-2">系统状态</h3>
          <p className="text-gray-600 text-sm">
            后端运行正常，讯飞星火已接通，5/6 种资源可真实生成。
          </p>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">核心创新</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• 可解释 AI 决策：每个推荐都有理由</li>
          <li>• 个性化遗忘曲线：根据实际数据拟合专属曲线</li>
          <li>• 知识脚手架动态生成：按掌握度调整支持程度</li>
        </ul>
      </div>
    </div>
  )
}
