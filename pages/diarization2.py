import streamlit as st
import assemblyai as aai
import time
import pandas as pd
from httpx import RemoteProtocolError
import io
import os
import uuid
from pydub import AudioSegment
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import re

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
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = None
if 'speaker_names' not in st.session_state:
    st.session_state.speaker_names = {}
if 'ai_suggestions_generated' not in st.session_state:
    st.session_state.ai_suggestions_generated = False

# Set AssemblyAI API key
aai.settings.api_key = st.secrets["aai"]  # Replace with your actual AssemblyAI API key

# Function to extract audio chunk
def extract_audio_chunk(file_path, start_time, end_time):
    audio = AudioSegment.from_file(file_path)
    chunk = audio[start_time * 1000:end_time * 1000]  # pydub works in milliseconds
    chunk_io = io.BytesIO()
    chunk.export(chunk_io, format="wav")
    chunk_io.seek(0)
    return chunk_io

# Function to compress audio file if it exceeds 200MB
def compress_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    compressed_path = f"{uuid.uuid4()}_compressed.wav"
    # Reduce the frame rate and sample width to compress the audio
    audio = audio.set_frame_rate(16000).set_sample_width(2)
    audio.export(compressed_path, format="wav", bitrate="128k")
    return compressed_path

# Function to transcribe audio
def transcribe_audio(file_path, num_speakers=None, word_boost=None, boost_param="default"):
    transcriber = aai.Transcriber()

    # Configuring custom vocabulary for ASR
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=num_speakers if num_speakers else None,
        word_boost=word_boost,  # List of custom vocabulary words
        boost_param=boost_param  # Control the weight of the word boost
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
            st.error(f"An error occurred during transcription: {str(e)}")
            break
    return None

# Function to get AI suggestions for speaker names using LangChain
def get_ai_suggestions(transcript_df):
    try:
        llm = ChatOpenAI(model_name="gpt-4o-2024-08-06", temperature=0, openai_api_key=st.secrets["gpt40"])

        prompt_template = """
You are an AI assistant that identifies speakers based on the context of a conversation.
Based on the following transcript, identify and name the speakers.
**Use the same speaker numbers as in the transcript when providing your suggestions.**

Provide the response in the exact format:

Speaker 1: [Suggested Name]
Speaker 2: [Suggested Name]
...

**Do not include any extra text or explanations.**

Transcript:
{transcript}
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)

        chain = LLMChain(llm=llm, prompt=prompt)

        full_transcript = "\n".join([f"Speaker {row['Speaker']}: {row['Text']}" for _, row in transcript_df.iterrows()])

        result = chain.run(transcript=full_transcript)

        # Display the AI's response for debugging
        st.write("AI's Response:")
        st.write(result)

        return result
    except Exception as e:
        st.error(f"An error occurred while fetching AI suggestions: {str(e)}")
        return "No suggestions available due to an error."

# Function to parse AI suggestions
def parse_ai_suggestions(ai_response):
    ai_suggestions_dict = {}
    # Adjust the pattern to match speaker labels that are either numbers or letters
    pattern = r"Speaker (\w+):\s*(.+)"
    matches = re.findall(pattern, ai_response)
    if not matches:
        st.warning("No matches found in AI response. Please check the AI's output.")
    for speaker_label, name in matches:
        ai_suggestions_dict[speaker_label.strip()] = name.strip()
    return ai_suggestions_dict

# Function to sanitize custom vocabulary input
def sanitize_custom_vocabulary(word_boost_input):
    words = [word.strip() for word in word_boost_input.split(',') if word.strip()]
    return words if words else None

# Main app layout
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h2 class='section-title'>Upload Audio</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a WAV file", type=["wav"])

    if uploaded_file is not None:
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}_audio.wav"
        with open(unique_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.file_path = unique_filename

        st.audio(unique_filename, format="audio/wav")

        # Custom vocabulary input
        st.markdown("<h2 class='section-title'>Custom Vocabulary</h2>", unsafe_allow_html=True)
        word_boost_input = st.text_area("Enter custom vocabulary words or phrases (comma-separated)")
        word_boost_list = sanitize_custom_vocabulary(word_boost_input)

        # Boost parameter selection
        boost_param = st.selectbox(
            "Set boost parameter (how much emphasis is placed on the custom vocabulary)",
            options=["low", "default", "high"],
            index=1
        )

        # Check if the file size exceeds 200MB
        if os.path.getsize(unique_filename) > 200 * 1024 * 1024:
            st.warning("The file size exceeds 200MB. Compressing...")

            # Compress the audio file
            compressed_file_path = compress_audio(unique_filename)

            # Update the file path in session state
            st.session_state.file_path = compressed_file_path

            # Show the compressed file size
            compressed_file_size = os.path.getsize(compressed_file_path) / (1024 * 1024)  # Convert to MB
            st.success(f"File compressed to {compressed_file_size:.2f} MB")

            # Play the compressed audio file
            st.audio(compressed_file_path, format="audio/wav")
        else:
            st.session_state.file_path = unique_filename

        set_speakers = st.checkbox("Specify the number of speakers")
        if set_speakers:
            num_speakers = st.slider("Number of speakers", min_value=1, max_value=10, value=2)
        else:
            num_speakers = None

        if st.button("Generate Transcript", key="generate_transcript"):
            with st.spinner("Transcribing audio..."):
                # Transcribe the uploaded file with custom vocabulary and boost settings
                transcript = transcribe_audio(
                    st.session_state.file_path,
                    num_speakers=num_speakers,
                    word_boost=word_boost_list,
                    boost_param=boost_param
                )

                if transcript and transcript.status == aai.TranscriptStatus.completed:
                    st.success("Transcription Successful!")

                    # Process transcript data
                    data = [(u.speaker, u.text, u.start / 1000, u.end / 1000, u.confidence) for u in transcript.utterances]
                    st.session_state.df = pd.DataFrame(data, columns=["Speaker", "Text", "Start", "End", "Confidence"])

                    st.session_state.transcript_generated = True
                else:
                    st.error("Transcription failed. Please try again.")

with col2:
    if st.session_state.transcript_generated:
        st.markdown("<h2 class='section-title'>Full Transcript</h2>", unsafe_allow_html=True)

        # Display the transcript using st.dataframe for efficiency
        st.dataframe(st.session_state.df)

        if st.button("Save Transcript", key="save_transcript"):
            st.session_state.df.to_csv("transcript_data.csv", index=False)
            st.success("Transcript saved as 'transcript_data.csv'")

        # Add a button to get AI suggestions
        if st.button("Get AI Suggestions", key="get_ai_suggestions"):
            with st.spinner("Fetching AI suggestions..."):
                # Get AI suggestions
                ai_suggestions_response = get_ai_suggestions(st.session_state.df)
                st.session_state.ai_suggestions = ai_suggestions_response
                st.session_state.ai_suggestions_generated = True
                st.success("AI suggestions fetched successfully!")

    if st.session_state.ai_suggestions_generated:
        st.markdown("<h2 class='section-title'>Speaker Identification</h2>", unsafe_allow_html=True)

        # Parse AI suggestions
        ai_suggestions_dict = parse_ai_suggestions(st.session_state.ai_suggestions)

        # Group utterances by speaker
        speaker_utterances = st.session_state.df.groupby("Speaker")

        for speaker, utterances in speaker_utterances:
            with st.expander(f"Speaker {speaker}", expanded=True):
                st.markdown(f"<div class='speaker-box'>", unsafe_allow_html=True)
                st.markdown(f"<h3 class='speaker-title'>Speaker {speaker}</h3>", unsafe_allow_html=True)

                # Display AI suggestion
                ai_suggestion = ai_suggestions_dict.get(speaker, "No suggestion")
                st.markdown(f"<p class='ai-suggestion'>AI Suggestion: {ai_suggestion}</p>", unsafe_allow_html=True)

                # Display audio samples and text
                for _, row in utterances.head(3).iterrows():
                    audio_chunk = extract_audio_chunk(st.session_state.file_path, row['Start'], row['End'])
                    st.audio(audio_chunk, format="audio/wav")
                    st.write(row['Text'])

                # Input for speaker name
                speaker_name_key = f"name_input_{speaker}"
                st.session_state.speaker_names[speaker] = st.text_input(f"Enter name for Speaker {speaker}", key=speaker_name_key, value=ai_suggestion)

                st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Apply Speaker Names", key="apply_names"):
            # Map the speaker numbers to names
            st.session_state.df['Speaker'] = st.session_state.df['Speaker'].map(st.session_state.speaker_names)
            st.success("Speaker names applied to the transcript!")

            st.markdown("<h2 class='section-title'>Final Transcript with Identified Speakers</h2>", unsafe_allow_html=True)
            st.dataframe(st.session_state.df)

            if st.button("Save Final Transcript", key="save_final_transcript"):
                st.session_state.df.to_csv("final_transcript_data.csv", index=False)
                st.success("Final transcript saved as 'final_transcript_data.csv'")
