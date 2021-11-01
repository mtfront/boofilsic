from django.core.management.base import BaseCommand, CommandError
from common.scraper import DoubanBookScraper
from users.models import User
from books.models import Book
import redis


class Command(BaseCommand):
    help = 'import from redis'

    def add_arguments(self, parser):
        parser.add_argument('threadId', type=int, help='% 8')

    def handle(self, *args, **options):
        r = redis.Redis(host='localhost')
        ks = r.keys('*')
        t = int(options['threadId'])
        request_user = User.objects.get(id=792)
        for k in ks:
            if int(k.decode("ascii")) % 8 == t:
                url = f'https://book.douban.com/subject/{k.decode("ascii")}/'
                try:
                    Book.objects.get(source_url=url)
                    self.stdout.write("Skip " + url)
                except Exception:
                    self.stdout.write("Download " + url)
                    try:
                        DoubanBookScraper.scrape(url)
                        DoubanBookScraper.save(request_user)
                        self.stdout.write("Saved " + url)
                    except Exception:
                        try:
                            self.stdout.write(self.style.WARNING('Retry'))
                            DoubanBookScraper.scrape(url)
                            DoubanBookScraper.save(request_user)
                            self.stdout.write("Saved " + url)
                        except Exception:
                            self.stdout.write(self.style.ERROR('Failed'))
        self.stdout.write(self.style.SUCCESS('Success'))
