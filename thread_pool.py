from .logger import get_logger
from concurrent.futures import ThreadPoolExecutor

THREAD_POOL = None


def get_thread_pool(max_workers):
    global THREAD_POOL

    if THREAD_POOL is None:
        logger = get_logger()
        logger.info('   @@ before create thread_pool')
        THREAD_POOL = ThreadPoolExecutor(max_workers=max_workers)
        logger.info('Create thread_pool(%s)' % id(THREAD_POOL))

    return THREAD_POOL
