import json
import os
import argparse
from pathlib import Path

import polars as pl
import moviepy as mpy
from moviepy.video.fx.Crop import Crop


def parse_transcript(data: dict):
    # create dictionary of audio events with the start time as the key
    audio_events = {}
    for event in data['audio_events']:
        audio_events[event['start_time']] = {'confidence': event['confidence'],
                                            'type': event['type'],
                                            'end_time': event['end_time']}
    # parse the whole result to make a sentence
    # save it in a list of dictionary with 'sentence', 'start_time', 'end_time', and 'confidence' as the keys
    sentences = []
    sentence = ''
    confidences = []
    weights = []
    the_start = True
    for result in data['results']:
        # if the word is a end of sentence, save the sentence
        if result['alternatives'][0]['content'] in ['.', '?', '!'] and result['is_eos'] and result['type'] == 'punctuation':
            weighted_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
            sentences.append({'sentence': sentence.strip() + result['alternatives'][0]['content'],
                            'start_time': start_time,
                            'end_time': end_time,
                            'confidence': weighted_confidence})
            sentence = ''
            confidences = []
            weights = []
            the_start = True
            continue

        # if the current start time is in the audio event, skip the word
        current_start_time = result['start_time']
        for audio_events_st in audio_events.keys():
            if audio_events_st <= current_start_time <= audio_events[audio_events_st]['end_time']:
                continue

        # add word by word to the sentence
        if result.get('attaches_to') == 'previous':
            sentence += result['alternatives'][0]['content']
        else:
            sentence += ' ' + result['alternatives'][0]['content']

        if the_start:
            start_time = result['start_time']
            the_start = False
        end_time = result['end_time']
        confidences.append(result['alternatives'][0]['confidence'])

        # Calculate word duration and store it as weight
        word_duration = result['end_time'] - result['start_time']
        weights.append(word_duration)

    return sentences


def convert_to_dataframe(sentences: list, name: str, confidence=0.9, offset=0, write = True, write_dir = '../data/processed/'):
    name = name.replace('transcript_', '')
    trcp = pl.DataFrame(sentences)

    # select rows with only confidence > 0.90
    trcp = trcp.filter(pl.col("confidence") > 0.90)

    if offset:
        trcp = trcp.with_columns([
            pl.col("start_time") + offset,
            pl.col("end_time") + offset
        ])

    if write:
        trcp.write_csv(f'{os.path.join(write_dir, name)}.tsv', separator='\t')

    return trcp


def trim_video(data: pl.DataFrame, video_path: str, name: str, video_save_path: str = '../data/processed', post_delay: int = 1.71, xy: tuple = (1569, 770), w=190):
    # post_delay is the delay after the last word is spoken
    # xy is the position of the top left corner of the bounding box
    # w is the width of the bounding box

    # load the sample video
    clip = mpy.VideoFileClip(video_path)

    video_result_dir = os.path.join(video_save_path, name)
    if not os.path.exists(video_result_dir):
        os.mkdir(video_result_dir)

    # loop over the trcp polars dataframe
    # insert new column 'video_path' with the path to the trimmed video
    # and process the video and save it

    video_paths = []
    for i, row in enumerate(data.iter_rows(named=True)):
        trimmed_clip = clip.subclipped(row['start_time'], row['end_time'] + post_delay)
        cropped_clip = Crop(x1=xy[0], y1=xy[1], width=w, height=w).apply(trimmed_clip)
        path = f'{video_result_dir}/{i}.mp4'
        cropped_clip.write_videofile(path)
        video_paths.append(path)

if __name__ == '__main__':
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    parser = argparse.ArgumentParser(
        description='Parse the transcript and trim the video based on the transcript'
    )
    parser.add_argument('--transcript-file', type=str, required=True)
    parser.add_argument('--audio-offset', type=float, default=0)
    parser.add_argument('--df-write-dir', type=str, default=os.path.join(project_dir, 'data', 'processed'))
    parser.add_argument('--video-path', type=str, required=True)
    parser.add_argument('--video-save-path', type=str, default=os.path.join(project_dir, 'data', 'processed'))
    args = parser.parse_args()

    with open(args.transcript_file, 'r') as f:
        data = json.load(f)

    name = Path(args.transcript_file).stem
    name = name.replace('transcript_', '')

    sentences = parse_transcript(data)
    df = convert_to_dataframe(sentences, name, offset=args.audio_offset, write=True, write_dir=args.df_write_dir)
    trim_video(df, args.video_path, name, args.video_save_path)
