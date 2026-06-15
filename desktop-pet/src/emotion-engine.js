/**
 * 宠物情感引擎 - Pet Emotion Engine
 *
 * 根据学生的行为、对话、时间等信号，计算宠物的情感状态，
 * 驱动宠物做出相应的表情、动作和回应。
 *
 * 情感维度：
 * - valence（效价）：-1(难过) ~ +1(开心)
 * - arousal（唤醒）：0(平静) ~ 1(兴奋)
 * - trust（信任）：0~1，基于长期互动积累
 */

class PetEmotionEngine {
  constructor() {
    this.valence = 0.3;    // 初始偏开心
    this.arousal = 0.2;    // 初始平静
    this.trust = 0.1;      // 初始信任低，随互动增长
    this.energy = 0.8;     // 精力值，随时间下降
    this.mood = 'neutral'; // 当前心情标签

    // 情感衰减参数
    this.decayRate = 0.001;  // 情感自然衰减
    this.energyDecay = 0.0005; // 精力自然衰减

    // 情绪阈值
    this.thresholds = {
      happy:    { valence: 0.5,  arousal: 0.3 },
      excited:  { valence: 0.7,  arousal: 0.6 },
      calm:     { valence: 0.0,  arousal: 0.1 },
      worried:  { valence: -0.3, arousal: 0.2 },
      sad:      { valence: -0.5, arousal: 0.1 },
      sleepy:   { valence: 0.0,  arousal: 0.0, energy: 0.3 },
    };

    // 互动历史
    this.interactionCount = 0;
    this.lastInteractionTime = Date.now();
    this.positiveInteractions = 0;
    this.negativeInteractions = 0;

    // 学习状态感知
    this.studySessionStart = null;
    this.quizStreak = 0;       // 连续答对
    this.quizFailStreak = 0;   // 连续答错
    this.lastQuizScore = null;

    // 时间感知
    this.timeContext = null;
  }

  /**
   * 处理对话内容，分析情感
   */
  analyzeMessage(message) {
    const lower = message.toLowerCase();

    // 积极信号
    const positiveWords = ['开心', '高兴', '太好了', '棒', '厉害', '谢谢', '哈哈', '😊', '👍', '爱', '喜欢'];
    const negativeWords = ['难过', '烦', '累', '不想', '放弃', '讨厌', '差', '笨', '😢', '😭', '烦死了'];
    const anxiousWords = ['担心', '害怕', '紧张', '考不好', '来不及', '怎么办', '焦虑'];
    const tiredWords = ['困', '累', '想睡', '休息', '晚安', '好累'];

    let valenceDelta = 0;
    let arousalDelta = 0;

    positiveWords.forEach(w => { if (message.includes(w)) valenceDelta += 0.15; arousalDelta += 0.05; });
    negativeWords.forEach(w => { if (message.includes(w)) valenceDelta -= 0.2; });
    anxiousWords.forEach(w => { if (message.includes(w)) { valenceDelta -= 0.1; arousalDelta += 0.15; } });
    tiredWords.forEach(w => { if (message.includes(w)) { arousalDelta -= 0.2; this.energy -= 0.1; } });

    this.valence = Math.max(-1, Math.min(1, this.valence + valenceDelta));
    this.arousal = Math.max(0, Math.min(1, this.arousal + arousalDelta));
    this.trust = Math.min(1, this.trust + 0.02);
    this.interactionCount++;
    this.lastInteractionTime = Date.now();

    if (valenceDelta > 0) this.positiveInteractions++;
    if (valenceDelta < 0) this.negativeInteractions++;

    this.updateMood();
    return this.getMood();
  }

  /**
   * 处理测验结果
   */
  processQuizResult(score, totalQuestions) {
    const ratio = score / totalQuestions;
    this.lastQuizScore = ratio;

    if (ratio >= 0.8) {
      this.quizStreak++;
      this.quizFailStreak = 0;
      this.valence = Math.min(1, this.valence + 0.3);
      this.arousal = Math.min(1, this.arousal + 0.2);
    } else if (ratio >= 0.6) {
      this.quizStreak = 0;
      this.quizFailStreak = 0;
      this.valence = Math.min(1, this.valence + 0.1);
    } else {
      this.quizStreak = 0;
      this.quizFailStreak++;
      this.valence = Math.max(-1, this.valence - 0.15);
      this.arousal = Math.min(1, this.arousal + 0.1);
    }

    this.updateMood();
    return this.getMood();
  }

  /**
   * 时间上下文感知
   */
  updateTimeContext() {
    const hour = new Date().getHours();
    const dayOfWeek = new Date().getDay();

    if (hour >= 0 && hour < 6) {
      this.timeContext = 'late_night';
      this.energy = Math.max(0, this.energy - 0.1);
      this.arousal = Math.max(0, this.arousal - 0.1);
    } else if (hour >= 6 && hour < 9) {
      this.timeContext = 'morning';
      this.energy = Math.min(1, this.energy + 0.1);
    } else if (hour >= 12 && hour < 14) {
      this.timeContext = 'afternoon';
    } else if (hour >= 22 && hour < 24) {
      this.timeContext = 'evening';
      this.energy = Math.max(0, this.energy - 0.05);
    } else {
      this.timeContext = 'daytime';
    }

    // 周末 vs 工作日
    this.isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

    this.updateMood();
  }

  /**
   * 学习会话开始
   */
  startStudySession() {
    this.studySessionStart = Date.now();
    this.arousal = Math.min(1, this.arousal + 0.1);
  }

  /**
   * 获取学习时长（分钟）
   */
  getStudyDuration() {
    if (!this.studySessionStart) return 0;
    return Math.floor((Date.now() - this.studySessionStart) / 60000);
  }

  /**
   * 自然衰减（每帧调用）
   */
  tick() {
    // 情感向中性衰减
    this.valence *= (1 - this.decayRate);
    this.arousal *= (1 - this.decayRate * 2);

    // 精力衰减
    this.energy = Math.max(0, this.energy - this.energyDecay);

    // 长时间不互动，信任缓慢下降
    const timeSinceLastInteraction = (Date.now() - this.lastInteractionTime) / 1000 / 60; // 分钟
    if (timeSinceLastInteraction > 30) {
      this.trust = Math.max(0.05, this.trust - 0.001);
    }

    // 精力低时自动变困
    if (this.energy < 0.3) {
      this.arousal = Math.min(this.arousal, 0.2);
    }

    this.updateMood();
  }

  /**
   * 更新心情标签
   */
  updateMood() {
    const t = this.thresholds;

    if (this.energy < t.sleepy.energy) {
      this.mood = 'sleepy';
    } else if (this.valence > t.excited.valence && this.arousal > t.excited.arousal) {
      this.mood = 'excited';
    } else if (this.valence > t.happy.valence) {
      this.mood = 'happy';
    } else if (this.valence < t.sad.valence) {
      this.mood = 'sad';
    } else if (this.valence < t.worried.valence && this.arousal > t.worried.arousal) {
      this.mood = 'worried';
    } else if (this.arousal < t.calm.arousal) {
      this.mood = 'calm';
    } else {
      this.mood = 'neutral';
    }
  }

  /**
   * 获取当前心情和推荐行为
   */
  getMood() {
    return {
      mood: this.mood,
      valence: Math.round(this.valence * 100) / 100,
      arousal: Math.round(this.arousal * 100) / 100,
      trust: Math.round(this.trust * 100) / 100,
      energy: Math.round(this.energy * 100) / 100,
      timeContext: this.timeContext,
      interactionCount: this.interactionCount,
      quizStreak: this.quizStreak,
      quizFailStreak: this.quizFailStreak,
      studyDuration: this.getStudyDuration(),
    };
  }

  /**
   * 根据心情生成主动关心语
   */
  getProactiveMessage() {
    const mood = this.getMood();

    // 深夜
    if (mood.timeContext === 'late_night') {
      return '已经很晚了，早点休息吧~ 明天还要继续加油呢！🌙';
    }

    // 学习太久
    if (mood.studyDuration > 45) {
      return '你已经学习很久了，休息一下吧！起来活动活动~ 🐱';
    }

    // 连续答错
    if (mood.quizFailStreak >= 3) {
      return '没关系，错题是学习最好的老师。我们换个方式试试？💪';
    }

    // 连续答对
    if (mood.quizStreak >= 3) {
      return '太厉害了！连续答对这么多，你真的在进步！🎉';
    }

    // 精力低
    if (mood.energy < 0.3) {
      return '我有点困了... 你是不是也该休息一下了？😴';
    }

    // 长时间不互动
    const timeSinceLast = (Date.now() - this.lastInteractionTime) / 1000 / 60;
    if (timeSinceLast > 10 && mood.mood === 'calm') {
      return '嘿，好久没说话了~ 今天学得怎么样？😊';
    }

    // 默认
    const defaults = [
      '我在你身边哦~ 有什么需要帮忙的吗？',
      '加油！你一定可以的！✨',
      '学习累了就看看我，我会一直陪着你的~ ',
      '今天的你比昨天更优秀了！',
    ];
    return defaults[Math.floor(Math.random() * defaults.length)];
  }

  /**
   * 根据对话内容生成宠物回应前缀（情感修饰）
   */
  getEmotionPrefix(userMessage) {
    const mood = this.getMood();

    switch (mood.mood) {
      case 'excited': return '🎉 ';
      case 'happy':   return '😊 ';
      case 'worried': return ' ';
      case 'sad':     return ' ';
      case 'sleepy':  return '😴 ';
      default:        return '';
    }
  }

  /**
   * 重置（新的一天）
   */
  newDay() {
    this.energy = 0.8;
    this.arousal = 0.2;
    this.quizStreak = 0;
    this.quizFailStreak = 0;
    this.studySessionStart = null;
  }
}

module.exports = PetEmotionEngine;
