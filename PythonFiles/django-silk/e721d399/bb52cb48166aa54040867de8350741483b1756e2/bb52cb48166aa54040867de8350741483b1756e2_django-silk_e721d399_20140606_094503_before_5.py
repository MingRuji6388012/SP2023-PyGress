import json

from django.shortcuts import render_to_response
from django.views.generic import View

from silk.code_generation.curl import curl_cmd
from silk.models import Request
from silk.code_generation.django_test_client import gen


class RequestView(View):

    def get(self, request, request_id):
        silk_request = Request.objects.get(pk=request_id)
        query_params = None
        if silk_request.query_params:
            query_params = json.loads(silk_request.query_params)
        body = silk_request.raw_body
        try:
            body = json.loads(body)  # Incase encoded as JSON
        except (ValueError, TypeError):
            pass
        context = {
            'silk_request': silk_request,
            'curl': curl_cmd(url=request.build_absolute_uri(silk_request.path),
                             method=silk_request.method,
                             query_params=query_params,
                             body=body,
                             content_type=silk_request.content_type),
            'query_params': json.dumps(query_params, sort_keys=True, indent=4) if query_params else None,
            'client': gen(path=silk_request.path,
                          method=silk_request.method,
                          query_params=query_params,
                          data=body,
                          content_type=silk_request.content_type),
            'request': request
        }
        return render_to_response('silk/templates/silk/request.html', context)




