###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Views related to admin tasks in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


import csv

from django.http import HttpResponse

from crowd.models.assignment import AssignmentSession


def report(request):
    import time
    t0 = time.clock()

    response = HttpResponse(mimetype='text/csv')
    writer = csv.DictWriter(response,
        ['seg_prob_id', 'assignment_id', 'session_id', 'seg_prob_img',
         'algorithm', 'tile_dimension', 'tile_overlap', 'tile_border',
         'tile', 'session_worker', 'session_duration', 'session_result'],
        delimiter=' ')

    writer.writeheader()
    for s in AssignmentSession.objects.get_w_result().select_related():
        a = s.assignment
        sb = a.seg_prob
        sb_details = sb.details

        writer.writerow({
            'seg_prob_id': sb.id,
            'assignment_id': a.id,
            'session_id': s.id,
            'seg_prob_img': sb.image,
            'algorithm': sb_details.algorithm,
            'tile_dimension': sb_details.tiles_dimension,
            'tile_overlap': sb_details.tiles_overlap,
            'tile_border': sb_details.tiles_border,
            'tile': a.tile,
            'session_worker': s.worker,
            'session_duration': (s.close_time - s.start_time).total_seconds(),
            'session_result': s.result
        })

    print time.clock() - t0

    return response

