#!/usr/bin/env python3
"""
AI 自动化生成“睡前听书”视频流水线 (v1.0)
支持单本/批量生成，多账号矩阵配置。
"""

import asyncio
import edge_tts
import os
import sys
import json
import argparse
import random
import time
import requests
import textwrap
from pathlib import Path
from datetime import datetime

try:
    from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips
    HAS_MOVIEPY = True
except ImportError:
    print("⚠️ MoviePy not installed. Video composition disabled.")
    HAS_MOVIEPY = False

# 默认配置
DEFAULT_CONFIG = {
    "output_dir": "output_videos",
    "default_bgm_vol": 0.15,
    "tts_rate": "-15%",
    "tts_volume": "+10%",
    "image_resolution": [1920, 1080],
    "fps": 24
}

# 预设的账号矩阵（示例）
ACCOUNTS = [
    {
        "id": "account_1",
        "name": "睡前听书助眠",
        "voice": "zh-CN-YunxiNeural",
        "bgm_url": "https://cdn.pixabay.com/audio/2022/02/07/audio_329944336b.mp3", # 治愈钢琴
        "bg_image": "https://images.unsplash.com/photo-1478720568477-152d9b164e63?auto=format&fit=crop&w=1920&q=80" # 书房
    },
    {
        "id": "account_2",
        "name": "深夜读书馆",
        "voice": "zh-CN-XiaoxiaoNeural",
        "bgm_url": "https://cdn.pixabay.com/audio/2022/03/10/audio_a57c334882.mp3", # 雨声
        "bg_image": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80" # 书架
    }
]

def generate_script_llm(book_title, style="治愈"):
    """
    模拟 LLM 生成文案。
    实际生产环境中，请在此处接入 OpenAI/DashScope 等 API。
    """
    prompt = f"请为《{book_title}》写一段睡前听书的文案，风格{style}。引导放松，核心观点明确。"
    print(f"📝 正在为《{book_title}》生成文案...")
    
    # Mock 文案（真实使用时替换为 API 调用）
    return textwrap.dedent(f"""
    大家好，欢迎来到睡前听书。今晚，我想和你分享一本好书——《{book_title}》。
    在这个快节奏的时代，我们的心常常被焦虑填满。
    而这本书告诉我们：试着慢下来，去感受当下的力量。
    深呼吸，放下一天的疲惫。
    愿这本书的文字，能像一阵温柔的风，吹散你心头的乌云。
    祝你今晚，好梦。
    """).strip()

async def generate_audio(text, voice, output_path, rate="-15%", volume="+10%"):
    """使用 Edge TTS 生成语音"""
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output_path)
    return output_path

def download_file(url, filepath):
    """下载文件，支持断点续传"""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return filepath
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    print(f"📥 下载: {os.path.basename(filepath)}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    return filepath

def create_video_with_moviepy(audio_path, bgm_path, image_path, output_path, bgm_vol=0.15, fps=24):
    """使用 MoviePy 合成视频"""
    if not HAS_MOVIEPY:
        print("❌ MoviePy 未安装，无法合成视频。")
        return False

    try:
        print("🎬 开始合成视频...")
        audio = AudioFileClip(audio_path)
        
        # 创建视频轨道：静态图片拉伸到音频长度
        video = ImageClip(image_path).set_duration(audio.duration)
        video = video.set_fps(fps).resize(width=1920).resize(height=1080)
        video = video.set_audio(audio)

        # 如果提供了 BGM，则进行混音
        if bgm_path and os.path.exists(bgm_path):
            bgm = AudioFileClip(bgm_path)
            # 裁剪 BGM 到人声长度
            if bgm.duration > audio.duration:
                bgm = bgm.subclip(0, audio.duration)
            else:
                # 如果 BGM 太短，循环播放（简单实现：拼接）
                loops = int(audio.duration / bgm.duration) + 1
                bgm = concatenate_audioclips([bgm] * loops).subclip(0, audio.duration)
            
            bgm = bgm.volumex(bgm_vol)
            final_audio = CompositeAudioClip([audio, bgm])
            video = video.set_audio(final_audio)
            bgm.close()

        # 导出
        video.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            fps=fps, 
            preset="fast",
            logger=None # 关闭 MoviePy 的冗余日志
        )
        
        audio.close()
        video.close()
        print(f"✅ 视频已保存: {output_path}")
        return True
    except Exception as e:
        print(f"❌ 视频合成失败: {e}")
        return False

async def process_book(book, account, output_dir, config):
    """处理单本书的生成任务"""
    book_title = book.get("title", "未知书籍")
    account_name = account.get("name", "默认账号")
    safe_title = book_title.replace(" ", "_").replace("/", "_")
    account_safe = account_name.replace(" ", "_")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    task_dir = os.path.join(output_dir, f"{account_safe}_{safe_title}_{timestamp}")
    os.makedirs(task_dir, exist_ok=True)
    
    print(f"\n🚀 开始任务: [{account_name}] -> 《{book_title}》")
    
    # 1. 生成文案
    script = generate_script_llm(book_title, book.get("style", "治愈"))
    
    # 2. 生成语音
    voice_path = os.path.join(task_dir, "voice.mp3")
    await generate_audio(script, account["voice"], voice_path, 
                         rate=config.get("tts_rate", "-15%"),
                         volume=config.get("tts_volume", "+10%"))
    
    # 3. 下载/准备素材
    bg_image = download_file(account["bg_image"], os.path.join(task_dir, "bg.jpg"))
    bgm_path = None
    if "bgm_url" in account:
        bgm_path = download_file(account["bgm_url"], os.path.join(task_dir, "bgm.mp3"))
    
    # 4. 合成视频
    output_video = os.path.join(output_dir, f"{account_safe}_{safe_title}.mp4")
    success = create_video_with_moviepy(
        voice_path, 
        bgm_path, 
        bg_image, 
        output_video,
        bgm_vol=config.get("default_bgm_vol", 0.15),
        fps=config.get("fps", 24)
    )
    
    if success:
        return output_video
    return None

async def run_batch(config_path=None):
    """批量处理"""
    output_dir = DEFAULT_CONFIG["output_dir"]
    
    # 加载配置
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
            accounts = data.get("accounts", ACCOUNTS)
            books = data.get("books", [{"title": "被讨厌的勇气"}])
            config = {**DEFAULT_CONFIG, **data.get("settings", {})}
    else:
        accounts = ACCOUNTS
        books = [{"title": "被讨厌的勇气"}]
        config = DEFAULT_CONFIG

    print(f"📚 任务列表: {len(accounts)} 个账号 x {len(books)} 本书")
    
    # 随机组合（模拟矩阵号运营）
    tasks = [(random.choice(accounts), book) for book in books]
    
    for account, book in tasks:
        try:
            await process_book(book, account, output_dir, config)
            time.sleep(2) # 礼貌间隔
        except Exception as e:
            print(f"❌ 任务失败: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 睡前听书视频生成器")
    parser.add_argument("--book", type=str, help="指定书名")
    parser.add_argument("--account", type=str, help="指定账号 ID (如 account_1)")
    parser.add_argument("--batch", type=str, help="批量任务配置文件路径")
    args = parser.parse_args()

    if args.batch:
        asyncio.run(run_batch(args.batch))
    elif args.book:
        # 单本模式
        account = ACCOUNTS[0]
        if args.account:
            for acc in ACCOUNTS:
                if acc["id"] == args.account:
                    account = acc
                    break
        
        asyncio.run(process_book(
            {"title": args.book}, 
            account, 
            DEFAULT_CONFIG["output_dir"],
            DEFAULT_CONFIG
        ))
    else:
        # 默认演示模式
        print("ℹ️ 运行默认演示模式：生成《被讨厌的勇气》")
        asyncio.run(process_book(
            {"title": "被讨厌的勇气"}, 
            ACCOUNTS[0], 
            DEFAULT_CONFIG["output_dir"],
            DEFAULT_CONFIG
        ))
