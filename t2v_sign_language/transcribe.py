import argparse
import os
from dotenv import load_dotenv, find_dotenv

from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError

# find .env automagically by walking up directories until it's found
dotenv_path = find_dotenv()

# load up the entries as environment variables
load_dotenv(dotenv_path)

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.getenv('SP_API_KEY')

def transcribe(audio_file_path, language='id'):
    settings = ConnectionSettings(
        url='https://asr.api.speechmatics.com/v2',
        auth_token=API_KEY
    )

    conf = {
        "type": "transcription",
        "audio_events_config": {
            "types": [
            "laughter",
            "music",
            "applause"
            ]
        },
        "transcription_config": {
            "language": language,
            "diarization": "speaker",
            "operating_point": "enhanced",
            "enable_entities": True,
            "audio_filtering_config": {
            "volume_threshold": 0
            }
        }
    }

    # Open the client using a context manager
    with BatchClient(settings) as client:
        try:
            job_id = client.submit_job(
                audio=audio_file_path,
                transcription_config=conf,
            )
            print(f'job {job_id} submitted successfully, waiting for transcript')

            with open(os.path.join(project_dir, 't2v_sign_language', 'job_id.txt'), 'w') as f:
                f.write(job_id)

        except HTTPStatusError as e:
            if e.response.status_code == 401:
                print('Invalid API key - Check your API_KEY at the top of the code!')
            elif e.response.status_code == 400:
                print(e.response.json()['detail'])
            else:
                raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio-file-path', type=str, required=True, help='Path to audio file')
    args = parser.parse_args()

    transcribe(args.audio_file_path)
