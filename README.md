---
name: sleep-audiobook-video
description: "AI 自动化生成“睡前听书/助眠”视频流水线。支持多账号矩阵、批量文案生成、TTS 配音和视频合成。"
author: "老八"
version: "0.1.0"
dependencies:
  - python3
  - ffmpeg
---

# Sleep Audiobook Video Generator

## 📖 简介
这是一个用于批量生产“睡前听书”、“助眠读书”类短视频的自动化流水线。
适合抖音、快手、小红书、视频号等平台的**矩阵号运营**。

## 🚀 核心功能
- **文案生成**：集成 LLM 自动将书籍简介/内容转化为“睡前电台”风格文案。
- **AI 配音**：支持 Edge-TTS 的 10+ 种高质量中文音色（男声、女声、童声）。
- **视频合成**：一键合成 1080P 视频（静态/动态背景 + 人声 + 环境白噪音）。
- **矩阵配置**：支持在 `config.json` 中配置多个账号的不同人设（音色、BGM、背景）。

## 🛠️ 使用方法

### 1. 快速上手
```bash
python3 scripts/generate_video.py --book "被讨厌的勇气"
```

### 2. 批量生成（生产模式）
```bash
python3 scripts/generate_video.py --batch config.json
```

### 3. 自定义配置
编辑 `config.json`：
```json
{
  "accounts": [
    {
      "name": "深夜读书馆",
      "voice": "zh-CN-YunxiNeural",
      "bgm": "assets/rain.mp3",
      "bg_image": "assets/night_reading.jpg"
    }
  ],
  "books": [
    { "title": "被讨厌的勇气", "style": "治愈、心理学" },
    { "title": "金刚经", "style": "禅修、空灵" }
  ]
}
```

## ⚙️ 环境要求
- Python 3.8+
- FFmpeg 已安装
- 依赖库：`edge-tts`, `moviepy`, `requests`, `pillow`

## 📦 安装依赖
```bash
pip install -r requirements.txt
```

## ⚠️ 注意事项
- 首次运行会自动下载 TTS 模型缓存。
- 确保有足够的磁盘空间（视频文件较大）。

## ⚡️ 服务器端避坑指南 (Server Pitfalls)
**老八实战总结：**
1. **FFmpeg `zoompan` 超时**: 在服务器上避免使用复杂的 `zoompan` 滤镜（极慢且易超时）。**推荐方案**：直接使用静态背景图 (`-tune stillimage`) 或简单的 `scale` 缩放，合成速度提升 10 倍。
2. **素材下载 403/超时**: Pixabay/Unsplash 等图源常有反爬或连接超时。**推荐方案**：批量任务前，先将 BGM 和背景图下载到本地 `assets/` 目录，脚本优先读取本地文件。
3. **GitHub 推送认证**: 服务器无交互终端，`gh auth login` 经常失败。**推荐方案**：使用 `git remote add origin https://<TOKEN>@github.com/...` 格式推送，稳定可靠。
