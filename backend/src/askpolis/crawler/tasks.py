from celery import shared_task


@shared_task(name="crawl_abgeordnetenwatch")
def crawl_abgeordnetenwatch() -> None:
    print("Crawling Abgeordnetenwatch...")
