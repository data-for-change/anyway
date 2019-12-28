import itertools
import os

if os.environ.get("ANYWAY_DISABLE_CELERY"):
    from functools import partial


    class MockTaskQueue(object):
        @staticmethod
        def task(f):
            f.delay = f
            return f


    task_queue = MockTaskQueue

    task_signature = partial


    def map_task(task, candidates):
        return list(itertools.chain.from_iterable(task(candidate) for candidate in candidates))

else:
    from celery import Celery, group

    task_queue = Celery('tasks',
                        backend=os.environ.get('CELERY_BACKEND_URL', 'rpc://'),
                        broker=os.environ.get('CELERY_BROKER_URL', 'amqp://guest@localhost//'))


    def task_signature(task, *args, **kwargs):
        return task.s(*args, **kwargs)


    def map_task(task, candidates):
        job = group([task.clone([candidate]) for candidate in candidates])
        result = job.apply_async()
        result.join()
        return list(itertools.chain.from_iterable(result.get()))
