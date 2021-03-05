# meDocr

\ ˌmē-dē-ˈō-kər \\

_Match exam documents by optical character recognition._ 

**Das Problem:** Für die Korrektur der Klausuren werden diese eingescannt und dann als .pdf Dokumente an die Helfer:innen verteilt. Ein:e Helfer:in korrigiert dabei meistens eine Aufgabe auf allen Klausurbögen. Die Scans müssen also für die Korrektur nach Aufgaben gruppiert werden und später für die Einsicht wieder zu den Klausurbögen zusammengefügt werden. 

**Die Lösung:** Die Klausurbögen werden individuell markiert. Das Projekt [examsfbmathe](https://gitlab.rhrk.uni-kl.de/exercisesheetmanager/examsfbmathe) enthält eine LaTex Vorlage, mit der diese speziell markierten Klausurbögen erstellt werden können. 
Dieses Programm kann anhand der Marker aus jeder gescannte Seite folgende Information ablesen:

- Die Nummer der Klausur (exam id)
- Die Nummer des Klausurbogens (sheet id)
- Die Nummer der Aufgabe (task id)
- Die Nummer der Seite (page id)

Damit können die Seiten nach Aufgaben oder nach Klausurbögen gruppiert werden. 
Das Programm beinhaltet außerdem eine umfangreiche Validierung der Scans, sodass mit großer Wahrscheinlichkeit keine Seiten verloren gehen oder falsch eingeordnet werden. 

## Setup

Ich empfehle, die nötigen Abhängigkeiten mit [conda](https://docs.conda.io/projects/conda/en/latest/) in eine eigene Umgebung zu installieren. 

> conda create -f medocr.yml

Die Umgebung kann dann mit 

> conda activate medocr

aktiviert werden. 

## Aufbau der Markierungen

Die Markierungen bestehen aus zwei sogenannten _ArUco_ Markern (https://docs.opencv.org/master/d5/dae/tutorial_aruco_detection.html) die ein Textfeld einrahmen. 

Der linke ArUco Marker kodiert die Id der Klausur, der rechte Marker hat immer die Id 0. 
Diese Marker ermöglichen eine genaue Positionierung des Textfeldes auch bei gedrehten und verschobenen Scans. 

Das Textfeld hat drei Einträge. Von links nach rechts:
1. Die Nummer des Klausurbogens (Diese Zahl ist auf einem Klasurbogen jeweils konstant)
2. Die Nummer der Aufgabe (Das Deckblatt hast die Nummer 0, leer für die Leerseiten am Ende des Bogens)
3. Die Seitenzahl

Jeder Eintrag besteht aus vier Ziffern. 
Dabei enthalten die linken drei Ziffern die eigentliche Zahl (Nummer des Bogens, der Aufgabe, oder der Seite), und die vierte Ziffer ist eine Prüfziffer. 

Für eine Zahl von 0 bis 999 wird der Eintrag wie folgt generiert:
- Die Zahl wird bis auf 3 Stellen mit Nullen aufgefüllt
- Die Einerstelle der Quersumme wird als Prüfziffer angehängt

Beispiele: 
- 0 -> 0000
- 1 -> 0011
- 99 -> 0998
- 999 -> 9997

Dadurch wird sicher verhindert, dass einzelne Ziffern falsch erkannt werden. 
Gleichzeitig ist die Methode leicht von Menschen nachvollziehbar. 

## Vorgehensweise

### Klausur erstellen und drucken

In dem Projekt [examsfbmathe](https://gitlab.rhrk.uni-kl.de/exercisesheetmanager/examsfbmathe) gibt es drei LaTex Vorlagen:
1. Einen markierten Klausurbogen, auf dem die Nummern für die Klausur, die Aufgabe und die Seite eingetragen sind. 
Die Nummer des Bogens ist noch leer. 
2. Eine Vorlage, die für die gewünschte Anzahl an Klausurbögen durchnummerierte aber ansonsten leere Seiten erzeugt. 
3. Eine Vorlage für leere Extraseiten, die während der Klausur ausgeteilt werden, wenn der Platz auf dem Bogen nicht reicht. Auf diesen Seiten ist nur die Klausurnummer markiert. Die Nummern für Klausurbogen, Aufgabe und Seite sind leer und müssen nachher von Hand eingetragen werden. 

Im nächsten Schritt kann man mit dem Skript 

> create_marked_exams.py \<klausurbogen.pdf\> \<nummernseiten.pdf\> -o \<ausgabeordner\>

die durchnummerierten Klausurbögen erstellen. 
Das Skript erzeugt für jeden Klausurbogen eine eigene .pdf Datei. 
Dieses Format ist auch von der Druckerei am RHRK so gewünscht. 

**Hinweis:** Wenn die Studierenden auf die Rückseite schreiben dürfen, muss in der Vorlage die Option für bedruckte Rückseiten aktiviert sein. 

### Vor der Korrektur

#### Indizieren
Man kann die Klausuren immer Paketweise einscannen lassen. 
Die eingescannten Dokumente kann man dann mit dem Befehl

> python3 medocr.py add \<collection\> \<file\>

erkennen und indizieren. 
\<collection\> ist der Pfad der Ausgabe und \<file\> ist das .pdf Dokument was indiziert werden soll. 
Dabei passieren mehrere Dinge: 
- Wenn der angegebene Pfad nicht existiert, wird eine neue Sammlung angelegt (ein Ordner in dem eine Datei mit dem Namen _index_ enthalten ist)
- Die Datei \<file\> wird in den Ordner kopiert
- Die index Datei wird im Ausgabeordner aktualisiert. Diese enthält die erkannte Marker-Information im json Format.

Man kann mehrere .pdfs dem gleichen Ordner hinzufügen. 

#### Validieren
Bei der Indizierung gibt es immer Seiten, die nicht erkannt werden. 
Deshalb sollte man **immer** validieren, nachdem man alle Seiten zur Sammlung hinzugefügt hat! 

> python3 medocr.py validate \<collection\> 

Bei der Validierung werden folgende Dinge überprüft:
- Stimmt die Anzahl der Seiten im Index mit der Anzahl der Seiten in den .pdfs überein?
- Für jede Seite: Wurde die Seite korrekt erkannt? Wenn nicht, ist eine Nutzereingabe erforderlich. 
- Gibt es doppelt vorkommende Seiten? (Dies kann durch eine falsche Eingabe im vorigen Schritt passieren, oder durch eine falsch Erkannte Seite). Bei doppelten Seiten ist wieder eine Eingabe erforderlich.
- Fehlen Seiten? Fehlende Seiten werden einfach nur angezeigt. 

#### Sortieren nach Aufgabe

Mit dem Befehl

> python3 medocr.py order-by \<collection\> task \<collection-task\>

wird die neue Sammlung \<collection-task\> angelegt, in der für jede Aufgabe ein eigenes .pdf existiert. 
Diese Dateien können dann an die Helfer:innen weitergegeben werden. 

Vorher bitte immer **validieren!!!**

### Einsicht

- Die korrigierten, nach Aufgabe gruppierten .pdf Dokumente in einen Ordner \<collection-corr\> zusammenfügen.
- Die Datei _index_ aus \<collection-task\> in diesen Ordner kopieren
- Den Befehl 

> python3 medocr.py order-by \<collection-corr\> sheet \<collection-sheet\>

ausführen 

## Sonderfälle: 

### Freie Seiten am Ende des Klausurbogens
Ans Ende der meisten Klausurbögen werden noch einige leere Seiten angeheftet, falls der Platz nicht reicht. 
Da man vorher nicht wissen kann, ob oder für welche Aufgabe diese Seiten benutzt werden, bleibt hier die Markierung für die Aufgabennummer leer. 

Es gibt zwei Fälle: 

1. Die Seite wurde nicht beschrieben: 
Dann kann man die Aufgabennummer leer lassen. Das Programm erkennt das und weist der Seite die Aufgabennummer -1 zu (für unbenutze Seite).
Beim Sortieren nach Aufgabe wird dann automatisch auch eine Datei für die Leerseiten erzeugt. 

2. Die Seite wurde beschrieben: 
Dann sollte man die Nummer der Aufgabe von Hand eintragen. 
- Die Seite wird dann automatisch der richtigen Aufgabe zugeordnet, wenn das Programm die Handschrift erkennt. 
- Wenn das Programm die Handschrift nicht lesen kann, wird bei der Validierung die Seite noch mal gezeigt. 
- Wenn das Programm fälschlicherweise das Feld als leer erkennt, obwohl etwas eingetragen wurde, wird die Seite ohne Kommentar den Leerseiten zugeordnet. **Deshalb sollte man nach dem Sortieren das Dokument mit den Leerseiten noch einmal durchgehen!**

### Aufgabe wurde auf der falschen Seite bearbeitet
Wenn jemand aus Versehen eine Aufgabe auf eine andere Seite geschrieben hat, und das während der Klausur merkt, sollte er/sie **die letzte Stelle der Aufgabennummer** unkenntlich machen (komplett übermalen). 
Dann erkennt das Programm einen Fehler beim Einlesen und man kann die Seite bei der Validierung händisch zuordnen. 

### Extraseite wurde benutzt
Bei den Extraseiten sind alle Felder der Markierung leer. Für diese Seiten gibt es zwei Optionen:
- Vor dem Scannen die Information handschriftlich hinzufügen und hoffen, dass das Programm die Handschrift erkennt.
- Alles leer lassen. Das Programm sollte dann einen Fehler erkennen und die Seite zur manuellen Eingabe bei der Validierung vorlegen. 

In jedem Fall sollte man für die Seitenzahl eine Zahl eingeben, die nicht auf dem normalen Klausurbogen vorkommt. 
Man sollte bei der Validierung mit 

> python3 medocr.py validate \<collection\> --extra-pages \<zahl1\> \<zahl2\> ... \<zahlN\>

eine Liste der Seitennummern angeben, die für Extraseiten  vergeben wurden. 
Diese Seitennummern werden ausgelassen, wenn die fehlenden Seiten berechnet werden. 
_Wenn man das nicht macht, bei jeder Klasur, bei der keine Extraseite benutzt wurde, die Extraseiten als Fehlend gemeldet._

