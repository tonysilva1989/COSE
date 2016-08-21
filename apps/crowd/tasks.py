from __future__ import absolute_import
from datetime import timedelta, datetime
from celery.app import shared_task

from django.core.cache import cache

from celery.task import PeriodicTask, task

from apps.profiles.models import WorkerProfile


class RankingTask(PeriodicTask):
    """
    Updates the ranking

    Perform a query of the workers profiles ordered
    by score and set the key 'ranking' in the cache.
    """

    run_every = timedelta(seconds=5)

    def run(self):
        # ranking is a dictionary where the keys are the users ids
        # and the content are the users positions.
        ranking_keys = []
        ranking_dict = {}
        position = 1
        previous_el = None
        for el in WorkerProfile.objects.all_ordered_by_score():
            if previous_el and el.score != previous_el.score:
                position += 1

            ranking_dict[el.userprofile_ptr_id] = (el.username,
               "{:,d}".format(el.score), position, "{:,d}".format(el.mileage_sum), str(el.accumulated_accuracy))
            ranking_keys.append(el.userprofile_ptr_id)

            previous_el = el

        cache.set('ranking_dict', ranking_dict)
        cache.set('ranking_keys', ranking_keys)

# class ScoreDecreaseByTimeTask(PeriodicTask):
#     time_unity = 1
#     score_penalty = 300
#     run_every = timedelta(secods=time_unity)
#
#     def run(self):
#         WorkerProfile.objects.penalize_by_time(datetime.today(),
#                                                2*(self.time_unity),
#                                                self.score_penalty)











