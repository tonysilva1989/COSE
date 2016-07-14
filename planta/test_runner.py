###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Test runner for planta project.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# =====================
# Python stdlib imports
# =====================

import os
import shutil

# ==============
# Django imports
# ==============

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

# ===============
# project imports
# ===============

from helpers import filesystem as h_fs


class TestRunner(DjangoTestSuiteRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        media_path = h_fs.get_absolute_path('../media/test', __file__)
        to_be_loaded_path = os.path.join(media_path, 'to_be_loaded')
        session_path = os.path.join(media_path, 'session')

        h_fs.rm(session_path, ignore_errors=True)
        shutil.copytree(to_be_loaded_path, session_path)

        settings.MEDIA_ROOT = session_path

        super(TestRunner, self).run_tests(test_labels, extra_tests, **kwargs)
