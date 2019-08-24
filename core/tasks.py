from django.conf import settings

from celery import shared_task, current_task, task
from celery.utils.log import get_task_logger

from pytube import YouTube

logger = get_task_logger(__name__)

@shared_task(name="core_debug_task")
def core_debug_task():
    logger.info("Core Debug Task Complete")

@shared_task(name="download_video_task")
def download_video_task(video, itag):
    def calculate_process_percent(stream, chunk, file_handle, bytes_remaining):
        process_percent = 100 - int(100 * bytes_remaining / stream.filesize)
        return current_task.update_state(state='DOWNLOADING',
        meta={'process_percent': process_percent})

    yt = YouTube(f'http://youtube.com/watch?v={video}')
    yt.register_on_progress_callback(calculate_process_percent)
    
    yt.streams.get_by_itag(itag).download(settings.VIDEO_DIR)

    logger.info("Video Download Completed")