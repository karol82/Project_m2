from scraper_engine import NieruchomosciScraper


class ScraperManager:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.scraped_offers = []

    def start_scraping(self, city, district, price_min, price_max, area_min, area_max, rooms, services, num_pages):
        """Rozpoczyna proces scrapowania i zapisuje wyniki do bazy danych oraz zwraca oferty."""
        print("scrapowanie - start")
        # Najpierw wyczyść tabelę offers
        self.database_manager.clear_offers_table()

        # Rozpocznij scrapowanie
        scraper = NieruchomosciScraper(
            selected_city=city,
            selected_district=district,
            price_min=price_min,
            price_max=price_max,
            area_min=area_min,
            area_max=area_max,
            rooms_number=rooms,
            num_pages=num_pages,  # Możesz dostosować liczbę stron do scrapowania
        )
        all_offers = scraper.scrape(services)

        self.scraped_offers = all_offers
        # self.database_manager.insert_offers(all_offers)
        return all_offers

    def get_scraped_offers(self):
        return self.scraped_offers
