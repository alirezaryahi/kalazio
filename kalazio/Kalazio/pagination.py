from django.conf import settings
from rest_framework import pagination
from rest_framework.response import Response


class StandardResultsSetPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


class FavoritrResultsSetPagination(pagination.PageNumberPagination):
    page_size = 8
    page_query_param = "page"
    page_size_query_param = "per_page"
    max_page_size = 1000
