from .tables import Table


class URLs(Table):
    """
    Stores information about URLs

    The URLs table stores all crawling metadata to crawled, scheduled to be crawled  and found urls.
    This table is mainly populated by url generators which create urls to crawl by for example basing them on parliament session dates. Crawlers are then responsible for storing the crawling metadata for each url and can additionally append found urls.

    Attributes:

        rule : VARCHAR(100)
            name of the rule used to generate the URL
        url : TEXT
            the generated URL
        found : boolean
             True if a crawler found this URL in a document
        enqueued : boolean
            True if the URLGenerator has enqueued the URL to be crawled, is set to False on startup
        crawled : boolean
            has this URL been crawled
        crawled_at : datetime
            when has this URL been crawled
        file_path : TEXT
            where is the downloaded document stored
        recrawl : boolean
            should this url be recrawled
        recrawl_after : datetime
            the document will be recrawled sometime after this timestamp

    """

    schema = "public"
    table_name = "urls"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id integer NOT NULL,
                            rule VARCHAR(100) NOT NULL,
                            url TEXT NOT NULL,
                            found boolean NOT NULL,
                            created time with time zone NOT NULL,
                            enqueued boolean NOT NULL,
                            enqueued_at time with time zone,
                            enqueued_times integer NOT NULL,
                            crawled boolean NOT NULL,
                            crawled_at time with time zone,
                            failed boolean NOT NULL,
                            file_path TEXT,
                            recrawl boolean NOT NULL,
                            recrawl_after time with time zone,
                            PRIMARY KEY(id)
                          );"""
