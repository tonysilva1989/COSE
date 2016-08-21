###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Tests for models related to assignments in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# =============
# Python stdlib
# =============

import datetime
import hashlib
import os

# ==============
# Django imports
# ==============

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ===============
# project imports
# ===============

from crowd.models.assignment import Assignment
from crowd.models.assignment import AssignmentSession
from crowd.models.exceptions import InvalidStateError
from crowd.models.segprob import SegmentationProblem
from helpers.django_related.tests import TimezoneNowMockedTestCase


def _close_session_w_result(session):
    result_path = os.path.join(settings.MEDIA_ROOT,
        'assignment_session_raw_result.png')
    with open(result_path, 'rb') as f:
        session.close(f)


class AssignmentManagerTest(TimezoneNowMockedTestCase):
    fixtures = ('initial.json',)

    @staticmethod
    def _create_sessions_for_assignment(assignment, n):
        sessions = []
        for u in User.objects.all()[0:n]:
            sessions.append(AssignmentSession.objects.create(
                assignment=assignment, worker=u))
        return sessions

    def test_get_public_wo_published_seg_probs(self):
        SegmentationProblem.objects.update(published=False)
        self.assertEqual(Assignment.objects.get_public().count(), 0)

    def test_get_public_wo_workable_assignments(self):
        Assignment.objects.update(workable=False)
        self.assertEqual(Assignment.objects.get_public().count(), 0)

        Assignment.objects.update(workable=None)
        self.assertEqual(Assignment.objects.get_public().count(), 0)

    def test_get_public_w_every_seg_prob_published(self):
        SegmentationProblem.objects.update(published=True)
        self.assertEqual(Assignment.objects.get_public().count(),
            Assignment.objects.filter(workable=True).count())

    def test_get_public_when_only_one_is_public(self):
        SegmentationProblem.objects.update(published=False)
        Assignment.objects.update(workable=False)

        a = Assignment.objects.order_by('?')[0]
        a.workable = True
        a.seg_prob.published = True
        a.seg_prob.save()
        a.save()

        self.assertQuerysetEqual(Assignment.objects.get_public(), [a.pk],
            lambda a: a.pk)

    def test_get_available_is_subset_of_get_public(self):
        self.assertTrue(set(Assignment.objects.get_available()).issubset(
            set(Assignment.objects.get_public())))

    def test_get_available_w_expired_sessions(self):
        assignment = Assignment.objects.get_public().order_by('?')[0]

        seg_prob_details = assignment.seg_prob.details
        min_res_per_assignment = seg_prob_details.min_results_per_assignment
        assignments_timeout = seg_prob_details.assignments_timeout

        AssignmentManagerTest._create_sessions_for_assignment(assignment,
            min_res_per_assignment)

        # there are now 'min_res_per_assignment' active sessions, so
        # 'assignment' should not be available anymore
        self.assertNotIn(assignment, Assignment.objects.get_available())

        # force expiration
        self.now += datetime.timedelta(seconds=assignments_timeout + 1)

        # and now, 'assignment' must be available again
        self.assertIn(assignment, Assignment.objects.get_available())

    def test_get_available_w_skipped_session(self):
        assignment = Assignment.objects.get_public().order_by('?')[0]

        seg_prob_details = assignment.seg_prob.details
        min_res_per_assignment = seg_prob_details.min_results_per_assignment

        additional_sessions = 2

        sessions = AssignmentManagerTest._create_sessions_for_assignment(
            assignment, min_res_per_assignment + additional_sessions)

        self.assertNotIn(assignment, Assignment.objects.get_available())

        # skipping sessions reduces the number of "active" ones. While this
        # doesn't go below 'min_res_per_assignment', 'assignment' is not made
        # available for new sessions. The meaning of it is that there's enough
        # working force allocated to the assignment, so any new worker should
        # be allocated to another assignment.
        for s in sessions[0:additional_sessions]:
            s.close()
            s.save()
            self.assertNotIn(assignment, Assignment.objects.get_available())

        # ...but, as soon as the number of "active" sessions goes below
        # 'min_res_per_assignment', 'assignment' is made available again.
        sessions[additional_sessions].close()
        sessions[additional_sessions].save()
        self.assertIn(assignment, Assignment.objects.get_available())

    def test_get_available_w_finished_session(self):
        assignment = Assignment.objects.get_public().order_by('?')[0]

        seg_prob_details = assignment.seg_prob.details
        min_res_per_assignment = seg_prob_details.min_results_per_assignment

        sessions = AssignmentManagerTest._create_sessions_for_assignment(
            assignment, min_res_per_assignment)

        self.assertNotIn(assignment, Assignment.objects.get_available())

        # closing a session with results does not make 'assignment' available.
        # On the contrary, it implies less sessions are required to complete
        # the assignment.
        _close_session_w_result(sessions[0])
        sessions[0].save()

        self.assertNotIn(assignment, Assignment.objects.get_available())
        
    def test_get_available_skip_and_close_and_expiration(self):
        assignment = Assignment.objects.get_public().order_by('?')[0]
        
        seg_prob_details = assignment.seg_prob.details
        min_res_per_assignment = seg_prob_details.min_results_per_assignment

        sessions = AssignmentManagerTest._create_sessions_for_assignment(
            assignment, min_res_per_assignment)
        
        self.assertNotIn(assignment, Assignment.objects.get_available())
        
        session_index = random.choice(range(0, min_res_per_assignment - 1))
        
        # skipping a session        
        sessions[session_index].close()
        sessions[session_index].save()
        self.assertIn(assignment, Assignment.objects.get_available())
        
        # creating a new session
        u = User.objects.all()[min_res_per_assignment]
        sessions[session_index] = AssignmentSession.objects.create(assignment=assignment, worker=u)
        self.assertNotIn(assignment, Assignment.objects.get_available())
        
        session_index = random.choice(range(0, min_res_per_assignment - 1))
        
        # finishing a session with result.
        # The assignment remains unavailable because it needs fewer results
        # to be concluded.
        _close_session_w_result(sessions[session_index])
        sessions[session_index].save()
        self.assertNotIn(assignment, Assignment.objects.get_available())
        
        # force expiration.
        # All sessions will expire and assignment will be available.
        assign_timeout = seg_prob_details.assignments_timeout
        self.now += datetime.timedelta(seconds=assign_timeout+1)        
        self.assertIn(assignment, Assignment.objects.get_available())
        
class AssignmentSessionManagerTest(TimezoneNowMockedTestCase):
    fixtures = ('initial.json',)

    def setUp(self):
        super(AssignmentSessionManagerTest, self).setUp()

        self.workers = []
        self.workers.append(User.objects.get(username='worker1'))
        self.workers.append(User.objects.get(username='worker2'))
        self.workers.append(User.objects.get(username='worker3'))
        self.workers.append(User.objects.get(username='worker4'))
        self.workers.append(User.objects.get(username='worker5'))
        self.workers.append(User.objects.get(username='worker6'))
        self.workers.append(User.objects.get(username='worker7'))
        self.workers.append(User.objects.get(username='worker8'))
        self.workers.append(User.objects.get(username='worker9'))
        self.workers.append(User.objects.get(username='worker10'))

    def test_get_by_worker_allocation(self):
        w1 = self.workers[0]
        s1_w1 = AssignmentSession.objects.get_by_worker(w1)

        # workers are allocated to the same assignment until a maximum. This
        # maximum is the minimum of sessions that must be created in order to
        # complete the assignment.
        s1_w1_a = s1_w1.assignment
        for i in xrange(1, s1_w1_a.n_sessions_until_conclusion):
            s = AssignmentSession.objects.get_by_worker(self.workers[i])
            self.assertNotEqual(s.pk, s1_w1.pk)
            self.assertEqual(s.assignment.pk, s1_w1.assignment.pk)

        # after this maximum, new workers are allocated to new assignments.
        wn = self.workers[s1_w1_a.n_sessions_until_conclusion]
        s1_wn = AssignmentSession.objects.get_by_worker(wn)
        self.assertNotEqual(s1_w1.assignment.pk, s1_wn.assignment.pk)

        # in case any session is finished without success, the assignment is
        # freed to be allocated to workers that didn't try it yet

        # worker 1 skipped its session
        s1_w1.close()
        s1_w1.save()

        # worker n skipped its session
        s1_wn.close()
        s1_wn.save()

        s2_w1 = AssignmentSession.objects.get_by_worker(w1)
        # because worker n didn't try the assignment allocated previously to
        # worker 1, it can try now again since it's freed
        s2_wn = AssignmentSession.objects.get_by_worker(wn)

        self.assertEqual(s2_w1.assignment.pk, s1_wn.assignment.pk)
        self.assertEqual(s2_wn.assignment.pk, s1_w1.assignment.pk)

    def test_get_by_worker_expiration(self):
        s1 = AssignmentSession.objects.get_by_worker(self.workers[0])
        s2 = AssignmentSession.objects.get_by_worker(self.workers[0])
        self.assertEqual(s1.pk, s2.pk)

        self.now += s1.timeout + datetime.timedelta(seconds=1)
        self.assertTrue(s1.expired)

        # even if it's expired, the same session will be returned. This occurs
        # because, despite expired, the session remains opened.
        s3 = AssignmentSession.objects.get_by_worker(self.workers[0])
        self.assertEqual(s1.pk, s3.pk)

        s3.close()
        s3.save()

        # now that the session was closed, a new session can be retrieved
        s4 = AssignmentSession.objects.get_by_worker(self.workers[0])
        self.assertNotEqual(s3.pk, s4.pk)

    def test_get_by_worker_ordering(self):
        """'get_by_worker' must return only sessions for available assignments
        in the orders in which the associated tasks (primary) and assignments
        (secondary) were created."""

        assignments = Assignment.objects.get_available().order_by(
            'seg_prob__task__created_on', 'id')
        for a in assignments:
            s = AssignmentSession.objects.get_by_worker(self.workers[0])
            self.assertEqual(s.assignment.pk, a.pk)

            # skip this session
            s.close()
            s.save()

        self.assertIsNone(AssignmentSession.objects.get_by_worker(
            self.workers[0]))

    def test_get_by_worker_wo_available_assignments(self):
        Assignment.objects.update(workable=False)
        self.assertIsNone(AssignmentSession.objects.get_by_worker(
            self.workers[0]))


class AssignmentSessionModelTest(TimezoneNowMockedTestCase):
    fixtures = ('initial.json',)

    def setUp(self):
        super(AssignmentSessionModelTest, self).setUp()

        w = User.objects.get(username='worker1')
        a = Assignment.objects.order_by('?')[0]
        self.session = AssignmentSession.objects.create(assignment=a, worker=w)

    def test_session_initial_state(self):
        self.assertTrue(self.session.active)
        self.assertFalse(self.session.expired)
        self.assertFalse(self.session.skipped)
        self.assertFalse(self.session.closed)
        self.assertFalse(self.session.has_result)

        self.assertEqual(self.session.timeout.total_seconds(),
            self.session.assignment.seg_prob.details.assignments_timeout)
        self.assertEqual(self.session.remaining_time.total_seconds(),
            self.session.timeout.total_seconds())
        self.assertEqual(self.session.elapsed_time.total_seconds(), 0)

    def test_session_closing_twice(self):
        self.session.close()
        self.assertRaises(InvalidStateError, self.session.close)

    def test_session_closing_w_result(self):
        # results should be set only by closing

        _close_session_w_result(self.session)
        self.assertTrue(self.session.has_result)
        self.assertTrue(self.session.closed)

        # a session closed with results before expiration is not skipped
        self.assertFalse(self.session.skipped)

        result_sha1 = hashlib.sha1()
        with open(self.session.result.path, 'rb') as f:
            result_sha1.update(f.read())

        expected_result_file_path = os.path.join(settings.MEDIA_ROOT,
            'assignment_session_processed_result.png')
        expected_result_sha1 = hashlib.sha1()
        with open(expected_result_file_path, 'rb') as f:
            expected_result_sha1.update(f.read())

        self.assertEqual(result_sha1.digest(), expected_result_sha1.digest())

    def test_session_closing_wo_result(self):
        self.session.close()
        self.assertTrue(self.session.closed)
        self.assertFalse(self.session.has_result)

        # a session closed without results before expiration is considered
        # skipped
        self.assertTrue(self.session.skipped)

    def test_session_closing_wo_result_after_expiration(self):
        self._test_session_closing_after_expiration(with_result=False)

    def test_session_closing_w_result_after_expiration(self):
        self._test_session_closing_after_expiration(with_result=True)

    def _test_session_closing_after_expiration(self, with_result):
        self.now += self.session.timeout + datetime.timedelta(seconds=1)

        if with_result:
            _close_session_w_result(self.session)
        else:
            self.session.close()

        self.assertTrue(self.session.expired)
        self.assertTrue(self.session.closed)
        self.assertFalse(self.session.active)
        self.assertFalse(self.session.skipped)
        self.assertFalse(self.session.has_result)

    def test_session_state_after_expiration(self):
        self.now += self.session.timeout + datetime.timedelta(seconds=1)

        self.assertTrue(self.session.expired)
        self.assertFalse(self.session.skipped)
        self.assertFalse(self.session.closed)
        self.assertFalse(self.session.active)
        self.assertFalse(self.session.has_result)
        self.assertGreater(self.session.elapsed_time.total_seconds(),
            self.session.timeout.total_seconds())

    def test_session_worker_busy_already(self):
        another_assignment = Assignment.objects.exclude(
            pk=self.session.assignment.pk).order_by('?')[0]
        self.assertRaises(ValidationError, AssignmentSession.objects.create,
            assignment=another_assignment, worker=self.session.worker)

        # closing the session unlocks the worker
        self.session.close()
        self.session.save()

        AssignmentSession.objects.create(assignment=another_assignment,
            worker=self.session.worker)

    def test_session_has_result_wo_closing(self):
        self.session.result = 'some result'
        self.assertRaises(ValidationError, self.session.save)

        _close_session_w_result(self.session)
        self.session.save()

    def test_session_implicit_closing_after_expiration(self):
        self.now += self.session.timeout + datetime.timedelta(seconds=1)

        self.assertFalse(self.session.closed)
        self.session.save()
        self.assertTrue(self.session.closed)
