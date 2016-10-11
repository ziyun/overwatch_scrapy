from scrapy import Spider
from scrapy import Request
from datetime import datetime
from collections import OrderedDict
import json
import re


class PlayerSpider(Spider):

    name = "player"

    def start_requests(self):
        btag = getattr(self, 'battletag', None)
        if btag is None:
            self.logger.error("Missing player battle tag")
            return
        if re.match('.#[0-9]{4}', btag):
            btag = btag.replace('#', '-')

        urls = ["https://playoverwatch.com/en-us/career/pc/kr/{}".format(btag)]
        for url in urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        results = self.parse_competitive(response)
        competitive_rank = response.css('div.competitive-rank > div.h6::text').extract_first()
        results['competitive_rank'] = int(competitive_rank)
        player_name = response.css('h1.header-masthead::text').extract_first()
        results['player_name'] = player_name
        fname = response.url.split('/')[-1]

        t = datetime.utcnow().replace(microsecond=1)
        results['created_on'] = t.isoformat()
        with open('{}_{}.json'.format(fname, t.isoformat()), 'w') as fp:
            json.dump(results, fp, indent=4, separators=(',', ': '))

    def parse_competitive(self, response):
        competitive_play = response.css('div#competitive-play')
        # Comparison legend
        comparison_legend = competitive_play.css(
            'section.hero-comparison-section option')
        legend = {}
        for i in comparison_legend:
            key = i.css('::attr(value)').extract_first()
            val = i.css('::text').extract_first()
            legend[key] = val

        # Comparisons
        comparisons = competitive_play.css('div[data-group-id="comparisons"]')
        comparison_data = OrderedDict()
        for c in comparisons:
            category_id = c.css('::attr(data-category-id)').extract_first()
            category_id = legend[category_id]
            comparison_data[category_id] = OrderedDict()
            bar_text = c.css('div.bar-text div::text').extract()
            for i in range(0, len(bar_text), 2):
                key = bar_text[i]
                val = bar_text[i + 1]
                comparison_data[category_id][key] = val

        # Stat legend
        stats_legend = competitive_play.css('section.career-stats-section '
                                            'option')
        for i in stats_legend:
            key = i.css('::attr(value)').extract_first()
            val = i.css('::text').extract_first()
            legend[key] = val

        # Stats
        stats = competitive_play.css('div[data-group-id="stats"]')
        stats_data = OrderedDict()
        for s in stats:
            category_id = s.css('::attr(data-category-id)').extract_first()
            category_id = legend[category_id]
            stats_data[category_id] = OrderedDict()
            tables = s.css('table.data-table')
            for t in tables:
                table_name = t.css('th > span::text').extract_first()
                stats_data[category_id][table_name] = OrderedDict()
                table_data = t.css('td::text').extract()
                for i in range(0, len(table_data), 2):
                    key = table_data[i]
                    val = table_data[i + 1]
                    stats_data[category_id][table_name][key] = val
        return {'comparisons': comparison_data,
                'stats': stats_data}
