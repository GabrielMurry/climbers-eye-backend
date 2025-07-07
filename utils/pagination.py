from rest_framework.pagination import PageNumberPagination, CursorPagination

class StandardPagination(PageNumberPagination):
    page_size = 10

class CreatedCursorPagination(CursorPagination):
    page_size = 5