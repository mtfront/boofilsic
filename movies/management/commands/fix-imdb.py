from django.core.management.base import BaseCommand, CommandError
from common.scraper import *


class DoubanPatcherMixin:
    @classmethod
    def download_page(cls, url, headers):
        url = cls.get_effective_url(url)
        r = None
        error = 'DoubanScrapper: error occured when downloading ' + url
        content = None

        def get(url, timeout):
            nonlocal r
            # print('Douban GET ' + url)
            try:
                r = requests.get(url, timeout=timeout)
            except Exception as e:
                r = requests.Response()
                r.status_code = f"Exception when GET {url} {e}" + url
            # print('Douban CODE ' + str(r.status_code))
            return r

        def check_content():
            nonlocal r, error, content
            content = None
            if r.status_code == 200:
                content = r.content.decode('utf-8')
                if content.find('关于豆瓣') == -1:
                    content = None
                    error = error + 'Content not authentic'  # response is garbage
                elif re.search('不存在[^<]+</title>', content, re.MULTILINE):
                    content = None
                    error = error + 'Not found or hidden by Douban'
            else:
                error = error + str(r.status_code)

        def fix_wayback_links():
            nonlocal content
            # fix links
            content = re.sub(r'href="http[^"]+http', r'href="http', content)
            # https://img9.doubanio.com/view/subject/{l|m|s}/public/s1234.jpg
            content = re.sub(r'src="[^"]+/(s\d+\.\w+)"',
                             r'src="https://img9.doubanio.com/view/subject/m/public/\1"', content)
            # https://img9.doubanio.com/view/photo/s_ratio_poster/public/p2681329386.jpg
            # https://img9.doubanio.com/view/photo/{l|m|s}/public/p1234.webp
            content = re.sub(r'src="[^"]+/(p\d+\.\w+)"',
                             r'src="https://img9.doubanio.com/view/photo/m/public/\1"', content)

        # Wayback Machine: get latest available
        def wayback():
            nonlocal r, error, content
            error = error + '\nWayback: '
            get('http://archive.org/wayback/available?url=' + url, 10)
            if r.status_code == 200:
                w = r.json()
                if w['archived_snapshots'] and w['archived_snapshots']['closest']:
                    get(w['archived_snapshots']['closest']['url'], 10)
                    check_content()
                    if content is not None:
                        fix_wayback_links()
                else:
                    error = error + 'No snapshot available'
            else:
                error = error + str(r.status_code)

        # Wayback Machine: guess via CDX API
        def wayback_cdx():
            nonlocal r, error, content
            error = error + '\nWayback: '
            get('http://web.archive.org/cdx/search/cdx?url=' + url, 10)
            if r.status_code == 200:
                dates = re.findall(r'[^\s]+\s+(\d+)\s+[^\s]+\s+[^\s]+\s+\d+\s+[^\s]+\s+\d{5,}',
                                   r.content.decode('utf-8'))
                # assume snapshots whose size >9999 contain real content, use the latest one of them
                if len(dates) > 0:
                    get('http://web.archive.org/web/' + dates[-1] + '/' + url, 10)
                    check_content()
                    if content is not None:
                        fix_wayback_links()
                else:
                    error = error + 'No snapshot available'
            else:
                error = error + str(r.status_code)

        def latest():
            nonlocal r, error, content
            if settings.SCRAPERAPI_KEY is None:
                error = error + '\nDirect: '
                get(url, 30)
            else:
                error = error + '\nScraperAPI: '
                get(f'http://api.scraperapi.com?api_key={settings.SCRAPERAPI_KEY}&url={url}', 30)
            check_content()

        wayback_cdx()
        if content is None:
            latest()

        if content is None:
            logger.error(error)
            content = '<html />'
        return html.fromstring(content)

    @classmethod
    def download_image(cls, url, item_url=None):
        raw_img = None
        ext = None

        dl_url = url
        if settings.SCRAPERAPI_KEY is not None:
            dl_url = f'http://api.scraperapi.com?api_key={settings.SCRAPERAPI_KEY}&url={url}'

        try:
            img_response = requests.get(dl_url, timeout=30)
            if img_response.status_code == 200:
                raw_img = img_response.content
                content_type = img_response.headers.get('Content-Type')
                ext = guess_extension(content_type.partition(';')[0].strip())
                img = Image.open(BytesIO(raw_img))
                img.load()  # corrupted image will trigger exception
            else:
                logger.error(f"Douban: download image failed {img_response.status_code} {dl_url} {item_url}")
                # raise RuntimeError(f"Douban: download image failed {img_response.status_code} {dl_url}")
        except Exception as e:
            raw_img = None
            ext = None
            logger.error(f"Douban: download image failed {e} {dl_url} {item_url}")

        return raw_img, ext


class DoubanMoviePatcher(DoubanPatcherMixin, AbstractScraper):
    site_name = SourceSiteEnum.DOUBAN.value
    host = 'movie.douban.com'
    data_class = Movie
    form_class = MovieForm

    regex = re.compile(r"https://movie\.douban\.com/subject/\d+/{0,1}")

    def scrape(self, url):
        headers = DEFAULT_REQUEST_HEADERS.copy()
        headers['Host'] = self.host
        content = self.download_page(url, headers)
        imdb_elem = content.xpath(
            "//div[@id='info']//span[text()='IMDb链接:']/following-sibling::a[1]/text()")
        if not imdb_elem:
            imdb_elem = content.xpath(
                "//div[@id='info']//span[text()='IMDb:']/following-sibling::text()[1]")
        imdb_code = imdb_elem[0].strip() if imdb_elem else None
        return {
            'imdb_code': imdb_code,
        }


class Command(BaseCommand):
    help = 'fix imdb code'

    def handle(self, *args, **options):
        for m in Movie.objects.filter(imdb_code='', source_site='douban'):
            print(f'Refreshing {m.source_url}')
            try:
                m.imdb_code = DoubanMoviePatcher.scrape(m.source_url)['imdb_code']
                if m.imdb_code is not None:
                    m.save()
                else:
                    print(f'Skip {m.source_url}')
            except Exception as e:
                print(e)
