from apps.profiles.models import WorkerProfile
from helpers.django_related.tests import TimezoneNowMockedTestCase

import datetime

class WorkerProfileManagerTest(TimezoneNowMockedTestCase):
    fixtures = ('ranking_test.json',)

    def test_all_ordered_by_score(self):
        list1 = [wp.user.id for wp in WorkerProfile.objects.all().order_by('-score')]
        list2 = [wp.userprofile_ptr_id for wp in WorkerProfile.objects.all_ordered_by_score()]

        self.assertEqual(list1, list2, True)

    def test_penalize_by_time(self):
        now = datetime.datetime.now()
        allowed_inactive_time = datetime.timedelta(days=2)
        penalty = 100

        WorkerProfile.objects.penalize_by_time(now, allowed_inactive_time, 100)
