from kivymd.app import MDApp
from kivy.lang import Builder
from database_manager import DatabaseManager
from ui_manager import UIManager
from scraper_manager import ScraperManager
from kivy.clock import Clock
import threading


class SzukajMieszkaniaApp(MDApp):
    def build(self):
        self.root = Builder.load_file("app.kv")
        self.current_offers = []  # Pusta lista ofert
        self.database_manager = DatabaseManager()  # Połączenie z bazą danych
        scraper_manager = ScraperManager(database_manager=self.database_manager)
        self.ui_manager = UIManager(self, self.root, self.database_manager, scraper_manager)
        self.scraper_manager = ScraperManager(self.database_manager)
        self.enabled_services = {"otodom.pl", "domiporta.pl", "nieruchomosci-online.pl", "gratka.pl", "morizon.pl"}

        self.sorting = "price"  # Domyślne sortowanie
        self.offer_limit = 25  # Domyślny limit ofert do wyświetlenia

        return self.root

    def on_start(self):
        self.service_offsets = {service: 0 for service in self.enabled_services}  # Inicjalizacja offsetu dla każdego serwisu
        self.ui_manager.filter_and_display_offers()
        self.ui_manager.update_count()

    # def start_scraping_with_loading(self, city, district, price_min, price_max, area_min, area_max, rooms, services):
    #     """Rozpoczyna proces scrapowania i wyświetla ekran ładowania z paskiem postępu."""
    #     self.root.ids.nav_drawer.set_state("close")
    #     self.root.ids.screen_manager.current = "loading_screen"  # Przełącz na ekran ładowania
    #     self.progress = 0  # Zresetuj pasek postępu
    #     self.offer_count = 0
    #     self.root.ids.progress_bar.value = 0
    #     self.root.ids.offer_count_label.text = "Wczytano 0 ofert"

    #     # Uruchamiamy scrapowanie w osobnym wątku, aby nie blokować interfejsu użytkownika
    #     threading.Thread(target=self.start_scraping, args=(city, district, price_min, price_max, area_min, area_max, rooms, services)).start()

    # def start_scraping(self, city, district, price_min, price_max, area_min, area_max, rooms, services):
    #     """Rozpoczyna faktyczny proces scrapowania z aktualizacją paska postępu."""
    #     num_services = len(services)
    #     progress_step = 100 / num_services  # Krok paska postępu dla każdego serwisu

    #     def update_progress(service_name):
    #         self.progress += progress_step
    #         Clock.schedule_once(lambda dt: self.update_ui_progress(service_name), 0)

    #     # Rozpocznij scrapowanie
    #     for i, service in enumerate(services):
    #         update_progress(service)  # Zaktualizuj pasek postępu i tekst
    #         offers = self.scraper_manager.start_scraping(city, district, price_min, price_max, area_min, area_max, rooms, [service])
    #         self.current_offers.extend(offers)
    #         self.offer_count += len(offers)
    #         Clock.schedule_once(lambda dt: self.update_offer_count(), 0)

    #     # Po zakończeniu wróć na ekran wyników
    #     Clock.schedule_once(lambda dt: self.finish_scraping(), 0)

    # def update_ui_progress(self, service_name):
    #     """Aktualizuje pasek postępu i tekst na ekranie ładowania."""
    #     self.root.ids.progress_bar.value = self.progress
    #     self.root.ids.loading_label.text = f"Ładowanie ofert z serwisu: {service_name}..."

    # def update_offer_count(self):
    #     """Aktualizuje licznik wczytanych ofert."""
    #     self.root.ids.offer_count_label.text = f"Wczytano {self.offer_count} ofert"

    # def finish_scraping(self):
    #     """Kończy scrapowanie i przełącza widok na ekran wyników."""
    #     self.ui_manager.filter_and_display_offers()
    #     self.root.ids.screen_manager.current = "offers"  # Przełącz na ekran wyników
    #     self.ui_manager.filter_and_display_offers()  # Wyświetl wyniki
    #     self.ui_manager.update_count()  # Aktualizuj liczbę ofert

    def start_scraping_with_loading(self, city, district, price_min, price_max, area_min, area_max, rooms, services, num_pages=1):
        """Rozpoczyna proces scrapowania i wyświetla ekran ładowania z paskiem postępu."""
        self.root.ids.screen_manager.current = "loading_screen"  # Przełącz na ekran ładowania
        self.root.ids.nav_drawer.set_state("close")  # Zamknij menu boczne (jeśli jest otwarte)
        self.progress = 0  # Zresetuj pasek postępu
        self.offer_count = 0  # Zresetuj licznik ofert
        self.root.ids.progress_bar.value = 0
        self.root.ids.offer_count_label.text = "Wczytano 0 ofert"  # Ustaw licznik na 0

        # Uruchamiamy scrapowanie w osobnym wątku, aby nie blokować interfejsu użytkownika
        threading.Thread(target=self.scrape_offers_in_thread, args=(city, district, price_min, price_max, area_min, area_max, rooms, services, num_pages)).start()

    # def scrape_offers_in_thread(self, city, district, price_min, price_max, area_min, area_max, rooms, services):
    #     """Scrapowanie w tle i aktualizowanie UI."""
    #     num_services = len(services)
    #     progress_step = 100 / num_services  # Krok paska postępu dla każdego serwisu
    #     all_offers = []  # Lista do zbierania wszystkich ofert z serwisów

    #     for service in services:
    #         # Scrapujemy oferty z aktualnego serwisu
    #         offers = self.scraper_manager.start_scraping(city, district, price_min, price_max, area_min, area_max, rooms, [service])
    #         all_offers.extend(offers)  # Dodajemy oferty do listy

    #         # Zaktualizuj postęp i licznik ofert
    #         self.progress += progress_step
    #         Clock.schedule_once(lambda dt, srv=service, off=offers: self.update_progress(srv, off), 0)

    #     # # Po zakończeniu scrapowania wywołaj zapis do bazy
    #     # Clock.schedule_once(lambda dt, offers=all_offers: self.save_offers_to_database(offers), 0)

    #     # Sprawdzenie, czy nie ma ofert
    #     if len(all_offers) == 0:
    #         Clock.schedule_once(lambda dt: self.handle_no_offers(), 0)
    #     else:
    #         Clock.schedule_once(lambda dt, offers=all_offers: self.save_offers_to_database(offers), 0)
    def scrape_offers_in_thread(self, city, district, price_min, price_max, area_min, area_max, rooms, services, num_pages):
        """Scrapowanie w tle i aktualizowanie UI."""
        num_services = len(services)
        progress_step = 100 / num_services  # Krok paska postępu dla każdego serwisu
        all_offers = []  # Lista do zbierania wszystkich ofert z serwisów

        for service in services:
            offers = self.scraper_manager.start_scraping(city, district, price_min, price_max, area_min, area_max, rooms, [service], num_pages)

            # Sprawdzenie, czy zostały znalezione oferty
            if offers:
                all_offers.extend(offers)
                self.progress += progress_step
                Clock.schedule_once(lambda dt, srv=service, off=offers: self.update_progress(srv, off), 0)
            else:
                # Jeśli brak ofert, nadal zwiększamy postęp, ale nie aktualizujemy licznika ofert
                self.progress += progress_step
                Clock.schedule_once(lambda dt, srv=service: self.update_progress_no_offers(srv), 0)

        # Sprawdzenie, czy nie ma żadnych ofert w ogóle
        if len(all_offers) == 0:
            Clock.schedule_once(lambda dt: self.handle_no_offers(), 0)
        else:
            Clock.schedule_once(lambda dt, offers=all_offers: self.save_offers_to_database(offers), 0)

    def handle_no_offers(self):
        """Obsługa sytuacji, gdy nie znaleziono żadnych ofert."""
        self.root.ids.loading_label.text = "Brak ofert do wyświetlenia"
        self.root.ids.offer_count_label.text = "Wczytano 0 ofert"
        # Po krótkim czasie wróć na ekran wyszukiwania lub wyświetl pustą listę
        Clock.schedule_once(lambda dt: self.finish_scraping(), 1)

    def update_progress_no_offers(self, service_name):
        """Aktualizuje pasek postępu, gdy nie znaleziono ofert dla danego serwisu."""
        self.root.ids.progress_bar.value = self.progress
        self.root.ids.loading_label.text = f"Brak ofert z serwisu: {service_name}"

    def update_progress(self, service_name, offers):
        """Aktualizuje licznik ofert i pasek postępu."""
        if offers:
            self.offer_count += len(offers)
            self.root.ids.offer_count_label.text = f"Wczytano {self.offer_count} ofert"
        self.root.ids.progress_bar.value = self.progress
        self.root.ids.loading_label.text = f"Ładowanie ofert z serwisu: {service_name}..."

    def save_offers_to_database(self, offers):
        """Zapisuje wszystkie oferty do bazy danych po zakończeniu scrapowania."""

        # Wyświetlamy komunikat o usuwaniu duplikatów
        self.root.ids.loading_label.text = "Usuwanie zduplikowanych ofert..."

        # Usunięcie zduplikowanych ofert na podstawie pola 'link'
        unique_offers = self.remove_duplicates(offers)

        # Po 1 sekundzie zmieniamy komunikat na "Zapisywanie do bazy danych..." i kontynuujemy
        Clock.schedule_once(lambda dt: self.proceed_to_saving(unique_offers), 2)

    def proceed_to_saving(self, unique_offers):
        """Zapisuje unikalne oferty do bazy danych po opóźnieniu."""
        self.root.ids.loading_label.text = "Zapisywanie do bazy danych..."
        self.database_manager.insert_offers(unique_offers)
        Clock.schedule_once(lambda dt: self.finish_scraping(), 2)

    def remove_duplicates(self, offers):
        """Usuwa zduplikowane oferty na podstawie pola 'link'."""
        unique_offers = []
        seen_links = set()

        for offer in offers:
            if offer["link"] not in seen_links:
                unique_offers.append(offer)
                seen_links.add(offer["link"])
        return unique_offers

    def finish_scraping(self):
        """Kończy proces i przełącza widok na ekran wyników."""
        self.root.ids.screen_manager.current = "offers"  # Przełącz na ekran wyników
        self.ui_manager.filter_and_display_offers()  # Wyświetl wyniki
        self.ui_manager.update_count()  # Aktualizuj liczbę ofert


SzukajMieszkaniaApp().run()
