#!/usr/bin/env python3
"""
AI 自动化生成"睡前听书"视频脚本 —— 老八特制版
功能：自动文案生成 + TTS 配音 + 画面合成 + 批量输出
依赖：pip install edge-tts moviepy requests pillow
"""

import asyncio
import edge_tts
import os
import random
import requests
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip

# ================= 配置区 =================
OUTPUT_DIR = "sleep_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 账号矩阵配置（可无限扩展）
ACCOUNTS = [
    {
        "name": "睡前听书助眠",
        "voice": "zh-CN-YunxiNeural",  # 磁性男声
        "bg_image": "https://images.unsplash.com/photo-1478720568477-152d9b164e63?auto=format&fit=crop&w=1920&q=80",
        "bgm_url": "https://cdn.pixabay.com/audio/2022/02/07/audio_329944336b.mp3",
        "bgm_vol": 0.15
    },
    {
        "name": "深夜读书馆",
        "voice": "zh-CN-XiaoxiaoNeural",  # 温柔女声
        "bg_image": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80",
        "bgm_url": "https://cdn.pixabay.com/audio/2022/03/10/audio_a57c334882.mp3",
        "bgm_vol": 0.10
    },
]

# 书籍与文案 Prompt
BOOKS = [
    {
        "title": "被讨厌的勇气",
        "prompt": "请用舒缓、治愈的口吻，拆解《被讨厌的勇气》。核心观点：一切烦恼皆源于人际关系、课题分离、被讨厌的勇气。开头要引导用户放松深呼吸，结尾引导入睡。约 800 字。"
    },
    {
        "title": "当下的力量",
        "prompt": "请用空灵、平静的口吻，拆解《当下的力量》。核心观点：停止思维反刍、进入当下时刻、观察你的情绪。开头要引导用户放下焦虑，结尾引导入眠。约 800 字。"
    }
]

# ================= 核心逻辑 =================

async def generate_audio(text, voice, output_file):
    """生成 TTS 音频"""
    print(f"🎙️ 正在生成配音 (音色: {voice}) ...")
    communicate = edge_tts.Communicate(text, voice, rate="-15%", volume="+10%")
    await communicate.save(output_file)
    return output_file

def download_file(url, filepath):
    """下载素材"""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return filepath
    print(f"📥 下载: {filepath}")
    r = requests.get(url)
    with open(filepath, "wb") as f:
        f.write(r.content)
    return filepath

def create_video(audio_path, bgm_path, image_path, output_path, bgm_vol=0.15):
    """合成视频：画面 + 配音 + BGM"""
    print("🎬 正在合成视频...")
    audio = AudioFileClip(audio_path)
    
    # 画面：静态图拉伸到音频长度
    video = ImageClip(image_path).set_duration(audio.duration)
    video = video.set_fps(24).resize(height=1080).resize(width=1920)
    video = video.set_audio(audio)
    
    # 混合 BGM
    if os.path.exists(bgm_path):
        bgm = AudioFileClip(bgm_path).set_duration(audio.duration)
        bgm = bgm.volumex(bgm_vol)
        final_audio = CompositeAudioClip([audio, bgm])
        video = video.set_audio(final_audio)
    
    # 导出
    video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast")
    print(f"✅ 完成: {output_path} ({video.duration:.1f}s)")

def llm_write_script(prompt):
    """模拟 LLM 生成文案 (实际使用时替换为你的 API 调用)"""
    # 这里为了演示直接返回一段硬编码的治愈系文案
    return """
    大家好，我是你的深夜读书人。今晚，我们一起读一本让你灵魂安静的书——《被讨厌的勇气》。
    阿德勒说：人的一切烦恼，皆源于人际关系。
    你是不是也常常为了讨好别人，而委屈了自己？你是不是总担心别人眼里的你不够好？
    其实，你不必活在他人的期待里。别人如何评价你，那是别人的课题，你无法左右，也不必在意。
    你需要拥有的，仅仅是一份"被讨厌的勇气"。
    这不代表你要去故意惹人讨厌，而是当你不再为了满足别人的期待而活时，你才真正获得了自由。
    今晚，试着放下那些无谓的顾虑吧。
    深呼吸，把注意力收回到自己身上。告诉自己：我不需要让所有人都喜欢我，这就足够了。
    愿你今晚，放下包袱，做个好梦。
    """

async def main():
    # 选择一个账号配置和一本书
    account = random.choice(ACCOUNTS)
    book = random.choice(BOOKS)
    
    book_title = book["title"]
    safe_title = book_title.replace(" ", "_")
    print(f"🚀 开始任务: {account['name']} - 《{book_title}》")

    # 1. 生成文案
    script_text = llm_write_script(book["prompt"])
    
    # 2. 生成配音
    audio_path = f"{OUTPUT_DIR}/{safe_title}_voice.mp3"
    await generate_audio(script_text, account["voice"], audio_path)
    
    # 3. 下载素材
    bg_image = download_file(account["bg_image"], f"{OUTPUT_DIR}/bg_{safe_title}.jpg")
    bgm = download_file(account["bgm_url"], f"{OUTPUT_DIR}/bgm_{safe_title}.mp3")
    
    # 4. 合成视频
    output_video = f"{OUTPUT_DIR}/{account['name']}_{safe_title}.mp4"
    create_video(audio_path, bgm, bg_image, output_video, account["bgm_vol"])
    
    # 清理临时音频
    if os.path.exists(audio_path): os.remove(audio_path)

if __name__ == "__main__":
    asyncio.run(main())
