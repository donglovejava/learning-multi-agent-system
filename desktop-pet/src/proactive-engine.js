/**
 * 宠物主动行为引擎 - Pet Proactive Behavior
 *
 * 宠物不只是被动回应，还会主动关心学生：
 * - 检测到学习太久 → 提醒休息
 * - 检测到深夜 → 催睡觉
 * - 检测到连续答错 → 安慰鼓励
 * - 检测到成就 → 庆祝
 * - 长时间不互动 → 主动搭话
 *
 * 通过定时轮询 + 事件监听实现。
 */

class PetProactiveEngine {
  constructor(emotionEngine, memory) {
    this.emotion = emotionEngine;
    this.memory = memory;
    this.timers = [];
    this.proactiveCallbacks = [];
    this.lastProactiveTime = 0;
    this.proactiveCooldown = 30000; // 30 秒内不重复主动
  }

  /**
   * 启动所有主动行为监听
   */
  start() {
    // 每 30 秒检查一次是否需要主动关心
    const checkTimer = setInterval(() => this.check(), 30000);
    this.timers.push(checkTimer);

    // 每分钟更新情感引擎的时间上下文
    const timeTimer = setInterval(() => this.emotion.updateTimeContext(), 60000);
    this.timers.push(timeTimer);

    // 每 5 分钟自然衰减
    const decayTimer = setInterval(() => {
      for (let i = 0; i < 60; i++) this.emotion.tick(); // 60 ticks = 3 秒
    }, 3000);
    this.timers.push(decayTimer);

    // 每天零点重置
    const now = new Date();
    const msToMidnight = (24 - now.getHours()) * 3600000 - now.getMinutes() * 60000 - now.getSeconds() * 1000;
    const midnightTimer = setTimeout(() => {
      this.emotion.newDay();
      this.memory.newDay();
      // 设置每日循环
      setInterval(() => {
        this.emotion.newDay();
        this.memory.newDay();
      }, 86400000);
    }, msToMidnight);
    this.timers.push(midnightTimer);

    this.emotion.updateTimeContext();
  }

  /**
   * 注册主动行为回调
   */
  onProactive(callback) {
    this.proactiveCallbacks.push(callback);
  }

  /**
   * 检查是否需要主动关心
   */
  check() {
    const now = Date.now();
    if (now - this.lastProactiveTime < this.proactiveCooldown) return;

    const mood = this.emotion.getMood();
    let message = null;
    let action = null;

    // 1. 深夜检测
    if (mood.timeContext === 'late_night') {
      message = this.emotion.getProactiveMessage();
      action = 'sleepy';
    }
    // 2. 学习太久
    else if (mood.studyDuration > 45) {
      message = this.emotion.getProactiveMessage();
      action = 'worry';
    }
    // 3. 连续答错
    else if (mood.quizFailStreak >= 3) {
      message = this.emotion.getProactiveMessage();
      action = 'worry';
    }
    // 4. 连续答对
    else if (mood.quizStreak >= 3) {
      message = this.emotion.getProactiveMessage();
      action = 'happy';
    }
    // 5. 精力低
    else if (mood.energy < 0.3) {
      message = this.emotion.getProactiveMessage();
      action = 'sleep';
    }
    // 6. 长时间不互动
    else {
      const timeSinceLast = (now - this.emotion.lastInteractionTime) / 1000 / 60;
      if (timeSinceLast > 5 && mood.mood === 'calm') {
        message = this.emotion.getProactiveMessage();
        action = 'idle';
      }
    }

    if (message) {
      this.lastProactiveTime = now;
      this.proactiveCallbacks.forEach(cb => cb(message, action));
    }
  }

  /**
   * 外部事件通知（由主进程调用）
   */
  notifyEvent(event, data) {
    switch (event) {
      case 'quiz_result':
        this.emotion.processQuizResult(data.score, data.total);
        this.memory.addQuizResult(data.subject || '综合', data.score, data.total);
        if (data.score / data.total >= 0.9) {
          this.memory.addMilestone('测验优秀', `${data.subject || '综合'}测验得分 ${data.score}/${data.total}`);
        }
        break;

      case 'study_start':
        this.emotion.startStudySession();
        break;

      case 'study_end':
        const duration = this.emotion.getStudyDuration();
        this.memory.addStudyLog(data.subject || '综合', duration, data.note || '');
        break;

      case 'chat':
        this.emotion.analyzeMessage(data.message);
        this.memory.addConversation('user', data.message);
        this.memory.incrementInteraction();
        break;

      case 'chat_reply':
        this.memory.addConversation('pet', data.reply);
        break;

      case 'student_info':
        if (data.name) this.memory.setStudentName(data.name);
        if (data.grade) this.memory.setStudentGrade(data.grade);
        if (data.favoriteSubject) this.memory.setFavoriteSubject(data.favoriteSubject);
        if (data.weakestSubject) this.memory.setWeakestSubject(data.weakestSubject);
        if (data.goal) this.memory.setGoal(data.goal);
        break;
    }
  }

  /**
   * 停止所有定时器
   */
  stop() {
    this.timers.forEach(t => clearInterval(t));
    this.timers = [];
  }
}

module.exports = PetProactiveEngine;
