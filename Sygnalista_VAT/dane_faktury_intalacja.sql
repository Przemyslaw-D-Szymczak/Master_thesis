/*  Witaj!
	Aby dodaæ bazê danych do programu faktura; w zak³adce "Query" wybierz opcjê "SQLCMD Mode", a nastêpnie
	ustaw odpowiedni¹ œcie¿kê do folderu z danymi poni¿ej wed³ug wzoru:											*/

:setvar SqlSamplesSourceDataPath "C:\...tutaj podaj œcie¿kê...\Sygnalista_VAT\dane\"

-- Teraz uruchom zapytanie klikaj¹c "Execute"



:setvar DatabaseName "Faktura"

USE [master];
GO

IF EXISTS (SELECT [name] FROM [master].[sys].[databases] WHERE [name] = N'$(DatabaseName)')
	ALTER DATABASE $(DatabaseName) set single_user with rollback immediate
    DROP DATABASE $(DatabaseName);

CREATE DATABASE $(DatabaseName);
GO

USE $(DatabaseName);
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[banki](
	[Bank] [nvarchar](300) NOT NULL,
	[Oddzial_banku] [nvarchar](200) NOT NULL,
	[Nr_banku] [nvarchar](10) NOT NULL
) ON [PRIMARY];
GO

CREATE TABLE [dbo].[konta](
	[Nr_konta] [nvarchar](50) NOT NULL,
	[Bank] [nvarchar](100) NULL,
	[Oddzial_banku] [nvarchar](100) NULL
) ON [PRIMARY]
GO

CREATE TABLE [dbo].[faktury_pozycje](
	[Nr_faktury] [nvarchar](50) NOT NULL,
	[Towar_lub_usluga] [nvarchar] (100) NULL,
	[Ilosc_towaru] [varchar](50) NULL,
	[Cena_jednostkowa] [varchar](50) NULL,
	[Stawka_podatku] [varchar](50) NULL
) ON [PRIMARY]
GO

CREATE TABLE [dbo].[faktury_dane](
	[Przedsiebiorstwo] [nvarchar](100) NOT NULL,
	[Nr_faktury] [nvarchar](50) NOT NULL,
	[Data_wystawienia] [varchar](50) NULL,
	[Nr_konta] [varchar](50) NULL,
	[Sposob_platnosci] [nvarchar](10) NOT NULL,
	[Metoda_kasowa] [nvarchar](10) NOT NULL,
	[Samofakturowanie] [nvarchar](10) NOT NULL,
	[Odwrotne_obciazenie] [nvarchar](10) NOT NULL,
	[Podzielona_platnosc] [nvarchar](10) NOT NULL,
	[Nabywca] [nvarchar](20) NOT NULL,
	[NIP_nabywcy] [varchar](50) NULL,
) ON [PRIMARY]
GO

CREATE TABLE [dbo].[przedsiebiorstwa](
	[Przedsiebiorstwo] [nvarchar](100) NOT NULL,
	[NIP] [varchar](50) NULL,
	[Adres] [nvarchar](100) NULL,
	[Kod_pocztowy] [varchar](50) NULL,
	[Miasto] [nvarchar](50) NULL
) ON [PRIMARY]
GO

BEGIN TRY
BULK INSERT [dbo].[banki] FROM '$(SqlSamplesSourceDataPath)banki.csv'
WITH (FORMAT = 'csv',
	FIRSTROW = 2,
	CHECK_CONSTRAINTS,
	CODEPAGE='65001',
	DATAFILETYPE='widechar',
	FIELDTERMINATOR=';',
	ROWTERMINATOR='\n',
	TABLOCK
	);
END TRY
BEGIN CATCH
	SELECT ERROR_LINE(), ERROR_MESSAGE();
END CATCH
GO

BEGIN TRY
	BULK INSERT [dbo].[faktury_pozycje] FROM '$(SqlSamplesSourceDataPath)faktury_pozycje.csv'
	WITH (FORMAT = 'csv',
		FIRSTROW = 2,
		CHECK_CONSTRAINTS,
		CODEPAGE='65001',
		DATAFILETYPE='char',
		FIELDTERMINATOR=';',
		ROWTERMINATOR='\n',
		TABLOCK
        );
END TRY
BEGIN CATCH
	SELECT ERROR_LINE(), ERROR_MESSAGE();
END CATCH
GO

BEGIN TRY
	BULK INSERT [dbo].[faktury_dane] FROM '$(SqlSamplesSourceDataPath)faktury_dane.csv'
	WITH (FORMAT = 'csv',
		FIRSTROW = 2,
		CHECK_CONSTRAINTS,
		CODEPAGE='65001',
		DATAFILETYPE='char',
		FIELDTERMINATOR=';',
		ROWTERMINATOR='\n',
		TABLOCK
		);
END TRY
BEGIN CATCH
	SELECT ERROR_LINE(), ERROR_MESSAGE();
END CATCH
GO

BEGIN TRY
	BULK INSERT [dbo].[konta] FROM '$(SqlSamplesSourceDataPath)konta.csv'
	WITH (FORMAT = 'csv',
		FIRSTROW = 2,
		CHECK_CONSTRAINTS,
		CODEPAGE='65001',
		DATAFILETYPE='char',
		FIELDTERMINATOR=';',
		ROWTERMINATOR='\n',
		TABLOCK
		);
END TRY
BEGIN CATCH
	SELECT ERROR_LINE(), ERROR_MESSAGE();
END CATCH
GO

BEGIN TRY
	BULK INSERT [dbo].[przedsiebiorstwa] FROM '$(SqlSamplesSourceDataPath)przedsiebiorstwa.csv'
	WITH (FORMAT = 'csv',
		FIRSTROW = 2,
		CHECK_CONSTRAINTS,
		CODEPAGE='65001',
		DATAFILETYPE='char',
		FIELDTERMINATOR=';',
		ROWTERMINATOR='\n',
		TABLOCK
		);
END TRY
BEGIN CATCH
	SELECT ERROR_LINE(), ERROR_MESSAGE();
END CATCH;