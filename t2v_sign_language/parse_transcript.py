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
    for event in data["audio_events"]:
        audio_events[event["start_time"]] = {
            "confidence": event["confidence"],
            "type": event["type"],
            "end_time": event["end_time"],
        }
    # parse the whole result to make a sentence
    # save it in a list of dictionary with 'sentence', 'start_time', 'end_time', and 'confidence' as the keys
    sentences = []
    sentence = ""
    confidences = []
    weights = []
    the_start = True
    for result in data["results"]:
        # if the word is a end of sentence, save the sentence
        if (
            result["alternatives"][0]["content"] in [".", "?", "!"]
            and result["is_eos"]
            and result["type"] == "punctuation"
        ):
            weighted_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
            sentences.append(
                {
                    "sentence": sentence.strip() + result["alternatives"][0]["content"],
                    "start_time": start_time,
                    "end_time": end_time,
                    "confidence": weighted_confidence,
                }
            )
            sentence = ""
            confidences = []
            weights = []
            the_start = True
            continue

        # if the current start time is in the audio event, skip the word
        current_start_time = result["start_time"]
        for audio_events_st in audio_events.keys():
            if audio_events_st <= current_start_time <= audio_events[audio_events_st]["end_time"]:
                continue

        # add word by word to the sentence
        if result.get("attaches_to") == "previous":
            sentence += result["alternatives"][0]["content"]
        else:
            sentence += " " + result["alternatives"][0]["content"]

        if the_start:
            start_time = result["start_time"]
            the_start = False
        end_time = result["end_time"]
        confidences.append(result["alternatives"][0]["confidence"])

        # Calculate word duration and store it as weight
        word_duration = result["end_time"] - result["start_time"]
        weights.append(word_duration)

    return sentences


def convert_to_dataframe(
    sentences: list,
    name: str,
    write_dir='',
    confidence=0.9,
    offset=0,
    write=False
):
    if write and not write_dir:
        print('No such directory', write_dir)
        exit()

    name = name.replace("transcript_", "")
    trcp = pl.DataFrame(sentences)

    # select rows with only confidence > 0.90
    trcp = trcp.filter(pl.col("confidence") > 0.90)

    if offset:
        trcp = trcp.with_columns([pl.col("start_time") + offset, pl.col("end_time") + offset])

    if write:
        trcp.write_csv(f"{os.path.join(write_dir, name)}.tsv", separator="\t")

    return trcp


def trim_video(
    data: pl.DataFrame,
    video_path: str,
    name: str,
    video_info_path: str,
    df_write_dir: str = "../data/processed",
    video_save_path: str = "../data/processed",
    post_delay: float = 1.71,
    xy: tuple = (1569, 770),
    w=190,
):
    # post_delay is the delay after the last word is spoken
    # xy is the position of the top left corner of the bounding box
    # w is the width of the bounding box

    # load the sample video
    clip = mpy.VideoFileClip(video_path)
    video_paths = ['' for _ in range(len(data))]
    use_video_info = False

    def time_to_seconds(time: str):
        h, m, s = time.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    def trim_crop_save_clip(start_time, end_time, x1, y1, w, h):
        trimmed_clip = clip.subclipped(start_time, end_time + post_delay)
        cropped_clip = Crop(x1=x1, y1=y1, width=w, height=h).apply(trimmed_clip)
        path = f"{video_result_dir}/{i}.mp4"
        cropped_clip.write_videofile(path)
        return path[path.index('data'):]

    video_result_dir = os.path.join(video_save_path, name)
    if not os.path.exists(video_result_dir):
        os.mkdir(video_result_dir)

    # read the video info data if provided
    if video_info_path:
        print("Using video info", video_info_path)
        with open(video_info_path, "r") as f:
            video_info = json.load(f)

        # select the one that match current video name
        video_name = Path(video_path).name
        video_info = [video for video in video_info["videos"] if video["name"] == video_name]
        if not video_info:
            print("Video info not found")
            exit()
        else:
            video_info = video_info[0]
        # convert the time string into seconds
        video_info["props_position"] = [
            {**pos, "start": time_to_seconds(pos["start"]), "end": time_to_seconds(pos["end"])}
            for pos in video_info["props_position"]
        ]
        use_video_info = True

    # loop over the trcp polars dataframe
    # insert new column 'video_path' with the path to the trimmed video
    # and process the video and save it

    if use_video_info:
        for i, row in enumerate(data.iter_rows(named=True)):

            prop_positions = video_info["props_position"]
            for pos in prop_positions:
                xywh = pos["position"]

                # trim and crop clip if it's under the props_position start and end
                if pos["start"] <= row["start_time"] <= pos["end"]:
                    path = trim_crop_save_clip(
                        row["start_time"] + post_delay,
                        row["end_time"] + post_delay,
                        xywh["x1"],
                        xywh["y1"],
                        xywh["w"],
                        xywh["h"],
                    )
                    video_paths[i] = path
                    break
    else:
        for i, row in enumerate(data.iter_rows(named=True)):
            path = trim_crop_save_clip(row["start_time"] + post_delay, row["end_time"] + post_delay, xy[0], xy[1], w, w)
            video_paths[i] = path

    data = data.with_columns(pl.Series('video_path', video_paths))
    data.write_csv(f"{os.path.join(df_write_dir, name)}.tsv", separator="\t")


if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    parser = argparse.ArgumentParser(
        description="Parse the transcript and trim the video based on the transcript"
    )
    parser.add_argument("--transcript-file-path", type=str, required=True)
    parser.add_argument("--audio-offset", type=float, default=0)
    parser.add_argument("--df-write-dir", type=str,
                        default=os.path.join(project_dir, "data", "processed"))
    parser.add_argument("--video-path", type=str, required=True)
    parser.add_argument("--video-save-path", type=str,
                        default=os.path.join(project_dir, "data", "processed"))
    parser.add_argument("--video-info-path", type=str)
    args = parser.parse_args()

    with open(args.transcript_file_path, "r") as f:
        data = json.load(f)

    name = Path(args.transcript_file_path).stem
    name = name.replace("transcript_", "")

    sentences = parse_transcript(data)
    df = convert_to_dataframe(sentences, name, offset=args.audio_offset)
    trim_video(
        data=df,
        video_path=args.video_path,
        name=name,
        df_write_dir=args.df_write_dir,
        video_info_path=args.video_info_path,
        video_save_path=args.video_save_path,
    )
