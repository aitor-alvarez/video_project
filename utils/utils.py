from google.cloud import speech
from pydub import AudioSegment
from google.cloud import storage
import datetime
from webvtt import WebVTT, Caption
import boto3
from video_project import settings


import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= settings.gcloud_creds


def process_speech_to_txt(path, lang):
	client = speech.SpeechClient()
	audio = speech.RecognitionAudio(path)
	config = speech.RecognitionConfig(
		encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
		language_code=lang,
	)
	response = client.recognize(config=config, audio=audio)
	## print results
	for i, result in enumerate(response.results):
		alternative = result.alternatives[0]
		print("-" * 20)
		print("First alternative of result {}".format(i))
		print(u"Transcript: {}".format(alternative.transcript))
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
			return ({'url':url, 'status':1})
		except:
			return ({'txt': "File was not uploaded. There seems to be a problem with your file.", 'status': 0})
	else:
		bucket = storage_client.create_bucket(bucket_name)
		print("Bucket {} created.".format(bucket.name))
		bucket = storage_client.bucket(bucket_name)
		blob = bucket.blob(audio_file)
		try:
			blob.upload_from_filename(audio_file)
			return ({'url':url, 'status':1})
		except:
			return ({'txt':"File was not uploaded. There seems to be a problem with your file.", 'status':0})



def extract_audio_from_video(video_path):
	if video_path.endswith('.mp4'):
		audiofile = AudioSegment.from_file(video_path)
		output_file = 'tmp/audio/'+video_path.replace('mp4', 'flac')
		try:
			AudioSegment.from_file(video_path).export(output_file, format='flac')
			return {'file': output_file, 'status':1}
		except:
			return {'txt': "There has been an error with your audio file. The file might be corrupted or damaged.", 'status':0}
	else:
		return {'txt': "This video file is not in mp4 format", 'status':0}


def generate_vtt_caption(speech_txt_response, bin=3):
	vtt = WebVTT()
	index = 0
	for result in speech_txt_response:
		try:
			if result.alternatives[0].words[0].start_time.seconds:
				# bin start -> for first word of result
				start_sec = result.alternatives[0].words[0].start_time.seconds
				start_microsec = result.alternatives[0].words[0].start_time.nanos * 0.001
			else:
				# bin start -> For First word of response
				start_sec = 0
				start_microsec = 0
			end_sec = start_sec + bin  # bin end sec

			# for last word of result
			last_word_end_sec = result.alternatives[0].words[-1].end_time.seconds
			last_word_end_microsec = result.alternatives[0].words[-1].end_time.nanos * 0.001

			# bin transcript
			transcript = result.alternatives[0].words[0].word

			index += 1  # subtitle index

			for i in range(len(result.alternatives[0].words) - 1):
				try:
					word = result.alternatives[0].words[i + 1].word
					word_start_sec = result.alternatives[0].words[i + 1].start_time.seconds
					word_start_microsec = result.alternatives[0].words[
						                      i + 1].start_time.nanos * 0.001  # 0.001 to convert nana -> micro
					word_end_sec = result.alternatives[0].words[i + 1].end_time.seconds
					word_end_microsec = result.alternatives[0].words[i + 1].end_time.nanos * 0.001

					if word_end_sec < end_sec:
						transcript = transcript + " " + word
					else:
						previous_word_end_sec = result.alternatives[0].words[i].end_time.seconds
						previous_word_end_microsec = result.alternatives[0].words[i].end_time.nanos * 0.001

						# append bin transcript
						caption = Caption(datetime.timedelta(0, start_sec, start_microsec),
						                                   datetime.timedelta(0, previous_word_end_sec, previous_word_end_microsec),
						                                   transcript)
						vtt.captions.append(caption)

						# reset bin parameters
						start_sec = word_start_sec
						start_microsec = word_start_microsec
						end_sec = start_sec + bin
						transcript = result.alternatives[0].words[i + 1].word

						index += 1
				except IndexError:
					pass
			# append transcript of last transcript in bin
			vtt.captions.append(Caption(datetime.timedelta(0, start_sec, start_microsec),
			                                   datetime.timedelta(0, last_word_end_sec, last_word_end_microsec), transcript))
			vtt.save('my_captions.vtt')
		except IndexError:
			pass
		return vtt


def s3_upload_file_to_bucket(file, bucket, Key, metadata):
	client = boto3.client('s3')
	response = client.upload_file(file, bucket, Key, {'Metadata':metadata})
	if response:
		return response



