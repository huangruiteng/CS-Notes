#!/usr/bin/env python3
"""
Speech-to-Text Tool
Uses OpenAI Whisper API or local Whisper model
"""

import sys
import os
import argparse

# Try to import openai-whisper
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    print("Warning: openai-whisper not installed, trying OpenAI API...")

# Try to import openai
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: openai not installed")

# 配置 Whisper 模型下载路径
WHISPER_MODEL_DIR = os.path.expanduser("~/.cache/whisper")
os.makedirs(WHISPER_MODEL_DIR, exist_ok=True)

def transcribe_audio(file_path: str, model: str = "medium") -> str:
    """
    Transcribe audio file to text
    """
    if HAS_WHISPER:
        print(f"Using local Whisper model: {model}")
        print(f"Model directory: {WHISPER_MODEL_DIR}")
        
        # 如果 model 参数是一个文件路径，直接加载
        if os.path.exists(model):
            print(f"Loading model from file path: {model}")
            model_obj = whisper.load_model(model)
        else:
            # 指定模型下载路径
            model_obj = whisper.load_model(model, download_root=WHISPER_MODEL_DIR)
        
        result = model_obj.transcribe(file_path)
        return result["text"]
    elif HAS_OPENAI:
        print("Using OpenAI Whisper API")
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        with open(file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return transcript.text
    else:
        raise ImportError("Neither openai-whisper nor openai installed")


def main():
    parser = argparse.ArgumentParser(description="Speech-to-Text Tool")
    parser.add_argument("file", help="Audio file path")
    parser.add_argument("--model", default="small", help="Whisper model (base, small, medium, large, large-v2, large-v3, large-v3-turbo, turbo)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found")
        sys.exit(1)

    try:
        text = transcribe_audio(args.file, args.model)
        print("\n--- Transcription ---\n")
        print(text)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
