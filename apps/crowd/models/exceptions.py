###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Exceptions related to the models of crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


from django.core.exceptions import ValidationError


class InvalidStateError(ValidationError):
    pass
