from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class DefaultPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        next_page = self.page.number+1 if self.get_next_link() else None
        prev_page = self.page.number-1 if self.get_previous_link() else None
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('current', self.page.number),
            ('next', next_page),
            ('previous', prev_page),
            ('results', data)
        ]))


class StandardResultsSetPagination(DefaultPageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50