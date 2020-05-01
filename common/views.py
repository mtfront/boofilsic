from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from books.models import Book
from common.models import MarkStatusEnum
from users.models import Report, User
from django.core.paginator import Paginator 
from django.db.models import Q
from django.http import HttpResponseBadRequest


# how many books have in each set at the home page
BOOKS_PER_SET = 5

# how many items are showed in one search result page
ITEMS_PER_PAGE = 20


@login_required
def home(request):
    if request.method == 'GET':
        books = Book.objects.filter(book_marks__owner=request.user)

        do_books = books.filter(book_marks__status=MarkStatusEnum.DO)
        do_books_more = True if do_books.count() > BOOKS_PER_SET else False
        wish_books = books.filter(book_marks__status=MarkStatusEnum.WISH)
        wish_books_more = True if wish_books.count() > BOOKS_PER_SET else False
        collect_books = books.filter(book_marks__status=MarkStatusEnum.COLLECT)
        collect_books_more = True if collect_books.count() > BOOKS_PER_SET else False

        reports = Report.objects.order_by('-submitted_time').filter(is_read=False)
        # reports = Report.objects.latest('submitted_time').filter(is_read=False)

        return render(
            request,
            'common/home.html',
            {
                'do_books': do_books[:BOOKS_PER_SET],
                'wish_books': wish_books[:BOOKS_PER_SET],
                'collect_books': collect_books[:BOOKS_PER_SET],
                'do_books_more': do_books_more,
                'wish_books_more': wish_books_more,
                'collect_books_more': collect_books_more,
                'reports': reports,
            }
        )
    else:
        return HttpResponseBadRequest()


def search(request):
    if request.method == 'GET':
        # in the future when more modules are added...
        # category = request.GET.get("category")
        q = Q()
        keywords = request.GET.get("keywords", default='').split()
        query_args = []
        for keyword in keywords:
            q = q | Q(title__icontains=keyword)
            q = q | Q(subtitle__istartswith=keyword)
            q = q | Q(orig_title__icontains=keyword)
        query_args.append(q)
        queryset = Book.objects.filter(*query_args)

        paginator = Paginator(queryset, ITEMS_PER_PAGE)
        page_number = request.GET.get('page', default=1)
        items = paginator.get_page(page_number)

        return render(
            request,
            "common/search_result.html",
            {
                "items": items,
            }
        )

    else:
        return HttpResponseBadRequest()