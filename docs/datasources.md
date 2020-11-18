# Überblick über mögliche Quellen für EU Dokumente

{{TOC}}

## Definitionen

### Sitzungs-/Vorgangsorientierung:
Die EU dokumentiert ihre Tätigkeiten auf zwei unterschiedliche Weisen.
Die sitzungsorientierte Dokumentation protokolliert Sitzungen und Tagungen von z.B. dem Parlament und fasst somit alle Vorgänge zusammen die an einem Tag behandelt wurden.
Die vorgangsorientierte Dokumentation fasst alle Aktionen die im Zusammenhang mit einem Entscheidungsprozess stehen zusammen.
Beide Dokumentationen verweisen aufeinander.

## Sitzungsorientierte Dokumentation
Das Europaparlament [veröffentlicht](https://www.europarl.europa.eu/plenary/) diverse Dokumente die dessen Tätigkeiten sitzungsorientiert dokumentieren.
Direkt verlinkt werden nur die Dokumente der letzten Parlamentssitzungen. Ältere Dokumente lassen sich über die Suche auffinden.

### Besonderheiten
Die Dokumente lassen sich durch die feste URL-Struktur gut enumerieren. Die  Menge der möglichen Werte für das Datum reduziert sich auf die Sitzungstage seit  dem 01.07.1994.
Da die Dokumente direkt vom Webserver des Europaparlaments und nicht von einem CDN stammen, muss zurückhaltend gecrawled werden um nicht blockiert zu werden.

Vorläufige und endgültige Fassungen von Dokumenten werden unter der gleichen URL veröffentlicht. Ein erneutes scrapen ist notwendig.

### Dokumenten-Typen
Das ist eine Liste der direkt verlinkten Dokumententypen.
Es existieren weitere Dokumententypen, diese müssen allerdings zuerst über verlinkungen identifiziert werden.

Alle URLs beginnen mit "https://www.europarl.europa.eu/doceo/document/"


#### Tagesordnungen

**Beispiel:**
- [...]/OJQ-9-2020-11-23_DE.html
- [...]/OJ-9-2020-11-23-SYN_DE.html
- [...]/OJ-9-2020-11-23_DE.pdf

**Struktur:**\
Übersicht:
- [...]/OJ-{Wahlperiode}-{Datum erster Sitzungstag}-SYN-{Sprache}.html
- [...]/OJ-{Wahlperiode}-{Datum erster Sitzungstag}-{Sprache}.pdf

Tagesweise:
- [...]/OJQ-{Wahlperiode}-{Datum Sitzungstag}-{Sprache}.html

**Enthält Links auf:**
- Geschäftsordnung
- Prozessübersicht https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do?lang=en&reference=2020/2801(RSP)


#### Eingereichte Texte

**Beispiel:**
- [...]/A-9-2020-0197_DE.pdf

**Struktur**
- [...]/A-{Wahlperiode}-{Jahr}-{fortlaufende Nummer}_{Sprache}.{pdf|docx}


#### Abstimmungsergebnisse

**Beispiel:**
- [...]/PV-9-2020-10-06-VOT_DE.pdf
- [...]/PV-9-2020-10-06-RCV_FR.pdf

**Struktur:**
- [...]/PV-{Wahlperiode}-{Datum}-VOT_{Sprache}.pdf
- [...]/PV-{Wahlperiode}-{Datum}-RCV_{Sprache}.pdf


#### Protokoll

**Beispiel:**
- [...]/PV-9-2020-10-19-TOC_DE.html

**Struktur:**\
Anwesenheitsliste:
- [...]/PV-{Wahlperiode}-{Datum}-ATT_{Sprache}.{html|docx|pdf}

Inhaltsverzeichnis:
- [...]/PV-{Wahlperiode}-{Datum}-TOC_{Sprache}.html

Protokoll:
- [...]/PV-{Wahlperiode}-{Datum}_{Sprache}.{html|docx|pdf}

Tagesordnungspunkt:
- [...]/PV-{Wahlperiode}-{Datum}-ITM-{fortlaufende Nummer, 3 Ziffern}_{Sprache}.{html}

**Enthält Links auf:**
- Geschäftsordnung
- Dokumente
- Wortprotokolle
- Prozessübersicht https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do?lang=en&reference=2020/2801(RSP)


#### Wortprotokoll

**Beispiel:**
- [...]/CRE-9-2020-07-09-TOC_DE.html

**Struktur:**\
Inhaltsverzeichnis:
- [...]/CRE-{Wahlperiode}-{Datum}-TOC_{Sprache}.html

Protokoll:
- [...]/CRE-{Wahlperiode}-{Datum}_{Sprache}.{html|pdf}

Tagesordnungspunkt:
- [...]/CRE-{Wahlperiode}-{Datum}-ITM-{fortlaufende Nummer, 3 Ziffern}_{Sprache}.{html}


**Enthält Links auf:**
- Protokolle
- Eingereichte Texte
- Angenommene Texte
- Geschäftsordnung
- Dokumente
- Prozessübersicht https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do?lang=en&reference=2020/2801(RSP)


#### Angenommene Texte

**Beispiel:**
- [...]/TA-9-2020-10-20-TOC_DE.html

**Struktur:**\
Inhaltsverzeichnis:
- [...]/TA-{Wahlperiode}-{Datum}-TOC_{Sprache}.html

Einzelner Text:
- [...]/TA-{Wahlperiode}-{Jahr}_{fortlaufende Nummer}.{html|pdf|docx}

**Enthält Links auf:**
- Eingereichte Texte
- Wortprotokolle
- Protokolle


## Vorgangsorientierte Dokumentation

Die vorgangsorientierte Dokumentation soll es ermöglichen den Entscheidungsprozess zu einem Thema nachvollziehen zu können.
Auf dieser [Webseite](https://oeil.secure.europarl.europa.eu/oeil/home/home.do)
kann nach Prozessen gesucht werden.
Für jeden Prozess gibt es eine [Übersichtsseite](https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do?reference=2020/0156(COD)). Diese verlinkt alle beteiligten Institutionen & Dokumente und stellt zusätzlich eine nicht offizielle Zusammenfassung des Themas zu Verfügung. Dieser Dienst wird nur in Französisch und Englisch angeboten.

### Besonderheiten
Alle Vorgänge lassen sich leicht enumerieren. Es ist nur eine Jahreszahl und laufende Nummer notwendig.\
Die Menge an unterschiedlichen referenzierten Quellen scheint bedeutend höher zu sein als im Falle der sitzungsorientierten Dokumentation. Dadurch steigt die Anzahl der benötigten Seiten-spezifischen Crawlern die in der Lage sind die Dokumente herunterzuladen.\
Die Qualität der Verlinkung scheint bedeutend schlechter zu sein. Viele Links führen ins leere oder verweisen auf eine Suchmaske.\
Auch alte Dokumente werden aktualisiert, z.B. um auf neue Änderungsanträge zu verweisen.

### Dokumenten-Typen

Alle URLs beginnen mit https://oeil.secure.europarl.europa.eu/oeil/popups/


#### Prozessübersicht
**Beispiel:**\

- [...]ficheprocedure.do?reference=2020/0156(COD)

**Struktur:**

- [...]reference={Jahreszahl}/{in der Wahlperiode fortlaufende Nummer, 4 stellig}{optionales Kürzel}

**Enthält Links auf:**
- alles mögliche

#### PDF-Host

**Beispiel:**
- [...]printficheglobal.pdf?id=23569

**Struktur:**

- [...]printficheglobal.pdf?id={laufende Nummer}



## Weitere Quellen

### Eur-Lex
Gesetze und Gesetzesentwürfe
[https://eur-lex.europa.eu/](https://eur-lex.europa.eu/)

### Public Register of Documents
Enthält alle öffentlichen Dokumente, nur über Suchinterface benutzbar
[https://www.europarl.europa.eu/RegistreWeb/search/simple.htm?searchLanguages=EN&sortAndOrder=DATE_DOCU_DESC](https://www.europarl.europa.eu/RegistreWeb/search/simple.htm?searchLanguages=EN&sortAndOrder=DATE_DOCU_DESC)

### Register der delegierten Rechtsakte und Durchführungsrechtsakte
Übersicht über die delegierten Rechtsakte
[https://webgate.ec.europa.eu/](https://webgate.ec.europa.eu/)

### Register der Expertengruppen
Übersicht über die Expertengruppen inkl. ihrer Protokolle [https://ec.europa.eu/transparency/regexpert/](https://ec.europa.eu/transparency/regexpert/)


### Open Data Portal
https://data.europa.eu/euodp/en/data/
https://ec.europa.eu/dgs/secretariat_general/tools/opendata/