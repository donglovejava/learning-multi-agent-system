/**
 * 宠物长期记忆系统
 *
 * 记住学生的名字、喜好、历史对话、学习里程碑等，
 * 让宠物真正"懂你"。
 *
 * 存储：本地 JSON 文件（desktop-pet/data/memory.json）
 * 未来可接入 PostgreSQL（复用后端数据库）
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const MEMORY_FILE = path.join(DATA_DIR, 'memory.json');

class PetMemory {
  constructor() {
    this.data = this.load();
  }

  load() {
    try {
      if (fs.existsSync(MEMORY_FILE)) {
        return JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf-8'));
      }
    } catch (e) {
      console.error('加载记忆失败:', e.message);
    }
    return this.defaultMemory();
  }

  save() {
    try {
      if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
      }
      fs.writeFileSync(MEMORY_FILE, JSON.stringify(this.data, null, 2), 'utf-8');
    } catch (e) {
      console.error('保存记忆失败:', e.message);
    }
  }

  defaultMemory() {
    return {
      student: {
        name: null,
        grade: null,
        favoriteSubject: null,
        weakestSubject: null,
        goal: null,
        personality: null,
      },
      relationship: {
        daysKnown: 0,
        totalInteractions: 0,
        trustLevel: 0.1,
        nickname: null, // 宠物给学生的昵称
        petName: '小橘',
      },
      memories: [], // 重要事件记录
      milestones: [], // 学习里程碑
      preferences: {
        talkTime: [], // 喜欢聊天的时间段
        topics: [],   // 喜欢聊的话题
        encouragements: [], // 有效的鼓励方式
      },
      conversationHistory: [], // 最近对话（保留最近 50 条）
      quizHistory: [], // 测验历史
      studyLog: [], // 学习日志
    };
  }

  // === 学生信息 ===

  setStudentName(name) {
    this.data.student.name = name;
    this.save();
  }

  setStudentGrade(grade) {
    this.data.student.grade = grade;
    this.save();
  }

  setFavoriteSubject(subject) {
    this.data.student.favoriteSubject = subject;
    this.save();
  }

  setWeakestSubject(subject) {
    this.data.student.weakestSubject = subject;
    this.save();
  }

  setGoal(goal) {
    this.data.student.goal = goal;
    this.save();
  }

  // === 关系 ===

  incrementInteraction() {
    this.data.relationship.totalInteractions++;
    this.data.relationship.trustLevel = Math.min(1, this.data.relationship.trustLevel + 0.01);
    this.save();
  }

  newDay() {
    this.data.relationship.daysKnown++;
    this.save();
  }

  getDaysKnown() {
    return this.data.relationship.daysKnown;
  }

  getTrustLevel() {
    return this.data.relationship.trustLevel;
  }

  // === 重要事件 ===

  addMemory(event, emotion, detail) {
    this.data.memories.push({
      event,
      emotion,
      detail,
      timestamp: Date.now(),
    });
    // 只保留最近 100 条
    if (this.data.memories.length > 100) {
      this.data.memories = this.data.memories.slice(-100);
    }
    this.save();
  }

  getRecentMemories(count = 5) {
    return this.data.memories.slice(-count);
  }

  // === 里程碑 ===

  addMilestone(title, description) {
    this.data.milestones.push({
      title,
      description,
      timestamp: Date.now(),
    });
    this.save();
  }

  getMilestones() {
    return this.data.milestones;
  }

  // === 对话历史 ===

  addConversation(role, content) {
    this.data.conversationHistory.push({
      role,
      content,
      timestamp: Date.now(),
    });
    // 只保留最近 50 条
    if (this.data.conversationHistory.length > 50) {
      this.data.conversationHistory = this.data.conversationHistory.slice(-50);
    }
    this.save();
  }

  getRecentConversations(count = 10) {
    return this.data.conversationHistory.slice(-count);
  }

  // === 测验历史 ===

  addQuizResult(subject, score, total) {
    this.data.quizHistory.push({
      subject,
      score,
      total,
      ratio: score / total,
      timestamp: Date.now(),
    });
    if (this.data.quizHistory.length > 100) {
      this.data.quizHistory = this.data.quizHistory.slice(-100);
    }
    this.save();
  }

  getRecentQuizResults(count = 5) {
    return this.data.quizHistory.slice(-count);
  }

  getAverageScore() {
    if (this.data.quizHistory.length === 0) return null;
    const sum = this.data.quizHistory.reduce((acc, q) => acc + q.ratio, 0);
    return sum / this.data.quizHistory.length;
  }

  // === 学习日志 ===

  addStudyLog(subject, duration, note) {
    this.data.studyLog.push({
      subject,
      duration,
      note,
      timestamp: Date.now(),
    });
    if (this.data.studyLog.length > 200) {
      this.data.studyLog = this.data.studyLog.slice(-200);
    }
    this.save();
  }

  // === 智能回忆 ===

  /**
   * 根据当前情境，从记忆中检索相关信息，用于生成个性化回应
   */
  recall(context) {
    const recalls = [];

    // 如果知道学生名字
    if (this.data.student.name) {
      recalls.push(`学生叫${this.data.student.name}`);
    }

    // 如果知道薄弱科目
    if (this.data.student.weakestSubject) {
      recalls.push(`${this.data.student.weakestSubject}比较薄弱`);
    }

    // 如果知道目标
    if (this.data.student.goal) {
      recalls.push(`目标是${this.data.student.goal}`);
    }

    // 最近的测验表现
    const recentQuizzes = this.getRecentQuizResults(3);
    if (recentQuizzes.length > 0) {
      const avgRatio = recentQuizzes.reduce((a, q) => a + q.ratio, 0) / recentQuizzes.length;
      if (avgRatio > 0.8) {
        recalls.push('最近测验表现很好');
      } else if (avgRatio < 0.5) {
        recalls.push('最近测验需要加油');
      }
    }

    // 认识多久了
    const days = this.getDaysKnown();
    if (days > 30) {
      recalls.push(`已经陪伴${days}天了`);
    } else if (days > 0) {
      recalls.push(`认识${days}天了`);
    }

    // 信任度
    const trust = this.getTrustLevel();
    if (trust > 0.7) {
      recalls.push('关系很亲密');
    } else if (trust > 0.4) {
      recalls.push('关系不错');
    }

    return recalls;
  }

  /**
   * 生成个性化问候语
   */
  getGreeting() {
    const hour = new Date().getHours();
    const name = this.data.student.name ? this.data.student.name : '同学';
    const days = this.getDaysKnown();

    let timeGreeting = '';
    if (hour >= 5 && hour < 9) timeGreeting = '早上好';
    else if (hour >= 9 && hour < 12) timeGreeting = '上午好';
    else if (hour >= 12 && hour < 14) timeGreeting = '中午好';
    else if (hour >= 14 && hour < 18) timeGreeting = '下午好';
    else if (hour >= 18 && hour < 22) timeGreeting = '晚上好';
    else timeGreeting = '夜深了';

    let personalTouch = '';
    if (days === 0) {
      personalTouch = `你好${name}！我是小橘，从今天开始我会一直陪着你的！`;
    } else if (days === 1) {
      personalTouch = `${name}，第二天见面啦！昨天学得怎么样？`;
    } else if (days < 7) {
      personalTouch = `${name}，我们已经认识${days}天啦！`;
    } else if (days < 30) {
      personalTouch = `${name}，${days}天了，越来越了解你了~`;
    } else {
      personalTouch = `${name}，${days}天了！你是我最重要的朋友~`;
    }

    // 如果有薄弱科目，适时提醒
    if (this.data.student.weakestSubject && Math.random() < 0.3) {
      personalTouch += ` 今天的${this.data.student.weakestSubject}也要加油哦！`;
    }

    return `${timeGreeting}，${personalTouch}`;
  }
}

module.exports = PetMemory;
