import sqlite3


class DatabaseManager:
    def __init__(self, db_path="database.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()  # Tworzenie kursora do zapytań SQL

    def insert_offers(self, offers):
        """Wstawia nowe oferty do bazy danych."""
        query = """
            INSERT INTO offers (web, desc, price, area, rooms, price_m2, link)
            VALUES (:web, :desc, :price, :area, :rooms, :price_m2, :link)
        """
        cursor = self.conn.cursor()
        cursor.executemany(query, offers)  # Używamy słownika do bindowania
        self.conn.commit()
        print("insert ofert do bazy")

    def fetch_favorites(self):  # Pobiera ulubione linki.
        cursor = self.conn.cursor()
        cursor.execute("SELECT link FROM favorites")
        favorites = cursor.fetchall()
        return {fav[0] for fav in favorites}  # Zwraca zbiór (set) unikalnych linków

    def fetch_favorite_offers(self):
        """Pobiera wszystkie oferty z tabeli ulubionych."""
        query = "SELECT * FROM favorites"
        cursor = self.conn.cursor()
        cursor.execute(query)

        return cursor.fetchall()

    def fetch_offers(self, enabled_services, limit=40, sort_by="price"):
        """Pobiera oferty z bazy danych tylko dla aktywnych serwisów, z możliwością sortowania, wykluczając oferty z ceną 0."""
        if not enabled_services:
            return []  # Jeśli nie ma aktywnych serwisów, zwracamy pustą listę

        print(f"Aktywne serwisy: {enabled_services}, Limit: {limit}, Sortowanie: {sort_by}")

        # Określamy, jak ma być sortowane
        order_clause = self._determine_order_clause(sort_by)
        query = f"""
            SELECT * FROM offers
            WHERE web IN ({",".join("?" for _ in enabled_services)})
            AND price > 10000  -- Wykluczamy oferty z ceną poniżej 10000 zł
            AND link NOT IN (SELECT link FROM blacklist)  -- Wykluczamy oferty z czarnej listy
            {order_clause}
            LIMIT ? 
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (*enabled_services, limit))
        results = cursor.fetchall()
        print(f"Liczba ofert pobranych z bazy: {len(results)}")
        return results

    def _determine_order_clause(self, sort_by):
        """Pomocnicza funkcja do określenia klauzuli ORDER BY."""
        if sort_by == "price":
            return "ORDER BY price ASC"
        elif sort_by == "price_m2":
            return "ORDER BY price_m2 ASC"
        elif sort_by == "area":
            return "ORDER BY area DESC"
        else:
            return "ORDER BY price ASC"  # Domyślne sortowanie

    def add_to_favorites(self, offer):
        """Dodaje pełne dane oferty do ulubionych, jeśli oferta nie istnieje."""
        query = "SELECT COUNT(*) FROM favorites WHERE link = ?"
        self.cursor.execute(query, (offer["link"],))
        result = self.cursor.fetchone()[0]

        if result == 0:
            # Dodajemy pełne dane oferty do tabeli "favorites"
            insert_query = """
                INSERT INTO favorites (web, desc, price, area, rooms, price_m2, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(insert_query, (offer["web"], offer["desc"], offer["price"], offer["area"], offer["rooms"], offer["price_m2"], offer["link"]))
            self.conn.commit()
            print(f"Oferta dodana do ulubionych: {offer['link']}")
        else:
            print(f"Oferta już istnieje w ulubionych: {offer['link']}")

        # Usuwamy ofertę z czarnej listy, jeśli się tam znajduje
        self.remove_from_blacklist(offer["link"])

    def add_to_blacklist(self, offer):
        """Dodaje pełne dane oferty do czarnej listy, jeśli oferta nie istnieje."""
        query = "SELECT COUNT(*) FROM blacklist WHERE link = ?"
        self.cursor.execute(query, (offer["link"],))
        result = self.cursor.fetchone()[0]

        if result == 0:
            # Dodajemy pełne dane oferty do tabeli "blacklist"
            insert_query = """
                INSERT INTO blacklist (web, desc, price, area, rooms, price_m2, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(insert_query, (offer["web"], offer["desc"], offer["price"], offer["area"], offer["rooms"], offer["price_m2"], offer["link"]))
            self.conn.commit()
            print(f"Oferta dodana do czarnej listy: {offer['link']}")
        else:
            print(f"Oferta już istnieje w czarnej liście: {offer['link']}")

    def fetch_blacklist_offers(self):
        """Pobiera wszystkie oferty z czarnej listy."""
        query = """
            SELECT * FROM blacklist
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def fetch_blacklist(self):
        """Pobiera wszystkie linki z czarnej listy."""
        query = "SELECT link FROM blacklist"
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return [result[0] for result in results]  # Zwracamy listę linków

    def remove_from_blacklist(self, link):
        """Usuwa ofertę z czarnej listy na podstawie linku."""
        query = "DELETE FROM blacklist WHERE link = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (link,))
        self.conn.commit()

    def clear_offers_table(self):
        """Czyści tabelę offers."""
        query = "DELETE FROM offers"
        self.cursor.execute(query)
        self.conn.commit()

    def remove_from_favorites(self, link):
        """Usuwa ofertę z ulubionych na podstawie linku."""
        query = "DELETE FROM favorites WHERE link = ?"
        self.cursor.execute(query, (link,))
        self.conn.commit()
        print(f"Oferta usunięta z ulubionych: {link}")
