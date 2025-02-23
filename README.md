# Master_thesis

*Polski:*

Repozytorium zawiera:
- folder z plikami potrzebnymi do działania aplikacji *Sygnalista VAT* (kod, dane, interfejs graficzny, instalator bazy danych)
- pdf z pracą magisterską
  
Praca powstała i została obroniona w 2024 r. Przedstawia wszystko związane z aplikacją Sygnalista VAT tj. genezę powstania, podstawy prawne, przegląd rynku, wykorzystywane technologie, instrukcję instalacji programu, generacji bazy danych i obslugi programu. Przestawione zostały także najbardziej interesujące framenty kodu i ich działanie oraz propozycje dalszego rozwoju.

Aplikacja jest odpowiedzią na potrzeby związane z fakturą VAT. W pracy uargumentowane zostało, że czasami konieczne może być weryfikowanie poprawności faktur. *Syngalista VAT* napisany został w Pythonie i wykorzysuje dane z MS SQL Server i plików CSV, co więcej korzysta z API Ministerstwa Finansów i NBP. W trakcie weryfikacji sprawdzane są: braki danych, informacje o sprzedawcy i nabywcy, dane banków, typy faktury oraz stawki podatków dóbr i usług. Po tym przeprowadzane są kalkulacje a rezultaty prezentowane są na interfejsie graficznym.



*English:*

Repository contains:
- folder with the *Sygnalista VAT* application files (code, data, GUI, database installer)
- pdf with bachelor thesis
  
The thesis was written in Polish, and its defence took place in 2024. It describes everything about the *Sygnalista VAT* application, i.e. genesis, legal fundamentals, market research, the technology used, instructions regarding needed programs installation, database generation and application handling. Most interesting code fragments and their functionality were alse presented, and finally, propositions for future improvements were listed.

The application is a response to needs regarding VAT invoices. In thesis it was suggested that sometimes it might be necessary to verify the invoices' correctness. *Sygnalista VAT* was written in Python and uses data from MS SQL Server and CSV files, moreover it uses APIs of Polish Ministry of Finance and Central Bank. During invoice verification, the following elements are checked: missing values, seller and buyer enterprise details, bank data, invoice types and tax rates for goods and services. After that, calculations are executed, and results are presented in the graphical user interface.
