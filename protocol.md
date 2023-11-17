# Protokoll

## Datentyp
- JSON in Form von "packets"
- Attribute
  - `type`: Typ des Pakets
    - `SD`: Spiel Daten
    - `SS`: Spiel Start
    - `SE`: Spiel Ende
    - `AD`: Aktualisierung Design
    - `AM`: Aktualisierung Mechanik
- Inhalt
  - `S...`
    - `PosX1`: X-Position des ersten Spielers
    - `PosY1`: Y-Position des ersten Spielers
    - `PosX2`: X-Position des zweiten Spielers
    - `PosY2`: Y-Position des zweiten Spielers
    - `PosXB`: X-Position des Balls
    - `PosYB`: Y-Position des Balls
  - `A...`
    - `ID`: ID des Spieles
    - ...