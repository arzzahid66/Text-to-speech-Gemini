import streamlit as st
import requests
import base64
import json
import struct
import wave
import io

# Page configuration
st.set_page_config(
    page_title="Gemini Text-to-Speech",
    page_icon="🎙️",
    layout="centered"
)

def convert_l16_to_wav(pcm_data):
    """Convert L16 PCM audio to WAV format"""
    sample_rate = 24000
    num_channels = 1
    sample_width = 2  # 16-bit
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    
    wav_buffer.seek(0)
    return wav_buffer.getvalue()

def generate_speech(api_key, text, voice_name="Puck"):
    """Generate speech using Gemini 2.5 Flash TTS API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": text}]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        
        # Extract audio data
        if "candidates" in result and len(result["candidates"]) > 0:
            inline_data = result["candidates"][0]["content"]["parts"][0].get("inlineData")
            if inline_data:
                audio_data = base64.b64decode(inline_data["data"])
                mime_type = inline_data["mimeType"]
                
                # Convert L16 PCM to WAV
                if "audio/L16" in mime_type or "audio/pcm" in mime_type:
                    audio_data = convert_l16_to_wav(audio_data)
                
                return audio_data, None
        
        return None, "No audio data in response"
        
    except requests.exceptions.RequestException as e:
        return None, f"API Error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

# Main UI
st.title("🎙️ Gemini Text-to-Speech")
st.markdown("Convert text to speech using Google's Gemini 2.5 Flash TTS model")

# API Key input
api_key = st.text_input(
    "Enter your Gemini API Key",
    type="password",
    help="Get your free API key from https://aistudio.google.com/apikey"
)

# Voice selection
voices = [
    "Puck", "Charon", "Kore", "Fenrir", "Aoede",
    "Leda", "Grus", "Elio", "Kiera", "Orion"
]

selected_voice = st.selectbox(
    "Select Voice",
    voices,
    help="Choose a voice for the audio output"
)

# Text input with character limit warning
st.markdown("### Enter Text to Convert")
st.info("💡 Recommended: Keep text under 2000 characters for best results. The model supports up to ~32k tokens but may truncate longer audio.")

text_input = st.text_area(
    "Text Input",
    placeholder="Enter the text you want to convert to speech...",
    height=200,
    max_chars=5000,
    label_visibility="collapsed"
)

# Character counter
char_count = len(text_input)
if char_count > 0:
    color = "red" if char_count > 2000 else "orange" if char_count > 1500 else "green"
    st.markdown(f"<p style='color: {color}; font-size: 14px;'>Characters: {char_count}/5000</p>", unsafe_allow_html=True)

# Generate button
if st.button("🎵 Generate Speech", type="primary", disabled=not api_key or not text_input):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API key")
    elif not text_input:
        st.error("⚠️ Please enter some text to convert")
    else:
        with st.spinner("Generating audio..."):
            audio_data, error = generate_speech(api_key, text_input, selected_voice)
            
            if error:
                st.error(f"❌ {error}")
            elif audio_data:
                st.success("✅ Audio generated successfully!")
                
                # Display audio player
                st.audio(audio_data, format="audio/wav")
                
                # Download button
                st.download_button(
                    label="📥 Download Audio",
                    data=audio_data,
                    file_name="gemini_tts_output.wav",
                    mime="audio/wav"
                )

# Footer with instructions
st.markdown("---")
st.markdown("""
### 📋 Instructions:
1. Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Paste your API key in the input field above
3. Select your preferred voice
4. Enter the text you want to convert (keep it under 2000 characters for optimal results)
5. Click "Generate Speech" to create your audio
6. Listen and download the generated audio file

### ℹ️ About:
- **Model**: Gemini 2.5 Flash TTS (Preview)
- **Format**: WAV audio (24kHz, 16-bit PCM)
- **Limit**: Recommended 2000 characters per request
- **Audio Length**: Supports up to ~10 minutes of audio output
""")

st.markdown("---")
st.markdown("*Made with ❤️ using Streamlit and Google Gemini API*")