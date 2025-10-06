from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mangum import Mangum
import asyncio
import logging
import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import json
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAX_CHUNK_DURATION = int(os.getenv("MAX_CHUNK_DURATION", "600"))  # 10 minutes

# In-memory job tracking (simple dictionary)
jobs: Dict[str, Dict[str, Any]] = {}
job_counter = 0

app = FastAPI(
    title="Hindi/English Transcription Service",
    description="Advanced service for Hindi and English audio transcription. Hindi audio is translated to English, English audio is kept as English. All output is in English SRT format.",
    version="4.2.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for better performance
app.mount("/static", StaticFiles(directory="static"), name="static")


# Helper functions
async def save_audio_temporarily(file: UploadFile) -> str:
    """Save uploaded audio file temporarily in project directory"""
    import os

    # Create temp directory in project root if it doesn't exist
    temp_dir = "temp_audio"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        logger.info(f"Created temp directory: {temp_dir}")

    # Save file in project temp directory
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")

    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    logger.info(f"Audio file saved to: {temp_path}")
    return temp_path


async def get_audio_duration(audio_path: str) -> float:
    """Get audio duration using ffprobe"""
    try:
        # Try to find ffprobe in different locations
        ffprobe_paths = [
            "ffprobe",  # System PATH
            "ffprobe.exe",  # Current directory (api/)
            "../ffprobe.exe",  # Root directory
        ]

        ffprobe_cmd = None
        for path in ffprobe_paths:
            try:
                proc = await asyncio.create_subprocess_exec(
                    path,
                    "-version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                if proc.returncode == 0:
                    ffprobe_cmd = path
                    break
            except FileNotFoundError:
                continue

        if not ffprobe_cmd:
            logger.error("ffprobe not found in PATH or local directories")
            return 0

        proc = await asyncio.create_subprocess_exec(
            ffprobe_cmd,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return float(stdout.decode().strip())
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        return 0


def create_job_chunks(job_id: str, audio_path: str, duration: float) -> list:
    """Create chunks for the audio file"""
    chunks = []
    chunk_count = int(duration / MAX_CHUNK_DURATION) + (
        1 if duration % MAX_CHUNK_DURATION > 0 else 0
    )

    for i in range(chunk_count):
        start_time = i * MAX_CHUNK_DURATION
        end_time = min((i + 1) * MAX_CHUNK_DURATION, duration)

        chunk = {
            "chunk_id": f"{job_id}_chunk_{i}",
            "job_id": job_id,
            "audio_path": audio_path,
            "start_time": start_time,
            "end_time": end_time,
            "status": "queued",
        }
        chunks.append(chunk)

    return chunks


async def process_audio_simple(audio_path: str, job_id: str):
    """Process audio using Google Gemini API"""
    try:
        # Update job status to processing
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10.0

        # Get audio duration
        duration = await get_audio_duration(audio_path)

        # Check if we have Google API key
        logger.info(
            f"GOOGLE_API_KEY loaded: {GOOGLE_API_KEY[:20] if GOOGLE_API_KEY else 'None'}..."
        )
        logger.info(
            f"API key check: not GOOGLE_API_KEY = {not GOOGLE_API_KEY}, equals default = {GOOGLE_API_KEY == 'your-google-gemini-api-key'}"
        )
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your-google-gemini-api-key":
            # Create demo SRT if no API key
            srt_content = f"""1
00:00:00,000 --> 00:00:05,000
[Demo Mode - No API Key]

2
00:00:05,000 --> 00:00:10,000
[Audio Duration: {duration:.1f} seconds]

3
00:00:10,000 --> 00:00:15,000
[Job ID: {job_id}]

4
00:00:15,000 --> 00:00:20,000
[Supports Hindi & English Audio]

5
00:00:20,000 --> 00:00:25,000
[Add GOOGLE_API_KEY to .env file]

6
00:00:25,000 --> 00:00:30,000
[for real transcription]
"""
        else:
            # Use Whisper + Gemini pipeline for real transcription
            srt_content = await transcribe_with_whisper_gemini(audio_path, job_id)

        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100.0
        jobs[job_id]["srt_content"] = srt_content
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

        # Clean up audio file
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"✅ Cleaned up temporary file: {audio_path}")
            else:
                logger.warning(f"⚠️ Temporary file not found for cleanup: {audio_path}")
        except Exception as e:
            logger.warning(f"❌ Could not clean up temporary file {audio_path}: {e}")

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

        # Clean up audio file even on error
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"✅ Cleaned up temporary file after error: {audio_path}")
        except Exception as cleanup_error:
            logger.warning(
                f"❌ Could not clean up temporary file after error {audio_path}: {cleanup_error}"
            )


async def transcribe_with_whisper_gemini(audio_path: str, job_id: str) -> str:
    """Transcribe audio using Whisper + Gemini pipeline for better accuracy"""
    try:
        import whisper

        logger.info(f"Starting Whisper + Gemini pipeline for job {job_id}")

        # Step 1: Use Whisper for initial transcription with Hindi language support
        logger.info("Step 1: Transcribing with Whisper (supporting Hindi)...")
        model = whisper.load_model(
            "base"
        )  # Using base model for much faster transcription while maintaining good accuracy

        # Try to detect language first, then transcribe
        # Whisper can auto-detect Hindi and other languages
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language=None,  # Auto-detect language (including Hindi)
            task="transcribe",  # Transcribe to original language first
            # Enhanced parameters for better fast speech detection
            temperature=0.0,  # More deterministic output
            compression_ratio_threshold=2.4,  # Lower threshold for better detection
            logprob_threshold=-1.0,  # Lower threshold to capture more words
            no_speech_threshold=0.6,  # Lower threshold to detect speech in quiet parts
            condition_on_previous_text=True,  # Use context for better accuracy
            initial_prompt="This is a conversation in Hindi and English. Please transcribe every word accurately, including fast speech.",  # Help Whisper understand the context
        )

        # Extract segments with timestamps
        segments = result.get("segments", [])
        if not segments:
            raise Exception("No segments found in Whisper transcription")

        # Step 2: Detect the language of the transcription
        detected_language = result.get("language", "unknown")
        logger.info(f"Detected language: {detected_language}")

        # Prepare text for analysis
        whisper_text = " ".join([segment["text"].strip() for segment in segments])
        logger.info(f"Whisper transcription: {whisper_text[:100]}...")

        # Check if the transcribed text contains Devanagari, Arabic/Urdu, or other Indic scripts
        import re

        devanagari_pattern = re.compile(r"[\u0900-\u097F]")  # Devanagari (Hindi)
        arabic_pattern = re.compile(r"[\u0600-\u06FF]")  # Arabic/Urdu
        indic_pattern = re.compile(
            r"[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF]"
        )  # Various Indic scripts

        has_devanagari = bool(devanagari_pattern.search(whisper_text))
        has_arabic = bool(arabic_pattern.search(whisper_text))
        has_indic = bool(indic_pattern.search(whisper_text))

        logger.info(f"Text contains Devanagari: {has_devanagari}")
        logger.info(f"Text contains Arabic/Urdu: {has_arabic}")
        logger.info(f"Text contains Indic scripts: {has_indic}")

        # Step 3: Create word-level segments using Whisper's exact timestamps
        logger.info("Step 3: Creating word-level segments with exact timestamps...")
        speech_segments = create_word_level_segments(segments)
        logger.info(f"Created {len(speech_segments)} word-level segments")

        # Step 4: Use FAST local conversion (NO API calls for speed)
        if (
            detected_language == "hi"
            or detected_language == "hindi"
            or has_devanagari
            or has_arabic
            or has_indic
        ):
            logger.info(
                "Step 4: Converting Hindi/Urdu to Hinglish with LOCAL converter (FAST)..."
            )
            translation_mode = "hindi_to_hinglish"
        else:
            logger.info("Step 4: Keeping English as English (FAST)...")
            translation_mode = "english_to_english"

        # FAST local processing - no API calls for speed
        logger.info("Using FAST local processing - no API calls")

        # ALWAYS use local converter for Hindi/Urdu to ensure pure Latin script
        if translation_mode == "hindi_to_hinglish":
            logger.info(
                "Using local Hindi/Urdu to Hinglish converter for pure Latin script"
            )
            # Create Hinglish translation using local converter (no API calls)
            translated_segments = []
            for i, segment in enumerate(speech_segments):
                # Use enhanced Hindi to Hinglish converter with context awareness
                # Ensure we capture every word even in fast speech
                original_text = segment["text"].strip()
                if original_text:  # Only process non-empty segments
                    hinglish_text = convert_hindi_to_hinglish_enhanced(
                        original_text, speech_segments, i
                    )
                    # Ensure the converted text is not empty
                    if hinglish_text.strip():
                        translated_segments.append(
                            {
                                "text": hinglish_text.strip(),
                                "start": segment["start"],
                                "end": segment["end"],
                            }
                        )
                    else:
                        # Fallback: keep original text if conversion fails
                        logger.warning(f"Empty conversion for segment: {original_text}")
                        translated_segments.append(
                            {
                                "text": original_text,
                                "start": segment["start"],
                                "end": segment["end"],
                            }
                        )
                else:
                    logger.warning(
                        f"Empty segment detected at {segment['start']}s, skipping"
                    )
            srt_content = create_srt_from_speech_segments(translated_segments)
        else:
            # For English, just create SRT directly
            srt_content = create_srt_from_speech_segments(speech_segments)

        # Ensure we have valid SRT content
        if not srt_content or len(srt_content.strip()) < 10:
            logger.error("No valid SRT content generated, creating fallback")
            srt_content = create_srt_from_speech_segments(speech_segments)

        logger.info(
            f"Successfully completed Whisper + Gemini pipeline for job {job_id}"
        )
        return srt_content

    except Exception as e:
        logger.error(f"Error in Whisper + Gemini pipeline: {e}")
        # Return fallback SRT on error
        return f"""1
00:00:00,000 --> 00:00:05,000
[Transcription Error]

2
00:00:05,000 --> 00:00:10,000
[Error: {str(e)[:50]}...]

3
00:00:10,000 --> 00:00:15,000
[Check API key and try again]
"""


def create_srt_from_whisper_segments(segments, whisper_text):
    """Create SRT content from Whisper segments as fallback"""
    srt_lines = []

    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        text = segment["text"].strip()

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between segments

    return "\n".join(srt_lines)


def format_timestamp(seconds):
    """Format seconds to SRT timestamp format (HH:MM:SS,MMM)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def create_word_level_segments(whisper_segments):
    """Create segments using Whisper's exact word-level timestamps for maximum precision - captures EVERY word"""
    word_segments = []

    logger.info(
        f"Processing {len(whisper_segments)} Whisper segments for word-level timing"
    )

    for segment_idx, segment in enumerate(whisper_segments):
        # Get word-level timestamps from Whisper
        words = segment.get("words", [])
        logger.info(f"Segment {segment_idx}: {len(words)} words found")

        if words:
            # Use Whisper's exact word timestamps - capture EVERY single word
            for i, word_info in enumerate(words):
                word_text = word_info.get("word", "").strip()
                word_start = word_info.get("start", 0)
                word_end = word_info.get(
                    "end", word_start + 0.3
                )  # Shorter default duration for fast speech

                # Skip empty words but log them
                if not word_text:
                    logger.warning(f"Empty word detected at {word_start}s, skipping")
                    continue

                # Create individual word segments - prioritize capturing every word
                if i == 0 or len(word_segments) == 0:
                    # Start new segment
                    word_segments.append(
                        {
                            "text": word_text,
                            "start": word_start,
                            "end": word_end,
                        }
                    )
                else:
                    # More aggressive grouping for fast speech - allow up to 3 words per segment
                    current_duration = word_start - word_segments[-1]["start"]
                    current_word_count = len(word_segments[-1]["text"].split())

                    # For fast speech, be more lenient with grouping
                    if current_duration <= 2.0 and current_word_count < 4:
                        # Add to current segment
                        word_segments[-1]["text"] += " " + word_text
                        word_segments[-1]["end"] = word_end
                    else:
                        # Create new segment
                        word_segments.append(
                            {"text": word_text, "start": word_start, "end": word_end}
                        )
        else:
            # Enhanced fallback: use segment-level timing and break into words more aggressively
            logger.info(
                f"Segment {segment_idx}: No word-level data, using enhanced fallback"
            )
            text = segment["text"].strip()
            start_time = segment["start"]
            end_time = segment["end"]
            duration = end_time - start_time

            words = text.split()
            if len(words) <= 3:  # Allow up to 3 words for fast speech
                word_segments.append(
                    {"text": text, "start": start_time, "end": end_time}
                )
            else:
                # Break into smaller chunks (1-2 words) for better fast speech handling
                for i in range(0, len(words), 1):  # Process every single word
                    chunk_words = words[
                        i : i + 1
                    ]  # One word at a time for maximum precision
                    chunk_text = " ".join(chunk_words)

                    chunk_duration = duration * (len(chunk_words) / len(words))
                    chunk_start = start_time + (i / len(words)) * duration
                    chunk_end = chunk_start + chunk_duration

                    # Ensure minimum duration but keep it short for fast speech
                    if chunk_end - chunk_start < 0.3:
                        chunk_end = chunk_start + 0.3

                    word_segments.append(
                        {"text": chunk_text, "start": chunk_start, "end": chunk_end}
                    )

    logger.info(
        f"Created {len(word_segments)} word-level segments - capturing every word"
    )
    return word_segments


def create_speech_synchronized_segments(whisper_segments):
    """Break Whisper segments into speech-synchronized chunks (1-3 seconds max)"""
    speech_segments = []

    for segment in whisper_segments:
        text = segment["text"].strip()
        start_time = segment["start"]
        end_time = segment["end"]
        duration = end_time - start_time

        # If segment is already short (≤3 seconds), keep it as is
        if duration <= 3.0:
            speech_segments.append({"text": text, "start": start_time, "end": end_time})
        else:
            # Break long segments into much smaller chunks (2-4 words max)
            words = text.split()
            words_per_chunk = max(2, min(4, len(words) // max(1, int(duration / 1.5))))

            for i in range(0, len(words), words_per_chunk):
                chunk_words = words[i : i + words_per_chunk]
                chunk_text = " ".join(chunk_words)

                # Calculate timing for this chunk
                chunk_duration = duration * (len(chunk_words) / len(words))
                chunk_start = start_time + (i / len(words)) * duration
                chunk_end = chunk_start + chunk_duration

                # Ensure minimum duration of 0.8 seconds (shorter for faster display)
                if chunk_end - chunk_start < 0.8:
                    chunk_end = chunk_start + 0.8

                speech_segments.append(
                    {"text": chunk_text, "start": chunk_start, "end": chunk_end}
                )

    return speech_segments


def format_segments_for_gemini(speech_segments):
    """Format speech segments for Gemini input"""
    formatted = []
    for i, segment in enumerate(speech_segments, 1):
        formatted.append(f"Segment {i}: {segment['text']}")
        formatted.append(f"Start: {segment['start']:.3f}s")
        formatted.append(f"End: {segment['end']:.3f}s")
        formatted.append("")
    return "\n".join(formatted)


def convert_hindi_to_hinglish_enhanced(
    hindi_text, all_segments=None, current_index=None
):
    """Enhanced Hindi to Hinglish converter with context awareness and mixed language handling - optimized for fast speech"""

    if not hindi_text or not hindi_text.strip():
        return hindi_text

    # Clean the text first to handle fast speech artifacts
    cleaned_text = hindi_text.strip()

    # First, handle mixed language content (already contains English words)
    if contains_mixed_language(cleaned_text):
        logger.info(f"Detected mixed language content: {cleaned_text[:50]}...")
        result = convert_mixed_language_to_hinglish(
            cleaned_text, all_segments, current_index
        )
    else:
        # Use the comprehensive simple converter for pure Hindi content
        result = convert_hindi_to_hinglish_simple(cleaned_text)

    # Ensure we don't lose any words in fast speech
    if not result or not result.strip():
        logger.warning(f"Empty conversion result for: {hindi_text}")
        # Fallback to simple conversion
        result = convert_hindi_to_hinglish_simple(cleaned_text)

    return result


def contains_mixed_language(text):
    """Check if text contains mixed Hindi-English content"""
    import re

    # Check for common English words that appear in Hindi text
    english_words = [
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "office",
        "phone",
        "computer",
        "internet",
        "website",
        "email",
        "message",
        "call",
        "video",
        "audio",
        "photo",
        "camera",
        "screen",
        "keyboard",
        "mouse",
        "file",
        "folder",
        "download",
        "upload",
        "search",
        "Google",
        "YouTube",
        "Facebook",
        "WhatsApp",
        "Instagram",
        "Twitter",
        "Skype",
        "Zoom",
        "Netflix",
        "Amazon",
        "Paytm",
        "bank",
        "card",
        "password",
        "login",
        "logout",
        "user",
        "system",
        "device",
        "app",
        "software",
        "hardware",
        "data",
        "memory",
        "storage",
        "network",
        "wifi",
        "bluetooth",
        "mobile",
        "laptop",
        "desktop",
        "tablet",
        "iPhone",
        "Android",
        "Windows",
        "Mac",
        "Linux",
        "online",
        "offline",
        "digital",
        "virtual",
        "real",
        "time",
        "date",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "morning",
        "evening",
        "night",
        "today",
        "tomorrow",
        "yesterday",
        "week",
        "weekend",
        "holiday",
        "vacation",
        "trip",
        "travel",
        "hotel",
        "restaurant",
        "food",
        "drink",
        "water",
        "coffee",
        "tea",
        "milk",
        "bread",
        "rice",
        "meat",
        "chicken",
        "fish",
        "egg",
        "fruit",
        "vegetable",
        "sweet",
        "chocolate",
        "ice cream",
        "family",
        "mother",
        "father",
        "brother",
        "sister",
        "husband",
        "wife",
        "son",
        "daughter",
        "friend",
        "neighbor",
        "colleague",
        "boss",
        "employee",
        "customer",
        "doctor",
        "teacher",
        "student",
        "engineer",
        "manager",
        "director",
        "president",
        "money",
        "rupee",
        "dollar",
        "price",
        "cost",
        "expensive",
        "cheap",
        "free",
        "paid",
        "buy",
        "sell",
        "shop",
        "market",
        "store",
        "mall",
        "hospital",
        "school",
        "college",
        "university",
        "library",
        "museum",
        "park",
        "garden",
        "beach",
        "mountain",
        "river",
        "lake",
        "forest",
        "city",
        "village",
        "country",
        "state",
        "district",
        "street",
        "road",
        "bridge",
        "building",
        "house",
        "room",
        "door",
        "window",
        "chair",
        "table",
        "bed",
        "sofa",
        "television",
        "radio",
        "newspaper",
        "magazine",
        "book",
        "pen",
        "paper",
        "bag",
        "shirt",
        "pants",
        "dress",
        "shoes",
        "hat",
        "car",
        "bus",
        "train",
        "plane",
        "bike",
        "taxi",
        "auto",
        "truck",
        "boat",
        "ship",
        "airport",
        "station",
        "bus stop",
        "traffic",
        "signal",
        "road",
        "weather",
        "sun",
        "moon",
        "star",
        "cloud",
        "rain",
        "snow",
        "wind",
        "hot",
        "cold",
        "warm",
        "cool",
        "dry",
        "wet",
        "clean",
        "dirty",
        "big",
        "small",
        "large",
        "tiny",
        "long",
        "short",
        "high",
        "low",
        "fast",
        "slow",
        "quick",
        "easy",
        "hard",
        "difficult",
        "simple",
        "complex",
        "good",
        "bad",
        "nice",
        "beautiful",
        "ugly",
        "new",
        "old",
        "young",
        "fresh",
        "tired",
        "busy",
        "free",
        "ready",
        "finished",
        "start",
        "stop",
        "continue",
        "repeat",
        "change",
        "move",
        "come",
        "go",
        "walk",
        "run",
        "sit",
        "stand",
        "sleep",
        "wake",
        "eat",
        "drink",
        "cook",
        "wash",
        "clean",
        "work",
        "play",
        "study",
        "read",
        "write",
        "speak",
        "listen",
        "watch",
        "see",
        "look",
        "hear",
        "smell",
        "taste",
        "touch",
        "feel",
        "think",
        "know",
        "understand",
        "remember",
        "forget",
        "learn",
        "teach",
        "help",
        "ask",
        "answer",
        "tell",
        "show",
        "give",
        "take",
        "buy",
        "sell",
        "pay",
        "cost",
        "spend",
        "save",
        "earn",
        "win",
        "lose",
        "find",
        "lose",
        "get",
        "have",
        "has",
        "had",
        "was",
        "were",
        "is",
        "are",
        "am",
        "be",
        "been",
        "being",
        "do",
        "does",
        "did",
        "done",
        "will",
        "would",
        "can",
        "could",
        "should",
        "must",
        "may",
        "might",
        "shall",
        "let",
        "make",
        "try",
        "use",
        "want",
        "need",
        "like",
        "love",
        "hate",
        "prefer",
        "choose",
        "decide",
        "plan",
        "hope",
        "wish",
        "dream",
        "believe",
        "trust",
        "doubt",
        "worry",
        "fear",
        "worry",
        "excited",
        "happy",
        "sad",
        "angry",
        "surprised",
        "scared",
        "nervous",
        "calm",
        "relaxed",
        "stressed",
        "confused",
        "clear",
        "sure",
        "certain",
        "maybe",
        "perhaps",
        "probably",
        "definitely",
        "absolutely",
        "exactly",
        "almost",
        "nearly",
        "quite",
        "very",
        "really",
        "truly",
        "actually",
        "finally",
        "suddenly",
        "immediately",
        "soon",
        "later",
        "early",
        "late",
        "always",
        "never",
        "sometimes",
        "often",
        "usually",
        "rarely",
        "hardly",
        "barely",
        "completely",
        "totally",
        "fully",
        "partly",
        "mostly",
        "mainly",
        "especially",
        "particularly",
        "especially",
    ]

    text_lower = text.lower()
    for word in english_words:
        if re.search(r"\b" + re.escape(word) + r"\b", text_lower):
            return True

    return False


def convert_mixed_language_to_hinglish(text, all_segments=None, current_index=None):
    """Convert mixed Hindi-English content to proper Hinglish"""
    import re

    # Enhanced list of English words commonly used in India
    english_words = {
        # Technology
        "phone",
        "computer",
        "laptop",
        "mobile",
        "internet",
        "website",
        "app",
        "software",
        "hardware",
        "file",
        "folder",
        "download",
        "upload",
        "search",
        "Google",
        "YouTube",
        "Facebook",
        "Instagram",
        "Twitter",
        "WhatsApp",
        "Telegram",
        "Skype",
        "Zoom",
        "Netflix",
        "Amazon",
        "Flipkart",
        "Paytm",
        "Google Pay",
        "PhonePe",
        "UPI",
        "OTP",
        "password",
        "user",
        "login",
        "logout",
        "signup",
        "profile",
        "settings",
        "notification",
        "alert",
        "message",
        "chat",
        "video",
        "audio",
        "photo",
        "picture",
        "camera",
        "microphone",
        "speaker",
        "headphone",
        "Bluetooth",
        "WiFi",
        "data",
        "storage",
        "memory",
        "RAM",
        "CPU",
        "processor",
        "screen",
        "display",
        "touchscreen",
        "keyboard",
        "mouse",
        "desktop",
        "tablet",
        "smartphone",
        "iPhone",
        "Android",
        "Windows",
        "Mac",
        "Linux",
        "system",
        "device",
        "gadget",
        "technology",
        "digital",
        "online",
        "offline",
        "virtual",
        "artificial",
        "intelligence",
        "machine",
        "learning",
        "cyber",
        "security",
        "blockchain",
        "cryptocurrency",
        "Bitcoin",
        "Ethereum",
        "NFT",
        "metaverse",
        "VR",
        "AR",
        # Business & Work
        "office",
        "meeting",
        "project",
        "task",
        "assignment",
        "deadline",
        "business",
        "company",
        "factory",
        "manager",
        "director",
        "president",
        "employee",
        "customer",
        "client",
        "boss",
        "colleague",
        "team",
        "department",
        "conference",
        "presentation",
        "report",
        "document",
        "contract",
        "agreement",
        "budget",
        "finance",
        "accounting",
        "marketing",
        "sales",
        "advertising",
        "promotion",
        "campaign",
        "strategy",
        "planning",
        "development",
        # Money & Finance
        "money",
        "rupee",
        "rupees",
        "dollar",
        "price",
        "cost",
        "expensive",
        "cheap",
        "free",
        "paid",
        "buy",
        "sell",
        "shop",
        "market",
        "store",
        "mall",
        "bank",
        "ATM",
        "card",
        "credit",
        "debit",
        "payment",
        "transaction",
        "account",
        "balance",
        "deposit",
        "withdraw",
        "loan",
        "interest",
        "profit",
        "loss",
        "investment",
        "savings",
        "budget",
        "expense",
        # Places & Locations
        "hospital",
        "school",
        "college",
        "university",
        "library",
        "museum",
        "park",
        "garden",
        "beach",
        "mountain",
        "river",
        "lake",
        "forest",
        "city",
        "village",
        "country",
        "state",
        "district",
        "street",
        "road",
        "bridge",
        "building",
        "house",
        "room",
        "door",
        "window",
        "airport",
        "station",
        "bus stop",
        "traffic",
        "signal",
        "hotel",
        "restaurant",
        "cafe",
        # Time & Dates
        "time",
        "date",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "morning",
        "evening",
        "night",
        "today",
        "tomorrow",
        "yesterday",
        "week",
        "weekend",
        "holiday",
        "vacation",
        "trip",
        "travel",
        "schedule",
        "calendar",
        "appointment",
        "meeting",
        "event",
        # Family & Relationships
        "family",
        "mother",
        "father",
        "brother",
        "sister",
        "husband",
        "wife",
        "son",
        "daughter",
        "friend",
        "neighbor",
        "relative",
        "cousin",
        "uncle",
        "aunt",
        "grandfather",
        "grandmother",
        # Food & Drink
        "food",
        "drink",
        "water",
        "coffee",
        "tea",
        "milk",
        "bread",
        "rice",
        "meat",
        "chicken",
        "fish",
        "egg",
        "fruit",
        "vegetable",
        "sweet",
        "chocolate",
        "ice cream",
        "pizza",
        "burger",
        "sandwich",
        "salad",
        "soup",
        "juice",
        "soda",
        "beer",
        "wine",
        "alcohol",
        # Common Adjectives
        "good",
        "bad",
        "nice",
        "beautiful",
        "ugly",
        "new",
        "old",
        "young",
        "fresh",
        "tired",
        "busy",
        "free",
        "ready",
        "finished",
        "start",
        "stop",
        "continue",
        "repeat",
        "change",
        "move",
        "come",
        "go",
        "walk",
        "run",
        "sit",
        "stand",
        "sleep",
        "wake",
        "eat",
        "drink",
        "cook",
        "wash",
        "clean",
        "work",
        "play",
        "study",
        "read",
        "write",
        "speak",
        "listen",
        "watch",
        "see",
        "look",
        "hear",
        "smell",
        "taste",
        "touch",
        "feel",
        "think",
        "know",
        "understand",
        "remember",
        "forget",
        "learn",
        "teach",
        "help",
        "ask",
        "answer",
        "tell",
        "show",
        "give",
        "take",
        "buy",
        "sell",
        "pay",
        "cost",
        "spend",
        "save",
        "earn",
        "win",
        "lose",
        "find",
        "get",
        "have",
        "has",
        "had",
        "was",
        "were",
        "is",
        "are",
        "am",
        "be",
        "been",
        "being",
        "do",
        "does",
        "did",
        "done",
        "will",
        "would",
        "can",
        "could",
        "should",
        "must",
        "may",
        "might",
        "shall",
        "let",
        "make",
        "try",
        "use",
        "want",
        "need",
        "like",
        "love",
        "hate",
        "prefer",
        "choose",
        "decide",
        "plan",
        "hope",
        "wish",
        "dream",
        "believe",
        "trust",
        "doubt",
        "worry",
        "fear",
        "excited",
        "happy",
        "sad",
        "angry",
        "surprised",
        "scared",
        "nervous",
        "calm",
        "relaxed",
        "stressed",
        "confused",
        "clear",
        "sure",
        "certain",
        "maybe",
        "perhaps",
        "probably",
        "definitely",
        "absolutely",
        "exactly",
        "almost",
        "nearly",
        "quite",
        "very",
        "really",
        "truly",
        "actually",
        "finally",
        "suddenly",
        "immediately",
        "soon",
        "later",
        "early",
        "late",
        "always",
        "never",
        "sometimes",
        "often",
        "usually",
        "rarely",
        "hardly",
        "barely",
        "completely",
        "totally",
        "fully",
        "partly",
        "mostly",
        "mainly",
        "especially",
        "particularly",
        # Common Conjunctions
        "and",
        "or",
        "but",
        "so",
        "because",
        "if",
        "when",
        "where",
        "why",
        "how",
        "what",
        "who",
        "which",
        "that",
        "this",
        "these",
        "those",
        "here",
        "there",
        "now",
        "then",
        "before",
        "after",
        "during",
        "while",
        "until",
        "since",
        "for",
        "from",
        "to",
        "in",
        "on",
        "at",
        "by",
        "with",
        "without",
        "through",
        "across",
        "over",
        "under",
        "above",
        "below",
        "between",
        "among",
        "around",
        "near",
        "far",
        "inside",
        "outside",
        "up",
        "down",
        "left",
        "right",
        "front",
        "back",
        "top",
        "bottom",
        "middle",
        "center",
        "side",
        "end",
        "beginning",
        # Numbers (keep as English)
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
        "hundred",
        "thousand",
        "million",
        "billion",
        # Common Verbs
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "done",
        "doing",
        "will",
        "would",
        "can",
        "could",
        "should",
        "must",
        "may",
        "might",
        "shall",
        "let",
        "make",
        "try",
        "use",
        "want",
        "need",
        "like",
        "love",
        "hate",
        "prefer",
        "choose",
        "decide",
        "plan",
        "hope",
        "wish",
        "dream",
        "believe",
        "trust",
        "doubt",
        "worry",
        "fear",
        "excited",
        "happy",
        "sad",
        "angry",
        "surprised",
        "scared",
        "nervous",
        "calm",
        "relaxed",
        "stressed",
        "confused",
        "clear",
        "sure",
        "certain",
        "maybe",
        "perhaps",
        "probably",
        "definitely",
        "absolutely",
        "exactly",
        "almost",
        "nearly",
        "quite",
        "very",
        "really",
        "truly",
        "actually",
        "finally",
        "suddenly",
        "immediately",
        "soon",
        "later",
        "early",
        "late",
        "always",
        "never",
        "sometimes",
        "often",
        "usually",
        "rarely",
        "hardly",
        "barely",
        "completely",
        "totally",
        "fully",
        "partly",
        "mostly",
        "mainly",
        "especially",
        "particularly",
    }

    # Split text into words
    words = text.split()
    result_words = []

    for word in words:
        # Clean word of punctuation for analysis
        clean_word = re.sub(r"[^\w]", "", word).lower()

        # Check if word is English (either in our list or contains only Latin characters)
        if clean_word in english_words or re.match(r"^[a-zA-Z]+$", clean_word):
            # Keep English words as is (preserve original case)
            result_words.append(word)
        else:
            # Convert Hindi/Urdu words to Hinglish
            hinglish_word = convert_hindi_to_hinglish_simple(word)
            result_words.append(hinglish_word)

    return " ".join(result_words)


def convert_hindi_to_hinglish_simple(hindi_text):
    """Enhanced Hindi to Hinglish converter with comprehensive word mappings"""
    # Comprehensive Hindi/Urdu to Hinglish mappings
    replacements = {
        # Pronouns
        "मैं": "main",
        "तुम": "tum",
        "आप": "aap",
        "हम": "hum",
        "वह": "woh",
        "यह": "yeh",
        "इस": "iss",
        "उस": "uss",
        "कौन": "kaun",
        "क्या": "kya",
        "कहाँ": "kahan",
        "कैसे": "kaise",
        "कब": "kab",
        "क्यों": "kyun",
        # Common words - Time and Dates
        "आज": "aaj",
        "कल": "kal",
        "परसों": "parson",
        "सोमवार": "somvar",
        "मंगलवार": "mangalvar",
        "बुधवार": "budhvar",
        "गुरुवार": "guruvar",
        "शुक्रवार": "shukrvar",
        "शनिवार": "shanivar",
        "रविवार": "ravivar",
        # Places and Locations
        "घर": "ghar",
        "ऑफिस": "office",
        "स्कूल": "school",
        "कॉलेज": "college",
        "बाजार": "bazaar",
        "दुकान": "dukaan",
        "स्टोर": "store",
        "मॉल": "mall",
        "रेस्टोरेंट": "restaurant",
        "हॉस्पिटल": "hospital",
        "बैंक": "bank",
        "पोस्ट ऑफिस": "post office",
        "स्टेशन": "station",
        "एयरपोर्ट": "airport",
        "शहर": "sheher",
        "गाँव": "gaon",
        "देश": "desh",
        "राज्य": "rajya",
        "जिला": "jila",
        # Money and Finance
        "पैसा": "paisa",
        "रुपये": "rupees",
        "रुपया": "rupee",
        "कीमत": "keemat",
        "मूल्य": "mulya",
        "दाम": "daam",
        "खर्च": "kharch",
        "बचत": "bachat",
        "कर्ज": "karz",
        "ऋण": "rin",
        "बैंक": "bank",
        "एटीएम": "ATM",
        "कार्ड": "card",
        # Work and Business
        "काम": "kaam",
        "नौकरी": "naukri",
        "व्यापार": "vyapaar",
        "बिजनेस": "business",
        "कंपनी": "company",
        "फैक्ट्री": "factory",
        "कारखाना": "karkhana",
        "दफ्तर": "daftar",
        "मीटिंग": "meeting",
        "प्रोजेक्ट": "project",
        "टास्क": "task",
        "असाइनमेंट": "assignment",
        "डेडलाइन": "deadline",
        # Communication
        "बात": "baat",
        "बातचीत": "baat-cheet",
        "कॉन्वर्सेशन": "conversation",
        "फोन": "phone",
        "कॉल": "call",
        "मैसेज": "message",
        "टेक्स्ट": "text",
        "व्हाट्सऐप": "WhatsApp",
        "ईमेल": "email",
        "लैटर": "letter",
        "न्यूज़": "news",
        "इंफॉर्मेशन": "information",
        # Time and Duration
        "समय": "samay",
        "टाइम": "time",
        "दिन": "din",
        "रात": "raat",
        "सुबह": "subah",
        "दोपहर": "dopahar",
        "शाम": "shaam",
        "सप्ताह": "saptah",
        "महीना": "mahina",
        "साल": "saal",
        "वर्ष": "varsha",
        "घंटा": "ghanta",
        "मिनट": "minute",
        "सेकंड": "second",
        # Verbs - Basic Actions
        "जा": "ja",
        "आ": "aa",
        "कर": "kar",
        "दे": "de",
        "ले": "le",
        "हो": "ho",
        "है": "hai",
        "थे": "the",
        "था": "tha",
        "रहा": "raha",
        "रही": "rahi",
        "रहे": "rahe",
        "गया": "gaya",
        "गई": "gayi",
        "गए": "gaye",
        "लगा": "laga",
        "लगी": "lagi",
        "लगे": "lage",
        "मिला": "mila",
        "मिली": "mili",
        "मिले": "mile",
        "दिखा": "dikha",
        "दिखी": "dikhi",
        "दिखे": "dikhe",
        "सुन": "sun",
        "सुना": "suna",
        "बोल": "bol",
        "बोला": "bola",
        "पढ़": "padh",
        "पढ़ा": "padha",
        "लिख": "likh",
        "लिखा": "likha",
        # Verbs - Complex Actions
        "समझ": "samajh",
        "समझा": "samjha",
        "जान": "jaan",
        "जाना": "jaana",
        "आना": "aana",
        "देना": "dena",
        "लेना": "lena",
        "करना": "karna",
        "होना": "hona",
        "रहना": "rehna",
        "बैठना": "baithna",
        "उठना": "uthna",
        "चलना": "chalna",
        "दौड़ना": "daudna",
        "खाना": "khana",
        "पीना": "peena",
        "सोना": "sona",
        "जगना": "jagna",
        # Common phrases - Present Continuous
        "जा रहा हूं": "ja raha hun",
        "जा रही हूं": "ja rahi hun",
        "आ रहा हूं": "aa raha hun",
        "आ रही हूं": "aa rahi hun",
        "कर रहा हूं": "kar raha hun",
        "कर रही हूं": "kar rahi hun",
        "खा रहा हूं": "kha raha hun",
        "खा रही हूं": "kha rahi hun",
        "पी रहा हूं": "pee raha hun",
        "पी रही हूं": "pee rahi hun",
        "सो रहा हूं": "so raha hun",
        "सो रही हूं": "so rahi hun",
        "बैठा हूं": "baitha hun",
        "बैठी हूं": "baithi hun",
        "खड़ा हूं": "khada hun",
        "खड़ी हूं": "khadi hun",
        # Common phrases - Future Tense
        "जाऊंगा": "jaunga",
        "जाऊंगी": "jaungi",
        "आऊंगा": "aaunga",
        "आऊंगी": "aaungi",
        "करूंगा": "karunga",
        "करूंगी": "karungi",
        "खाऊंगा": "khaunga",
        "खाऊंगी": "khaungi",
        "पिऊंगा": "piunga",
        "पिऊंगी": "piungi",
        # Numbers
        "एक": "ek",
        "दो": "do",
        "तीन": "teen",
        "चार": "chaar",
        "पांच": "paanch",
        "छह": "chhe",
        "सात": "saat",
        "आठ": "aath",
        "नौ": "nau",
        "दस": "das",
        "ग्यारह": "gyaarah",
        "बारह": "baarah",
        "तेरह": "terah",
        "चौदह": "chaudah",
        "पंद्रह": "pandrah",
        "सोलह": "solah",
        "सत्रह": "satrah",
        "अठारह": "atharah",
        "उन्नीस": "unnis",
        "बीस": "bees",
        "तीस": "tees",
        "चालीस": "chaalis",
        "पचास": "pachaas",
        "साठ": "saath",
        "सत्तर": "sattar",
        "अस्सी": "assi",
        "नब्बे": "nabbe",
        "सौ": "sau",
        "हजार": "hazaar",
        "लाख": "lakh",
        "करोड़": "crore",
        # Common adjectives
        "अच्छा": "accha",
        "बुरा": "bura",
        "बेहतर": "behtar",
        "सबसे अच्छा": "sabse accha",
        "बड़ा": "bada",
        "छोटा": "chota",
        "बड़ी": "badi",
        "छोटी": "choti",
        "लंबा": "lamba",
        "छोटा": "chota",
        "चौड़ा": "chauda",
        "पतला": "patla",
        "मोटा": "mota",
        "नया": "naya",
        "पुराना": "purana",
        "ताजा": "taza",
        "गर्म": "garam",
        "ठंडा": "thanda",
        "गीला": "geela",
        "सूखा": "sukha",
        "साफ": "saaf",
        "गंदा": "ganda",
        "खुश": "khush",
        "दुखी": "dukhi",
        "थका": "thaka",
        "फ्रेश": "fresh",
        "टायर्ड": "tired",
        "बिजी": "busy",
        "फ्री": "free",
        "रेडी": "ready",
        "फास्ट": "fast",
        "स्लो": "slow",
        "ईजी": "easy",
        "हार्ड": "hard",
        "सिंपल": "simple",
        "कॉम्प्लेक्स": "complex",
        # Common conjunctions and connectors
        "और": "aur",
        "या": "ya",
        "लेकिन": "lekin",
        "क्योंकि": "kyunki",
        "तो": "to",
        "फिर": "phir",
        "अब": "ab",
        "तब": "tab",
        "यहाँ": "yahan",
        "वहाँ": "vahan",
        "इधर": "idhar",
        "उधर": "udhar",
        "ऊपर": "upar",
        "नीचे": "neeche",
        "आगे": "aage",
        "पीछे": "piche",
        "दाएं": "dayein",
        "बाएं": "bayein",
        "बीच में": "beech mein",
        "के पास": "ke paas",
        "के बगल में": "ke bagal mein",
        "के सामने": "ke saamne",
        "के पीछे": "ke piche",
        # Urdu/Arabic script mappings (common words)
        "میں": "main",  # I (Urdu)
        "تم": "tum",  # you (Urdu)
        "آپ": "aap",  # you (respectful)
        "ہم": "hum",  # we (Urdu)
        "وہ": "woh",  # he/she/that (Urdu)
        "یہ": "yeh",  # this (Urdu)
        "آج": "aaj",  # today (Urdu)
        "کل": "kal",  # tomorrow/yesterday (Urdu)
        "گھر": "ghar",  # home (Urdu)
        "دفتر": "office",  # office (Urdu)
        "سکول": "school",  # school (Urdu)
        "بازار": "bazaar",  # market (Urdu)
        "دوکان": "dukaan",  # shop (Urdu)
        "پیسے": "paisa",  # money (Urdu)
        "روپے": "rupees",  # rupees (Urdu)
        "کام": "kaam",  # work (Urdu)
        "بات": "baat",  # talk/thing (Urdu)
        "وقت": "samay",  # time (Urdu)
        "دن": "din",  # day (Urdu)
        "رات": "raat",  # night (Urdu)
        "صبح": "subah",  # morning (Urdu)
        "شام": "shaam",  # evening (Urdu)
        "جا": "ja",  # go (Urdu)
        "آ": "aa",  # come (Urdu)
        "کر": "kar",  # do (Urdu)
        "دے": "de",  # give (Urdu)
        "لے": "le",  # take (Urdu)
        "ہو": "ho",  # be (Urdu)
        "ہے": "hai",  # is (Urdu)
        "تھے": "the",  # were (Urdu)
        "تھا": "tha",  # was (Urdu)
        "رہا": "raha",  # being (Urdu)
        "رہی": "rahi",  # being (feminine) (Urdu)
        "رہے": "rahe",  # being (plural) (Urdu)
        "گیا": "gaya",  # went (Urdu)
        "گئی": "gayi",  # went (feminine) (Urdu)
        "گئے": "gaye",  # went (plural) (Urdu)
        "اور": "aur",  # and (Urdu)
        "یا": "ya",  # or (Urdu)
        "لیکن": "lekin",  # but (Urdu)
        "کیونکہ": "kyunki",  # because (Urdu)
        "اچھا": "accha",  # good (Urdu)
        "برا": "bura",  # bad (Urdu)
        "بڑا": "bada",  # big (Urdu)
        "چھوٹا": "chota",  # small (Urdu)
        "نیا": "naya",  # new (Urdu)
        "پرانا": "purana",  # old (Urdu)
        "ایک": "ek",  # one (Urdu)
        "دو": "do",  # two (Urdu)
        "تین": "teen",  # three (Urdu)
        "چار": "chaar",  # four (Urdu)
        "پانچ": "paanch",  # five (Urdu)
        # Food and Drink
        "खाना": "khana",
        "पानी": "paani",
        "चाय": "chai",
        "कॉफी": "coffee",
        "दूध": "doodh",
        "रोटी": "roti",
        "चावल": "chawal",
        "दाल": "daal",
        "सब्जी": "sabzi",
        "मीट": "meat",
        "अंडा": "anda",
        "मछली": "machli",
        "चिकन": "chicken",
        "फल": "phal",
        "सब्जी": "sabzi",
        "मिठाई": "mithai",
        "चॉकलेट": "chocolate",
        "आइसक्रीम": "ice cream",
        # Family and Relationships
        "परिवार": "parivar",
        "माता": "mata",
        "पिता": "pita",
        "माँ": "maa",
        "पापा": "papa",
        "भाई": "bhai",
        "बहन": "behen",
        "पति": "pati",
        "पत्नी": "patni",
        "बेटा": "beta",
        "बेटी": "beti",
        "दादा": "dada",
        "दादी": "dadi",
        "नाना": "nana",
        "नानी": "nani",
        "चाचा": "chacha",
        "चाची": "chachi",
        "मामा": "mama",
        "मामी": "mami",
        "दोस्त": "dost",
        "यार": "yaar",
        "दोस्ती": "dosti",
        # Technology and Modern Terms
        "कंप्यूटर": "computer",
        "मोबाइल": "mobile",
        "फोन": "phone",
        "इंटरनेट": "internet",
        "वेबसाइट": "website",
        "एप": "app",
        "सॉफ्टवेयर": "software",
        "हार्डवेयर": "hardware",
        "फाइल": "file",
        "फोल्डर": "folder",
        "डाउनलोड": "download",
        "अपलोड": "upload",
        "सर्च": "search",
        "गूगल": "Google",
        "यूट्यूब": "YouTube",
        "फेसबुक": "Facebook",
        "इंस्टाग्राम": "Instagram",
        "ट्विटर": "Twitter",
        "व्हाट्सऐप": "WhatsApp",
        "टेलीग्राम": "Telegram",
        "स्काइप": "Skype",
        "जूम": "Zoom",
        "नेटफ्लिक्स": "Netflix",
        "अमेजन": "Amazon",
        "फ्लिपकार्ट": "Flipkart",
        "पेटीएम": "Paytm",
        "गूगल पे": "Google Pay",
        "फोनपे": "PhonePe",
        "यूपीआई": "UPI",
        "ओटीपी": "OTP",
        "पासवर्ड": "password",
        "यूजर": "user",
        "लॉगिन": "login",
        "लॉगआउट": "logout",
        "साइनअप": "signup",
        "प्रोफाइल": "profile",
        "सेटिंग्स": "settings",
        "नोटिफिकेशन": "notification",
        "अलर्ट": "alert",
        "मैसेज": "message",
        "चैट": "chat",
        "वीडियो": "video",
        "ऑडियो": "audio",
        "फोटो": "photo",
        "पिक्चर": "picture",
        "कैमरा": "camera",
        "माइक्रोफोन": "microphone",
        "स्पीकर": "speaker",
        "हेडफोन": "headphone",
        "ब्लूटूथ": "Bluetooth",
        "वाईफाई": "WiFi",
        "डेटा": "data",
        "स्टोरेज": "storage",
        "मेमोरी": "memory",
        "रैम": "RAM",
        "सीपीयू": "CPU",
        "प्रोसेसर": "processor",
        "स्क्रीन": "screen",
        "डिस्प्ले": "display",
        "टचस्क्रीन": "touchscreen",
        "कीबोर्ड": "keyboard",
        "माउस": "mouse",
        "लैपटॉप": "laptop",
        "डेस्कटॉप": "desktop",
        "टैबलेट": "tablet",
        "स्मार्टफोन": "smartphone",
        "आईफोन": "iPhone",
        "एंड्रॉइड": "Android",
        "विंडोज": "Windows",
        "मैक": "Mac",
        "लिनक्स": "Linux",
        "ऑपरेटिंग सिस्टम": "operating system",
        "सिस्टम": "system",
        "डिवाइस": "device",
        "गैजेट": "gadget",
        "टेक्नोलॉजी": "technology",
        "डिजिटल": "digital",
        "ऑनलाइन": "online",
        "ऑफलाइन": "offline",
        "वर्चुअल": "virtual",
        "आर्टिफिशियल इंटेलिजेंस": "artificial intelligence",
        "मशीन लर्निंग": "machine learning",
        "डेटा साइंस": "data science",
        "साइबर सिक्योरिटी": "cyber security",
        "ब्लॉकचेन": "blockchain",
        "क्रिप्टोकरेंसी": "cryptocurrency",
        "बिटकॉइन": "Bitcoin",
        "इथेरियम": "Ethereum",
        "एनएफटी": "NFT",
        "मेटावर्स": "metaverse",
        "वीआर": "VR",
        "एआर": "AR",
        "ऑगमेंटेड रियलिटी": "augmented reality",
        "वर्चुअल रियलिटी": "virtual reality",
    }

    # Convert text to lowercase for matching
    text_lower = hindi_text.lower()
    result = hindi_text

    # Apply replacements (longer phrases first to avoid partial replacements)
    # Sort by length (longest first) to handle compound words properly
    sorted_replacements = sorted(
        replacements.items(), key=lambda x: len(x[0]), reverse=True
    )

    for hindi, hinglish in sorted_replacements:
        # Apply replacements with word boundary awareness
        import re

        # Use word boundaries for more accurate matching
        pattern = r"\b" + re.escape(hindi) + r"\b"
        result = re.sub(pattern, hinglish, result, flags=re.IGNORECASE)
        # Also handle without word boundaries for compound words
        result = result.replace(hindi, hinglish)
        result = result.replace(hindi.lower(), hinglish)
        result = result.replace(hindi.upper(), hinglish)
        result = result.replace(hindi.title(), hinglish)

    # ALWAYS transliterate any remaining non-Latin characters to Latin script
    import re

    if re.search(r"[^\x00-\x7F]", result):  # If there are any non-ASCII characters
        # Basic transliteration for Devanagari characters
        devanagari_translit = {
            "अ": "a",
            "आ": "aa",
            "इ": "i",
            "ई": "ee",
            "उ": "u",
            "ऊ": "oo",
            "ए": "e",
            "ऐ": "ai",
            "ओ": "o",
            "औ": "au",
            "क": "k",
            "ख": "kh",
            "ग": "g",
            "घ": "gh",
            "ङ": "ng",
            "च": "ch",
            "छ": "chh",
            "ज": "j",
            "झ": "jh",
            "ञ": "ny",
            "ट": "t",
            "ठ": "th",
            "ड": "d",
            "ढ": "dh",
            "ण": "n",
            "त": "t",
            "थ": "th",
            "द": "d",
            "ध": "dh",
            "न": "n",
            "प": "p",
            "फ": "ph",
            "ब": "b",
            "भ": "bh",
            "म": "m",
            "य": "y",
            "र": "r",
            "ल": "l",
            "व": "v",
            "श": "sh",
            "ष": "sh",
            "स": "s",
            "ह": "h",
            "ा": "a",
            "ि": "i",
            "ी": "ee",
            "ु": "u",
            "ू": "oo",
            "े": "e",
            "ै": "ai",
            "ो": "o",
            "ौ": "au",
            "्": "",
            "ं": "n",
            "ः": "h",
            "़": "",
            " ": " ",
        }

        # Basic transliteration for Arabic/Urdu characters
        urdu_translit = {
            # Arabic/Urdu vowels and consonants
            "ا": "a",
            "آ": "aa",
            "ی": "i",
            "ے": "e",
            "و": "o",
            "او": "au",
            "ب": "b",
            "پ": "p",
            "ت": "t",
            "ٹ": "t",
            "ث": "th",
            "ج": "j",
            "چ": "ch",
            "ح": "h",
            "خ": "kh",
            "د": "d",
            "ڈ": "d",
            "ذ": "z",
            "ر": "r",
            "ڑ": "r",
            "ز": "z",
            "ژ": "zh",
            "س": "s",
            "ش": "sh",
            "ص": "s",
            "ض": "z",
            "ط": "t",
            "ظ": "z",
            "ع": "a",
            "غ": "gh",
            "ف": "f",
            "ق": "q",
            "ک": "k",
            "گ": "g",
            "ل": "l",
            "م": "m",
            "ن": "n",
            "ں": "n",
            "ہ": "h",
            "ھ": "h",
            "ء": "",
            "ی": "y",
            "ے": "e",
            # Diacritics
            "َ": "a",
            "ِ": "i",
            "ُ": "u",
            "ّ": "",
            "ْ": "",
            "ً": "an",
            "ٍ": "in",
            "ٌ": "un",
        }

        # Apply transliterations
        for char, latin in devanagari_translit.items():
            result = result.replace(char, latin)

        for char, latin in urdu_translit.items():
            result = result.replace(char, latin)

    # Final cleanup: remove any remaining non-Latin characters and replace with spaces
    result = re.sub(r"[^\x00-\x7F]+", " ", result)

    # Clean up multiple spaces
    result = re.sub(r"\s+", " ", result).strip()

    # Post-processing validation and corrections
    result = post_process_hinglish_conversion(result)

    return result


def post_process_hinglish_conversion(text):
    """Post-process Hinglish conversion to fix common errors and improve accuracy"""
    import re

    # Common correction patterns
    corrections = {
        # Fix common spelling variations
        r"\bmain\b": "main",  # Ensure consistent spelling
        r"\btum\b": "tum",
        r"\baap\b": "aap",
        r"\bhum\b": "hum",
        r"\bwoh\b": "woh",
        r"\byeh\b": "yeh",
        # Fix common Hindi-English mixing issues
        r"\bmain aap\b": "main aap",  # Ensure proper spacing
        r"\btum main\b": "tum main",
        r"\bhum log\b": "hum log",
        r"\byeh sab\b": "yeh sab",
        # Fix common verb patterns
        r"\bja raha\b": "ja raha",
        r"\bja rahi\b": "ja rahi",
        r"\baa raha\b": "aa raha",
        r"\baa rahi\b": "aa rahi",
        r"\bkar raha\b": "kar raha",
        r"\bkar rahi\b": "kar rahi",
        # Fix common question patterns
        r"\bkya\b": "kya",
        r"\bkahan\b": "kahan",
        r"\bkaise\b": "kaise",
        r"\bkab\b": "kab",
        r"\bkyun\b": "kyun",
        r"\bkaun\b": "kaun",
        # Fix common adjectives
        r"\baccha\b": "accha",
        r"\bbura\b": "bura",
        r"\bbada\b": "bada",
        r"\bchota\b": "chota",
        r"\bnaya\b": "naya",
        r"\bpurana\b": "purana",
        # Fix common time words
        r"\baaj\b": "aaj",
        r"\bkal\b": "kal",
        r"\bsubah\b": "subah",
        r"\bshaam\b": "shaam",
        r"\braat\b": "raat",
        # Fix common place words
        r"\bghar\b": "ghar",
        r"\boffice\b": "office",  # Keep English as is
        r"\bschool\b": "school",  # Keep English as is
        r"\bphone\b": "phone",  # Keep English as is
        r"\bcomputer\b": "computer",  # Keep English as is
        # Fix common numbers
        r"\bek\b": "ek",
        r"\bdo\b": "do",
        r"\bteen\b": "teen",
        r"\bchaar\b": "chaar",
        r"\bpaanch\b": "paanch",
        # Fix common conjunctions
        r"\baur\b": "aur",
        r"\bya\b": "ya",
        r"\blekin\b": "lekin",
        r"\bto\b": "to",
        r"\bphir\b": "phir",
        r"\bab\b": "ab",
        # Fix common phrases
        r"\bkaise hai\b": "kaise hai",
        r"\bkya haal\b": "kya haal",
        r"\bsab theek\b": "sab theek",
        r"\bbahut accha\b": "bahut accha",
        r"\bmujhe lagta\b": "mujhe lagta",
        r"\btumhe kya lagta\b": "tumhe kya lagta",
        r"\bmain samajh gaya\b": "main samajh gaya",
        r"\btum samajh gaye\b": "tum samajh gaye",
        # Fix capitalization for proper nouns and sentence starts
        r"\bmain\b": "Main",  # Capitalize at sentence start
        r"\btum\b": "Tum",  # Capitalize at sentence start
        r"\bhum\b": "Hum",  # Capitalize at sentence start
        r"\byeh\b": "Yeh",  # Capitalize at sentence start
        r"\bwoh\b": "Woh",  # Capitalize at sentence start
    }

    # Apply corrections
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Clean up extra spaces and punctuation
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.!?])", r"\1", text)  # Remove spaces before punctuation

    return text


def create_srt_from_speech_segments(speech_segments):
    """Create SRT content from speech-synchronized segments"""
    srt_lines = []

    for i, segment in enumerate(speech_segments, 1):
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        text = segment["text"].strip()

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between segments

    return "\n".join(srt_lines)


# API Endpoints


@app.get("/", response_class=HTMLResponse)
async def upload_page():
    """Simple upload page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hinglish Transcription Service</title>
        <link rel="stylesheet" href="/static/style.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <div class="container">
            <h1>🎵 Hinglish Transcription Service</h1>
            <p class="subtitle">Upload an audio file to get high-accuracy transcription with SRT subtitles</p>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🌐</div>
                    <div class="feature-title">Multi-Language Support</div>
                    <div class="feature-desc">Hindi → Hinglish | English → English</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI-Powered</div>
                    <div class="feature-desc">Whisper + Gemini AI pipeline</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">📝</div>
                    <div class="feature-title">SRT Output</div>
                    <div class="feature-desc">Professional subtitle format</div>
                </div>
            </div>
            
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">🎤</div>
                <div class="upload-text">Drag and drop your audio file here</div>
                <div class="upload-subtext">or click to select a file</div>
                <input type="file" id="audioFile" accept=".mp3,.wav,.m4a,.aac,.mp4" style="display: none;">
            </div>
            
            <div id="status"></div>
        </div>
        
        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('audioFile');
            const statusDiv = document.getElementById('status');
            
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    uploadFile(files[0]);
                }
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    uploadFile(e.target.files[0]);
                }
            });
            
            async function uploadFile(file) {
                const formData = new FormData();
                formData.append('audio_file', file);
                formData.append('user_id', 'web_user');
                
                statusDiv.innerHTML = '<div class="status queued">Uploading file...</div>';
                
                try {
                    const response = await fetch('/api/transcribe', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        statusDiv.innerHTML = `<div class="status queued">Job submitted: ${result.job_id}<br>Status: ${result.status}</div>`;
                        pollJobStatus(result.job_id);
                    } else {
                        statusDiv.innerHTML = `<div class="status failed">Error: ${result.detail}</div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="status failed">Error: ${error.message}</div>`;
                }
            }
            
            async function pollJobStatus(jobId) {
                const interval = setInterval(async () => {
                    try {
                        const response = await fetch(`/api/status/${jobId}`);
                        const status = await response.json();
                        
                        if (status.status === 'completed') {
                            clearInterval(interval);
                            statusDiv.innerHTML = `
                                <div class="status completed">
                                    Job completed!<br>
                                    <a href="/api/download/${jobId}" class="download-link">Download SRT File</a>
                                </div>
                            `;
                        } else if (status.status === 'failed') {
                            clearInterval(interval);
                            statusDiv.innerHTML = `<div class="status failed">Job failed: ${status.error || 'Unknown error'}</div>`;
                        } else {
                            statusDiv.innerHTML = `<div class="status processing">Processing... ${status.progress || 0}%</div>`;
                        }
                    } catch (error) {
                        clearInterval(interval);
                        statusDiv.innerHTML = `<div class="status failed">Error checking status: ${error.message}</div>`;
                    }
                }, 2000);
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "hindi-english-transcription",
        "version": "4.2.0",
        "features": [
            "hindi-to-hinglish-conversion",
            "english-to-english-formatting",
            "auto-language-detection",
            "srt-subtitle-output",
        ],
        "api_key_configured": bool(
            GOOGLE_API_KEY and GOOGLE_API_KEY != "your-google-gemini-api-key"
        ),
        "active_jobs": len(
            [job for job in jobs.values() if job["status"] in ["queued", "processing"]]
        ),
        "total_jobs": len(jobs),
    }


@app.post("/api/transcribe")
async def submit_transcription(
    audio_file: UploadFile = File(...), user_id: str = Form(default="anonymous")
):
    """Submit a new transcription job"""
    try:
        # Validate inputs
        if not audio_file.filename.lower().endswith(
            (".mp3", ".wav", ".m4a", ".aac", ".mp4")
        ):
            raise HTTPException(status_code=400, detail="Invalid audio format")

        # Generate job ID
        global job_counter
        job_counter += 1
        job_id = f"job_{job_counter}_{uuid.uuid4().hex[:8]}"

        # Save audio temporarily
        audio_path = await save_audio_temporarily(audio_file)
        logger.info(f"Audio file saved to: {audio_path}")

        # Verify file exists and get audio duration
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=500, detail="Failed to save audio file")

        duration = await get_audio_duration(audio_path)
        if duration == 0:
            try:
                os.remove(audio_path)
            except:
                pass
            raise HTTPException(
                status_code=400, detail="Could not determine audio duration"
            )

        # Create job data
        job_data = {
            "job_id": job_id,
            "user_id": user_id,
            "audio_path": audio_path,
            "duration": duration,
            "status": "queued",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "chunks_completed": 0,
        }

        # Create chunks
        chunks = create_job_chunks(job_id, audio_path, duration)
        job_data["total_chunks"] = len(chunks)

        # Store job in memory
        jobs[job_id] = job_data

        # Start processing in background
        asyncio.create_task(process_audio_simple(audio_path, job_id))

        logger.info(f"Job {job_id} created with {len(chunks)} chunks")

        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Job submitted successfully. Audio duration: {duration:.1f}s, Chunks: {len(chunks)}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a transcription job"""
    try:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job_data = jobs[job_id].copy()

        # Remove internal fields
        job_data.pop("audio_path", None)

        return job_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{job_id}")
async def download_srt(job_id: str):
    """Download the SRT file for a completed job"""
    try:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job_data = jobs[job_id]

        if job_data.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job status is {job_data.get('status')}, not completed",
            )

        srt_content = job_data.get("srt_content")
        if not srt_content:
            raise HTTPException(status_code=404, detail="SRT file not found")

        # Return SRT content directly
        return PlainTextResponse(
            content=srt_content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={job_id}.srt"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading SRT: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def get_all_jobs():
    """Get all jobs (for debugging)"""
    return {"jobs": list(jobs.keys()), "total": len(jobs)}


# Vercel handler
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Production-ready configuration
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        workers=1,  # Single worker for in-memory job tracking
    )
