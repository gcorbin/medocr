# meDocr

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

## Vorgehensweise

### Klausur erstellen und drucken

In dem Projekt [examsfbmathe](https://gitlab.rhrk.uni-kl.de/exercisesheetmanager/examsfbmathe) gibt es drei LaTex Vorlagen:
1. Einen markierten Klausurbogen, auf dem die Nummern für die Klausur, die Aufgabe und die Seite eingetragen sind. 
Die Nummer des Bogens ist noch leer. 
2. Eine Vorlage, die für die gewünschte Anzahl an Klausurbögen durchnummerierte aber ansonsten leere Seiten erzeugt. 
3. Eine Vorlage für leere Extraseiten, die während der Klausur ausgeteilt werden, wenn der Platz auf dem Bogen nicht reicht. Auf diesen Seiten ist nur die Klausurnummer markiert. Die Nummern für Klausurbogen, Aufgabe und Seite sind leer und müssen nachher von Hand eingetragen werden. 

Im nächsten Schritt kann man mit dem Skript 

> create_marked_exams.py <klausurbogen.pdf> <nummernseiten.pdf> -o <ausgabeordner>

die durchnummerierten Klausurbögen erstellen. 
Das Skript erzeugt für jeden Klausurbogen eine eigene .pdf Datei. 
Dieses Format ist auch von der Druckerei am RHRK so gewünscht. 

**Hinweis:** Wenn die Studierenden auf die Rückseite schreiben dürfen, muss in der Vorlage die Option für bedruckte Rückseiten aktiviert sein. 

### Korrektur



### Einsicht
