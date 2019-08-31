from django.conf import settings

from celery import shared_task, current_task, task, states
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger

from pytube import YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable, LiveStreamError

logger = get_task_logger(__name__)

@shared_task(name="core_debug_task")
def core_debug_task():
    logger.info("Core Debug Task Complete")

@shared_task(name="download_video_task")
def download_video_task(video, *args, **kwargs):
    def calculate_process_percent(stream, chunk, file_handle, bytes_remaining):
        process_percent = 100 - int(100 * bytes_remaining / stream.filesize)
        return current_task.update_state(state='DOWNLOADING',
        meta={'process_percent': process_percent})
    
    itag = kwargs.get('itag', None)
    try:
        yt = YouTube(f'http://youtube.com/watch?v={video}')
    except (RegexMatchError, VideoUnavailable, LiveStreamError) as e:
        logger.error(e)
        current_task.update_state(
            state=states.FAILURE,
        )
        raise Ignore()
    else:
        yt.register_on_progress_callback(calculate_process_percent)
    
    if itag is not None:
        if yt.streams.get_by_itag(itag) is None:
            logger.error(f"Invalid Itag: ID:{video}, itag:{itag}")
            current_task.update_state(
                state=states.FAILURE,
            )
            raise Ignore()
        else:
            yt.streams.get_by_itag(itag).download(settings.VIDEO_DIR)
            logger.info(f"Video Download Completed: ID:{video}, itag:{itag}")
    else:
        yt.streams.first().download(settings.VIDEO_DIR)
        logger.info(f"Video Download Completed: ID:{video}")
        
    
    