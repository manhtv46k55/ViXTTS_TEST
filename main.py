import os
import torch
import io
import requests
from io import BytesIO
import numpy as np
from huggingface_hub import snapshot_download
from TTS.tts.configs.xtts_config import XttsConfig # type: ignore
from TTS.tts.models.xtts import Xtts # type: ignore
import soundfile as sf




device = "cuda" if torch.cuda.is_available() else "cpu"

snapshot_download(repo_id="capleaf/viXTTS",
                  repo_type="model",
                  local_dir="model")

config = XttsConfig()
config.load_json("model/config.json")
XTTS_MODEL = Xtts.init_from_config(config)
XTTS_MODEL.load_checkpoint(config, checkpoint_dir="model/")
XTTS_MODEL.eval()
if torch.cuda.is_available():
    XTTS_MODEL.cuda()

gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
    audio_path="model/456.mp3",#cho mẫu giọng nói vào thư mục model
    gpt_cond_len=XTTS_MODEL.config.gpt_cond_len,
    max_ref_length=XTTS_MODEL.config.max_ref_len,
    sound_norm_refs=XTTS_MODEL.config.sound_norm_refs,
)

text_chunks = "Xin chào ! Hôm nay bạn thế nào, những ngày mưa có lẽ cũng khiến cho tâm hồn ta có đôi chút mệt mỏi."#250 ký tự
temp_files = []

out_wav = XTTS_MODEL.inference(
        text=text_chunks,
        language="vi",
        gpt_cond_latent=gpt_cond_latent,
        speaker_embedding=speaker_embedding,
        temperature=0.3,
        length_penalty=1.0,
        repetition_penalty=10.0,
        top_k=30,
        top_p=0.85,
    )
    
wav_data = out_wav["wav"]
sample_rate = 24000
    
if wav_data is not None and len(wav_data) > 0:
    temp_file = f"temp_audio_chunk.wav"
    temp_files.append(temp_file)
    # Ghi file tạm thời
    sf.write(temp_file, wav_data, samplerate=sample_rate)
else:
    print(f"Warning: chunk has no audio data")

# Gộp các file tạm thành một file cuối
combined_audio = []

for temp_file in temp_files:
    if os.path.exists(temp_file):
        data, _ = sf.read(temp_file)
        combined_audio.append(data)
    else:
        print(f"Warning: {temp_file} does not exist")

if not combined_audio:
    print ({"message": "No audio chunks were generated."})

# Chuyển list thành numpy array và ghi vào file
combined_audio = np.concatenate(combined_audio, axis=0)
final_file = "final_output.wav"
sf.write(final_file, combined_audio, samplerate=sample_rate)

# Xóa các file tạm sau khi gộp
for temp_file in temp_files:
    if os.path.exists(temp_file):
        os.remove(temp_file)



