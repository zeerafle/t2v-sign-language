import os
from dotenv import load_dotenv, find_dotenv
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError
import json

# Find .env automagically by walking up directories until it's found
dotenv_path = find_dotenv()

# Load up the entries as environment variables
load_dotenv(dotenv_path)

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.getenv('SP_API_KEY')

settings = ConnectionSettings(
    url='https://asr.api.speechmatics.com/v2',
    auth_token=API_KEY
)

# Read the job ID from the file
with open(os.path.join(project_dir, 't2v_sign_language', 'job_id.txt'), 'r') as f:
    job_id = f.read().strip()

# Open the client using a context manager
with BatchClient(settings) as client:
    try:
        job_status = client.check_job_status(job_id)
        print(f'job {job_id} status: {job_status["job"]["status"]}')

        if job_status['job']['status'] == 'done':
            transcript = client.get_job_result(job_id, transcription_format='json-v2')

            with open(os.path.join(project_dir, 'data', 'interim', 'transcript_detik_detik_proklamasi_part2.json'), 'w') as f:
                json.dump(transcript, f)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print('Invalid API key - Check your API_KEY at the top of the code!')
        elif e.response.status_code == 400:
            print(e.response.json()['detail'])
        else:
            raise e
