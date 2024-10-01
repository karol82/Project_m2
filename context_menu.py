from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivymd.uix.list import ThreeLineListItem
from kivymd.uix.menu import MDDropdownMenu
import webbrowser


class LongPressListItem(ThreeLineListItem):
    """Obsługa długiego kliknięcia na element listy."""

    def __init__(self, app, link, web, price, area, rooms, price_m2, database_manager, list_view, display_offers_callback, is_favorite=False, is_in_blacklist_view=False, **kwargs):
        super().__init__(**kwargs)
        self.app = app  # Przechowujemy referencję do instancji aplikacji
        self.link = link  # Przypisujemy link jako atrybut klasy
        self.price = price  # Cena oferty
        self.area = area  # Powierzchnia oferty
        self.rooms = rooms  # Liczba pokoi
        self.price_m2 = price_m2  # Cena za m²
        self.web = web  # Źródło serwisu (np. otodom.pl)

        self.database_manager = database_manager  # Przypisujemy database_manager jako atrybut klasy
        self.list_view = list_view  # Referencja do MDList, która zawiera widgety
        self.touch_time = None
        self.display_offers_callback = display_offers_callback  # Callback do odświeżania widoku
        self.is_favorite = is_favorite  # Przypisujemy is_favorite jako atrybut klasy
        self.is_in_blacklist_view = is_in_blacklist_view  # Informacja o tym, czy oferta jest w widoku czarnej listy

        self.update_background(is_favorite)  # Rysujemy domyślne tło (biały lub zielony jeśli ulubiony)
        self.bind(pos=self.update_rect, size=self.update_rect)  # Ustawiamy aktualizację prostokąta tła przy zmianie rozmiaru/pozycji

        # Ustawienie czcionki monospacjalnej (np. Courier)
        monospaced_font = "fonts/Lekton-Regular.ttf"  # Możesz również dodać własną ścieżkę do pliku z czcionką

        # Aktualizacja tekstu z odpowiednią czcionką
        # self.ids._lbl_primary.font_name = monospaced_font
        self.ids._lbl_secondary.font_name = monospaced_font
        self.ids._lbl_tertiary.font_name = monospaced_font

    def update_background(self, is_favorite):
        """Aktualizuje tło elementu w zależności od tego, czy oferta jest ulubiona."""
        self.canvas.before.clear()  # Czyścimy poprzedni canvas, aby nałożyć nowy kolor tła
        with self.canvas.before:
            if is_favorite:
                Color(0.8, 1, 0.8, 1)  # Lekko zielony kolor tła, jeśli oferta jest w ulubionych
            else:
                Color(1, 1, 1, 1)  # Domyślny kolor tła (biały)
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def update_rect(self, *args):
        """Aktualizuje prostokąt tła, aby dostosować go do rozmiaru i pozycji widgetu."""
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Wykrycie początku dotyku, inicjujemy timer
            self.touch_time = Clock.schedule_once(self.show_menu, 0.5)  # 500ms to długie kliknięcie
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.touch_time:
            # Zatrzymujemy timer, jeśli dotyk został przerwany
            Clock.unschedule(self.touch_time)
            self.touch_time = None
        return super().on_touch_up(touch)

    def show_menu(self, *args):
        """Wyświetlenie menu po długim kliknięciu, dynamicznie dostosowane do stanu oferty."""

        # Dynamiczna lista opcji menu
        menu_items = []

        # Jeśli oferta nie jest w ulubionych, dodaj opcję "Dodaj do ulubionych"
        if not self.is_favorite:
            menu_items.append(
                {
                    "viewclass": "OneLineListItem",
                    "text": "Dodaj do ulubionych",
                    "on_release": lambda: self.menu_callback("Dodaj do ulubionych"),
                }
            )

        # Jeśli oferta jest w ulubionych, dodaj opcję "Usuń z ulubionych"
        if self.is_favorite:
            menu_items.append(
                {
                    "viewclass": "OneLineListItem",
                    "text": "Usuń z ulubionych",
                    "on_release": lambda: self.menu_callback("Usuń z ulubionych"),
                }
            )

        # Sprawdź, czy oferta jest na czarnej liście
        is_blacklisted = self.link in self.database_manager.fetch_blacklist()

        # Jeśli oferta nie jest na czarnej liście, dodaj opcję "Dodaj do czarnej listy"
        if not is_blacklisted:
            menu_items.append(
                {
                    "viewclass": "OneLineListItem",
                    "text": "Dodaj do czarnej listy",
                    "on_release": lambda: self.menu_callback("Dodaj do czarnej listy"),
                }
            )

        # Jeśli oferta jest na czarnej liście, dodaj opcję "Usuń z czarnej listy"
        if is_blacklisted:
            menu_items.append(
                {
                    "viewclass": "OneLineListItem",
                    "text": "Usuń z czarnej listy",
                    "on_release": lambda: self.menu_callback("Usuń z czarnej listy"),
                }
            )

        # Zawsze dodaj opcję "Przejdź do oferty"
        menu_items.append(
            {
                "viewclass": "OneLineListItem",
                "text": "Przejdź do oferty",
                "on_release": lambda: self.menu_callback("Przejdź do oferty"),
            }
        )

        # Tworzenie menu
        self.menu = MDDropdownMenu(
            caller=self,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def menu_callback(self, option):
        """Obsługa wybranej opcji z menu kontekstowego."""
        print(f"Wybrana opcja: {option}")
        self.menu.dismiss()  # Zamknięcie menu

        # Pełny słownik danych oferty
        offer = {
            "link": self.link,  # Link do oferty
            "price": self.price,  # Cena oferty
            "area": self.area,  # Powierzchnia oferty
            "rooms": self.rooms,  # Liczba pokoi
            "price_m2": self.price_m2,  # Cena za m²
            "web": self.web,  # Serwis, z którego pochodzi oferta
            "desc": self.text,  # Opis oferty
        }
        print("Znajdujesz się w: ", self.app.ui_manager.current_view)
        if option == "Dodaj do ulubionych":
            self.database_manager.add_to_favorites(offer)  # Dodaj do ulubionych
            self.is_favorite = True  # Ustawiamy ofertę jako ulubioną
            self.update_background(is_favorite=True)  # Zmieniamy kolor tła na zielony
            self.app.ui_manager.update_count()

            # Usuwamy z listy tylko wtedy, gdy jesteśmy w czarnej liście
            if self.is_in_blacklist_view:
                self.list_view.remove_widget(self)  # Usuwamy widget z listy

        elif option == "Usuń z ulubionych":
            self.database_manager.remove_from_favorites(self.link)  # Usuwamy z ulubionych
            self.is_favorite = False  # Ustawiamy ofertę jako nie-ulubioną
            self.update_background(is_favorite=False)  # Zmieniamy kolor tła

            if self.app.ui_manager.current_view == "ulubione":
                self.app.ui_manager.update_count()
                self.list_view.remove_widget(self)  # Usuwamy widget z listy

        elif option == "Dodaj do czarnej listy":
            self.list_view.remove_widget(self)  # Usuwa widget z listy
            self.database_manager.add_to_blacklist(offer)  # Dodaj do czarnej listy
            self.database_manager.remove_from_favorites(self.link)  # Usuń z ulubionych
            # Sprawdzamy aktualny widok i aktualizujemy odpowiedni licznik
            # if self.app.ui_manager.current_view == "ulubione":
            #     self.app.ui_manager.update_count("ulubione")
            # else:
            #     print("aktualizuje licznik w oferty")
            self.app.current_offers = [o for o in self.app.current_offers if o["link"] != offer["link"]]
            #     self.app.ui_manager.update_count("oferty")
            self.app.ui_manager.update_count()

        elif option == "Usuń z czarnej listy":
            self.database_manager.remove_from_blacklist(self.link)  # Usuń z czarnej listy
            self.list_view.remove_widget(self)  # Usuwamy widget z listy natychmiast
            # self.app.ui_manager.update_count("czarna_lista")
            self.app.ui_manager.update_count()
        elif option == "Przejdź do oferty":
            webbrowser.open(self.link)  # Otwieramy link w przeglądarce
