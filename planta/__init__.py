###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## planta project package.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from celeryapp import app as celery_app