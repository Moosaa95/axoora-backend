from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        count = self.page.paginator.count if self.page and self.page.paginator else 0
        return Response({
            'count': count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })


def paginate_queryset(queryset, request, view=None, page_size=20):
    paginator = StandardPagination()
    if page_size:
        paginator.page_size = page_size
    page = paginator.paginate_queryset(queryset, request, view=view)
    return paginator, page
