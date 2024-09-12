


import streamlit as st
import assemblyai as aai
import time
import pandas as pd
from httpx import RemoteProtocolError
import wave
import io
import os
import zipfile
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Set page configuration
st.set_page_config(page_title="Audio Transcription App", layout="wide")

# Custom CSS for modern look
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        font-family: 'Helvetica', 'Arial', sans-serif;
    }
    .logo-container {
        text-align: center;
        margin-bottom: 1rem;
    }
    .logo {
        max-width: 300px;
        margin: 0 auto;
    }
    .main-title {
        color: #4A4A4A;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    .video-container {
        margin-bottom: 2rem;
    }
    .section-title {
        color: #2C3E50;
        font-size: 1.8rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .speaker-box {
        background-color: #F0F3F9;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .speaker-title {
        color: #34495E;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .ai-suggestion {
        color: #16A085;
        font-style: italic;
        margin-bottom: 0.5rem;
    }
    .transcript-line {
        margin-bottom: 0.5rem;
    }
    .timestamp {
        color: #7F8C8D;
        font-size: 0.9rem;
    }
    .confidence {
        color: #95A5A6;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Display logo
st.markdown("""
<div class="logo-container">
    <img class="logo" src="https://www.mediascience.com/wp-content/uploads/2020/06/MediaScience_Logo-dark.png" alt="MediaScience Logo">
</div>
""", unsafe_allow_html=True)

# Streamlit app title
st.markdown("<h1 class='main-title'>Audio Transcription with Speaker Identification</h1>", unsafe_allow_html=True)

# Embed YouTube video
st.markdown("<div class='video-container'>", unsafe_allow_html=True)
st.video("https://www.youtube.com/watch?v=SAL-mNE10TA&t=43s")
st.markdown("</div>", unsafe_allow_html=True)

# Initialize session state
if 'transcript_generated' not in st.session_state:
    st.session_state.transcript_generated = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'file_path' not in st.session_state:
    st.session_state.file_path = None
if 'compressed_file_path' not in st.session_state:
    st.session_state.compressed_file_path = None
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = None
if 'speaker_names' not in st.session_state:
    st.session_state.speaker_names = {}

# Set AssemblyAI API key
aai.settings.api_key = st.secrets["aai"]  # Replace with your actual AssemblyAI API key

# Function to extract audio chunk
def extract_audio_chunk(file_path, start_time, end_time):
    with wave.open(file_path, 'rb') as wav_file:
        framerate = wav_file.getframerate()
        start_frame = int(start_time * framerate)
        end_frame = int(end_time * framerate)
        wav_file.setpos(start_frame)
        chunk_frames = wav_file.readframes(end_frame - start_frame)
        
    chunk_io = io.BytesIO()
    with wave.open(chunk_io, 'wb') as chunk_wav:
        chunk_wav.setnchannels(wav_file.getnchannels())
        chunk_wav.setsampwidth(wav_file.getsampwidth())
        chunk_wav.setframerate(framerate)
        chunk_wav.writeframes(chunk_frames)
    
    chunk_io.seek(0)
    return chunk_io

# Function to compress audio file if it exceeds 200MB
def compress_audio(file_path):
    compressed_path = "compressed_audio.zip"
    with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, os.path.basename(file_path))
    return compressed_path

# Function to transcribe audio
def transcribe_audio(file_path, num_speakers=None):
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=num_speakers if num_speakers else None
    )
    attempts = 3

    for attempt in range(attempts):
        try:
            transcript = transcriber.transcribe(file_path, config=config)
            return transcript
        except RemoteProtocolError as e:
            st.warning(f"Attempt {attempt + 1}/{attempts} failed. Retrying...")
            time.sleep(2)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if hasattr(e, 'response'):
                st.error(f"Response content: {e.response.text}")
            break
    return None

# Function to get AI suggestions for speaker names using LangChain
def get_ai_suggestions(transcript):
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=st.secrets["gpt40"])  # Replace with your OpenAI API key
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant that can identify speakers based on the context of a conversation."),
        ("human", "Based on the following transcript, can you identify the speakers and give them names? Please provide the response in the format 'Speaker A: [suggested name]'. Here's the transcript:\n\n{transcript}")
    ])
    
    chain = prompt | llm
    
    full_transcript = "\n".join([f"Speaker {row['Speaker']}: {row['Text']}" for _, row in transcript.iterrows()])
    
    result = chain.invoke({"transcript": full_transcript})
    
    return result.content

# Main app layout
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h2 class='section-title'>Upload Audio</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a WAV file", type=["wav"])
    
    if uploaded_file is not None:
        st.audio(uploaded_file, format="audio/wav")
        
        # Check if the file size exceeds 200MB
        if uploaded_file.size > 200 * 1024 * 1024:
            st.warning("The file size exceeds 200MB. Compressing...")
            # Save the file and compress it
            with open("temp_audio.wav", "wb") as f:
                f.write(uploaded_file.getbuffer())
            compressed_file_path = compress_audio("temp_audio.wav")
            
            # Save compressed path in session state
            st.session_state.compressed_file_path = compressed_file_path
            
            # Show the compressed file size
            compressed_file_size = os.path.getsize(compressed_file_path) / (1024 * 1024)  # Convert to MB
            st.success(f"File compressed to {compressed_file_size:.2f} MB")
            
            # Unzip and play the compressed audio file
            with zipfile.ZipFile(compressed_file_path, 'r') as zip_ref:
                zip_ref.extractall(".")
                extracted_file_path = zip_ref.namelist()[0]
                st.audio(extracted_file_path, format="audio/wav")
        else:
            st.session_state.file_path = "temp_audio.wav"
            with open(st.session_state.file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        set_speakers = st.checkbox("Specify the number of speakers")
        if set_speakers:
            num_speakers = st.slider("Number of speakers", min_value=1, max_value=10, value=2)
        else:
            num_speakers = None
        
        if st.button("Generate Transcript", key="generate_transcript"):
            with st.spinner("Transcribing audio..."):
                # Transcribe the uploaded file
                transcript = transcribe_audio(st.session_state.file_path, num_speakers=num_speakers)
                
                if transcript and transcript.status == aai.TranscriptStatus.completed:
                    st.success("Transcription Successful!")
                    
                    # Process transcript data
                    data = [(u.speaker, u.text, u.start / 1000, u.end / 1000, u.confidence) for u in transcript.utterances]
                    st.session_state.df = pd.DataFrame(data, columns=["Speaker", "Text", "Start", "End", "Confidence"])
                    
                    # Get AI suggestions
                    st.session_state.ai_suggestions = get_ai_suggestions(st.session_state.df)
                    
                    st.session_state.transcript_generated = True
                else:
                    st.error("Transcription failed. Please try again.")

with col2:
    if st.session_state.transcript_generated:
        st.markdown("<h2 class='section-title'>Full Transcript</h2>", unsafe_allow_html=True)
        for _, row in st.session_state.df.iterrows():
            st.markdown(
                f"<div class='transcript-line'>"
                f"<strong>Speaker {row['Speaker']}:</strong> {row['Text']}<br>"
                f"<span class='timestamp'>Time: {row['Start']:.2f}s - {row['End']:.2f}s</span> | "
                f"<span class='confidence'>Confidence: {row['Confidence']:.2f}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        if st.button("Save Transcript", key="save_transcript"):
            st.session_state.df.to_csv("transcript_data.csv", index=False)
            st.success("Transcript saved as 'transcript_data.csv'")
        
        st.markdown("<h2 class='section-title'>Speaker Identification</h2>", unsafe_allow_html=True)
        
        # Process AI suggestions
        ai_suggestions_dict = {}
        for line in st.session_state.ai_suggestions.split('\n'):
            if ':' in line:
                speaker, name = line.split(':', 1)
                ai_suggestions_dict[speaker.strip()] = name.strip()
        
        # Group utterances by speaker
        speaker_utterances = st.session_state.df.groupby("Speaker")
        
        for speaker, utterances in speaker_utterances:
            with st.expander(f"Speaker {speaker}", expanded=True):
                st.markdown(f"<div class='speaker-box'>", unsafe_allow_html=True)
                st.markdown(f"<h3 class='speaker-title'>Speaker {speaker}</h3>", unsafe_allow_html=True)
                
                # Display AI suggestion
                ai_suggestion = ai_suggestions_dict.get(f"Speaker {speaker}", "No suggestion")
                st.markdown(f"<p class='ai-suggestion'>AI Suggestion: {ai_suggestion}</p>", unsafe_allow_html=True)
                
                # Display audio samples and text
                for _, row in utterances.head(3).iterrows():
                    audio_chunk = extract_audio_chunk(st.session_state.file_path, row['Start'], row['End'])
                    st.audio(audio_chunk, format="audio/wav")
                    st.write(row['Text'])
                
                # Input for speaker name
                st.session_state.speaker_names[speaker] = st.text_input(f"Enter name for Speaker {speaker}", key=f"name_input_{speaker}")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("Apply Speaker Names", key="apply_names"):
            st.session_state.df['Speaker'] = st.session_state.df['Speaker'].map(st.session_state.speaker_names)
            st.success("Speaker names applied to the transcript!")
            
            st.markdown("<h2 class='section-title'>Final Transcript with Identified Speakers</h2>", unsafe_allow_html=True)
            st.dataframe(st.session_state.df)
