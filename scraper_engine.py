import sqlite3
import requests
from bs4 import BeautifulSoup as bs


class NieruchomosciScraper:
    user_agent = {"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}

    def __init__(self, selected_city, selected_district=None, price_min=0, price_max=0, area_min=0, area_max=0, rooms_number=1, num_pages=1, db_path="database.db"):
        self.selected_city = selected_city
        self.selected_district = selected_district
        self.price_min = price_min
        self.price_max = price_max
        self.area_min = int(area_min)
        self.area_max = int(area_max)
        self.rooms_number = rooms_number
        self.num_pages = num_pages
        self.db_path = db_path

    def connect_db(self):
        """Połączenie z bazą danych."""
        conn = sqlite3.connect(self.db_path)
        return conn

    def find_city_data(self, column, city_name):
        """Znajdź dane o mieście na podstawie nazwy miejscowości."""
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {column} FROM localities WHERE miejscowosc = ?", (city_name.lower(),))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None

    @staticmethod
    def extract_price(price_temp) -> int:
        price_temp = price_temp.strip()
        if price_temp == "Zapytaj o cenę":
            return 0
        elif any(char.isdigit() for char in price_temp):
            offer_price = "".join([digit for digit in price_temp if digit.isdigit()])
            return int(offer_price)
        return 0

    def fetch_page(self, url):
        response = requests.get(url, headers=self.user_agent)
        return bs(response.text, "html.parser")

    def scrape_otodom(self):
        results = []
        service_url = "https://www.otodom.pl"
        print(f"Scrapuje {service_url}...")
        selected_city_corrected = self.find_city_data("miejscowosc2", self.selected_city)
        if not selected_city_corrected:
            print(f"Błąd: Nie znaleziono miejscowości {self.selected_city} w bazie danych.")
            return results  # Zwracamy pustą listę, jeśli miasto nie istnieje

        selected_region = self.find_city_data("powiat", self.selected_city)

        dict_rooms = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE"}

        for page in range(1, self.num_pages + 1):
            url = f"{service_url}/pl/wyniki/sprzedaz/mieszkanie/{self.selected_district.lower()}/{selected_region}/{selected_city_corrected.lower()}?distanceRadius=0&limit=72&ownerTypeSingleSelect=ALL&priceMin={self.price_min}&priceMax={self.price_max}&areaMin={self.area_min}&areaMax={self.area_max}&roomsNumber=%5B{dict_rooms[self.rooms_number]}%5D&by=DEFAULT&direction=DESC&viewType=listing&page={page}"
            soup = self.fetch_page(url)
            print(url)
            offers = soup.find_all("article", {"data-cy": "listing-item"})
            for offer in offers:
                offer_item = offer.find("section")
                offer_desc = offer.find("p", {"data-cy": "listing-item-title"}).text
                price_temp = offer_item.select("div > div > span")[-1].get_text()
                offer_price = int(self.extract_price(price_temp))
                if offer_price == 0:
                    continue
                offer_details_temp = offer_item.select("div > div > dl > dd")
                offer_area = float(offer_details_temp[1].text.split(" ")[0])
                offer_price_m2 = round(offer_price / offer_area)
                offer_link = service_url + offer.find("a", {"data-cy": "listing-item-link"})["href"]
                results.append({"web": "otodom.pl", "desc": offer_desc, "price": offer_price, "area": offer_area, "rooms": self.rooms_number, "price_m2": offer_price_m2, "link": offer_link})
        return results

    def scrape_nieruchomosci_online(self):
        results = []
        service_url = "https://www.nieruchomosci-online.pl"
        print(f"Scrapuje {service_url}...")
        selected_city_corrected = self.find_city_data("miejscowosc1", self.selected_city)
        if not selected_city_corrected:
            print(f"Błąd: Nie znaleziono miejscowości {self.selected_city} w bazie danych.")
            return results  # Zwracamy pustą listę, jeśli miasto nie istnieje

        selected_city_corrected = selected_city_corrected.replace(" ", "%20")
        for page in range(1, self.num_pages + 1):
            url = f"{service_url}/szukaj.html?3,mieszkanie,sprzedaz,,{selected_city_corrected},,,,{self.price_min}-{self.price_max},{self.area_min}-{self.area_max},,,,,,{self.rooms_number}-{self.rooms_number}&p={page}"
            # print(url)
            soup = self.fetch_page(url)

            all_sections = soup.find_all("div", {"class": "column-container column_default"})

            for section in all_sections:
                if section.find_previous("span", string="Lista ogłoszeń"):
                    offers = section.find_all("div", {"class": "tile"})
                    for offer in offers:
                        try:
                            offer_temp = offer.find("h2", {"class": "name"})
                            offer_desc = offer_temp.find("a").get_text().strip()
                            offer_link_tag = offer_temp.find("a")
                            offer_link = offer_link_tag["href"] if offer_link_tag else None
                            area_tag = offer.find("span", {"class": "area"})
                            offer_area = float(area_tag.get_text().split("\xa0")[0].replace(",", ".")) if area_tag else None

                            price_tag = offer.find("p", {"class": "title-a primary-display"})
                            if price_tag:
                                price_text = price_tag.select("span")[0].get_text()
                                offer_price = self.extract_price(price_text)
                            else:
                                continue

                            offer_price_m2 = round(offer_price / offer_area) if offer_price and offer_area else None
                            results.append(
                                {
                                    "web": "nieruchomosci-online.pl",
                                    "desc": offer_desc,
                                    "price": offer_price,
                                    "area": offer_area,
                                    "rooms": self.rooms_number,
                                    "price_m2": offer_price_m2,
                                    "link": offer_link,
                                }
                            )
                        except:
                            continue
        return results

    def scrape_gratka(self):
        results = []
        service_url = "https://gratka.pl"
        print(f"Scrapuje {service_url}...")
        selected_city_corrected = self.find_city_data("miejscowosc1", self.selected_city)
        if not selected_city_corrected:
            print(f"Błąd: Nie znaleziono miejscowości {self.selected_city} w bazie danych.")
            return results  # Zwracamy pustą listę, jeśli miasto nie istnieje
        selected_city_corrected = selected_city_corrected.replace(" ", "%20")

        for page in range(1, self.num_pages + 1):
            url = f"{service_url}/nieruchomosci/mieszkania/{selected_city_corrected}?cena-calkowita:min={self.price_min}&cena-calkowita:max={self.price_max}&powierzchnia-w-m2:min={self.area_min}&powierzchnia-w-m2:max={self.area_max}&liczba-pokoi:min={self.rooms_number}&liczba-pokoi:max={self.rooms_number}&page={page}"
            # print(url)
            soup = self.fetch_page(url)

            offers = soup.find_all("div", {"class": "card__outer"})
            for offer in offers:

                offer_link_tag = offer.find("a", href=True)
                offer_link = service_url + offer_link_tag["href"] if offer_link_tag else None
                offer_desc = offer_link_tag.get_text().strip() if offer_link_tag else "Brak opisu"

                price_tag = offer.find("div", string=lambda text: text and "zł" in text)
                if price_tag:
                    offer_price = int(price_tag.get_text().strip().replace("zł", "").replace(" ", "").replace(",", ""))
                else:
                    continue

                property_info = offer.find("div", {"class": "property-info"})
                if property_info:
                    offer_area = float(property_info.find("span").get_text().split(" ")[0].replace(",", "."))
                else:
                    continue

                offer_price_m2 = round(offer_price / offer_area)
                results.append({"web": "gratka.pl", "desc": offer_desc, "price": offer_price, "area": offer_area, "rooms": self.rooms_number, "price_m2": offer_price_m2, "link": offer_link})
        return results

    def scrape_morizon(self):
        results = []
        service_url = "https://morizon.pl"
        print(f"Scrapuje {service_url}...")
        selected_city_corrected = self.find_city_data("miejscowosc1", self.selected_city)
        if not selected_city_corrected:
            print(f"Błąd: Nie znaleziono miejscowości {self.selected_city} w bazie danych.")
            return results  # Zwracamy pustą listę, jeśli miasto nie istnieje
        selected_city_corrected = selected_city_corrected.replace(" ", "%20")

        for page in range(1, self.num_pages + 1):
            url = f"{service_url}/mieszkania/{selected_city_corrected}/?ps%5Bliving_area_from%5D={self.area_min}&ps%5Bliving_area_to%5D={self.area_max}&ps%5Bnumber_of_rooms_from%5D={self.rooms_number}&ps%5Bnumber_of_rooms_to%5D={self.rooms_number}&ps%5Bprice_from%5D={self.price_min}&ps%5Bprice_to%5D={self.price_max}&page={page}"
            # print(url)
            soup = self.fetch_page(url)

            offers = soup.find_all("div", {"class": "card__outer"})
            for offer in offers:
                offer_link = service_url + offer.select("a")[0]["href"]

                # old
                # offer_desc = offer.select("a > div > div")[1].contents[1].get_text()
                # Zaktualizowane pobieranie opisu, Pobieramy tekst z pierwszego <span>
                location_tree = offer.find("div", {"data-cy": "locationTree"})
                offer_desc = location_tree.find("span").get_text().strip().replace("\xa0", " ").replace("•", "").strip().replace("    ", ", ")

                offer_area = float(offer.find_all("div", {"class": "property-info"})[0].select("span")[0].get_text().split(" ")[0])
                # stare podejście
                # offer_price = self.extract_price(offer.select("a > div > div > div > div > span")[0].get_text())
                # nowe podejście - szukam frazy "zł", pomijamy pola "Zapytaj o cenę"
                price_tag = offer.find("div", string=lambda text: text and "zł" in text)
                if price_tag:
                    offer_price = int(price_tag.get_text().strip().replace("zł", "").replace(" ", "").replace(",", ""))
                else:
                    continue

                offer_price_m2 = round(offer_price / offer_area)
                results.append({"web": "morizon.pl", "desc": offer_desc, "price": offer_price, "area": offer_area, "rooms": self.rooms_number, "price_m2": offer_price_m2, "link": offer_link})
        return results

    def scrape_domiporta(self):
        results = []
        service_url = "https://domiporta.pl"
        print(f"Scrapuje {service_url}...")
        selected_city = self.selected_city.replace(" ", "%20")
        if not selected_city:
            print(f"Błąd: Nie znaleziono miejscowości {self.selected_city} w bazie danych.")
            return results  # Zwracamy pustą listę, jeśli miasto nie istnieje

        for page in range(1, self.num_pages + 1):
            url = f"{service_url}/mieszkanie/sprzedam?Localizations%5B0%5D.Name={selected_city}&Surface.From={self.area_min}&Surface.To={self.area_max}&Price.From={self.price_min}&Price.To={self.price_max}&Rooms.From={self.rooms_number}&Rooms.To={self.rooms_number}&PageNumber={page}"
            soup = self.fetch_page(url)

            offers = soup.find_all("div", {"class": "listing"})
            offers = offers[0].find_all("li", {"class": "grid-item grid-item--cover"})
            for offer in offers:
                offer_link = service_url + offer.select("article")[0]["data-href"]
                offer_desc = offer.find_all("span", {"class": "sneakpeak__title--inblock"})[0].get_text().replace("mieszkanie ", "")
                offer_area = float(offer.find_all("span", {"class": "sneakpeak__details_item sneakpeak__details_item--area"})[0].get_text().strip().split("\xa0")[0].replace(",", "."))
                offer_price = self.extract_price(offer.find_all("div", {"class": "sneakpeak__price"})[0].get_text().strip())
                offer_price_m2 = round(offer_price / offer_area)
                results.append({"web": "domiporta.pl", "desc": offer_desc, "price": offer_price, "area": offer_area, "rooms": self.rooms_number, "price_m2": offer_price_m2, "link": offer_link})
        return results

    def scrape(self, services):
        all_results = []
        for service in services:
            if service == "otodom.pl":
                all_results.extend(self.scrape_otodom())
            elif service == "nieruchomosci-online.pl":
                all_results.extend(self.scrape_nieruchomosci_online())
            elif service == "gratka.pl":
                all_results.extend(self.scrape_gratka())
            elif service == "domiporta.pl":
                all_results.extend(self.scrape_domiporta())
            elif service == "morizon.pl":
                all_results.extend(self.scrape_morizon())
        return all_results


## TESTY SERWISÓW ###

# selected_city = "Kraków"
# selected_district = "malopolskie"
# price_min = 300000
# price_max = 600000
# area_min = 50
# area_max = 70
# rooms_number = 2
# num_pages = 1
# db_path = "database.db"

# temp = NieruchomosciScraper(selected_city, selected_district, price_min, price_max, area_min, area_max, rooms_number, num_pages, db_path).scrape_otodom() # OK 71
# # temp = NieruchomosciScraper(selected_city, selected_district, price_min, price_max, area_min, area_max, rooms_number, num_pages, db_path).scrape_domiporta() # OK 36
# temp = NieruchomosciScraper(selected_city, selected_district, price_min, price_max, area_min, area_max, rooms_number, num_pages, db_path).scrape_nieruchomosci_online()  # OK 42
# # temp = NieruchomosciScraper(selected_city, selected_district, price_min, price_max, area_min, area_max, rooms_number, num_pages, db_path).scrape_morizon()  # OK 29
# # temp = NieruchomosciScraper(selected_city, selected_district, price_min, price_max, area_min, area_max, rooms_number, num_pages, db_path).scrape_gratka()  # OK 29


# print(len(temp))
# print("###" * 30)
# for each in temp:
#     print(each)
# print("###" * 30)
