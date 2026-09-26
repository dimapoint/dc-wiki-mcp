# Muestras de plantillas del dump (Fase 1, paso 3)

Dump `endcdatabase_pages_current.xml` (última revisión 2026-09-20T17:12Z, 681.361 páginas, 169.401 en ns 0, 41.382 redirecciones).
Las plantillas de infobox viven en el espacio `DC Database:` (ns 4), p. ej. `{{DC Database:Comic Template}}`; la lógica está en módulos Lua (`Module:ComicsInfobox/Comic`, `Module:StaffCorrection`).

## Hallazgos que definen el esquema

- **Créditos de números**: `Writer{historia}_{n}`, `Penciler#_#`, `Inker#_#`, `Colorist#_#`, `Letterer#_#`, `Editor#_#` (el primer índice es la historia, el segundo el orden). Tapa: `CoverArtist#` (tapa principal) y `Cover{k}Artist{n}` (variantes). `Executive Editor` aparte. Algunos traen `<!-- comentarios -->` y `[[links]]`.
- **Créditos de tomos**: sin índice de historia (`Writer1`, `Penciler3`, ...).
- **Nombres de autores**: el wiki normaliza con `Module:StaffCorrection/data` (tabla minúsculas → nombre canónico, p. ej. `tony daniel` → `Tony S. Daniel`). Se replica en la ingesta + redirecciones.
- **Fechas**: `Month`/`Year` = fecha de tapa. `Day` = día de salida; la fecha de publicación es `Pubmonth`/`Pubyear` si existen, si no tapa − 2 meses (regla de la propia plantilla). `ReleaseDate` explícito en ~377 páginas.
- **Eventos**: en los números, `Event`, `Event2`, `Event3` (a veces vía redirección: `Bad Seeds` → `Batman: Bad Seeds`). En las páginas de evento/arco, el parámetro `Issues` lista `{{c|...}}` en orden de lectura; también `First`/`Last`/`Collected`. Los `StoryTitle#` a veces enlazan al arco (`[[Batman R.I.P.]]—...`).
- **Contenido de tomos**: `IssueList` con viñetas `* {{c|Serie Vol N #}}: "Título"` en orden de lectura. `{{c|Batman #676}}` = `Batman Vol 1 676` (regla de `Template:C`).
- **Personajes**: el wiki está migrando títulos (`Bruce Wayne (Prime Earth)` es hoy redirección a `Batman (Bruce Wayne)`); se resuelve con el mapa de redirecciones.
- **Categorías**: casi todas las generan las plantillas, así que no están en el wikitext; solo se guardan las `[[Category:...]]` explícitas.

## Números sueltos (issue) — `DC Database:Comic Template` (52,250 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `Editor#_#` | 116,949 | Robert Greenberger |
| `Inker#_#` | 103,603 | Jack Abel |
| `Penciler#_#` | 101,977 | Pat Broderick |
| `Writer#_#` | 100,741 | Gerry Conway |
| `StoryTitle#` | 95,591 | "Day of the Bison" |
| `Synopsis#` | 95,009 | [[Firestorm]] and [[Firehawk]] fly about Manhattan Island and encircle |
| `Appearing#` | 92,683 | '''Featured Characters:''' * {{a\|[[Firestorm Matrix\|Firestorm]]}} ** |
| `CoverArtist#` | 81,799 | Dick Giordano |
| `Colorist#_#` | 73,895 | Gene D'Angelo |
| `Letterer#_#` | 72,261 | Todd Klein |
| `Title` | 52,246 | Superman |
| `Year` | 52,244 | 1968 |
| `Month` | 52,240 | 6 |
| `Executive Editor` | 52,164 | Dick Giordano |
| `Volume` | 52,137 | 1 |
| `Issue` | 52,130 | 6 |
| `Links` | 52,079 | * {{WP2\|Legends (comics)}} |
| `Recommended` | 52,050 | {{Firestorm RR}} |
| `Notes` | 52,045 | * Reprinted in {{co\|Firestorm the Nuclear Man (Collected)}}. |
| `Trivia` | 51,924 | *This comic book contains advertisements for the following products: * |
| `Quotation` | 50,950 | We're going to the mountains to find that belly-draggin' vermin, Snake |
| `Speaker` | 50,906 | [[Wally West (New Earth)\|Wally West]], to [[Tina McGee (New Earth)\|T |
| `Day` | 28,261 | 2 <!-- GCD --> |
| `Cover#Artist#` | 18,279 | Steve Mitchell |
| `Rating` | 14,814 | M |
| `Pubmonth` | 7,230 | 2 <!-- GCD --> |
| `Pubyear` | 7,224 | 1987 |
| `Event` | 6,723 | Teen Titans/Outsiders: The Insiders |
| `Publisher` | 5,314 | Vertigo |
| `NextIssue` | 4,899 | [[Teen Titans Annual Vol 3 2009]] |
| `PreviousIssue` | 2,429 | {{c\|The Flash Annual Vol 2 1\|The Flash Annual (Volume 2) #1}} |
| `OneShot` | 2,089 | Green Lantern; Alan Scott |
| `InkerPages#_#` | 964 | 10-11, 12 (½ page); 13-17 |
| `PencilerPages#_#` | 829 | 39–42 |
| `Event#` | 530 | One Year Later |

Muestras (20): `Batman Vol 1 676`; `Final Crisis Vol 1 1`; `Batman Vol 4 13`; `Firestorm Vol 1 4`; `Secret Origins Vol 1 4`; `Teen Titans Vol 3 11`; `Impulse Vol 1 1`; `Impulse Vol 1 16`; `Karate Kid Vol 1 7`; `All-American Men of War Vol 1 60`; `Jonah Hex: Two-Gun Mojo Vol 1 1`; `Action Comics Vol 1 240`; `Detective Comics Vol 1 261`; `Western Comics Vol 1 58`; `80-Page Giant Vol 1 1`; `2020 Visions Vol 1 1`; `2020 Visions Vol 1 11`; `100 Bullets Vol 1 73`; `Mobfire Vol 1 1`; `Forbidden Tales of Dark Mansion Vol 1 10`

<details><summary>Batman Vol 1 676</summary>

```
| Title = Batman
| Volume = 1
| Issue = 676
| Month = June
| Year = 2008
| Event = Batman R.I.P.
| Executive Editor = Dan DiDio
| CoverArtist1 = Alex Ross <!-- paints -->
| Cover2Artist1 = Tony S. Daniel
| Cover2Artist2 = Sandu Florea
| Cover2Artist3 = Guy Major
| Writer1_1 = Grant Morrison
| Penciler1_1 = Tony S. Daniel
| Inker1_1 = Sandu Florea
| Colorist1_1 = Guy Major
| Letterer1_1 = Randy Gentile
| Editor1_1 = Mike Marts
| Editor1_2 = Jeanine Schaefer <!-- Associate editor -->
| Quotation = Master Bruce has a very clear idea of '''human perfection''' towards which he constantly '''strives''', you un
| Speaker = [[Alfred Pennyworth (New Earth)|Alfred Pennyworth]]
| StoryTitle1 = [[Batman R.I.P.]]—Midnight in the House of Hurt
| Synopsis1 = '''Six Months From Now''' Rain falls from a crimson sky as Batman calls out from the shadows, "You're wrong! B
| Appearing1 = '''Featured Characters:''' * {{a|[[Bruce Wayne (New Earth)|Batman]]}} '''Supporting Characters:''' * {{a|[[Alf
| Notes = * This issue is reprinted in {{Co|Batman R.I.P. (Collected)}}. It is also reprinted in original pencils in {{C
| Trivia = *The [[Zur-En-Arrh]] phrase appears in the "Next in" section. * First appearance of the new Batmobile in actio
| Recommended = {{Batman RR}}
```
</details>

<details><summary>Final Crisis Vol 1 1</summary>

```
| Title = Final Crisis
| Event = Final Crisis
| Volume = 1
| Issue = 1
| Day = 28
| Month = July
| Year = 2008
| Executive Editor = Dan DiDio
| CoverArtist1 = J.G. Jones
| Editor1_1 = Eddie Berganza
| Editor1_2 = Adam Schlagman
| Writer1_1 = Grant Morrison
| Penciler1_1 = J.G. Jones
| Inker1_1 = J.G. Jones
| Colorist1_1 = Alex Sinclair
| Letterer1_1 = Rob Leigh
| PreviousIssue = [[DC Universe Vol 1 0]]
| Quotation = Gentlemen. Can't we monsters and masterminds work together, just this once, to achieve what we've always wante
| Speaker = [[Justin Ballantine (New Earth)|Libra]]
| StoryTitle1 = D. O. A.: The GOD of WAR!
| Synopsis1 = In the dawn of humanity, [[Anthro (New Earth)|Anthro]] is visited by [[Metron (New Earth)|Metron]], who gives 
| Appearing1 = '''Featured Characters:''' * {{a|[[Daniel Turpin (New Earth)|Dan "Terrible" Turpin]]}} * {{a|[[Justice League 
| Notes = * DC Comics' Solicitation: ''Witness the historic start of the final chapter in the [[Crisis]] trilogy that co
| Trivia = * The mobile phone the Human Flame is using is made by a company called 'Damrung'. In addition to echoing 'Sam
| Recommended = {{Crisis RR}}
```
</details>

## Números digitales (issue) — `DC Database:Digital Comic Template` (1,547 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `CoverArtist#` | 2,361 | Jheremy Raapack |
| `Editor#_#` | 2,229 | Sarah Gaydos |
| `Writer#_#` | 1,848 | Tom Taylor |
| `Inker#_#` | 1,813 | Jheremy Raapack |
| `Colorist#_#` | 1,762 | Santi Casas |
| `Penciler#_#` | 1,715 | Tom Derenick |
| `StoryTitle#` | 1,600 | Injustice: Gods Among Us - Chapter 4 |
| `Appearing#` | 1,600 | '''Featured Characters:''' * {{a\|[[Kal-El (Injustice)\|Superman (Kal- |
| `Letterer#_#` | 1,596 | Wes Abbott |
| `Title` | 1,547 | Injustice: Gods Among Us |
| `Day` | 1,547 | 26 |
| `Month` | 1,547 | 3 |
| `Year` | 1,547 | 2014 |
| `Volume` | 1,546 | 1 |
| `Chapter` | 1,535 | 7 |
| `Synopsis#` | 1,114 | Catwoman is seen in an alleyway, commentating the past life of a man,  |
| `Quotation` | 1,084 | [[Justice League (Injustice)\|They]] won't be looking for [[Shiera Hal |
| `Speaker` | 1,084 | [[Bruce Wayne (Injustice)\|Batman]] |
| `Recommended` | 1,066 | {{Supergirl RR}} |
| `Links` | 1,066 | * [https://www.dcuniverse.com/comics/book/young-justice-outsiders-dc-u |
| `Notes` | 1,065 | * This issue was digitally released on May 11, 2015. |
| `Executive Editor` | 1,060 | Bobbie Chase |
| `Trivia` | 1,059 | * Duke was trained by Catwoman in lock picking. * Based on her reactio |
| `Rating` | 980 | T |
| `Synopsis` | 486 |  |
| `PrintIssue` | 287 | Injustice: Gods Among Us Vol 1 8 |
| `NextChapter` | 189 | - |
| `PreviousChapter` | 170 | {{dig\|World's Finest: Batwoman and Supergirl Vol 1 1 (Digital)}} |
| `Publisher` | 58 | DC GO! |
| `Cover#Artist#` | 51 |  |
| `Artist#_#` | 25 | Mike S. Miller |

Muestras (20): `Injustice: Gods Among Us Vol 1 5 (Digital)`; `Injustice: Gods Among Us: Year Three Vol 1 8 (Digital)`; `Swamp Thing: New Roots Vol 1 8 (Digital)`; `Wonder Woman: Agent of Peace Vol 1 5 (Digital)`; `Teen Titans Go!: Booyah! Vol 1 1 (Digital)`; `DC Super Hero Girls: Past Times at Super Hero High Vol 1 12 (Digital)`; `Superman: Man of Tomorrow Vol 1 15 (Digital)`; `Infinite Crisis: Fight for the Multiverse Vol 1 3 (Digital)`; `Wonder Woman: Agent of Peace Vol 1 22 (Digital)`; `Batman: The Adventures Continue Vol 1 17 (Digital)`; `Represent! Vol 1 6 (Digital)`; `Sensational Wonder Woman Vol 1 9 (Digital)`; `RWBY/Justice League Vol 1 3 (Digital)`; `DC Super Hero Girls: Weird Science Vol 1 3 (Digital)`; `DC Super Hero Girls: Weird Science Vol 1 10 (Digital)`; `Red Hood: Outlaws Vol 1 15 (Digital)`; `Red Hood: Outlaws Vol 1 40 (Digital)`; `Zatanna & the Ripper Vol 1 47 (Digital)`; `DC Super Hero Girls: Spaced Out Vol 1 4 (Digital)`; `Arrow: The Dark Archer Vol 1 3 (Digital)`

<details><summary>Injustice: Gods Among Us Vol 1 5 (Digital)</summary>

```
| Title = Injustice: Gods Among Us
| Volume = 1
| Chapter = 5
| Day = 12
| Month = 2
| Year = 2013
| Rating = T
| Executive Editor = Bobbie Chase
| CoverArtist1 = Jheremy Raapack
| CoverArtist2 = Andrew Elder
| Writer1_1 = Tom Taylor
| Penciler1_1 = Bruno Redondo
| Inker1_1 = Bruno Redondo
| Colorist1_1 = Alejandro Sanchez
| Letterer1_1 = Wes Abbott
| Editor1_1 = Jim Chadwick
| Editor1_2 = Sarah Litt
| Quotation = [[Harleen Quinzel (Injustice)|You]] crashed a police car outside. You're not exactly keeping a low profile.
| Speaker = [[Oliver Queen (Injustice)|Green Arrow]]
| StoryTitle1 = Injustice: Gods Among Us - Chapter 6
| Synopsis1 = Harley Quinn, after having been taking captive by the authorities, is using her handcuffs to strangle her poli
| Appearing1 = '''Featured Characters:''' * {{a|[[Oliver Queen (Injustice)|Green Arrow (Oliver Queen)]]}} * {{a|[[Harleen Qui
| PrintIssue = Injustice: Gods Among Us Vol 1 2
```
</details>

<details><summary>Injustice: Gods Among Us: Year Three Vol 1 8 (Digital)</summary>

```
| Title = Injustice: Gods Among Us: Year Three
| Volume = 1
| Chapter = 8
| Day = 18
| Month = 11
| Year = 2014
| Rating = T
| PrintIssue = Injustice: Gods Among Us: Year Three Vol 1 4
| Executive Editor = Bobbie Chase
| CoverArtist1 = Neil Googe
| CoverArtist2 = Rex Lokus
| Writer1_1 = Tom Taylor
| Penciler1_1 = Mike S. Miller
| Inker1_1 = Mike S. Miller
| Colorist1_1 = J. Nanjan
| Letterer1_1 = Wes Abbott
| Editor1_1 = Aniz Ansari
| Editor1_2 = Jim Chadwick
| StoryTitle1 = Chapter Eight: Ragman's Souls
| Appearing1 = '''Featured Characters:''' * {{a|[[John Constantine (Injustice)|John Constantine]]}} * {{a|[[Rory Regan (Injus
```
</details>

## Tomos recopilatorios (collection) — `DC Database:Collected Template` (4,011 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `Inker#` | 19,094 | Ivan Reis |
| `Penciler#` | 17,207 | Tom Grummett |
| `Editor#` | 12,497 | Jann Jones |
| `Colorist#` | 11,132 | James Sinclair |
| `Writer#` | 10,573 | Brian Azzarello |
| `Letterer#` | 9,206 | Phil Balsman |
| `CoverArtist#` | 6,697 | Dexter Vines |
| `Month` | 4,010 | January |
| `Year` | 4,010 | 2006 |
| `Overview` | 4,009 | Spinning out of [[Identity Crisis\|IDENTITY CRISIS]], [[Countdown to I |
| `IssueList` | 4,006 | This paperback collects the following comic books: *{{C\|Batman Vol 1  |
| `ISBN` | 4,005 | 978-1401202453 |
| `Executive Editor` | 3,969 | Dan Didio |
| `Rating` | 3,953 | T |
| `StoryArcs` | 3,952 | Hellblazer: Freezes Over; Hellblazer: Lapdogs and Englishmen |
| `Notes` | 3,941 | * {{c\|Justice League of America Vol 1 58}} is not reprinted in this c |
| `Volume` | 3,899 | Superman Vol 1 |
| `Day` | 3,674 | 4 |
| `NextCollection` | 2,977 | Hellblazer: The Devil You Know (Collected) |
| `PreviousCollection` | 2,961 | 100 Bullets: Strychnine Lives (Collected) |
| `Publisher` | 322 | Wildstorm |
| `LinkOverride` | 165 | Green Lantern |
| `Co-Publisher` | 61 | Dark Horse Comics |
| `Cover#Artist#` | 43 |  |

Muestras (20): `Final Crisis New Edition (Collected)`; `Green Lantern: The Sinestro Corps War (Collected)`; `Jack Kirby's New Gods (Collected)`; `Hellblazer: Fear and Loathing (Collected)`; `All-Star Comics Archives Vol. 2 (Collected)`; `Sandman: Preludes and Nocturnes (Collected)`; `Simon Dark: Ashes (Collected)`; `Showcase Presents: Green Arrow Vol. 1 (Collected)`; `Plastic Man Archives Vol. 5 (Collected)`; `Wonder Woman Archives Vol. 5 (Collected)`; `Batman: The Dark Knight Archives Vol 7 (Collected)`; `Superman Chronicles Vol. 5 (Collected)`; `Diablo: Sword of Justice (Collected)`; `Batman: Contagion (Collected)`; `Swamp Thing: Rotworld - The Green Kingdom (Collected)`; `Batgirl: The Lesson (Collected)`; `Showcase Presents: Strange Adventures Vol. 2 (Collected)`; `Deadman: Book Four (Collected)`; `Batman and the Outsiders: The Chrysalis (Collected)`; `Justice Society Vol. 2 (Collected)`

<details><summary>Final Crisis New Edition (Collected)</summary>

```
| Volume = Final Crisis Vol 1
| Day = 16
| Month = 4
| Year = 2014
| Rating = T
| ISBN = 978-1401245177
| CoverArtist1 = J.G. Jones
| Writer1 = Grant Morrison
| Penciler1 = J.G. Jones
| Penciler2 = Carlos Pacheco
| Penciler3 = Doug Mahnke
| Penciler4 = Christian Alamy
| Penciler5 = Marco Rudy
| Penciler6 = Jesús Merino
| Penciler7 = Matthew Clark
| Penciler8 = Lee Garbett
| Inker1 = J.G. Jones
| Inker2 = Jesús Merino
| Inker3 = Marco Rudy
| Inker4 = Tom Nguyen
| Inker5 = Doug Mahnke
| Inker6 = Drew Geraci
| Inker7 = Christian Alamy
| Inker8 = Norm Rapmund
| Inker9 = Rodney Ramos
| Inker10 = Walden Wong
| Inker11 = Rob Hunter
| Inker12 = Don Ho
| Inker13 = Trevor Scott
| Colorist1 = Alex Sinclair
| Colorist2 = Pete Pantazis
| Colorist3 = Tony Aviña
| Colorist4 = David Baron
| Colorist5 = Richard Horie
| Colorist6 = Guy Major
| Letterer1 = Rob Leigh
| Letterer2 = Rob Clark, Jr.
| Letterer3 = Travis Lanham
| Letterer4 = Steve Wands
| Letterer5 = Ken Lopez
| Letterer6 = Nick J. Napolitano
| Letterer7 = Jared K. Fletcher
| Editor1 = Eddie Berganza
| Editor2 = Mike Marts
| StoryArcs = Final Crisis
| Overview = '''Final Crisis''' is a trade paperback collecting the main storyline of the [[Final Crisis]] crossover event.
| IssueList = This trade paperback reprints stories from the following issues: * {{c|DC Universe Vol 1 0}}: "Let There Be Li
| Notes = * This trade paperback contains an introduction by Jay Babcock and a variant cover gallery. * The title of the
```
</details>

<details><summary>Green Lantern: The Sinestro Corps War (Collected)</summary>

```
| Volume = Green Lantern Vol 4
| Day = 14
| Month = 9
| Year = 2011
| ISBN = 978-0857688040
| Executive Editor = Eddie Berganza
| CoverArtist1 = Ethan Van Sciver
| CoverArtist2 = Moose Baumann
| Writer1 = Geoff Johns
| Writer2 = Dave Gibbons
| Writer3 = Peter Tomasi
| Penciler1 = Ethan Van Sciver
| Penciler2 = Ivan Reis
| Penciler3 = Patrick Gleason
| Penciler4 = Angel Unzueta
| Penciler5 = Pascal Alixe
| Penciler6 = Dustin Nguyen
| Penciler7 = Jamal Igle
| Inker1 = Ethan Van Sciver
| Inker2 = Oclair Albert
| Inker3 = Prentis Rollins
| Inker4 = Drew Geraci
| Inker5 = Vicente Cifuentes
| Inker6 = Julio Ferreira
| Inker7 = Rodney Ramos
| Inker8 = Rob Hunter
| Inker9 = Marlo Alquiza
| Inker10 = Jerry Ordway
| Inker11 = Derek Fridolfs
| Inker12 = Tom Nguyen
| Inker13 = Dan Davis
| Inker14 = Rebecca Buchman
| Colorist1 = Moose Baumann
| Colorist2 = Guy Major
| Colorist3 = Rod Reis
| Colorist4 = David Curiel
| Colorist5 = J.D. Smith
| Colorist6 = Rod Reis
| Letterer1 = Rob Leigh
| Letterer2 = Phil Balsman
| Letterer3 = Steve Wands
| Letterer4 = Nick J. Napolitano
| Editor1 = Eddie Berganza
| Editor2 = Peter Tomasi
| StoryArcs = Sinestro Corps War
| Overview = '''Green Lantern: The Sinestro Corps War''' is a trade paperback that collects the main issues of the [[Sinest
| IssueList = This trade paperback collects the following chapters: * {{c|Green Lantern: Sinestro Corps Special Vol 1 1}}: "
| Notes = * This trade paperback includes a "Sinestro Corps War Journal", which is a conversation between [[Geoff Johns]
```
</details>

## Eventos (event) — `DC Database:Event Template` (132 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `OfficialName` | 132 | Brightest Day |
| `Universe` | 132 | New Earth |
| `Heroes` | 132 | [[Green Lantern Corps]]; [[Justice League International]]; [[New Guard |
| `Creators` | 132 | Bill Willingham; Lilah Sturges |
| `First` | 132 | DCU: Rebirth Vol 1 1 |
| `Overview` | 132 | '''Behold! The Millennium Giants!''' was an event that ran through sev |
| `HistoryText` | 132 | One of the main themes is looking at the iconography of the big three, |
| `Aliases` | 131 | Gorilla Warfare |
| `Locations` | 131 | [[Apokolips]], [[Earth]] |
| `Villains` | 131 | [[Anti-Monitor (Antimatter Universe)\|The Anti-Monitor]], [[Weaponers  |
| `Titles` | 131 | [[Legends Vol 1\|Legends]] |
| `Collected` | 131 | ''[[Batman: Knightfall Part Three - KnightsEnd (Collected)\|Batman: Kn |
| `Links` | 131 | * {{WP2\|''Underworld Unleashed''}} * [https://crisisonearthprime.com/ |
| `Others` | 130 | [[Justice Society of America (New Earth)\|Justice Society of America]] |
| `Last` | 130 | Blackest Night #1 |
| `Notes` | 130 | * All four issues of ''The Final Night'' were reprinted in trade paper |
| `Trivia` | 128 | * What Krona learnt during this crossover is put to use in the ongoing |
| `RecommendedReading` | 128 | {{JLApe}} |
| `Issues` | 127 | {{LegendsList}} |
| `Items` | 80 | [[Kryptonite]] |
| `Vehicles` | 78 | [[Batmobile]] |
| `Weapons` | 78 |  |
| `Title` | 74 | Black Diamond Probability |
| `Quotation` | 63 | Worlds lived, worlds died. Nothing will ever be the same. |
| `Speaker` | 63 | [[Caitlin Snow (Arrowverse)\|Caitlin Snow]] |
| `QuoteSource` | 62 | The Flash (2014 TV Series) Episode: Running to Stand Still |
| `Origin` | 56 |  |
| `Wikipedia` | 24 |  |
| `HistoryHeader` | 11 | Synopsis |
| `Distinguish#D` | 10 |  |
| `Distinguish#` | 10 |  |
| `CustomSection#` | 2 |  |
| `CustomText#` | 2 |  |

Muestras (20): `Final Crisis`; `Batman: Bad Seeds`; `Sinestro Corps War`; `Villains United`; `Lazarus Planet`

<details><summary>Final Crisis</summary>

```
| OfficialName = Final Crisis
| Aliases = "The Day Evil Won"{{cn}}<br>Darkseid Crisis<ref>{{c|Batman: The Brave and the Bold Vol 2 19}}</ref>
| Universe = New Earth; Prime Earth; Dark Multiverse
| Locations = [[DC Universe]]
| Quotation = There was a war in heaven, Mr. Turpin. And I won. Your future belongs to Darkseid now.
| Speaker = [[Darkseid (New Earth)|Darkseid]]
| QuoteSource = Final Crisis Vol 1 1
| Heroes = [[Kal-El (New Earth)|Superman]], [[Bruce Wayne (New Earth)|Batman]], [[Diana of Themyscira (New Earth)|Wonder 
| Villains = [[Darkseid (New Earth)|Darkseid]], [[Libra (New Earth)|Libra]],<br />[[Secret Society of Super-Villains (Villa
| Others = [[Monitors]],<br />[[Justice League of America (New Earth)|Justice League of America]], [[Justice Society of A
| Titles = [[Final Crisis Vol 1|Final Crisis]]
| Collected = {{co|Final Crisis (Collected)}}, {{co|Final Crisis New Edition (Collected)}}, {{co|Final Crisis Companion (Col
| Creators = Grant Morrison; J.G. Jones; Carlos Pacheco
| First = Final Crisis Vol 1 1
| Last = Final Crisis Vol 1 7
| Overview = '''Final Crisis''', "The Day Evil Won", is an all-out war and invasion of [[Earth]] by the forces of [[Darksei
| HistoryText = When the [[Source (New Earth)|Source]] initiated the demise of the [[Fourth World]] and the [[Death of the New
| Issues = '''Core Issues''': * {{c|Final Crisis Vol 1 1}} * {{c|Final Crisis Vol 1 2}} * {{c|Final Crisis Vol 1 3}} * {{
| Items = * '''[[Anti-Life Equation]]''' * '''[[Crime Bible]]''' * '''[[Miracle Machine]]''' * '''[[Mobius Chair]]''' * 
| Weapons = * [[Green Lantern Ring]] * [[Radion (material)|Radion]] gun
| Notes = * A recurring theme throughout the book is "fire," and what it means for humanity. ** [[Grant Morrison]] has s
| Trivia = * There were several early comments made to foreshadow ''Final Crisis''. [[Drake Burroughs (Pre-Zero Hour)|Wil
| RecommendedReading = * {{V|Crisis on Infinite Earths Vol 1}} * {{V|Zero Hour: Crisis in Time Vol 1}} * {{V|Identity Crisis Vol 1}} 
| Wikipedia = Final Crisis
| Links = * [https://www.youtube.com/watch?v=59_e1GxSijw History of Crisis in the DC Universe and Multiverse Video at Yo
```
</details>

<details><summary>Batman: Bad Seeds</summary>

```
| Title = Bad Seeds
| OfficialName = Batman: Bad Seeds
| Universe = Prime Earth
| Locations = [[Gotham City]]
| Heroes = [[Bruce Wayne (Prime Earth)|Batman (Bruce Wayne)]], [[Batman Family|Bat-Family]]
| Villains = [[Pamela Isley (Prime Earth)|Poison Ivy (Mayor Isley)]], [[Vandal Savage (Prime Earth)|Commissioner Savage]]
| Titles = {{v|Batman Vol 4}}; {{v|Poison Ivy Vol 1}}, {{v|Batgirl Vol 6}}, {{v|Batwoman Vol 4}}, {{v|Catwoman Vol 5}}, {
| Creators = Matt Fraction; G. Willow Wilson; Tom Taylor
| First = Batman: Bad Seeds - Sunset Vol 1 1
| Last = Batman: Bad Seeds - Sunrise Vol 1 1
| Overview = '''Batman: Bad Seeds''' is a [[2026]] crossover event written by [[Matt Fraction]] and [[G. Willow Wilson]] wh
| HistoryHeader = Synopsis
| HistoryText = === Prelude === {{Expand}} <!--- Should include: Poison Ivy 45 to 47, Batman Vol 4 9, who Verity is, why Poiso
| Issues = '''Prologue''' * {{c|Poison Ivy Vol 1 45}} * {{c|Poison Ivy Vol 1 46}} * {{c|Poison Ivy Vol 1 47}} '''Core''' 
| RecommendedReading = * {{Batman RR}} ** {{v|Batgirl Vol 6}} ** {{v|Batman Vol 4}} ** {{v|Batwoman Vol 4}} ** ''[[The Joker War]]'' 
| Links = * [https://www.dc.com/blog/2026-08-26/planting-gotham-city-s-bad-seeds Planting Gotham City's Bad Seeds]
```
</details>

## Arcos / storylines (event) — `DC Database:Storyline Template` (743 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `Universe` | 742 | New Earth |
| `Creators` | 742 | Ron Marz |
| `First` | 742 | Batman: The Long Halloween Vol 1 1 |
| `Overview` | 742 | '''''Whatever Happened to the Man of Tomorrow?''''' is a collection of |
| `OfficialName` | 741 | Emerald Twilight |
| `Titles` | 741 | ''[[Amazons Attack Vol 1\|Amazons Attack!]]'', [[Wonder Woman Vol 3\|' |
| `Heroes` | 740 | [[Batman]], [[Nightwing]], [[Robin]], [[Oracle]], [[The Penguin]], [[C |
| `Last` | 740 | Justice League: A Midsummer's Nightmare #3 |
| `Villains` | 736 | [[Kenneth Braverman (New Earth)\|Conduit]] |
| `Collected` | 734 | [[Batman: Ten Nights of the Beast (Collected)\|Batman: Ten Nights of t |
| `Issues` | 734 | * {{c\|Batman: Gordon of Gotham Vol 1 1}} * {{c\|Batman: Gordon of Got |
| `Locations` | 733 | [[Metropolis]]; [[Washington, D.C.]] |
| `Others` | 733 | [[Sheila Haywood (New Earth)\|Sheila Haywood]], [[Ralph Bundy (New Ear |
| `Notes` | 729 | * Due to the reality warping effects of Superboy-Prime's pounding of t |
| `Links` | 729 | * [[Wikipedia:Deathstroke\|Deathstroke at Wikipedia.org]] |
| `Aliases` | 728 | ''[[War Drums]]'', ''[[War Crimes]]'' |
| `RecommendedReading` | 728 | * [[Arkham Asylum: A Serious House on Serious Earth]] * [[Batman: Knig |
| `Trivia` | 724 | * Actor Henry Cavill cited ''Red Son'' as one of the four Superman com |
| `HistoryText` | 715 | The cold, fairly dystopian re-imagining of Krypton created by [[John B |
| `Title` | 548 | The Last Arkham |
| `Vehicles` | 489 | [[Quantum Jet]]; [[T-Jet]] |
| `Items` | 489 | * [[Kryptonite]] * [[Sunstone]] |
| `Weapons` | 486 | [[Toastmasters]]; Ultrasonic missiles |
| `Quotation` | 402 | It's just my '''true potential''', my '''inner spirit'''. I'm maturing |
| `Speaker` | 400 | [[Alfred Pennyworth (New Earth)\|Alfred Pennyworth]] |
| `QuoteSource` | 396 | Batman Vol 1 454 |
| `Origin` | 354 | [[Possible Futures]] |
| `#` | 9 |  |
| `Distinguish#` | 8 | Amazons Attack Vol 2 |
| `Distinguish#D` | 8 |  |

Muestras (20): `Batman R.I.P.`; `Batman: Ten Nights of the Beast`; `Superman/Batman: Public Enemies`; `Hellblazer: Dangerous Habits`; `Superboy: Watery Grave`; `Supergirl: Who Is Superwoman?`; `Batman: Freakout`; `JLA: Divided We Fall`; `Doom Patrol: Robotman Unchained`; `Batman: Life After Death`; `Green Lantern: Baptism of Fire`; `Robin: Unmasked!`; `Wonder Woman: Stoned`; `Justice League Dark: War for the Books of Magic`; `Wonder Woman: A Murder of Crows`; `Wonder Woman: Three Hearts`; `Supergirl: Plain Sight`; `The Flash: Year One`; `Batman: Watchtower`

<details><summary>Batman R.I.P.</summary>

```
| Title = Batman R.I.P.
| OfficialName = Batman R.I.P.
| Universe = New Earth; Prime Earth
| Locations = [[Gotham City]]
| Heroes = [[Bruce Wayne (New Earth)|Batman]], [[Club of Heroes]], [[Richard Grayson (New Earth)|Nightwing]], [[Timothy D
| Villains = [[Black Glove]], [[Club of Villains]], [[Simon Hurt (New Earth)|Doctor Hurt]], [[Joker (New Earth)|Joker]], [[
| Others = [[Alfred Pennyworth (New Earth)|Alfred Pennyworth]], [[Damian Wayne (New Earth)|Damian]], [[James Gordon (New 
| Titles = [[Batman Vol 1|Batman]], [[Batman and the Outsiders Vol 2|Batman and the Outsiders]], [[Detective Comics Vol 1
| Collected = [[Batman R.I.P. (Collected)|Batman R.I.P.]]
| Creators = Grant Morrison; Tony S. Daniel; Sandu Florea; Alex Ross; Paul Dini; Dustin Nguyen
| First = Batman #676
| Last = Batman #681
| Quotation = In the '''cave''', in '''Nanda Parbat''', I hunted down and '''killed''' and '''ate''' the last traces of fear
| Speaker = [[Bruce Wayne (New Earth)|Bruce Wayne]]
| QuoteSource = Batman Vol 1 681
| Overview = '''Batman R.I.P.''' is a [[Batman]] storyline written by [[Grant Morrison]] with illustrations by [[Tony S. Da
| HistoryText = === Prelude=== In a private meeting, [[Bruce Wayne (New Earth)|Batman]] talks to the [[Joker (New Earth)|Joker
| Issues = * ''[[Batman Vol 1|Batman R.I.P.]]'' ** {{c|Batman #676}} -- Midnight in the House of Hurt ** {{c|Batman #677}
| Vehicles = [[Batmobile]], [[Robin's Motorcycle]]
| Items = [[Bat-Radia]], [[Batcomputer]]
| Notes = * The Tie-Ins to the main storyline take place in the following order: ** [[Batman: Heart of Hush]] serves as 
| RecommendedReading = {{Batman RR}}
| Links = * {{WP2|Batman R.I.P.}}
```
</details>

<details><summary>Batman: Ten Nights of the Beast</summary>

```
| Title = Ten Nights of the Beast
| OfficialName = Batman: Ten Nights of the Beast
| Aliases = Ten Nights of the Beast
| Universe = New Earth
| Locations = [[Gotham City]]
| Heroes = [[Bruce Wayne (New Earth)|Batman]], [[Jason Todd (New Earth)|Robin]]
| Villains = [[Anatoli Knyazev (New Earth)|The KGBeast]], [[Nabih Salari]]
| Others = [[James Gordon (New Earth)|Commissioner James Gordon]],<br />[[Ralph Bundy (New Earth)|Ralph Bundy]], Keith Pa
| Titles = [[Batman Vol 1|Batman]]
| Collected = [[Batman: Ten Nights of the Beast (Collected)|Batman: Ten Nights of the Beast]], [[Batman: The Caped Crusader 
| Creators = Jim Starlin; Jim Aparo
| First = Batman #417
| Last = Batman #420
| Overview = '''Batman: Ten Nights of the Beast''' is a four part storyline written by [[Jim Starlin]] and illustrated by [
| HistoryText = The [[Anatoli Knyazev (New Earth)|KGBeast]] comes to [[Gotham City|Gotham]]. A top-secret cell in the [[KGB]] 
| Issues = * {{c|Batman #417}} * {{c|Batman #418}} * {{c|Batman #419}} * {{c|Batman #420}}
| Notes = [[File:KGBeast not dead.jpg|thumb|right|150px|[[Batman Vol 1 439|Murder isn't cool, kids]]]] * During the "[[B
| Trivia = * The {{WP|Strategic Defense Initiative}} has come up further in comics. [[Niles Caulder (New Earth)|Niles Cau
| RecommendedReading = * [[Batman: A Death in the Family]] * [[The Many Deaths of the Batman]] * [[Robin III: Cry of the Huntress]]
| Links = * {{WP2|KGBeast}}
```
</details>

## Series / volúmenes (series) — `DC Database:Volume Template` (2,634 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `TradePaperbackName#` | 4,741 | Superman: Action Comics: Invisible Mafia (Collected) |
| `TradePaperbackYear#` | 4,741 | 2013 |
| `TradePaperbackISBN#` | 4,697 | 978-1401241896 |
| `IssueImage` | 2,633 | Teen Titans v.1 1.jpg |
| `StartYear` | 2,633 | 2006 |
| `EndYear` | 2,633 | 2006 |
| `TotalIssues` | 2,629 | 53 |
| `IssueList` | 2,629 | *[[Doom Patrol Vol 1 86\|Doom Patrol (Volume 1) #86]] *[[Doom Patrol V |
| `Type` | 2,628 | Limited Series |
| `StartMonth` | 2,628 | September |
| `EndMonth` | 2,628 | September |
| `History` | 2,627 | '''Teen Titans (Volume 1)''' began publication in February of [[1966]] |
| `Featured` | 2,625 | Titans; Beast Boy; Blue Beetle; Cyborg; Kid Flash; Raven; Robin; Tim D |
| `Creators` | 2,619 | Vincent Sullivan |
| `SeeAlso` | 2,605 | *{{v\|Action Comics Vol 1}} *{{v\|Superman Vol 1}} *{{v\|World's Fines |
| `Publisher` | 2,604 | Charlton Comics |
| `Crossovers` | 2,588 | Day of Judgment; Our Worlds at War; Joker's Last Laugh; DC One Million |
| `SpecialName#` | 2,577 | {{C\|Action Comics Presents: Doomsday Special Vol 1 1}} |
| `SpecialYear#` | 2,576 | 2000 |
| `StoryArcs` | 2,544 | [[JSA: Justice Be Done\|Justice Be Done]]<br/>[[JSA: Injustice Be Done |
| `AnnualName#` | 2,508 | {{c\|Action Comics Annual Vol 1 3}} |
| `AnnualYear#` | 2,505 | 1993 |
| `NextVol` | 638 | Doom Patrol Vol 2 |
| `PreviousVol` | 619 | Hawk and Dove Vol 1 |
| `LogoImage` | 165 | Electric_Warriors_(2018)_logo.png |
| `Notes` | 164 | *''All-Star Superman'' was directly adapted into a [[All-Star Superman |
| `Volume` | 61 | 1 |
| `Storylines` | 44 |  |

Muestras (20): `Batman Vol 3`; `Ghosts Vol 1`; `Superman: The Man of Tomorrow Vol 1`; `Sandman Vol 1`; `Doorway to Nightmare Vol 1`; `Green Lantern: The New Corps Vol 1`; `Vext Vol 1`; `Batman/Lobo: Deadly Serious Vol 1`; `Plop Vol 1`; `DC/Wildstorm: Dreamwar Vol 1`; `Batman: Bane of the Demon Vol 1`; `Showcase '96 Vol 1`; `Hard Time: Season Two Vol 1`; `Zero Girl: Full Circle Vol 1`; `Friday the 13th: How I Spent My Summer Vacation Vol 1`; `Hourman Vol 1`; `Cosmic Boy Vol 1`; `Deadshot Vol 2`; `Legends of the DC Universe Vol 1`; `Red Robin Vol 1`

<details><summary>Batman Vol 3</summary>

```
| IssueImage = Batman Vol 3 1.jpg
| Type = Ongoing Series
| TotalIssues = 163
| StartMonth = 8
| StartYear = 2016
| EndMonth = 7
| EndYear = 2026
| Creators = Tom King; David Finch; James Tynion IV; Joshua Williamson; Chip Zdarsky; Jeph Loeb
| Featured = Batman; Batgirl; Gotham Academy; Catwoman; Robin; Vandal Savage; Joker
| StoryArcs = [[Batman: I Am Gotham|I Am Gotham]]; [[Batman: I Am Suicide|I Am Suicide]]; [[Batman: I Am Bane|I Am Bane]]; [
| Crossovers = DC Rebirth; Night of the Monster Men; The Button; The Price; Year of the Villain; The Joker War; Infinite Fron
| PreviousVol = Batman Vol 2
| NextVol = Batman Vol 4
| History = '''''Batman''''' '''(Volume 3)''' is a superhero comic book series published by [[DC Comics]] from [[2016]] to
| IssueList = <table><tr valign="top"><td> === 1–50 === * {{c|Batman Vol 3 1}} * {{c|Batman Vol 3 2}} * {{c|Batman Vol 3 3}}
| AnnualName1 = {{c|Batman Annual Vol 3 1}}
| AnnualYear1 = 2017
| AnnualName2 = {{c|Batman Annual Vol 3 2}}
| AnnualYear2 = 2018
| AnnualName3 = {{c|Batman Annual Vol 3 3}}
| AnnualYear3 = 2019
| AnnualName4 = {{c|Batman Annual Vol 3 4}}
| AnnualYear4 = 2019
| AnnualName5 = {{c|Batman Annual Vol 3 5}}
| AnnualYear5 = 2020
| AnnualName6 = {{c|Batman 2021 Annual Vol 3 1}}
| AnnualYear6 = 2021
| AnnualName7 = {{c|Batman 2022 Annual Vol 3 1}}
| AnnualYear7 = 2022
| SpecialName1 = {{c|Batman: Rebirth Vol 1 1}}
| SpecialYear1 = 2016
| SpecialName2 = {{c|Batman/Elmer Fudd Special Vol 1 1}}
| SpecialYear2 = 2017
| SpecialName3 = {{c|Batman: Pennyworth R.I.P. Vol 1 1}}
| SpecialYear3 = 2020
| SpecialName4 = {{c|Batman: The Joker War Zone Vol 1 1}}
| SpecialYear4 = 2020
| SpecialName5 = {{c|Batman: Fear State: Alpha Vol 1 1}}
| SpecialYear5 = 2021
| SpecialName6 = {{c|Batman: Fear State: Omega Vol 1 1}}
| SpecialYear6 = 2021
| SpecialName7 = {{c|Batman: Legends of Gotham Vol 1 1}}
| SpecialYear7 = 2023
| SpecialName8 = {{c|Batman/Catwoman: The Gotham War: Battle Lines Vol 1 1}}
| SpecialYear8 = 2023
| SpecialName9 = {{c|Batman/Catwoman: The Gotham War: Scorched Earth Vol 1 1}}
| SpecialYear9 = 2023
| SpecialName10 = {{c|Batman: Uncovered Vol 1 1}}
| SpecialYear10 = 2024
| TradePaperbackName1 = Batman: I Am Gotham (Collected)
| TradePaperbackYear1 = 2017
| TradePaperbackISBN1 = 978-1401267773
| TradePaperbackName2 = Batman: Night of the Monster Men (Collected)
| TradePaperbackYear2 = 2017
| TradePaperbackISBN2 = 978-1401270674
| TradePaperbackName3 = Batman: I Am Suicide (Collected)
| TradePaperbackYear3 = 2017
| TradePaperbackISBN3 = 978-1401268541
| TradePaperbackName4 = Batman: I Am Bane (Collected)
| TradePaperbackYear4 = 2017
| TradePaperbackISBN4 = 978-1401271312
| TradePaperbackName5 = Batman/The Flash: The Button (Collected)
| TradePaperbackYear5 = 2017
| TradePaperbackISBN5 = 978-1401276447
| TradePaperbackName6 = Batman: The War of Jokes and Riddles (Collected)
| TradePaperbackYear6 = 2017
| TradePaperbackISBN6 = 978-1401273613
| TradePaperbackName7 = Batman: Rules of Engagement (Rebirth) (Collected)
| TradePaperbackYear7 = 2018
| TradePaperbackISBN7 = 978-1401277314
| TradePaperbackName8 = Batman: Bride or Burglar? (Collected)
| TradePaperbackYear8 = 2018
| TradePaperbackISBN8 = 978-1401280277
| TradePaperbackName9 = Batman: The Wedding (Collected)
| TradePaperbackYear9 = 2018
| TradePaperbackISBN9 = 978-1401283381
| TradePaperbackName10 = Batman: Cold Days (Collected)
| TradePaperbackYear10 = 2018
| TradePaperbackISBN10 = 978-1401283520
| TradePaperbackName11 = Batman: The Tyrant Wing (Collected)
| TradePaperbackYear11 = 2019
| TradePaperbackISBN11 = 978-1401288440
| TradePaperbackName12 = Batman: Knightmares (Collected)
| TradePaperbackYear12 = 2019
| TradePaperbackISBN12 = 978-1401291430
| TradePaperbackName13 = Batman: The Fall and the Fallen (Collected)
| TradePaperbackYear13 = 2020
| TradePaperbackISBN13 = 978-1779501608
| TradePaperbackName14 = Batman: City of Bane Part 1 (Collected)
| TradePaperbackYear14 = 2020
| TradePaperbackISBN14 = 978-1401299583
| TradePaperbackName15 = Batman: City of Bane Part 2 (Collected)
| TradePaperbackYear15 = 2020
| TradePaperbackISBN15 = 978-1779502841
| TradePaperbackName16 = Batman: City of Bane: The Complete Collection (Collected)
| TradePaperbackYear16 = 2020
| TradePaperbackISBN16 = 978-1779505958
| TradePaperbackName17 = Batman: Their Dark Designs (Collected)
| TradePaperbackYear17 = 2020
| TradePaperbackISBN17 = 978-1779505569
| TradePaperbackName18 = Batman: The Joker War (Collected)
| TradePaperbackYear18 = 2021
| TradePaperbackISBN18 = 978-1779507907
| TradePaperbackName19 = The Joker War Saga (Collected)
| TradePaperbackYear19 = 2021
| TradePaperbackISBN19 = 978-1779514967
| TradePaperbackName20 = Batman: Ghost Stories (Collected)
| TradePaperbackYear20 = 2021
| TradePaperbackISBN20 = 978-1779510631
| TradePaperbackName21 = Batman: The Cowardly Lot (Collected)
| TradePaperbackYear21 = 2021
| TradePaperbackISBN21 = 978-1779511980
| TradePaperbackName22 = Batman: Fear State (Collected)
| TradePaperbackISBN22 = 978-1779514301
| TradePaperbackYear22 = 2022
| TradePaperbackName23 = Batman: Fear State Saga (Collected)
| TradePaperbackISBN23 = 978-1779520036
| TradePaperbackYear23 = 2022
| TradePaperbackName24 = Batman: Abyss (Collected)
| TradePaperbackISBN24 = 978-1779516565
| TradePaperbackYear24 = 2022
| TradePaperbackName25 = Batman: Failsafe (Collected)
| TradePaperbackISBN25 = 978-1779519931
| TradePaperbackYear25 = 2023
| TradePaperbackName26 = Batman: The Bat-Man of Gotham (Collected)
| TradePaperbackISBN26 = 978-1779520425
| TradePaperbackYear26 = 2023
| TradePaperbackName27 = Batman/Catwoman: The Gotham War (Collected)
| TradePaperbackISBN27 = 978-1779525987
| TradePaperbackYear27 = 2024
| TradePaperbackName28 = Batman: The Rebirth Deluxe Edition Book One (Collected)
| TradePaperbackYear28 = 2017
| TradePaperbackISBN28 = 978-1401271329
| TradePaperbackName29 = Batman: Rebirth Deluxe Edition Book 2 (Collected)
| TradePaperbackYear29 = 2018
| TradePaperbackISBN29 = 978-1401280352
| TradePaperbackName30 = Batman: Rebirth Deluxe Edition Book 3 (Collected)
| TradePaperbackYear30 = 2018
| TradePaperbackISBN30 = 978-1401285210
| TradePaperbackName31 = Batman: Deluxe Edition Book 4 (Collected)
| TradePaperbackYear31 = 2019
| TradePaperbackISBN31 = 978-1401291884
| TradePaperbackName32 = Batman: Deluxe Edition Book 5 (Collected)
| TradePaperbackYear32 = 2020
| TradePaperbackISBN32 = 978-1779503145
| TradePaperbackName33 = Batman: Deluxe Edition Book 6 (Collected)
| TradePaperbackYear33 = 2022
| TradePaperbackISBN33 = 978-1779515704
| TradePaperbackName34 = Batman/Catwoman: The Wedding Album (Collected)
| TradePaperbackYear34 = 2018
| TradePaperbackISBN34 = 978-1401286538
| TradePaperbackName35 = Batman by Tom King Omnibus Vol. 1 (Collected)
| TradePaperbackYear35 = 2025
| TradePaperbackISBN35 = 978-1799502395
| TradePaperbackName36 = Batman by Tom King Omnibus Vol. 2 (Collected)
| TradePaperbackYear36 = 2026
| TradePaperbackISBN36 = 978-1799508779
| TradePaperbackName37 = Batman by Tom King Omnibus Vol. 3 (Collected)
| TradePaperbackYear37 = 2026
| TradePaperbackISBN37 = 978-1799508861
| TradePaperbackName38 = Batman by James Tynion IV Omnibus Vol. 1 (Collected)
| TradePaperbackYear38 = 2025
| TradePaperbackISBN38 = 978-1799500636
| TradePaperbackName39 = Batman by James Tynion IV Omnibus Vol. 2 (Collected)
| TradePaperbackYear39 = 2026
| TradePaperbackISBN39 = 978-1799507369
| SeeAlso = {{Batman RR}}
```
</details>

<details><summary>Ghosts Vol 1</summary>

```
| IssueImage = Ghosts Vol 1 1.jpg
| Type = Ongoing Series
| TotalIssues = 112
| StartMonth = 10
| StartYear = 1971
| EndYear = 1982
| EndMonth = 5
| Featured = Horror; Doctor Thirteen
| History = '''Ghosts''' was the name of a supernatural anthology series published by DC Comics from [[:Category:1971|1971
| IssueList = *[[Ghosts Vol 1 1|Ghosts #1]] *[[Ghosts Vol 1 2|Ghosts #2]] *[[Ghosts Vol 1 3|Ghosts #3]] *[[Ghosts Vol 1 4|Gh
```
</details>

## Personajes (character) — `DC Database:Character Template` (30,216 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `RealName` | 30,208 | [[Jay Garrick\|Jason Peter "Jay" Garrick]]<ref>{{c\|The Flash Secret F |
| `Universe` | 30,208 | New Earth |
| `Gender` | 30,194 | Male |
| `First` | 30,191 | Showcase Vol 1 4 |
| `Overview` | 30,182 | '''Donna Troy''' is an honorary Amazon, divinely empowered by the [[Go |
| `Creators` | 30,167 | Dan Jurgens; Jerry Ordway; Roger Stern; Louise Simonson; Brett Breedin |
| `Identity` | 30,163 | Secret |
| `Notes` | 30,156 | {{multicont Earth-Two}} * In the [[Earth-Two]] version of Scott, the S |
| `Affiliation` | 30,145 | [[Teen Titans (New Earth)\|Teen Titans]],<br>[[Batman Family]],<br>[[B |
| `Hair` | 30,139 | Red |
| `Eyes` | 30,130 | Blue |
| `BaseOfOperations` | 30,126 | [[Central City]];<br>Formerly<br>[[Justice League Satellite]] |
| `Occupation` | 30,117 | [[Scientist]]; [[Engineer]] |
| `Relatives` | 30,094 | [[Simon Hurt (New Earth)\|Simon Hurt]] (ancestor)<br>[[Roderick Kane ( |
| `Powers` | 30,092 | *{{Super-Speed}} |
| `HistoryText` | 30,068 | {{Out-of-universe}} ===Early Life=== '''Lex Luthor''' was born and rai |
| `Trivia` | 30,061 | * Power Girl has gone by many human names, some of which include: Kare |
| `Abilities` | 30,055 | * {{Hand-to-Hand Combat (Advanced)}}: Barry reveals that he was taught |
| `MaritalStatus` | 30,047 | Single |
| `Equipment` | 30,042 | [[File:Booster Gold Equipment.jpg\|thumb\|right\|200px\|Equipment Diag |
| `Links` | 30,037 | {{ridethelightning\|alchemist.html\|The Alchemist}} |
| `Weapons` | 30,014 | * '''[[Captain Cold's Cold Gun]]''': Cold created his own freeze guns  |
| `Alignment` | 30,013 | Bad |
| `MainAlias` | 30,009 | [[Red Hood]] |
| `Transportation` | 30,004 | * '''[[Jokermobile]]''' |
| `Aliases` | 29,992 | [[Reverse-Flash]];<br> [[Zoom]];<br> [[Black Flash]];<br> [[Adrian Zoo |
| `Height` | 29,987 | 5'5"<ref name=DCE2008>{{c\|DC Comics Encyclopedia: Updated and Expande |
| `Weight` | 29,971 | 183 lbs |
| `Citizenship` | 29,412 | American |
| `Weaknesses` | 28,090 | * '''Rage''': Jason's most notable weakness is his rage. Batman and nu |
| `Recommended` | 24,893 | * ''[[The Power of Shazam! (graphic novel)\|The Power of Shazam!]] * { |
| `Quotation` | 22,359 | Hey, Kid. Name's '''The Flash''', nice to meet ya. |
| `Speaker` | 22,347 | [[Eobard Thawne (New Earth)\|Professor Zoom the Reverse-Flash]] |
| `QuoteSource` | 20,279 | JSA Vol 1 19 |
| `Wikipedia` | 18,314 | None |
| `Education` | 11,421 |  |
| `Death` | 8,554 | Justice League: Cry for Justice Vol 1 3 |
| `DC` | 8,162 | Batman |
| `AlienRace` | 6,965 | New Gods |
| `Distinguish#` | 6,715 | Jim Corrigan |
| `Last` | 6,666 | The Flash Vol 2 247 |
| `Other` | 2,443 | * {{Drug Addiction}} |
| `UnusualSkinColour` | 2,319 | Orange |
| `Marvel` | 1,704 |  |
| `Hair#` | 723 | White, (at temples) |
| `OriginalPublisher` | 519 | Fawcett Publications |
| `Race` | 474 | [[Star Conqueror]], [[Control Stars]] |
| `Sector` | 460 | 2813 |
| `PlaceOfBirth` | 449 |  |

Muestras (20): `Batman (Bruce Wayne)`; `Rory Regan (New Earth)`; `Sharon Vance (New Earth)`; `William Walker (New Earth)`; `Raymond Terrill (New Earth)`; `Jared Stevens (New Earth)`; `Niles Caulder (New Earth)`; `Jeanne Walker (New Earth)`; `Quentin Quale (New Earth)`; `Hunter Zolomon (New Earth)`; `Goth (New Earth)`; `Frederick Delmar (New Earth)`; `Andrea Rojas (New Earth)`; `Great Caesar (Earth-AD)`; `Jonathan Levine (Team Titans)`; `Sacker (Earth-AD)`; `Christopher Freeman (New Earth)`; `Helena Wayne (Earth-Two)`; `Michael Morice (New Earth)`; `Topo (New Earth)`

<details><summary>Batman (Bruce Wayne)</summary>

```
| PageTitle = Bruce Wayne (Prime Earth)
| RealName = [[Bruce Wayne|Bruce Thomas Wayne]]<ref name=BM3-20>{{c|Batman Vol 3 20}}</ref>
| MainAlias = [[Batman]]
| Aliases = [[Arkham Manor Vol 1|Jack Shaw]];<br> [[Matches Malone]];<br> [[Doctor Fate]]<br><small>(See [[Batman (Bruce W
| Identity = Secret
| Alignment = Good
| Affiliation = [[Batman Family]],<br> [[Guild of Detection]],<br> [[Justice League (Prime Earth)|Justice League Unlimited]],<
| Relatives = [[Catherine Van Derm (Prime Earth)|Catherine Van Derm]] (great-great-grandmother, deceased)<br> [[Alan Wayne (
| BaseOfOperations = [[Gotham City]]; [[Pennyworth Manor]];<br>Formerly [[Batcave]], [[Wayne Manor|Stately Wayne Manor]]; [[Hall of
| Gender = Male
| Height = 6'2"
| Weight = 210 lbs
| Eyes = Blue
| Hair = Black
| Citizenship = American
| MaritalStatus = Single
| Occupation = , [[Businessman]]
| Universe = Prime Earth
| Creators = Bill Finger; Bob Kane
| First = Flashpoint Vol 2 5
| Quotation = His parents died when he was so young. Shot. Killed right in front of him. He was raised alone. A kid in a [[W
| Speaker = [[Kal-El (Prime Earth)|Superman]]
| QuoteSource = Batman Vol 3 36
| Overview = '''Batman''' is the superhero protector of [[Gotham City]], a tortured, brooding vigilante dressed as a bat wh
| HistoryText = ===Early Life=== {{Main|Batman Origins}} ====New 52 Early Childhood==== Bruce Wayne was born to wealthy physic
| Powers = * '''[[Alpha Effect|Alpha]]/[[Omega Effect|Omega Energy]]''': After the [[DC K.O.|K.O. tournament]], Batman an
| Abilities = * {{Peak Human Condition}}: Through intense training, a specialized diet, and biofeedback treatments, Batman r
| Other = * {{Missing Limb}} {{Formerly}}: A battle with the '''Ghost-Breaker''' lead to the unfortunate loss of Bruce's
| Equipment = * '''[[Batsuit]]''': The costume Batman wears is composed of Kevlar and a small percentage of titanium; it's b
| Transportation = * '''[[Batboat]]''' * '''[[Batcycle]]''' * '''[[Batmobile]]''' * '''[[Batplane]]''' * '''[[Bat-Copter]]'''
| Weapons = * '''[[Batarang]]s:''' His main set of weapons. Some of these bat shaped blades are electrically or sonically 
| Notes = {{PEBoilerplate | Page = Bruce Wayne (Earth-Two) | Name = Batman | Creator1 = Bill Finger | Creator2 = Bob Kan
| Trivia = * Other less notable aliases Bruce has used are Bee Gee,<ref>{{c|Wonder Twins Vol 1 1}}</ref> [[Knute Brody]],
| DC = Batman
| Wikipedia = Batman
| Recommended = * [[Batman Vol 2|''Batman'' (Vol. 2)]] * [[Detective Comics Vol 2|''Detective Comics'' (Vol. 2)]] * [[Batman a
```
</details>

<details><summary>Rory Regan (New Earth)</summary>

```
| RealName = Rory Regan
| MainAlias = Ragman
| Aliases = [[Tatterdemalion of Justice]]
| Identity = Secret
| Alignment = Good
| Affiliation = [[Shadowpact]]; formerly [[Sentinels of Magic (New Earth)|Sentinels of Magic]], [[Justice Society Internationa
| Relatives = [[Jerzy Reganiewicz (New Earth)|Jerzy Reganiewicz]] (father, deceased)
| Universe = New Earth
| BaseOfOperations = [[Oblivion Bar]]<br>[[Gotham City]]
| Gender = Male
| Height = 5'11"
| Weight = 165 lbs
| Eyes = Blue
| Hair = Brown
| Citizenship = American
| MaritalStatus = Divorced
| Creators = Robert Kanigher; Joe Kubert
| First = Ragman Vol 2 1
| Overview = '''Rory Regan''' is the '''Ragman''', a hero who wears the mystical [[Suit of Souls]]. He was a member of the 
| HistoryText = ===Origin=== Rory Regan grew up in his father's shop, Rags and Tatters, in Gotham City. He is plagued with nig
| Abilities = [[File:Ragman 001.jpg|thumb|right|200px|Ragman in the night sky]] * {{Thievery|Lockpicking}}: Rory learned how
| Weaknesses = * {{Vulnerability to|Fire}}: The rags that make up the suit are extremely vulnerable to fire, a weakness added
| Equipment = * '''[[Suit of Souls|Ragman Suit]]''': The Great Collector Artifact, a mystical Jewish artifact created to pro
| Notes = {{Multicont Earth-One}} * In the distorted timeline of [[Justice Society International]] Ragman had a sidekick
| Recommended = {{Ragman RR}}
| DC = None
| Wikipedia = Ragman (comics)
```
</details>

## Autores (staff) — `DC Database:Staff Template` (8,631 páginas)

Parámetros (normalizados `#` = número), frecuencia y ejemplo:

| parámetro | usos | ejemplo |
|---|---:|---|
| `YearOfBirth` | 8,626 | 1932 |
| `MonthOfBirth` | 8,626 | September |
| `DayOfBirth` | 8,626 | 20 |
| `Links` | 8,554 | * [https://www.comics.org/creator/4951/ Gil Kane at the Grand Comics D |
| `CountryOfBirth` | 7,534 | USA |
| `CityOfBirth` | 7,501 | Brighton |
| `Gender` | 7,499 | Male |
| `First` | 7,496 | Star-Spangled Comics Vol 1 49 |
| `RealName` | 7,480 | Patrick R. Broderick |
| `Titles` | 7,416 | Writer; Editor; Executive Editor; |
| `StateOfBirth` | 7,392 | Northamptonshire |
| `Employers` | 7,325 | DC Comics; Marvel Comics; Continuity; Acclaim |
| `Trivia` | 6,945 | * [[Chris KL-99]] is loosely based on Hamilton's early pulp hero, Capt |
| `ProfessionalHistory` | 6,767 | Klaus Janson is a German-born American comic book artist, inker and wr |
| `YearOfDeath` | 6,628 | 2007 |
| `MonthOfDeath` | 6,623 | November |
| `DayOfDeath` | 6,619 | 27 |
| `Pseudonyms` | 6,531 | Dick Giordano |
| `PersonalHistory` | 6,523 | He was married to Marie Trapani, sister of artist [[Sal Trapani]]. |
| `OfficialWebsite` | 6,448 | * https://www.tothfans.com/ |
| `Creations` | 6,445 | [[Hawk and Dove]]; [[Gnarrk]]; [[Codename: Assassin]] |
| `Notes` | 6,443 | * Despite being credited by DC Comics as a colorist, Tanya is a color  |
| `WP` | 4,243 | ChrisCross |
| `IMDb` | 3,644 | nm0329213 |
| `Text` | 3,312 | was a comic book artist for [[DC Comics]] in the 1940s. |
| `ActingCredits` | 2,553 | {{!S\|Zeta Project (TV Series)\|Teenage Boy \| {{!E\|Zeta Project (TV  |
| `Caption` | 1,968 | Mark Lindsay Chapman as [[Anton Arcane (Swamp Thing 1990 TV Series)\|A |
| `Name` | 1,154 | Carrell Myers |
| `Main` | 1,127 |  |
| `Signature` | 978 | Terry Dodson Signature.jpg |
| `Marvel` | 482 | Robert_Stull |
| `Last` | 311 | Action Comics Vol 1 638 |
| `DC` | 181 | jeremy-roberts |

Muestras (20): `Grant Morrison`; `Chip Zdarsky`; `Gil Kane`; `Rick Bryant`; `Leo Dorfman`; `Bob Kane`; `Danny Bulanadi`; `Joe R. Lansdale`; `Adam Hughes`; `Brian Azzarello`; `Warren Pleece`; `Ricardo Villamonte`; `Richard Piers Rayner`; `Tristan Shane`; `Howard Porter`; `Ian Churchill`; `Tim Sale`; `Marc Andreyko`; `Nelson DeCastro`; `Jonathan Glapion`

<details><summary>Grant Morrison</summary>

```
| RealName = Grant Morrison
| Text = is an acclaimed Scottish comic book writer, with a surreal and optimistic style of storytelling. They are best
| Employers = DC Comics; Vertigo; Marvel Comics
| Titles = Writer
| YearOfBirth = 1960
| MonthOfBirth = January
| DayOfBirth = 31
| CountryOfBirth = Scotland
| CityOfBirth = Glasgow
| Gender = Non-binary
| Creations = [[Damian Wayne (New Earth)|Damian Wayne]], [[Danny the Street (New Earth)|Danny the Street]], [[Lazlo Valentin
| First = Animal Man Vol 1 1
| ProfessionalHistory = Grant Morrison is a Scottish comic book writer who began their career writing for [[2000 AD]] and ''{{WP|Docto
| PersonalHistory = Grant Morrison offered a biography for themself in 1994, using now defunct masculine pronouns: <!-- Don't chan
| ActingCredits = {{!S|Titans (TV Series)|Themself| {{!E|Titans (TV Series) Episode: Dude, Where's My Gar|Themself}}}}
| OfficialWebsite = https://www.grantmorrison.com/
| Marvel = Grant Morrison
| IMDb = nm1634601
| WP = Grant Morrison
```
</details>

<details><summary>Chip Zdarsky</summary>

```
| RealName = Steve Murray
| Pseudonyms = Chip Zdarsky
| Gender = Male
| YearOfBirth = 1975
| MonthOfBirth = December
| DayOfBirth = 21
| CityOfBirth = Edmonton
| StateOfBirth = Alberta
| CountryOfBirth = Canada
| Text = is a comic book writer and artist.
| WP = Chip Zdarsky
```
</details>
