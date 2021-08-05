from google.cloud import speech
from pydub import AudioSegment
from google.cloud import storage
import datetime
from webvtt import WebVTT, Caption
import boto3
from google.cloud import translate
from django.conf import settings
from boto3 import s3


import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= getattr(settings, "GCLOUD_CREDS", None)


def process_speech_to_txt(path, lang):
	client = speech.SpeechClient()
	audio = speech.RecognitionAudio(path)
	config = speech.RecognitionConfig(
		encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
		audio_channel_count = 2,
		language_code=lang,
		enable_word_time_offsets=True
	)
	operation = client.long_running_recognize(config=config, audio=audio)
	response = operation.result(timeout=660)
	return response


#Upload file to gcs
def upload_to_gcs(audio_file, bucket_name):
	storage_client = storage.Client()
	url = dict(uri='gs://' + bucket_name + '/' + audio_file)
	if storage_client.bucket(bucket_name):
		bucket = storage_client.bucket(bucket_name)
		blob = bucket.blob(audio_file)
		try:
			blob.upload_from_filename(audio_file)
			return url, blob
		except:
			return "File was not uploaded. There seems to be a problem with your file."
	else:
		bucket = storage_client.create_bucket(bucket_name)
		print("Bucket {} created.".format(bucket.name))
		bucket = storage_client.bucket(bucket_name)
		blob = bucket.blob(audio_file)
		try:
			blob.upload_from_filename(audio_file)
			return url, blob
		except:
			return "File was not uploaded. There seems to be a problem with your file."



def extract_audio_from_video(video_name):
	if video_name.endswith('.mp4'):
		output_file = 'tmp/audio/'+video_name.replace('mp4', 'flac')
		try:
			AudioSegment.from_file('tmp/video/'+video_name).export(output_file, format='flac', channels=2)
			return output_file
		except:
			return "There has been an error with your audio file. The file seems to be either mono or is corrupted."
	else:
		return  "This video file is not in mp4 format"


def generate_vtt_caption(speech_txt_response, lang, bin=4):

	vtt = WebVTT()
	vtt.captions.append('Kind: captions')
	vtt.captions.append('Language: '+lang)
	index = 0
	for result in speech_txt_response.results:
		try:
			if result.alternatives[0].words[0].start_time.seconds:
				# bin start -> for first word of result
				start_sec = result.alternatives[0].words[0].start_time.seconds
				start_microsec = result.alternatives[0].words[0].start_time.seconds
			else:
				# bin start -> For First word of response
				start_sec = 0
				start_microsec = 0
			end_sec = start_sec + bin  # bin end sec

			# for last word of result
			last_word_end_sec = result.alternatives[0].words[-1].end_time.seconds
			last_word_end_microsec = result.alternatives[0].words[-1].end_time.seconds

			# bin transcript
			transcript = result.alternatives[0].words[0].word

			index += 1  # subtitle index

			for i in range(len(result.alternatives[0].words) - 1):
				try:
					word = result.alternatives[0].words[i + 1].word
					word_start_sec = result.alternatives[0].words[i + 1].start_time.seconds
					word_start_microsec = result.alternatives[0].words[
						                      i + 1].start_time.seconds    # 0.001 to convert nana -> micro
					word_end_sec = result.alternatives[0].words[i + 1].end_time.seconds
					word_end_microsec = result.alternatives[0].words[i + 1].end_time.seconds

					if word_end_sec < end_sec:
						transcript = transcript + " " + word
					else:
						previous_word_end_sec = result.alternatives[0].words[i].end_time.seconds
						previous_word_end_microsec = result.alternatives[0].words[i].end_time.seconds

						# append bin transcript
						init_sec = '0'+str(datetime.timedelta( seconds=start_sec))+'.000'
						end_sec = '0'+str(datetime.timedelta( seconds=previous_word_end_sec))+'.000'
						vtt.captions.append(Caption(init_sec, end_sec, transcript))

						# reset bin parameters
						start_sec = word_start_sec
						start_microsec = word_start_microsec
						end_sec = start_sec + bin
						transcript = result.alternatives[0].words[i + 1].word

						index += 1
				except IndexError:
					pass
			# append transcript of last transcript in bin
			init_sec = '0' + str(datetime.timedelta(seconds=start_sec)) + '.000'
			end_sec = '0' + str(datetime.timedelta(seconds=last_word_end_sec)) + '.000'
			vtt.captions.append(Caption(init_sec, end_sec, transcript))

			index += 1
		except IndexError:
			pass
		return vtt


def s3_upload_file_to_bucket(file, bucket, Key, metadata):
	client = boto3.client('s3')
	response = client.upload_file(file, bucket, Key, {'Metadata':metadata})
	if response:
		return response


def generate_translation(vtt, lang):
	new_vtt = WebVTT()
	new_vtt.captions.append('Kind: captions')
	new_vtt.captions.append('Language: '+lang)
	for i in range(0, len(vtt.captions)-1):
		if isinstance(vtt[i], str):
			pass
		else:
			new_txt = translate_text(vtt[i].text, lang)
			new_vtt.captions.append(Caption(vtt[i].start, vtt[i].end, new_txt))
	return new_vtt


def translate_text(text, lang, project_id=getattr(settings, "GCLOUD_PROJECT", None)):

    client = translate.TranslationServiceClient()

    location = "global"

    parent = f"projects/{project_id}/locations/{location}"

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",
            "source_language_code": lang,
            "target_language_code": "en-US",
        }
    )

    # Get the translation from the response
    for translation in response.translations:
        return format(translation.translated_text)


def get_s3_url(bucket, key):
	url = s3.generate_presigned_url('get_object',
                                Params={
                                    'Bucket': bucket,
                                    'Key': key,
                                },
                                ExpiresIn=0)
	return url



