from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from context_menu import LongPressListItem
from kivy.metrics import dp
import socket


class UIManager:
    def __init__(self, app, root, database_manager, scraper_manager):
        self.root = root
        self.app = app  # Przechowuje instancję aplikacji
        self.database_manager = database_manager
        self.scraper_manager = scraper_manager  # Dodajemy scraper_manager

        self.favorite_links = database_manager.fetch_favorites()
        self.menu = None
        self.sorting = "price"
        self.enabled_services = {"otodom.pl", "morizon.pl", "gratka.pl", "nieruchomosci-online.pl", "domiporta.pl"}
        self.current_offers = []  # Lista aktualnych ofert
        self.all_offers = []  # Nowa zmienna do przechowywania wszystkich ofert
        self.loading_more_offers = False  # Flaga, aby uniknąć jednoczesnego wielokrotnego wczytywania
        self.selected_wojewodztwo = "malopolskie"
        self.load_all_offers()
        self.current_view = "oferty"  # Domyślnie widok ofert

        self.wojewodztwa = {
            "Dolnośląskie": "dolnoslaskie",
            "Kujawsko-Pomorskie": "kujawsko-pomorskie",
            "Lubelskie": "lubelskie",
            "Lubuskie": "lubuskie",
            "Mazowieckie": "mazowieckie",
            "Małopolskie": "malopolskie",
            "Opolskie": "opolskie",
            "Podkarpackie": "podkarpackie",
            "Podlaskie": "podlaskie",
            "Pomorskie": "pomorskie",
            "Warmińsko-Mazurskie": "warminsko-mazurskie",
            "Wielkopolskie": "wielkopolskie",
            "Zachodniopomorskie": "zachodniopomorskie",
            "Łódzkie": "lodzkie",
            "Śląskie": "slaskie",
            "Świętokrzyskie": "swietokrzyskie",
        }

    def set_offer_limit(self, limit, selected_button):
        """Ustawienie limitu ofert do wyświetlenia i aktualizacja wyglądu przycisków."""
        self.app.offer_limit = limit
        print("ustalono limit:", self.app.offer_limit)
        # Zaktualizuj kolory przycisków
        buttons = [self.app.root.ids.button_25, self.app.root.ids.button_50, self.app.root.ids.button_75, self.app.root.ids.button_100]
        for button in buttons:
            if button == selected_button:
                button.md_bg_color = self.app.theme_cls.primary_color
                button.text_color = (1, 1, 1, 1)
            else:
                button.md_bg_color = (0.9, 0.9, 0.9, 1)
                button.text_color = (0, 0, 0, 1)

        # Odświeżamy oferty, ale nie czyścimy listy
        self.filter_and_display_offers()
        self.update_count()

    def load_all_offers(self):
        """Wczytuje wszystkie oferty z bazy danych do zmiennej all_offers."""
        self.all_offers = self.database_manager.fetch_offers([], limit=None)  # Wczytaj wszystkie oferty
        print(f"Wczytano {len(self.all_offers)} ofert z bazy danych.")  # Log do śledzenia liczby ofert

    def show_wojewodztwa_menu(self, instance):
        """Wyświetla rozwijaną listę województw z polskimi znakami."""
        # Tworzymy elementy menu z województwami_PL
        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": wojewodztwo_PL,
                "on_release": lambda x=wojewodztwo_PL: self.set_wojewodztwo(x, instance),
            }
            for wojewodztwo_PL in self.wojewodztwa.keys()
        ]
        # Zamykanie poprzedniego menu, jeśli istnieje
        if hasattr(self, "menu") and self.menu:
            self.menu.dismiss()

        # Tworzymy rozwijane menu
        self.menu = MDDropdownMenu(caller=instance, items=menu_items, width_mult=4)
        self.menu.open()

    def set_wojewodztwo(self, wojewodztwo_PL, instance):
        """Ustawia wybrane województwo w polu tekstowym, a do scrapera przekazuje bez polskich znaków."""
        instance.text = wojewodztwo_PL
        self.selected_wojewodztwo = self.wojewodztwa[wojewodztwo_PL]  # Przechowujemy wersję bez polskich znaków
        self.menu.dismiss()

    def load_offers(self):
        self.current_view = "oferty"
        """Pobiera i wyświetla oferty oraz zmienia kolor i tytuł górnej belki."""
        self.filter_and_display_offers()  # Wywołujemy funkcję wyświetlającą oferty
        self.set_toolbar_color([0.12, 0.56, 1, 1])  # Zmieniamy kolor belki na niebieski
        self.root.ids.param_drawer.set_state("close")  # Zamykamy panel boczny

        self.update_count()

    def load_blacklist(self):
        self.current_view = "czarna_lista"
        blacklist_offers = self.database_manager.fetch_blacklist_offers()  # Pobierz wszystkie oferty z czarnej listy
        self.update_count()

        # Konwersja krotek na słowniki
        offer_keys = ["id", "web", "desc", "price", "area", "rooms", "price_m2", "link"]
        blacklist_dict = [dict(zip(offer_keys, offer)) for offer in blacklist_offers]

        self.display_offers(blacklist_dict, reset=True, is_in_blacklist_view=True)
        self.set_toolbar_color([0, 0, 0, 1])  # Zmieniamy kolor belki na czarny
        self.root.ids.param_drawer.set_state("close")  # Zamykamy panel boczny

    def load_favorites(self):
        self.current_view = "ulubione"
        favorite_offers = self.database_manager.fetch_favorite_offers()  # Pobierz wszystkie ulubione bez filtrowania
        self.update_count()

        # Konwersja krotek na słowniki
        offer_keys = ["id", "web", "desc", "price", "area", "rooms", "price_m2", "link"]
        favorites_dict = [dict(zip(offer_keys, offer)) for offer in favorite_offers]

        self.display_offers(favorites_dict, reset=True)  # Wyświetl ulubione bez filtrowania
        self.set_toolbar_color([0.0, 0.5, 0.0, 1])  # Zmieniamy kolor belki na zielony
        self.root.ids.param_drawer.set_state("close")  # Zamykamy panel boczny

    def set_toolbar_color(self, color):
        """Ustawia kolor górnej belki."""
        self.root.ids.top_app_bar.md_bg_color = color  # Zmieniamy kolor MDTopAppBar

    def set_toolbar_title(self, title):
        """Ustawia tytuł górnej belki."""
        self.root.ids.top_app_bar.title = title  # Zmieniamy tytuł MDTopAppBar

    def toggle_service(self, service, active):
        """Włączanie i wyłączanie serwisów."""
        if active:
            self.app.enabled_services.add(service)
        else:
            self.app.enabled_services.discard(service)

        # Sprawdź, czy są aktywne serwisy
        if not self.app.enabled_services:
            # Jeśli nie ma aktywnych serwisów, wyczyść listę
            self.root.ids.list.clear_widgets()
            print("Brak aktywnych serwisów. Lista wyczyszczona.")
        else:
            # Odśwież listę ofert z uwzględnieniem aktualnego sortowania
            self.apply_sorting_and_filtering()

        self.current_view = "oferty"
        self.update_count()

    def apply_sorting_and_filtering(self):
        """Pobiera i wyświetla oferty z uwzględnieniem aktualnych filtrów i sortowania."""
        print("Wywołanie apply_sorting_and_filtering z aktualnym sortowaniem:", self.app.sorting)

        self.current_view = "oferty"

        if not self.app.enabled_services:
            print("Brak aktywnych serwisów. Czyszczenie listy.")
            self.root.ids.list.clear_widgets()
            self.update_count()
            return

        # Pobierz oferty z uwzględnieniem aktualnego sortowania
        filtered_offers = self.database_manager.fetch_offers(self.app.enabled_services, limit=self.app.offer_limit, sort_by=self.app.sorting)  # Uwzględnij aktualne sortowanie

        num_offers = len(filtered_offers)
        if num_offers == 0:
            print("Brak ofert do wyświetlenia, czyszczenie listy.")
            self.app.current_offers = []
            self.root.ids.list.clear_widgets()  # Czyści widżety z listy
        else:
            # Konwersja ofert na słowniki i wyświetlenie ich
            offer_keys = ["id", "web", "desc", "price", "area", "rooms", "price_m2", "link"]
            offers_dict = [dict(zip(offer_keys, offer)) for offer in filtered_offers]
            self.app.current_offers = offers_dict
            self.display_offers(offers_dict, reset=True)  # Wyświetlenie ofert

        self.update_count()

    def filter_and_display_offers(self):
        """Filtruje i wyświetla oferty z aktualnym sortowaniem i filtrami."""
        print("Wywołanie filter_and_display_offers")

        if not self.app.enabled_services:
            print("Brak aktywnych serwisów. Czyszczenie listy.")
            self.root.ids.list.clear_widgets()
            return

        # Pobieramy oferty tylko z aktywnych serwisów (dotyczy to tylko widoku ofert, nie ulubionych/czarnej listy)
        if self.current_view == "oferty":
            filtered_offers = self.database_manager.fetch_offers(self.app.enabled_services, limit=self.app.offer_limit, sort_by=self.app.sorting)
            print(f"Wczytano {len(filtered_offers)} ofert z aktywnych serwisów.")

            # Konwersja krotek na słowniki
            offer_keys = ["id", "web", "desc", "price", "area", "rooms", "price_m2", "link"]
            offers_dict = [dict(zip(offer_keys, offer)) for offer in filtered_offers]

            if offers_dict:
                self.app.current_offers = offers_dict
                self.display_offers(offers_dict, reset=True)
            else:
                print("Brak ofert do wyświetlenia")

    def set_sorting(self, sort_option, active):
        """Ustawienie metody sortowania ofert."""
        if active:
            # Ustawienie nowej metody sortowania
            self.app.sorting = sort_option

            # Zastosowanie sortowania i filtrów
            self.apply_sorting_and_filtering()
        else:
            # Sprawdzamy, czy wszystkie pozostałe checkboxy są odznaczone
            checkbox_group = ["price", "price_m2", "area"]
            other_checkboxes_active = any(self.root.ids[f"{checkbox}"].active for checkbox in checkbox_group if checkbox != sort_option)

            if not other_checkboxes_active:
                # Jeśli próbujemy odznaczyć ostatni aktywny checkbox, ustawiamy go z powrotem jako aktywny
                self.root.ids[sort_option].active = True

    def on_search_button_pressed(self):
        """Rozpoczęcie scrapowania z ekranem ładowania oraz dynamicznym paskiem postępu."""

        def check_internet(host="8.8.8.8", port=53, timeout=3):
            try:
                socket.setdefaulttimeout(timeout)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                return True
            except:
                return False

        # Pobierz liczbę stron z pola tekstowego
        try:
            num_pages = int(self.root.ids.liczba_stron.text)
        except ValueError:
            num_pages = 1  # Jeśli użytkownik nie wprowadził liczby, ustawiamy domyślnie 1
        if not check_internet():
            # Wyświetlamy komunikat o braku połączenia z internetem
            self.root.ids.loading_label.text = "Brak połączenia z internetem. Sprawdź swoje połączenie."
            return  # Zatrzymujemy wyszukiwanie, ponieważ nie ma internetu

        # Przełącz na ekran ładowania
        self.root.ids.screen_manager.current = "loading_screen"
        self.app.start_scraping_with_loading(
            city=self.root.ids.miasto.text,
            district=self.selected_wojewodztwo,  # Przekazujemy nazwę województwa bez polskich znaków
            price_min=int(self.root.ids.cena_od.text),
            price_max=int(self.root.ids.cena_do.text),
            area_min=float(self.root.ids.powierzchnia_od.text),
            area_max=float(self.root.ids.powierzchnia_do.text),
            rooms=int(self.root.ids.pokoje.text),
            services=self.enabled_services,
            num_pages=num_pages,
        )

        # Zaktualizuj liczbę ofert
        self.update_count()

    def update_count(self):
        """Aktualizuje licznik ofert w zależności od wybranej kategorii."""
        current_view = self.app.ui_manager.current_view

        if current_view == "oferty":
            self.set_toolbar_color([0.12, 0.56, 1, 1])
            count = len(self.app.current_offers)
            self.root.ids.top_app_bar.title = f"Project_m2 - Oferty ({count})"

        elif current_view == "ulubione":
            count = len(self.database_manager.fetch_favorite_offers())
            self.root.ids.top_app_bar.title = f"Ulubione ({count})"

        elif current_view == "czarna_lista":
            count = len(self.database_manager.fetch_blacklist_offers())
            self.root.ids.top_app_bar.title = f"Czarna lista ({count})"

    def check_inputs(self):
        """Sprawdza, czy wszystkie pola formularza są wypełnione, i aktywuje przycisk 'Szukaj'."""

        miasto = self.root.ids.miasto.text.strip() != ""
        pokoje = self.root.ids.pokoje.text.strip() != ""
        powierzchnia_od = self.root.ids.powierzchnia_od.text.strip() != ""
        powierzchnia_do = self.root.ids.powierzchnia_do.text.strip() != ""
        cena_od = self.root.ids.cena_od.text.strip() != ""
        cena_do = self.root.ids.cena_do.text.strip() != ""

        if miasto and pokoje and powierzchnia_od and powierzchnia_do and cena_od and cena_do:
            self.root.ids.szukaj_button.disabled = False  # Aktywacja przycisku 'Szukaj'
        else:
            self.root.ids.szukaj_button.disabled = True  # Dezaktywacja przycisku 'Szukaj'

    def display_offers(self, offers, reset=False, is_in_blacklist_view=False):
        """Wyświetla oferty na ekranie. Jeśli reset=True, czyści istniejące oferty."""
        if reset:
            print("Czyszczenie listy ofert...")
            self.root.ids.list.clear_widgets()  # Czyści widżety, jeśli zaczynamy od nowa
            print("Lista ofert wyczyszczona.")
        else:
            print("Nie resetuję listy.")

        # Sprawdź, czy przeglądamy oferty, ulubione czy czarną listę
        if self.current_view in ["ulubione", "czarna_lista"]:
            print("Wyświetlam oferty bez filtrów serwisów dla ulubionych lub czarnej listy.")
        else:
            print(f"Wyświetlam oferty z filtrowaniem serwisów: {self.app.enabled_services}")

        # Pobieramy wszystkie linki z ulubionych jednorazowo
        favorite_links = self.database_manager.fetch_favorites()

        for offer in offers:
            # Sprawdź, czy oferta ma wszystkie wymagane klucze
            if not all(key in offer for key in ["web", "desc", "price", "area", "rooms", "price_m2", "link"]):
                print(offer)
                continue  # Pomiń oferty, które nie mają wszystkich kluczy

            if self.current_view == "oferty" and offer["web"] not in self.app.enabled_services:
                print(f"Oferta {offer['link']} nie spełnia warunków filtrowania i nie zostanie wyświetlona. xxx")
                continue  # Pomijamy oferty, które nie spełniają warunków filtrowania

            link = offer["link"]
            is_favorite = link in favorite_links  # Sprawdzenie, czy oferta jest w ulubionych

            # Tworzymy teksty do wyrównania
            price_per_m2_text = f"Cena/m2: {offer['price_m2']:,} zł".replace(",", " ")  # m²
            rooms_text = f"Pokoje: {offer['rooms']}"
            metraz_text = f"Metraż : {offer['area']} m2"
            web_text = offer["web"]

            second_line_text = price_per_m2_text + " " * (20 - len(price_per_m2_text)) + rooms_text
            third_line_text = metraz_text + " " * (20 - len(metraz_text)) + web_text
            # Tworzymy widget dla oferty

            item = LongPressListItem(
                app=self.app,
                text=f"{offer['desc']}",
                secondary_text=second_line_text,
                tertiary_text=third_line_text,
                link=link,
                web=offer["web"],
                area=offer["area"],
                rooms=offer["rooms"],
                price=offer["price"],
                price_m2=offer["price_m2"],
                database_manager=self.database_manager,
                list_view=self.root.ids.list,
                display_offers_callback=lambda: self.display_offers(offers),  # Odświeżenie listy po dodaniu do ulubionych
                is_favorite=is_favorite,
                is_in_blacklist_view=is_in_blacklist_view,
                secondary_theme_text_color="Custom",
                secondary_text_color=(0, 0.6, 0.6, 1),  # (0, 0.6, 1, 1)
                tertiary_theme_text_color="Custom",
                tertiary_text_color=(0, 0.6, 0.6, 1),
                pos_hint={"center_y": 0.2},
                # secondary_font_style="Roboto-Bold",
            )

            # Tworzymy widget dla kwoty po prawej stronie
            price_label = MDLabel(
                text=f"{int(offer['price'] / 1000)} tyś. zł",
                halign="right",
                theme_text_color="Custom",
                text_color=(0, 0.6, 0, 1),
                font_style="H6",
                pos_hint={"center_y": 0.58},
                padding_x=10,
            )
            # Wyłącz automatyczne dopasowanie wysokości i ustaw własną wysokość
            item.size_hint_y = None
            item.height = dp(70)  # Ustaw wysokość na 120dp lub inną wartość, którą chcesz

            item.add_widget(price_label)
            # Dodajemy item do listy, ale tylko te, które nie zostały usunięte
            if offer["price"] > 0 and (self.current_view in ["ulubione", "czarna_lista"] or offer["web"] in self.app.enabled_services):
                self.root.ids.list.add_widget(item)
            else:
                print(f"Oferta {offer['desc']} nie spełnia warunków filtrowania i nie zostanie wyświetlona.")
