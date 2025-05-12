import marimo

__generated_with = "0.13.6"
app = marimo.App(width="medium", app_title="marimo-rss-reader")


@app.cell
def _():
    import marimo as mo
    import urllib.request
    import xml.etree.ElementTree as ET
    from collections import defaultdict
    from datetime import datetime

    from pydantic import BaseModel, Field

    return BaseModel, ET, Field, datetime, defaultdict, mo, urllib


@app.cell
def _(BaseModel, Field):
    class FeedItem(BaseModel):
        title: str = Field(..., description="Title of the feed")
        link: str = Field(..., description="Link to the feed")
        description: str = Field(..., description="Description of the feed")
        pubDate: str = Field(..., description="Publication date of the feed")
        guid: str = Field(..., description="Unique identifier for the feed item")

    class RSSFeed(BaseModel):
        title: str = Field(..., description="Title of the feed")
        link: str = Field(..., description="Link to the feed")
        description: str = Field(..., description="Description of the feed")
        items: list[FeedItem] = Field(..., description="List of feed items")

    return FeedItem, RSSFeed


@app.cell
def _(urllib):
    def fetch_xml(url) -> bytes:
        """Fetches XML data from a URL"""

        with urllib.request.urlopen(url) as response:
            xml_content = response.read()

        return xml_content

    return (fetch_xml,)


@app.cell
def _(ET, FeedItem, RSSFeed):
    def parse_rss_feed(xml_string) -> RSSFeed:
        """
        Parses an RSS feed from an XML string and returns a `RSSFeed` object.

        Args:
            xml_string (str): The XML content of the RSS feed.

        Returns:
            RSSFeed: An object containing the parsed feed information.
        """
        root = ET.fromstring(xml_string)
        channel = root.find("channel")
        if channel is None:
            raise ValueError("No channel found in the XML string.")

        title = (
            channel.find("title").text if channel.find("title") is not None else None
        )
        link = channel.find("link").text if channel.find("link") is not None else None
        description = (
            channel.find("description").text
            if channel.find("description") is not None
            else None
        )

        items = []
        for item_element in channel.findall("item"):
            item = FeedItem(
                title=item_element.find("title").text
                if item_element.find("title") is not None
                else None,
                link=item_element.find("link").text
                if item_element.find("link") is not None
                else None,
                description=item_element.find("description").text
                if item_element.find("description") is not None
                else None,
                pubDate=item_element.find("pubDate").text
                if item_element.find("pubDate") is not None
                else None,
                guid=item_element.find("guid").text
                if item_element.find("guid") is not None
                else None,
            )
            items.append(item)

        return RSSFeed(title=title, link=link, description=description, items=items)

    return (parse_rss_feed,)


@app.cell
def _(datetime):
    def parse_date(date_str):
        """Parse a date string into a datetime object."""
        try:
            # ex: "2025-04-14 21:27:57"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    return (parse_date,)


@app.cell
def _(mo):
    def render(title, link, description, pubDate, guid, **kwargs):
        # some feeds have a link in the guid
        if not link and guid.startswith("http"):
            link = guid

        template = f"""
    <h1><a href='{link}'>{title}</a></h1>
    <br>published: {pubDate}<br>
    {description}"""

        return lambda: mo.md(template)

    # TODO: properly style the output
    return (render,)


@app.cell
def _(mo):
    query_params = mo.query_params()
    return (query_params,)


@app.cell
def _(fetch_xml, mo, parse_rss_feed, url_input):
    try:
        xml = fetch_xml(url_input.value)
    except Exception as e:
        mo.stop(True, mo.callout(f"Failed to fetch XML: {e}", kind="danger"))

    try:
        rss = parse_rss_feed(xml)
    except Exception as e:
        mo.stop(
            True,
            mo.vstack(
                [
                    mo.callout(f"Failed to parse XML: {e}", kind="danger"),
                    mo.ui.code_editor(
                        label="Raw XML",
                        value=xml.decode("utf-8"),
                        language="xml",
                        max_height=400,
                    ),
                ]
            ),
        )
    return rss, xml


@app.cell
def _(defaultdict, parse_date, render, rss, urllib):
    sidelinks = defaultdict(dict)
    routes = defaultdict(dict)

    for feed in rss.items:
        date = parse_date(feed.pubDate)
        side_link = f"#/{urllib.parse.quote(feed.guid)}"
        title = feed.title
        func = render(**feed.model_dump())

        {f"#/{feed.guid}": feed.title}
        if date:
            date_str = date.strftime("%Y-%m-%d")
            sidelinks[date_str][side_link] = title
            routes[side_link] = func
        else:
            sidelinks["Unknown"][side_link] = title
            routes[side_link] = func

    sidelinks = dict(sorted(sidelinks.items(), reverse=True))  # Sort by date
    return routes, sidelinks


@app.cell
def _(mo):
    mo.md(
        """
    # RSS Feed Reader build with marimo notebook
    [source code](https://github.com/kj-9/marimo-rss-reader)
    """
    )
    return


@app.cell
def _(mo, query_params):
    url_input = mo.ui.text(
        label="## Enter URL for RSS Feed:",
        value=query_params["url"]
        or "https://kj-9.github.io/hacker-news-ja-summary-rss/rss.xml",
        full_width=True,
        on_change=lambda value: query_params.set("url", value),
    )
    url_input
    return (url_input,)


@app.cell
def _(mo, rss, xml):
    mo.accordion(
        {
            "#### Raw XML": mo.ui.code_editor(
                value=xml.decode("utf-8"),
                language="xml",
                max_height=400,
            ),
            "#### Parsed Feeds Table": mo.ui.table(
                data=[item.model_dump() for item in rss.items]
            ),
        }
    )

    return


@app.cell
def _(mo):
    mo.md("""---""")
    return


@app.cell
def _(mo, rss, sidelinks):
    mo.sidebar(
        [
            mo.md(f" ##[{rss.title}]({rss.link})"),
            mo.md("---"),
            mo.nav_menu(
                sidelinks,
                orientation="vertical",
            ),
        ],
        width=400,
    )
    return


@app.cell
def _(mo, routes):
    routes[mo.routes.CATCH_ALL] = mo.callout(
        "Please select a feed to show from the side bar.", kind="info"
    )

    mo.routes(routes)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
