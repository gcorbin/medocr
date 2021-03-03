# meDocr

_Match exam documents by optical character recognition. _

**Das Problem: ** Für die Korrektur der Klausuren werden diese eingescannt und dann als .pdf Dokumente an die Helfer:innen verteilt. Ein:e Helfer:in korrigiert dabei meistens eine Aufgabe auf allen Klausurbögen. Die Scans müssen also für die Korrektur nach Aufgaben gruppiert werden und später für die Einsicht wieder zu den Klausurbögen zusammengefügt werden. 

**Die Lösung: ** Die Klausurbögen werden individuell markiert. Das Projekt [examsfbmathe](https://gitlab.rhrk.uni-kl.de/exercisesheetmanager/examsfbmathe) enthält eine LaTex Vorlage, mit der diese speziell markierten Klausurbögen erstellt werden können. 
Dieses Programm kann anhand der Marker aus jeder gescannte Seite folgende Information ablesen:

- Die Nummer der Klausur (exam id)
- Die Nummer des Klausurbogens (sheet id)
- Die Nummer der Aufagbe (task id)
- Die Nummer der Seite (page id)

Damit können die Seiten nach Aufgaben oder nach Klausurbögen gruppiert werden. 
Das Programm beinhaltet außerdem eine umfangreiche Validierung der Scans, sodass mit großer Wahrscheinlichkeit keine Seiten verloren gehen oder falsch eingeordnet werden. 

