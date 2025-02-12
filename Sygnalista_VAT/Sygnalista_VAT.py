# W tym miejscu podaj nazwę serwera z SQL Server Management Studio:
SQL_serwer = r""  



# Zaczytanie bibliotek, wykorzystywanych w programie
import os # biblioteka do obsługi ścieżek
import pandas as pd
import numpy as np  # biblioteki pandas i numpy do tabelarycznej obróbki danych i obliczeń
import csv  # biblioteka do zaczytania danych z plików typu 'csv'
import re  # biblioteka do wyszukiwania wyrażeń regularnych (regular expression - regex)
import datetime  # biblioteka do przetwarzania dat
import requests  # biblioteka do zapytań typu API
import xmltodict  # biblioteka do obsługi plików typu 'xml'
import json  # biblioteka do obsługi danych w formacie 'json'
from sqlalchemy import create_engine, text  # funkcje z biblioteki do zaczytywania danych z baz danych SQL
# poprzez zapytania
from PyQt5 import QtWidgets, QtCore, QtGui  # funkcje z biblioteki do wygenerowania interfejsu graficznego
import sys
from gui_program import Ui_mainwin  # interfejs graficzny programu 'Ui_mainwin' zapisany w pliku
# gui_program_faktura
pd.options.mode.chained_assignment = None


# przygotowanie do zaczytywania danych z bazy danych w SQL (Structured Query Language)
serwer = SQL_serwer  # nazwa serwera SQL, w którym znajdują się dane
baza = "Faktura"  # nazwa bazy danych
driver = "ODBC Driver 17 for SQL Server"  # starownik do obsługi połączenia z SQL
polaczenie = f'mssql://@{serwer}/{baza}?driver={driver}'  # połączenie z SQL (na danym serwerze, w danej bazie)
moje_querry = """select
        a.Przedsiebiorstwo, b.NIP, b.Adres, b.Kod_pocztowy, b.Miasto, 
        a.Nr_faktury, a.Data_wystawienia, 
        a.Sposob_platnosci, a.Nr_konta, c.Bank, c.Oddzial_banku, 
        a.Metoda_kasowa, a.Samofakturowanie, a.Odwrotne_obciazenie, a.Podzielona_platnosc,
        a.Nabywca, d.Przedsiebiorstwo as Przedsiebiorstwo_nabywcy, a.NIP_nabywcy, 
        d.Adres as Adres_nabywcy, d.Kod_pocztowy as Kod_pocztowy_nabywcy, d.Miasto as Miasto_nabywcy,
        e.Towar_lub_usluga, e.Ilosc_towaru, e.Cena_jednostkowa, e.Stawka_podatku
    from dbo.faktury_dane as a
        inner join dbo.przedsiebiorstwa as b on a.Przedsiebiorstwo = b.Przedsiebiorstwo
        left join dbo.konta as c on a.Nr_konta = c.Nr_konta
        left join dbo.przedsiebiorstwa as d on a.NIP_nabywcy = d.NIP
        inner join dbo.faktury_pozycje as e on a.Nr_faktury = e.Nr_faktury;"""  # zpytanie
engine = create_engine(polaczenie)  # silnik będący podstawą do połączenia z SQL
engine_link = engine.connect()  # połączenie z silnikiem

# zaczytanie danych
baza_danych = pd.read_sql_query(sql=text(moje_querry), con=engine_link)

# korekta danych pobranych z SQL, zamiana wartości 'None' na 'NA' oraz zmiana typu odpowiednich danych na numeryczne
baza_danych.replace({None: np.nan}, inplace=True)
baza_danych[["Ilosc_towaru", "Cena_jednostkowa"]] = baza_danych[["Ilosc_towaru",
                                                                 "Cena_jednostkowa"]].apply(pd.to_numeric)

# pliki z towarami dla poszczególnych stawek są w otwierane w pętli, a następnie nazwy towarów zapisane są do list
# w słowniku z odpowiednimi kluczami

sciezka = os.getcwd()
sciezka_dane = sciezka + "\\dane"
os.chdir(sciezka_dane)
listy_towarow = ["towary_8.csv", "towary_5.csv", "towary_0.csv", "towary_zw.csv"]
lista_kat_towarow = ["0.08", "0.05", "0.00", "zw."]
stawki_towarow = {}
towary_nie_23 = []
for lista, kat in zip(listy_towarow, lista_kat_towarow):
    f1 = open(lista, "r", encoding="utf-8")
    towary = list(csv.reader(f1, delimiter=";"))[0]
    stawki_towarow[kat] = towary
    towary_nie_23 += towary
    f1.close()

# zaczytanie listy towarów wrażliwych (podlegających mechanizmowi podzielonej płatności) analogicznie do powyższych
f2 = open("towary_podzielona.csv", "r", encoding="utf-8")
towary_podzielona = list(csv.reader(f2, delimiter=";"))[0]
f2.close()

os.chdir(sciezka)


# funkcja do aktualizacji bazy danych o bankach na podstawie pliku xml ze strony internetowej Narodowego Banku Polskiego
# oraz zapisanie danych jako baza SQL i zaczytanie danych


def aktualizacja_banki(decyzja):
    proba = 0
    if decyzja == "T":
        # trzykrotna próba pobrania danych o bankach
        while proba < 3:
            try: 
                # pobranie danych w formacie xml również w Pythonie, które następnie zostają przenoszone do słownika
                url = r"https://ewib.nbp.pl/plewiba?dokNazwa=plewiba.xml"
                response = requests.get(url, allow_redirects=True)
                banki_dane = xmltodict.parse(response.content)
                # pominięcie pierwszych dwóch niepotrzebnych zagnieżdżeń
                banki_dane = banki_dane["Instytucje"]["Instytucja"]
                # utworzenie pustych list, do których dodane będą dane banków (nazwa, oddział i odpowiedni nr oddziału)
                # dalej z list utworzona zostanie ramka danych
                lista_bankow = []
                lista_nr_bankow = []
                lista_oddzialow = []
                # wyciągnięcie danych dla ponad 600 banków z wykorzystaniem pętli
                for bank in range(len(banki_dane)):
                    try:
                        zm1 = banki_dane[bank]["Jednostka"][0]  # jeden ze sposobów przechowywania danych w pliku xml,
                        # jest to test czy bank ma informacje przechowywane w ten sposób (czy ma więcej niż jedną jednostkę)
                        for oddzial in range(len(banki_dane[bank]["Jednostka"])):  # jeśli tak następuje odwołanie pętlą do
                            # każdego oddziału banku
                            try:
                                zm2 = banki_dane[bank]["Jednostka"][oddzial]["NumerRozliczeniowy"][0]  # oddziały mogą mieć
                                # kilka numerów (czy jest ich więcej niż jeden), jeśli tak następuje odwołanie pętlą do każdego
                                for nr_roz in range(len(banki_dane[bank]["Jednostka"][oddzial]["NumerRozliczeniowy"])):
                                    # wyciągnięta zostaje nazwa banku i dodana do listy
                                    lista_bankow.append(banki_dane[bank]["NazwaInstytucji"])
                                    # wyciągnięty zostaje nr oddziału i dodany do listy
                                    lista_nr_bankow.append(banki_dane[bank]["Jednostka"][oddzial]["NumerRozliczeniowy"]
                                                           [nr_roz]["NrRozliczeniowy"])
                                    # wyciągnięta zostaje nazwa oddziału i dodana do listy
                                    lista_oddzialow.append(banki_dane[bank]["Jednostka"][oddzial]["NumerRozliczeniowy"]
                                                           [nr_roz]["NazwaNumeru"])
                            # jeżeli oddział posiada tylko jeden numer wykorzystany jest poniższy format przechowywania danych
                            except KeyError:
                                lista_bankow.append(banki_dane[bank]["NazwaInstytucji"])
                                try:  # sprawdzenie, czy dla danego oddziału występują dane dot. nazwy i numeru
                                    lista_nr_bankow.append(banki_dane[bank]["Jednostka"][oddzial]["NumerRozliczeniowy"]
                                                           ["NrRozliczeniowy"])
                                    lista_oddzialow.append(banki_dane[bank]["Jednostka"][oddzial]["NumerRozliczeniowy"]
                                                           ["NazwaNumeru"])
                                except KeyError:  # jeśli nie, te dane zapisane zostaną jako braki (0)
                                    lista_nr_bankow.append(0)
                                    lista_oddzialow.append(0)
                    # jeżeli bank posiada tylko jedną jednostkę wykorzystywany jest o poniższy format przechowywania danych
                    except KeyError:
                        try:
                            # sprawdzenie, czy ta jednostka banku posiada kilka numerów
                            zm3 = banki_dane[bank]["Jednostka"]["NumerRozliczeniowy"][0]
                            # jeśli tak pętlą wyciągnięte zostają dane
                            for nr_roz in range(len(banki_dane[bank]["Jednostka"]["NumerRozliczeniowy"])):
                                lista_bankow.append(banki_dane[bank]["NazwaInstytucji"])
                                lista_nr_bankow.append(banki_dane[bank]["Jednostka"]["NumerRozliczeniowy"][nr_roz]
                                                       ["NrRozliczeniowy"])
                                lista_oddzialow.append(banki_dane[bank]["Jednostka"]["NumerRozliczeniowy"][nr_roz]
                                                       ["NazwaNumeru"])
                        except KeyError:  # jeżeli nie dane zostają wyciągnięte dla tylko jednego numeru
                            try:
                                lista_bankow.append(banki_dane[bank]["NazwaInstytucji"])
                                lista_nr_bankow.append(banki_dane[bank]["Jednostka"]["NumerRozliczeniowy"]["NrRozliczeniowy"])
                                lista_oddzialow.append(banki_dane[bank]["Jednostka"]["NumerRozliczeniowy"]["NazwaNumeru"])
                            except KeyError:  # jeżeli jednostka nie posiada żadnego numeru dane zostają zapisane jako braki (0)
                                lista_nr_bankow.append(0)
                                lista_oddzialow.append(0)
                # zebranie danych do ramki danych
                global baza_banki
                lista_nr_bankow.pop(len(lista_nr_bankow)-1)
                baza_banki = pd.DataFrame({"Bank": lista_bankow, "Oddzial_banku": lista_oddzialow, "Nr_banku": lista_nr_bankow})
                # sprawdzenie, które pozycje w ramce mają braki danych (0)
                indeksy = np.where(baza_banki["Nr_banku"] == 0)[0]
                # usunięcie tych pozycje z ramki, jednoczesny reset indeksowania dla estetyki
                baza_banki = baza_banki.drop(indeksy, axis=0).reset_index(drop=True)
                baza_banki.to_sql(name='banki', con=engine, if_exists='replace', index=False, method=None)
                proba=3
                baza_banki.to_csv("bdv.csv", index=False)
            except requests.exceptions.RequestException:
                proba += 1
                baza_banki = pd.read_sql(sql=text("select * from dbo.banki"), con=engine_link)
            except ValueError:
                proba += 1
                baza_banki = pd.read_sql(sql=text("select * from dbo.banki"), con=engine_link)
    else:
        baza_banki = pd.read_sql(sql=text("select * from dbo.banki"), con=engine_link)
        return



# ------- funkcje sprawdzające elementy faktury -------

# listy, w których spisane zostaną elementy poprawne i błędne faktury podczaj jej sprawdzania
lista_poprawne = []
lista_bledne = []


# funkcja sprawdzająca, czy występują braki danych liczbowych, które uniemożliwiłyby policzenie wartości brutto
def check_braki_liczby(tabelka):
    if pd.isna(tabelka).any(axis=None):
        lista_bledne.append("W bazie, dla wybranej faktury, wystąpiły braki danych liczbowych.")
        global ilosc_bledow
        ilosc_bledow += 1
    else:
        lista_poprawne.append("Nie wystąpiły braki danych liczbowych.")
    return


# funkcja sprawdzająca, czy występują braki danych o wybranej firmie, które uniemożliwibyły sprawdzenie poprawności jej
# danych
def check_braki_firma(tabelka):
    if pd.isna(tabelka).any(axis=None):
        lista_bledne.append("W bazie, dla wybranej faktury, wystąpiły braki danych dla wybranego przedsiębiorstwa.")
    else:
        lista_poprawne.append("Nie wystąpiły braki danych dla wybranego przedsiębiorstwa.")
    return


# funkcja sprawdzająca, czy występują braki danych o fakturze, które uniemożliwiłyby sprawdzenie jej elementów typu:
# numer, rodzaj, data itp.
def check_braki_faktura(tabelka):
    if pd.isna(tabelka).any(axis=None):
        lista_bledne.append("W bazie, dla wybranej faktury, wystąpiły braki danych o fakturze.")
    else:
        lista_poprawne.append("Nie wystąpiły braki danych o wybranej fakturze.")
    return


# funkcja sprawdzająca, czy wystąpiły braki danych o odbiorcy lub banku, które uniemożliwiłyby sprawdzenia informacji
# o nich
def check_braki_dane(tabelka, zmienna):
    if zmienna == "osoba_prawna":
        if pd.isna(tabelka).any(axis=None):
            lista_bledne.append("W bazie, dla wybranej faktury, wystąpiły braki danych o nabywcy.")
        else:
            lista_poprawne.append("Nie wystąpiły braki danych o nabywcy.")
    pass
    if zmienna == "przelew":
        if pd.isna(tabelka).any(axis=None):
            lista_bledne.append("W bazie, dla wybranej faktury, wystąpiły braki danych o banku.")
        else:
            lista_poprawne.append("Nie wystąpiły braki danych o banku.")
    return


# funkcja sprawdzająca, czy wartości cen towarów są dodatnie
def check_ujemne_c(ceny):
    if any(ceny < 0):
        lista_bledne.append(f"W bazie, dla wybranej faktury, wystąpiły ujemne wartości wśród cen jednostkowych: "
                            f"{list(ceny)}")
        global ilosc_bledow
        ilosc_bledow += 1
    else:
        lista_poprawne.append("Wartości cen jednostkowych towarów są nieujemne.")
    return


# funkcja sprawdzająca, czy wartości ilości towarów są dodatnie
def check_ujemne_i(ilosci):
    if any(ilosci < 0):
        lista_bledne.append(f"W bazie, dla wybranej faktury, wystąpiły ujemne wartości wśród ilości towarów: "
                            f"{list(ilosci)}")
        global ilosc_bledow
        ilosc_bledow += 1
    else:
        lista_poprawne.append("Wartości ilości towarów są nieujemne.")
    return


# funkcja sprawdzająca, czy numer nip ma poprawny format, wykorzystując wyrażenia regularne
def check_nip_format(nip_b, kogo):
    if len(re.findall(r"\b\d{3}-\d{2}-\d{2}-\d{3}\b|\b\d{3} \d{2} \d{2} \d{3}\b|\b\d{10}\b", nip_b)) != 1:
        lista_bledne.append(f"W bazie danych, dla wybranej faktury, podano błędny format NIP {kogo}: {nip_b}. "
                            f"Dostępne formaty: xxx-xx-xx-xxx, xxx xx xx xxx, xxxxxxxxxx.")
    else:
        lista_poprawne.append(f"Format NIP {kogo} jest poprawny.")
    return


# funkcja sprawdzająca, czy nip ma poprawną cyfrę kontrolną, wykorzystując odpowiednią regułę wyliczania tej cyfry
# (reszta z dzielenia przez 11 sumy iloczynów 9 pierwszych cyfr i odpowiednich wag)
def check_nip(nip_b, kogo):
    nip_b = nip_b.replace(" ", "").replace("-", "")
    cyfry = [int(cyfra) for cyfra in nip_b]
    wagi = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    if sum(cyfra * waga for cyfra, waga in zip(cyfry, wagi)) % 11 == cyfry[9]:
        lista_poprawne.append(f"Poprawna cyfra kontrolna w numerze NIP {kogo}.")
    else:
        lista_bledne.append(f"Niepoprawna cyfra kontrolna w numerze NIP {kogo}: {nip_b}.")
    return


# funkcja sprawdzająca, czy kod pocztowy ma poprawny format, wykorzystując wyrażenia regularne
def check_kod_format(kod, kogo):
    if re.fullmatch(r"\b\d{2}-\d{3}\b", kod) is None:
        lista_bledne.append(f"W bazie danych, dla wybranej faktury, podano błędny format kodu pocztowego {kogo}: {kod}. "
                            f"Dostępny format: xx-xxx.")
    else:
        lista_poprawne.append(f"Format kodu pocztowego {kogo} jest poprawny.")
    return


# funkcja sprawdzająca czy podany nip istnieje, czy jest obecny na białej liście podatników VAT, łączy się poprzez API
# ze stroną Ministerstwa Finansów i pobiera dane o firmie o danym nip o ile takowa istnieje i usługa jest dostępna
def check_istnienie_nip(nip_c, kogo):
    nip_c = int(nip_c.replace(" ", "").replace("-", ""))
    api_1 = fr"https://wl-api.mf.gov.pl/api/search/nip/{nip_c}"
    strona = requests.get(api_1, params={"date": str(datetime.date.today())})
    if strona.status_code == 500:
        lista_bledne.append(f"Usługa API jest niedostępna, nie można sprawdzić poprawności danych firmy {kogo} dla "
                            f"wybranej faktury.")
    elif strona.status_code == 400:
        lista_bledne.append(f"W bazie danych, dla wybranej faktury, występuje nieistniejący NIP {kogo}.")
    elif strona.status_code == 429:
        lista_bledne.append(f"Wykorzystano limit sprawdzeń API, nie można sprawdzić poprawności danych firmy {kogo} dla"
                            f" wybranej faktury, wróć jutro.")
    else:
        dane = strona.text
        global dane_slownik
        dane_slownik = json.loads(dane)
        lista_poprawne.append("Usługa API jest dostępna.")
    return


# funkcja sprawdzająca, czy nazwa firmy w bazie danych przypisana do faktury jest zgodna z informacjami ze strony MF
def check_nazwa(nazwa, kogo):
    try:
        global nazwa_api
        nazwa_api = dane_slownik['result']['subject']['name']
        if nazwa.upper() == nazwa_api:
            lista_poprawne.append(f"Zgadza się nazwa {kogo}.")
        else:
            lista_bledne.append(f"Dla wybranej faktury nie zgadza się nazwa {kogo}. Podana: {nazwa.upper()}, "
                                f"poprawna: {nazwa_api}.")
    except (TypeError, KeyError):
        lista_bledne.append(f"Dla wybranej faktury podany NIP {kogo} nie figuruje w rejestrze VAT.")
        pass
    
    except NameError:
        lista_bledne.append(f"Dla wybranej faktury podany NIP {kogo} ma nieprawidłowy format lub cyfrę kontrolną, "
                            f"nie figuruje w rejestrze VAT.")
        pass
    return


# funkcja sprawdzająca, czy adres firmy w bazie danych przypisany do faktury jest zgodny z informacjami ze strony MF
def check_adres(adres, kogo):
    try:
        global adres_api
        adres_api = dane_slownik['result']['subject']['workingAddress']
        global adres_api_prim
        adres_api_prim = str(re.findall(".+,", adres_api)[0]).replace(",", "")
        if adres.upper() == adres_api_prim:
            lista_poprawne.append(f"Zgadza się adres firmy {kogo}.")
        else:
            lista_bledne.append(f"Dla wybranej faktury nie zgadza się adres {kogo}. "
                                f"Podany: {adres.upper()}, poprawny: {adres_api_prim}.")
    except (NameError, TypeError, KeyError):
        pass
    return


# funkcja sprawdzająca, czy kod pocztowy firmy w bazie danych przypisany do faktury jest zgodny z inf. ze strony MF
def check_kod(kod, kogo):
    try:
        global kod_api
        kod_api = dane_slownik['result']['subject']['workingAddress']
        global kod_api_prim
        kod_api_prim = str(re.findall(r'\d{2}-\d{3}', kod_api)[0])
        if kod == kod_api_prim:
            lista_poprawne.append(f"Zgadza się kod pocztowy {kogo}.")
        else:
            lista_bledne.append(f"Dla wybranej faktury nie zgadza się kod pocztowy {kogo}. "
                                f"Podany: {kod}, poprawny: {kod_api_prim}.")
    except (NameError, TypeError, KeyError):
        pass
    return


# funkcja sprawdzająca, czy miasto firmy w bazie danych przypisane do faktury jest zgodne z informacjami ze strony MF
def check_miasto(miasto, kogo):
    try:
        global miasto_api
        miasto_api = dane_slownik['result']['subject']['workingAddress']
        global miasto_api_prim
        miasto_api_prim = str(re.findall(r'\d{2}-\d{3}.+', miasto_api)[0])[7:]
        if miasto.upper() == miasto_api_prim:
            lista_poprawne.append(f"Zgadza się miasto {kogo}.")
        else:
            lista_bledne.append(f"Dla wybranej faktury nie zgadza się miasto {kogo}. Podane: {miasto.upper()}, "
                                f"poprawne: {miasto_api_prim}")
    except (NameError, TypeError, KeyError):
        pass
    return


# funkcja sprawdzająca, czy podany numer faktury ma poprawny format (zgodnie z zasadami opisanymi w ustawie o VAT)
def check_nr_faktury_format(nr_faktury):
    if len(re.findall(r"\b\d{1,4}/\d{4}\b|\b\d{1,4}/\d{1,2}/\d{4}\b|\b\d{1,4}/[A-Ż]{1,3}/\d{4}\b|"
                      r"\b\d{1,4}/\d{1,2}/[A-Ż]{1,3}/\d{4}\b", nr_faktury)) != 1:
        lista_bledne.append(f"W bazie danych, dla wybranej faktury, podano błędny format numery faktury: {nr_faktury} "
                            f"Dostępne formaty: id(kolejne numery)/rok, id/miesiąc/rok, id/nr wydziału/rok, "
                            f"id/inicjały pracownika/rok, id/oznaczenie literowe kontrahenta/rok, "
                            f"id/miesiąc/inicjały pracownika/rok")
    else:
        lista_poprawne.append("Format numeru faktury jest poprawny.")
    return


# funkcja sprawdzająca, czy data przypisana do wybranej faktury jest poprawna, wykorzystując do tego bibliotekę datetime
def check_data(data):
    global dzien, miesiac, rok
    dzien = int(data[0:2])
    miesiac = int(data[3:5])
    rok = int(data[6:10])
    while True:
        try:
            data2 = datetime.datetime(year=rok, month=miesiac, day=dzien)
            lista_poprawne.append("Data jest poprawna.")
            global zla_data
            zla_data = False
            break
        except ValueError:
            zla_data = True
            lista_bledne.append(f'W bazie danych, dla wybranej faktury, podano błędą datę: {data}. Dostępny format: '
                                f'ddmmrrrr (separatory ".", "-", "/"), dni z przedziału 01-31, miesiące z przedziału '
                                f'01-12')
            break
    return


# funkcja sprawdzająca, czy numer konta przypisany do faktury ma poprawny format
def check_nr_konta_format(nr_konta):
    if re.fullmatch(r"\b\d{2} \d{4} \d{4} \d{4} \d{4} \d{4} \d{4}\b", nr_konta) is None:
        lista_bledne.append(f"W bazie danych, dla wybranej faktury, podano błędny format numeru konta: {nr_konta}."
                            "Dostępny format: xx xxxx xxxx xxxx xxxx xxxx xxxx.")
    else:
        lista_poprawne.append("Format numeru konta jest poprawny.")
    return


# funkcja sprawdzająca, czy numer konta ma poprawne cyfry kontrolne, wykorzystując do tego odpowiednią formułę
# (reszta z dzielenia przez 97 odpowiedniego przekształcenia numeru konta powinna wynosić 1)
def check_cyfry_kontrolne_nr_konta(nr_konta_b):
    nr_konta_b = nr_konta_b.replace(" ", "")
    nr_konta_b2 = nr_konta_b[2:26] + "2521" + nr_konta_b[0:2]
    if int(nr_konta_b2) % 97 == 1:
        lista_poprawne.append("Cyfra kontrolna w numerze konta jest poprawna.")
    else:
        lista_bledne.append(f"Nie zgadza się cyfra kontrolna w numerze konta: {nr_konta_b}.")
    return


# funkcja sprawdzająca, czy bank przypisany do numeru konta istnieje, wykorzystując do tego bazę pobraną ze strony NBP
def check_istnienie_bank(nr_konta):
    try:
        indeks_banku = np.where(baza_banki["Nr_banku"] == nr_konta)[0][0]
        lista_poprawne.append("Istnieje bank z takim numerem")
    except IndexError:
        lista_bledne.append(f"Dla wybranej faktury nie istnieje bank o takim numerze identyfikacyjnym: {nr_konta[0:4]} "
                            f"{nr_konta[4:8]}")


# funkcja sprawdzająca, czy nazwa banku przypisana do numeru konta jest obecna w bazie pobranej ze strony NBP
def check_bank(nr_konta, bank):
    try:
        indeks_banku = np.where(baza_banki["Nr_banku"] == nr_konta)[0][0]
        bank_w_bazie = str(baza_banki.at[indeks_banku, "Bank"])
        if bank_w_bazie == bank:
            lista_poprawne.append("Podany bank jest poprawny.")
        else:
            lista_bledne.append(f"W bazie danych, dla wybranej faktury, podano błędny bank. Podany: {bank}, poprawny: "
                                f"{bank_w_bazie}")
    except IndexError:
        pass


# funkcja sprawdzająca, czy oddział banku przypisany do numeru konta jest obecny w bazie pobranej ze strony NBP
def check_oddzial_banku(nr_konta, oddzial):
    try:
        indeks_banku = np.where(baza_banki["Nr_banku"] == nr_konta)[0][0]
        oddzial_w_bazie = str(baza_banki.at[indeks_banku, "Oddzial_banku"])
        if oddzial_w_bazie == oddzial:
            lista_poprawne.append("Podany oddział banku jest poprawny.")
        else:
            lista_bledne.append(f"W bazie danych, dla wybranej faktury, podano błędny oddział banku. Podany: {oddzial},"
                  f" poprawny: {oddzial_w_bazie}.")
    except IndexError:
        pass


# dostępne stawki podatku VAT
lista_stawki = ["0.23", "0.08", "0.05", "0.00", "zw."]
slownik_stawki = {"0.23": "23%", "0.08": "8%", "0.05": "5%", "0.00": "0%", "zw.": "zw."}

# funkcja sprawdzająca, czy stawki VAT przypisane do faktury są poprawne
def check_stawki(stawka):
    if any(~stawka.isin(lista_stawki)):
        lista_bledne.append(f"Dla wybranej faktury nie zgadzają się stawki podatku. Dostępne stawki: {lista_stawki}, "
                            f"podane stawki: {list(stawka)}")
        global ilosc_bledow
        ilosc_bledow += 1
    else:
        lista_poprawne.append("Stawki podatku są poprawne.")
    return


# funkcja sprawdzająca, czy stawki VAT przypisane do faktury są poprawne pod względem przypisania ich do towarów/usług
def check_przypisanie_stawek(towary, stawki):
    for pozycja in range(0, len(towary)):
        if pd.isna(towary[pozycja]):
            lista_bledne.append(f"Brak nazwy dla towaru nr {pozycja + 1} na fakturze.")
        elif stawki[pozycja] not in lista_stawki:
            lista_bledne.append(f"Błędna stawka dla towaru nr {pozycja + 1} na fakturze: "
                  f"{str(int(float(stawki[pozycja])*100))+'%' if stawki[pozycja] != 'zw.' else stawki[pozycja]}"
                  f" dla towaru/usługi: {towary[pozycja]}.")
        else:
            if stawki[pozycja] != "0.23":
                if towary[pozycja] in stawki_towarow[stawki[pozycja]]:
                    lista_poprawne.append(f"Poprawne przypisanie stawki "
                        f"{str(int(float(stawki[pozycja])*100))+'%' if stawki[pozycja] != 'zw.' else stawki[pozycja]}"
                        f" do towaru/usługi: {towary[pozycja]}.")
                else:
                    lista_bledne.append(f"Błędne przypisanie stawki "
                        f"{str(int(float(stawki[pozycja])*100))+'%' if stawki[pozycja] != 'zw.' else stawki[pozycja]}"
                        f" do towaru/usługi: {towary[pozycja]}.")
            else:
                if towary[pozycja] in towary_nie_23:
                    lista_bledne.append(f"Do towaru, dla którego stawka podatku wynosi 23% przypisano błędną stawkę: "
                        f"{str(int(float(stawki[pozycja])*100))+'%' if stawki[pozycja] != 'zw.' else stawki[pozycja]}.")
                else:
                    lista_poprawne.append(f"Poprawne przypisanie stawki 23% do towaru/usługi: {towary[pozycja]}.")


# funkcja sprawdzająca, czy na faktura podlega mechanizmowi podzielonej płatności (zawiera towary wrażliwe o wartości
# co najmniej 15 000 PLN netto
def check_podzielona(brutto, produkty, podzielona):
    if (brutto >= 15000) and (any(produkty.isin(towary_podzielona))):
        if podzielona == "tak":
            lista_poprawne.append("Do wybranej faktury poprawnie zastosowano mechanizm podzielonej płatności.")
        else:
            lista_bledne.append("Do wybranej faktury należy zastosować mechanizm podzielonej płatności, dane wskazują "
                                "na jego brak.")
    else:
        if podzielona == "nie":
            lista_poprawne.append("Do wybranej faktury poprawnie nie zastosowano mechanizmu podzielonej płatności.")
        else:
            lista_bledne.append("Do wybranej faktury nie należy stosować mechanizmu podzielonej płatności, dane "
                                "wskazują na jego występowanie.")


# funkcja sprawdzająca, czy faktura podlega mechanizmowi odwrotnego obciążenia, wkorzystując informacje z bazy danych
# oraz informacje o terminie faktury (według ustawy o VAT mechanizmu nie stosuje się od 2019 roku)
def check_odwrotne_obciazenie(warunek):
    if zla_data:
        pass
    elif datetime.datetime(year=rok, month=miesiac, day=dzien) > datetime.datetime(year=2019, month=11, day=1):
        if warunek == "tak":
            lista_bledne.append('Na fakturze nie powinien znajdować się napis "Odwrotne obciążenie".')
        else:
            lista_poprawne.append('Na fakturze poprawnie nie znajduje się napis "Odwrotne obciążenie".')
    else:
        if warunek == "tak":
            lista_poprawne.append('Na fakturze poprawnie znajduje się napis "Odwrotne obciążenie".')
        else:
            lista_bledne.append('Na fakturze powinien znajdować się napis "Odwrotne obciążenie".')


# słowniki zawierające przekształcenia odpowiednich liczb na słowa - w celu wyrażenia kwoty do zapłaty słownie
jednosci = {"0": "", "1": "jeden ", "2": "dwa ", "3": "trzy ", "4": "cztery ", "5": "pięć ", "6": "sześć ",
            "7": "siedem ", "8": "osiem ", "9": "dziewieć "}
nascie = {"10": "dziesięć ", "11": "jedenaście ", "12": "dwanaście ", "13": "trzynaście ", "14": "czternaście ", "15":
          "piętnaście ", "16": "szesnaście ", "17": "siedemnaście ", "18": "osiemnaście ", "19": "dziewiętnaście "}
dziesiatki = {"0": "", "2": "dwadzieścia ", "3": "trzydzieści ", "4": "czterdzieści ", "5": "pięćdziesiąt ",
              "6": "sześćdziesiąt ", "7": "siedemdziesiąt ", "8": "osiemdziesiąt ", "9": "dziewiećdziesiąt "}
setki = {"0": "", "1": "sto ", "2": "dwieście ", "3": "trzysta ", "4": "czterysta ", "5": "pięćset ", "6": "sześćset ",
         "7": "siedemset ", "8": "osiemset ", "9": "dziewiećset "}


# ------- GUI  -------

# dodatkowe okno pojawiające się w momencie, gdy użytkownik nie wybierze żadnej firmy lub faktury
class Ui_okno_blad(object):
    def setupUi(self, okno_blad):
        okno_blad.setObjectName("okno_blad")
        okno_blad.resize(400, 150)
        okno_blad.setMinimumSize(QtCore.QSize(400, 150))
        okno_blad.setMaximumSize(QtCore.QSize(400, 150))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(248, 245, 205))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(248, 245, 205))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(248, 245, 205))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(248, 245, 205))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        okno_blad.setPalette(palette)
        font = QtGui.QFont()
        font.setFamily("Georgia")
        font.setPointSize(12)
        okno_blad.setFont(font)
        icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxCritical)
        okno_blad.setWindowIcon(icon)
        self.blad = QtWidgets.QWidget(okno_blad)
        self.blad.setObjectName("blad")
        self.komunikat = QtWidgets.QLabel(self.blad)
        self.komunikat.setGeometry(QtCore.QRect(50, 30, 300, 90))
        self.komunikat.setWordWrap(True)
        self.komunikat.setObjectName("komunikat")
        okno_blad.setCentralWidget(self.blad)

        self.retranslateUi(okno_blad)
        QtCore.QMetaObject.connectSlotsByName(okno_blad)

    def retranslateUi(self, okno_blad):
        _translate = QtCore.QCoreApplication.translate
        okno_blad.setWindowTitle(_translate("okno_blad", "Błąd"))
        self.komunikat.setText(_translate("okno_blad", "Nie można przejść do kolejnego etapu, należy wybrać co ma zostać sprawdzone!"))


# główne okno - interfejs graficzny programu
class Sygnalista(object):
    def __init__(self):
        self.main_win = QtWidgets.QMainWindow()  # dodanie okna
        self.ui = Ui_mainwin()  # nadanie oknu wyglądu pobranemu na początku
        self.ui.setupUi(self.main_win)

        self.ui.okna_zmienne.setCurrentWidget(self.ui.witaj)  # przedstawienie użytkownikowi powitalnego ekranu programu

        self.ui.przycisk_start.clicked.connect(self.do_banki)  # przejście do ekranu z aktualizacją bazy danych banków
        # gdy użytkownik kliknie przycisk start

        lista_firm_str = baza_danych["Przedsiebiorstwo"].unique()  # lista dostępnych firm z bazie, dla których
        # użytkownik może sprawdzić faktury
        self.ui.lista_firm.addItems(lista_firm_str)  # wprowadzenie firm na widget listy w interfejsie

        self.ui.przycisk_tak.clicked.connect(self.do_firmy_t)  # przejście do ekranu z wyborem firm z pobraniem
        # aktualizacji bazy danych banków, gdy użytkownik kliknie przycisk tak na ekranie z aktualizacją bazy
        self.ui.przycisk_nie.clicked.connect(self.do_firmy_n)  # przejście do ekranu z wyborem firm bez pobrania
        # aktualizacji bazy danych banków, gdy użytkownik kliknie przycisk nie na ekranie z aktualizacją bazy
        self.ui.przycisk_dalej_firmy.clicked.connect(self.do_faktury)  # przejście do ekranu z wyborem faktur, gdy
        # użytkownik wybierze firmę i kliknie przycisk dalej
        self.ui.przycisk_dalej_faktury.clicked.connect(self.do_wyniki)  # przejście do ekranu z widgetami list
        # poprawnych i błędnych elementów faktury, gdy użykownik wybierze fakturę i kliknie przycisk dalej
        self.ui.przycisk_powrot_faktury.clicked.connect(self.do_firmy_n)  # powrót do ekranu z wyborem firm, gdy
        # użytkownik kliknie przycisk powrotu na ekranie z wyborem faktur
        self.ui.przycisk_dalej_wyniki.clicked.connect(self.do_faktura)  # przejście do ekranu z wydrukiem faktury, gdy
        # użytkownik kliknie przycisk dalej
        self.ui.przycisk_powrot_wyniki.clicked.connect(self.do_faktury)  # powrót do ekranu z wyborem faktur, gdy
        # użytkownik kliknie przycisk powrotu na ekranie z widgetami list poprawnych i blednych el. faktury
        self.ui.przycisk_powrot_faktura.clicked.connect(self.do_wyniki_bez_akt)  # powrót do ekranu z widgetami list
        # poprawnych i blednych elementow, gdy uzytkownik kliknie przycisk powrotu na ekanie z wydrukiem faktury

    # funkcja przejścia do ekranu z aktualizacją bazy danych banków
    def do_banki(self):
        self.ui.okna_zmienne.setCurrentWidget(self.ui.bd_bankow)

    # funkcja przejścia do ekranu z listą firm do wyboru po aktualizacji bazy danych banków
    def do_firmy_t(self):
        aktualizacja_banki("T")
        self.ui.okna_zmienne.setCurrentWidget(self.ui.wybor_firma)

    # funkcja przejścia do ekranu z listą firm do wyboru bez aktualizacji bazy danych banków
    def do_firmy_n(self):
        aktualizacja_banki("N")
        self.ui.okna_zmienne.setCurrentWidget(self.ui.wybor_firma)

    # funkcja przejścia do ekranu z listą faktur
    def do_faktury(self):
        if self.ui.lista_firm.currentItem() is not None:  # gdy wybrana zostaje firma
            wybrana_firma = self.ui.lista_firm.currentItem().text()  # pobierana jest jej nazwa
            global nowa_baza0
            nowa_baza0 = baza_danych[baza_danych.Przedsiebiorstwo == wybrana_firma]  # i filtrowana jest baza danych by
            # zawierała wyłącznie faktury przypisane do firmy
            lista_faktur_str = nowa_baza0["Nr_faktury"].unique()  # powstaje lista faktur
            self.ui.lista_faktur.clear()  # która pokazywana jest na widget'cie (który wcześniej został oczyszczony)
            self.ui.lista_faktur.addItems(lista_faktur_str)
            self.ui.okna_zmienne.setCurrentWidget(self.ui.wybor_faktura)  # po czym następuje przejście do ekranu z
            # listą faktur
        else:
            self.okno_blad = QtWidgets.QMainWindow()  # jeżeli nie wybrana zostaje żadna faktura pojawia się okno
            # z bledem
            self.ui_blad = Ui_okno_blad()
            self.ui_blad.setupUi(self.okno_blad)
            self.okno_blad.show()

    # funkcja przejścia do ekranu z widgetami list poprawnych i blednych elementow faktury
    def do_wyniki(self):
        if self.ui.lista_faktur.currentItem() is not None:  # gdy użytkownik wybierze fakturę
            wybrany_numer = self.ui.lista_faktur.currentItem().text()  # pobierany jest jej numer
            global nowa_baza
            nowa_baza = nowa_baza0[nowa_baza0.Nr_faktury == wybrany_numer]  # i filtrowana jest baza danych by zawierała
            # elementu wyłącznie elementy tej faktury
            nowa_baza = nowa_baza.reset_index(drop=True)
            self.ui.lista_poprawne_ui.clear()  # widgety list poprawnych i blednych elementow faktury są oczyszczane
            # z poprzednich sprawdzań
            global lista_poprawne
            lista_poprawne = []  # listy, w których zapisywane są wyniki (podczas sprawdzania faktury) są oczyszczane
            # z poprzednich sprawdzań
            self.ui.lista_bledne_ui.clear()
            global lista_bledne
            lista_bledne = []
            global ilosc_bledow
            ilosc_bledow = 0  # zmienna, która zwiększa się, gdy wystąpią błędy uniemożliwiające policzenie kwot brutto
            # następuje sprawdzenie faktury, wykorzystując przedstawione wcześniej funkcje, wprowadzając do nich
            # odpowiednie dane
            check_braki_liczby(nowa_baza[["Ilosc_towaru", "Cena_jednostkowa", "Stawka_podatku"]])
            check_braki_firma(nowa_baza[["Przedsiebiorstwo", "NIP", "Adres", "Kod_pocztowy", "Miasto"]])
            check_braki_faktura(nowa_baza[["Nr_faktury", "Data_wystawienia", "Sposob_platnosci", "Metoda_kasowa",
                                           "Samofakturowanie", "Odwrotne_obciazenie", "Podzielona_platnosc", "Nabywca",
                                           "Towar_lub_usluga"]])
            check_ujemne_c(nowa_baza["Cena_jednostkowa"])
            check_ujemne_i(nowa_baza["Ilosc_towaru"])
            check_nip_format(str(nowa_baza.at[0, "NIP"]), "sprzedawcy")
            check_nip(str(nowa_baza.at[0, "NIP"]), "sprzedawcy")
            check_kod_format(str(nowa_baza.at[0, "Kod_pocztowy"]), "sprzedawcy")
            check_istnienie_nip(str(nowa_baza.at[0, "NIP"]), "sprzedawcy")
            check_nazwa(str(nowa_baza.at[0, "Przedsiebiorstwo"]), "sprzedawcy")
            check_kod(str(nowa_baza.at[0, "Kod_pocztowy"]), "sprzedawcy")
            check_miasto(str(nowa_baza.at[0, "Miasto"]), "sprzedawcy")
            check_adres(str(nowa_baza.at[0, "Adres"]), "sprzedawcy")
            try:
                del dane_slownik, nazwa_api, adres_api, adres_api_prim, kod_api, kod_api_prim, miasto_api, \
                    miasto_api_prim  # próba usunięcia zmiennych (oczyszczenie z poprzedniego sprawdzania)
            except NameError:
                pass

            # poniższe sprawdzanie dotyczy danych nabywcy, następuje to wyłącznie wtedy, gdy do faktury przypisana jest
            # osoba prawna
            if str(nowa_baza.at[0, "Nabywca"]) == "osoba_prawna":
                check_braki_dane(nowa_baza[["Przedsiebiorstwo_nabywcy", "NIP_nabywcy", "Adres_nabywcy",
                                            "Kod_pocztowy_nabywcy", "Miasto_nabywcy"]], str(nowa_baza.at[0, "Nabywca"]))
                if nowa_baza.at[0, "NIP_nabywcy"] != nowa_baza.at[0, "NIP_nabywcy"]:
                    pass
                else:
                    check_nip_format(str(nowa_baza.at[0, "NIP_nabywcy"]), "nabywcy")
                    check_nip(str(nowa_baza.at[0, "NIP_nabywcy"]), "nabywcy")
                    check_kod_format(str(nowa_baza.at[0, "Kod_pocztowy_nabywcy"]), "nabywcy")
                    check_istnienie_nip(str(nowa_baza.at[0, "NIP_nabywcy"]), "nabywcy")
                    check_nazwa(str(nowa_baza.at[0, "Przedsiebiorstwo_nabywcy"]), "nabywcy")
                    check_kod(str(nowa_baza.at[0, "Kod_pocztowy_nabywcy"]), "nabywcy")
                    check_miasto(str(nowa_baza.at[0, "Miasto_nabywcy"]), "nabywcy")
                    check_adres(str(nowa_baza.at[0, "Adres_nabywcy"]), "nabywcy")
                    try:
                        del dane_slownik, nazwa_api, adres_api, adres_api_prim, kod_api, kod_api_prim, miasto_api, \
                            miasto_api_prim
                    except NameError:
                        pass
            else:
                pass
            check_nr_faktury_format(str(nowa_baza.at[0, "Nr_faktury"]))
            check_data(str(nowa_baza.at[0, "Data_wystawienia"]))

            # poniższe sprawdzanie dotyczy danych banku, następuje wyłącznie wtedy, gdy faktura opłacona była przelewem
            if str(nowa_baza.at[0, "Sposob_platnosci"]) == "przelew":
                check_braki_dane(nowa_baza[["Nr_konta", "Bank", "Oddzial_banku"]],
                                 str(nowa_baza.at[0, "Sposob_platnosci"]))
                if nowa_baza.at[0, "Nr_konta"] != nowa_baza.at[0, "Nr_konta"]:
                    pass
                else:
                    check_nr_konta_format(str(nowa_baza.at[0, "Nr_konta"]))
                    check_cyfry_kontrolne_nr_konta(str(nowa_baza.at[0, "Nr_konta"]))
                    check_istnienie_bank(str(nowa_baza.at[0, "Nr_konta"]).replace(" ", "")[2:10])
                    check_bank(str(nowa_baza.at[0, "Nr_konta"]).replace(" ", "")[2:10], str(nowa_baza.at[0, "Bank"]))
                    check_oddzial_banku(str(nowa_baza.at[0, "Nr_konta"]).replace(" ", "")[2:10],
                                        str(nowa_baza.at[0, "Oddzial_banku"]))
            else:
                pass
            check_stawki(nowa_baza["Stawka_podatku"])
            check_przypisanie_stawek(nowa_baza["Towar_lub_usluga"], list(nowa_baza["Stawka_podatku"]))

            # obliczenia

            # wartość netto jako iloczyn ilości i ceny
            nowa_baza["Wartość_towaru_netto"] = nowa_baza["Ilosc_towaru"] * nowa_baza["Cena_jednostkowa"]
            # dodanie kolumny ze stawkami, które mogą zostać wykorzystane do obliczeń (nie są to teksty np. 'zw.')
            zwolnione = nowa_baza.index[nowa_baza["Stawka_podatku"] == "zw."].tolist()
            nowa_baza["Stawka_korekta"] = nowa_baza["Stawka_podatku"]
            nowa_baza.loc[zwolnione, "Stawka_korekta"] = 0
            # obliczenie kwot podatku na podstawie stawki oraz wartości netto
            nowa_baza["Kwota_podatku"] = round((
                    nowa_baza["Wartość_towaru_netto"] * pd.to_numeric(nowa_baza["Stawka_korekta"])), 2)
            # obliczenie wartości brutto jako sumy wartości netto i kwot podatku
            nowa_baza["Wartość_towaru_brutto"] = nowa_baza["Wartość_towaru_netto"] + nowa_baza["Kwota_podatku"]

            # zebranie w formie listy informacji o pozycjach, na którch znajdują się towary o danych stawkach VAT
            indeksy_stawki = [nowa_baza.index[nowa_baza["Stawka_podatku"] == "0.23"].tolist(),
                              nowa_baza.index[nowa_baza["Stawka_podatku"] == "0.08"].tolist(),
                              nowa_baza.index[nowa_baza["Stawka_podatku"] == "0.05"].tolist(),
                              nowa_baza.index[nowa_baza["Stawka_podatku"] == "0.00"].tolist(), zwolnione]

            # zebranie obliczonych wartości w formie tabelarycznej
            if ilosc_bledow == 0:  # jeżeli nie wystąpiły błędy, następuje wygenerowanie tabeli z towarami i wartościami
                # dla nich oraz tabeli z sumami wartości dla poszczególnych stawek podatku
                global baza_wydruk
                baza_wydruk = pd.DataFrame()
                lista_wydruk = ["Wartość_towaru_netto", "Stawka_podatku", "Kwota_podatku", "Wartość_towaru_brutto"]
                for kolumna in lista_wydruk:
                    for wiersz in range(0, 5):
                        baza_wydruk.at[wiersz + 1, kolumna] = nowa_baza.loc[indeksy_stawki[wiersz], kolumna].sum()
                baza_wydruk["Stawka_podatku"] = ["23%", "8%", "5%", "0%", "zw."]
                global do_zaplaty
                do_zaplaty = nowa_baza["Wartość_towaru_brutto"].sum()
                baza_wydruk.loc["Suma"] = [nowa_baza["Wartość_towaru_netto"].sum(), "-",
                                           nowa_baza["Kwota_podatku"].sum(), do_zaplaty]
                global baza_wydruk_towary
                baza_wydruk_towary = nowa_baza[
                    ["Towar_lub_usluga", "Ilosc_towaru", "Cena_jednostkowa", "Wartość_towaru_netto"]]
                baza_wydruk_towary["Stawka_podatku"] = [slownik_stawki.get(klucz) for klucz in nowa_baza["Stawka_podatku"]]
                baza_wydruk_towary["Kwota_podatku"] = nowa_baza["Kwota_podatku"]
                baza_wydruk_towary["Wartość_towaru_brutto"] = nowa_baza["Wartość_towaru_brutto"]                              
                baza_wydruk_towary.index = baza_wydruk_towary.index + 1
            else:  # jeżeli błędy wystąpiły, powstają tabele bez obliczeń wartości brutto
                lista_bledne.append("Wystąpiły błędy uniemożlwiające wyliczenie wartości brutto oraz kwot podatku")
                baza_wydruk = pd.DataFrame()
                lista_wydruk = ["Wartość_towaru_netto", "Stawka_podatku"]
                for kolumna in lista_wydruk:
                    for wiersz in range(0, 5):
                        baza_wydruk.at[wiersz + 1, kolumna] = nowa_baza.loc[indeksy_stawki[wiersz], kolumna].sum()
                baza_wydruk["Stawka_podatku"] = ["23%", "8%", "5%", "0%", "zw."]
                baza_wydruk.loc["Suma"] = [nowa_baza["Wartość_towaru_netto"].sum(), "-"]

                baza_wydruk_towary = nowa_baza[
                    ["Towar_lub_usluga", "Ilosc_towaru", "Cena_jednostkowa", "Wartość_towaru_netto"]]
                baza_wydruk_towary["Stawka_podatku"] = [slownik_stawki.get(klucz) for klucz in nowa_baza["Stawka_podatku"]]
                baza_wydruk_towary.index = baza_wydruk_towary.index + 1
                do_zaplaty = 0
            

            check_odwrotne_obciazenie(str(nowa_baza.at[0, "Odwrotne_obciazenie"]))
            check_podzielona(do_zaplaty, nowa_baza["Towar_lub_usluga"], nowa_baza.at[0, "Podzielona_platnosc"])

            # następuje wprowadzenie wartości list z elementami poprawnymi i blędnymi do widgetów
            self.ui.lista_poprawne_ui.addItems(lista_poprawne)
            self.ui.lista_bledne_ui.addItems(lista_bledne)
            # oraz następuje przejście do strony z tymi widgetami
            self.ui.okna_zmienne.setCurrentWidget(self.ui.wyniki)
        else:  # jeżeli użytkownik nie wybrał żadnej faktury, pojawia się okno z błędem
            self.okno_blad = QtWidgets.QMainWindow()
            self.ui_blad = Ui_okno_blad()
            self.ui_blad.setupUi(self.okno_blad)
            self.okno_blad.show()

    # funkcja przejścia do ekranu z wydrukiem faktury
    def do_faktura(self):
        # generowany jest tekst o cechach faktury - numer, data, mechanizmy
        wydruk_faktura = f'Faktura nr: {str(nowa_baza.at[0, "Nr_faktury"])}\n' \
                         f'Z dnia: {str(nowa_baza.at[0, "Data_wystawienia"])}\n'
        if str(nowa_baza.at[0, "Odwrotne_obciazenie"]) == "tak":
            wydruk_faktura += "Odwrotne obciążenie\n"
        if str(nowa_baza.at[0, "Podzielona_platnosc"]) == "tak":
            wydruk_faktura += "Podzielona płatność\n"
        if str(nowa_baza.at[0, "Samofakturowanie"]) == "tak":
            wydruk_faktura += "Samofakturowanie\n"
        if str(nowa_baza.at[0, "Metoda_kasowa"]) == "tak":
            wydruk_faktura += "Metoda kasowa"
        # wprowadzany jest on do widgetu
        self.ui.info_faktura.setText(wydruk_faktura)
        # generowany jest tekst o sprzedawcy
        wydruk_sprzedawca = f'Nazwa: {str(nowa_baza.at[0, "Przedsiebiorstwo"])}\nAdres: ' \
                            f'{str(nowa_baza.at[0, "Adres"])}, {str(nowa_baza.at[0, "Kod_pocztowy"])} ' \
                            f'{str(nowa_baza.at[0, "Miasto"])}\nNIP: {str(nowa_baza.at[0, "NIP"])}'
        self.ui.info_sprzedawca.setText(wydruk_sprzedawca)
        # generowany jest tekst o nabywcy i wprowadzany do widgetu wyłącznie, gdy jest on osobą prawną
        if nowa_baza.at[0, "Nabywca"] == "osoba_prawna":
            wydruk_nabywca = f'Nazwa: {str(nowa_baza.at[0, "Przedsiebiorstwo_nabywcy"])}\nAdres: ' \
                             f'{str(nowa_baza.at[0, "Adres_nabywcy"])}, {str(nowa_baza.at[0, "Kod_pocztowy_nabywcy"])}'\
                             f' {str(nowa_baza.at[0, "Miasto_nabywcy"])}\nNIP: {str(nowa_baza.at[0, "NIP_nabywcy"])}'
            self.ui.info_nabywca.setText(wydruk_nabywca)
        else:
            self.ui.info_nabywca.setText("")
        # generowany jest tekst o banku i wprowadzany do widgetu wyłącznie, gdy płatność nastąpiła przelewem
        if nowa_baza.at[0, "Sposob_platnosci"] == "przelew":
            wydruk_bank = f'Numer konta: {str(nowa_baza.at[0, "Nr_konta"])}\nW banku: {str(nowa_baza.at[0, "Bank"])} ' \
                          f'{str(nowa_baza.at[0, "Oddzial_banku"])}'
            self.ui.info_bank.setText(wydruk_bank)
        else:
            self.ui.info_bank.setText("")

        # generowana jest kwota do zapłaty słownie
        # na początku wybrana zostaje część całkowita (nie ułamkowa) kwoty
        zloty = str(int(do_zaplaty // 1))
        zloty_slownie = "Słownie: "
        # na podstawie wartości generowany jest tekst, wykorzystując kolejne cyfry w liczbie oraz słowniki
        # z przekształceniami cyfr na słowa
        if zloty == "0":
            zloty_slownie += "- , "
        else:
            try:
                zloty_slownie += setki[zloty[-6]]
            except IndexError:
                pass
            try:
                if zloty[-5] == "1":
                    zloty_slownie += nascie[zloty[-5:-3]]
                    zloty_slownie += "tysięcy "
                else:
                    zloty_slownie += dziesiatki[zloty[-5]]
                    try:
                        zloty_slownie += jednosci[zloty[-4]]
                        try:
                            zm4 = zloty[-5] == ""
                            if zloty[-4] in ("0", "1", "5", "6", "7", "8", "9"):
                                zloty_slownie += "tysięcy "
                            else:
                                zloty_slownie += "tysiące "
                        except IndexError:
                            if zloty[-4] == "0":
                                zloty_slownie += ""
                            elif zloty[-4] == "1":
                                zloty_slownie += "tysiąc "
                            elif zloty[-4] in ("5", "6", "7", "8", "9"):
                                zloty_slownie += "tysięcy "
                            else:
                                zloty_slownie += "tysiące "
                    except IndexError:
                        pass
            except IndexError:
                try:
                    if zloty[-4] == "1":
                        zloty_slownie += "tysiąc "
                    else:
                        zloty_slownie += jednosci[zloty[-4]]
                        try:
                            zm4 = zloty[-5] == ""
                            if zloty[-4] in ("0", "1", "5", "6", "7", "8", "9"):
                                zloty_slownie += "tysięcy "
                            else:
                                zloty_slownie += "tysiące "
                        except IndexError:
                            if zloty[-4] == "0":
                                zloty_slownie += ""
                            elif zloty[-4] == "1":
                                zloty_slownie += "tysiąc "
                            elif zloty[-4] in ("5", "6", "7", "8", "9"):
                                zloty_slownie += "tysięcy "
                            else:
                                zloty_slownie += "tysiące "
                except IndexError:
                    pass
            try:
                zloty_slownie += setki[zloty[-3]]
            except IndexError:
                pass
            try:
                if zloty[-2] == "1":
                    zloty_slownie += nascie[zloty[-2:]]
                else:
                    zloty_slownie += dziesiatki[zloty[-2]]
                    try:
                        zloty_slownie += jednosci[zloty[-1]]
                    except IndexError:
                        pass
            except IndexError:
                try:
                    zloty_slownie += jednosci[zloty[-1]]
                except IndexError:
                    pass

        # na końcu dodwana jest wartość ułamkowa oraz zwrot PLN - oznaczający polską walutę
        zloty_slownie += str(int(round(do_zaplaty - do_zaplaty // 1, 2) * 100)) + "/100"
        zloty_slownie += " PLN"
        
        # tekst wprowadzany jest do widgetu
        self.ui.kwota_slownie.setText(f"Kwota do zapłaty: {round(do_zaplaty,2)} PLN\n{zloty_slownie}")

        # wprowadzanie danych do widgetów tabel

        # pobrana zostaje informacja ile towarów/usług jest na faktrze, co wykorzystane zostaje do określenia liczby
        # wierszy na widgecie z towarami
        self.ui.tabela_towary.setRowCount(baza_wydruk_towary.shape[0])

        # widgety tabel oczyszczone zostają ze wcześniejszych sprawdzeń
        self.ui.tabela_towary.clearContents()
        self.ui.tabela_sumy.clearContents()

        # przekształcenie tabel z obliczonymi kwotami do słowników w celu łatwiejszego wprowadzania danych do widgetów
        baza_wydruk_towary_dict = baza_wydruk_towary.to_dict(orient="records")
        wiersz = 0
        # wprowadzanie danych do widgetów przy wykorzystaniu pętli - kolejne uzupełnianie komórek, gdy nie wystąpiły
        # błędy uniemożliwiające obliczenie kwot brutto wprowadzane są wszystkie wartości, w innym wypadku tylko ich
        # część
        if ilosc_bledow == 0:
            for towar in baza_wydruk_towary_dict:
                self.ui.tabela_towary.setItem(wiersz, 0, QtWidgets.QTableWidgetItem(towar["Towar_lub_usluga"]))
                self.ui.tabela_towary.setItem(wiersz, 1, QtWidgets.QTableWidgetItem(str(round(towar["Ilosc_towaru"]))))
                self.ui.tabela_towary.setItem(wiersz, 2, QtWidgets.QTableWidgetItem(
                    str(round(towar["Cena_jednostkowa"], 2))))
                self.ui.tabela_towary.setItem(wiersz, 3, QtWidgets.QTableWidgetItem(
                    str(round(towar["Wartość_towaru_netto"], 2))))
                self.ui.tabela_towary.setItem(wiersz, 4, QtWidgets.QTableWidgetItem(str(towar["Stawka_podatku"])))
                self.ui.tabela_towary.setItem(wiersz, 5, QtWidgets.QTableWidgetItem(
                    str(round(towar["Kwota_podatku"], 2))))
                self.ui.tabela_towary.setItem(wiersz, 6, QtWidgets.QTableWidgetItem(
                    str(round(towar["Wartość_towaru_brutto"], 2))))
                wiersz += 1
        else:
            for towar in baza_wydruk_towary_dict:
                self.ui.tabela_towary.setItem(wiersz, 0, QtWidgets.QTableWidgetItem(
                    towar["Towar_lub_usluga"]))
                self.ui.tabela_towary.setItem(wiersz, 1, QtWidgets.QTableWidgetItem(
                    str(towar["Ilosc_towaru"])))
                self.ui.tabela_towary.setItem(wiersz, 2, QtWidgets.QTableWidgetItem(
                    str(round(towar["Cena_jednostkowa"], 2))))
                self.ui.tabela_towary.setItem(wiersz, 3, QtWidgets.QTableWidgetItem(
                    str(round(towar["Wartość_towaru_netto"], 2))))
                self.ui.tabela_towary.setItem(wiersz, 4, QtWidgets.QTableWidgetItem(
                    str(towar["Stawka_podatku"])))
                wiersz += 1
        self.ui.tabela_sumy.setRowCount(baza_wydruk.shape[0])
        baza_wydruk_dict = baza_wydruk.to_dict(orient="records")
        wiersz = 0
        if ilosc_bledow == 0:
            for stawka in baza_wydruk_dict:
                self.ui.tabela_sumy.setItem(wiersz, 0, QtWidgets.QTableWidgetItem(
                    str(round(stawka["Wartość_towaru_netto"], 2))))
                self.ui.tabela_sumy.setItem(wiersz, 1, QtWidgets.QTableWidgetItem(
                    str(stawka["Stawka_podatku"])))
                self.ui.tabela_sumy.setItem(wiersz, 2, QtWidgets.QTableWidgetItem(
                    str(round(stawka["Kwota_podatku"], 2))))
                self.ui.tabela_sumy.setItem(wiersz, 3, QtWidgets.QTableWidgetItem(
                    str(round(stawka["Wartość_towaru_brutto"], 2))))
                wiersz += 1
        else:
            for stawka in baza_wydruk_dict:
                self.ui.tabela_sumy.setItem(wiersz, 0, QtWidgets.QTableWidgetItem(
                    str(round(stawka["Wartość_towaru_netto"], 2))))
                self.ui.tabela_sumy.setItem(wiersz, 1, QtWidgets.QTableWidgetItem(
                    str(stawka["Stawka_podatku"])))
                wiersz += 1

        # po uzupełnieniu widgetów tabel przedstawiany jest ekran z wydrukiem faktury
        self.ui.okna_zmienne.setCurrentWidget(self.ui.faktura)

    # funkcja powrotu do ekranu z widgetami list elementów poprawnych i błędnych (bez konieczności ponownego sprawdzania
    # faktury)
    def do_wyniki_bez_akt(self):
        self.ui.okna_zmienne.setCurrentWidget(self.ui.wyniki)

# uruchamianie programu - okna
app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")  # nadanie stylu okna
UIWindow = Sygnalista()  # nadanie wyglądu oknu
UIWindow.main_win.show()

sys.exit(app.exec_())  # zamknięcie aplikacji poprzez kliknięcie przycisku zamykania okna
