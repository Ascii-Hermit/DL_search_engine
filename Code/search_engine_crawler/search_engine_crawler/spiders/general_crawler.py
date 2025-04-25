import scrapy
from langdetect import detect

class GeneralCrawlerSpider(scrapy.Spider):
    name = "general_crawler"
    allowed_domains = ["wikipedia.org"]
    start_urls = ["https://en.wikipedia.org/wiki/Main_Page"]
    visited_urls = set()
    
    def parse(self, response):
        if response.url in self.visited_urls:
            return
        self.visited_urls.add(response.url)
        
        try:
            # Extract title
            title = response.css('title::text').get()
            
            # Extract content
            paragraphs = response.css('p::text').getall()
            content = ' '.join(paragraphs)
            
            # Check if content is in English
            if content and len(content) > 100:
                try:
                    language = detect(content[:1000])
                    if language != 'en':
                        self.logger.info(f"Skipping non-English page: {response.url}")
                        return
                except Exception as e:
                    self.logger.error(f"Language detection error: {e}")
            
            # Simple summarization: use first paragraph or first few sentences
            short_description = ""
            if paragraphs:
                first_para = paragraphs[0].strip()
                if len(first_para) > 20:  # Make sure it's not just a short fragment
                    short_description = first_para
                else:
                    # If first paragraph is too short, combine first few paragraphs
                    combined = ' '.join([p.strip() for p in paragraphs[:3]])
                    # Limit to ~50 words
                    words = combined.split()
                    if len(words) > 400:
                        short_description = ' '.join(words[:400]) + '...'
                    else:
                        short_description = combined
            
            yield {
                'url': response.url,
                'title': title,
                'short_description': short_description,
                'content': content,
            }
            
            # Follow links to other pages (only within Wikipedia)
            for link in response.css('a::attr(href)').getall():
                if link and link.startswith('/wiki/') and ':' not in link:
                    yield response.follow(link, self.parse)
                    
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {e}")
