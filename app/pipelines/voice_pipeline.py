from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np 

import io 
from functools import lru_cache
import librosa 


@lru_cache(maxsize=1)
def load_voice_encoder():
    return VoiceEncoder()


def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio) 

        embedding = encoder.embed_utterance(wav)

        return embedding.tolist()
    except Exception as e:
        print(f'voice recog error: {e}')
        return None



def identify_speaker(new_embedding, condidates_dict, threshold= 0.65):
    if new_embedding is None or not condidates_dict:
        return None, 0.0
    
    best_sid = None
    best_score = -1.0
    
    # condidates_dict list 
    for sid, stored_embedding in condidates_dict.items():
        if stored_embedding:
            similarity = np.dot(new_embedding, stored_embedding)
            if similarity> best_score:
                best_score = similarity
                best_sid = sid
    
    if best_score >= threshold:
        return best_sid, best_score
    
    return None, best_score


def process_bulk_audio(audio_bytes, condidates_dict, threshold= 0.65):
    try:
        encoder = load_voice_encoder()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)

        segments = librosa.effects.split(audio, top_db=30)

        identify_results = {}

        for start , end in segments:
            if(end-start) < sr*0.5:
                continue
            segments_audio = audio[start:end]
            wav = preprocess_wav(segments_audio)
            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding,condidates_dict, threshold)

            if sid :
                 if sid not in identify_results or  score > identify_results[sid]:
                     identify_results[sid] = score

        
        return identify_results
    except Exception as e:
        print(f'bulk process error: {e}')
        return {}