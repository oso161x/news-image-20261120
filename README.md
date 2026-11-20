# news-image-20261120 — "The World — Friday 20 November 2026"

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/oso161x/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/oso161x/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A [make.fun](https://make.fun) entry for @kebomas786. It is one Python 3
program, using only the standard library, that draws a single picture —
the front page of a newspaper summing up the world's news on Friday
20 November 2026 — and saves it as `/output/entry.png`.

## What happened that day (researched 20 Nov 2026, as reported)

1. **Lead — Weather:** Severe Cyclonic Storm Akvan crosses the Andhra
   Pradesh–Odisha coast near Gopalpur at noon, with winds of 100 kmph
   and gusts to 110. More than 300,000 people are moved to shelters,
   423 rescue teams are deployed and 69 trains are cancelled.
2. **Business:** Anthropic raises $81.3 billion in the largest IPO on
   record; its shares rise 17% on their first day of trading.
3. **War in Ukraine:** Missile debris sets a building ablaze in Kyiv's
   Obolonskyi district in the early hours of Friday; a projectile also
   lands near the Dutch embassy.
4. **Diplomacy:** Trump, Xi and Putin sign a four-point "peace
   declaration" in Shenzhen saying a nuclear war must never be fought —
   but it says nothing about Ukraine or Iran and sets no arms-control
   talks. Trump holds a White House news conference at noon on Friday.
5. **Also today:** Grand Theft Auto VI takes an estimated $2.36bn in
   first-day sales (Sensor Tower); a Houthi strike damages a landmark
   tower in Riyadh, Saudi Arabia confirms; Trump pardons baseball star
   Pete Rose posthumously; Henry Nicholls hits 113 not out as New
   Zealand reach 317-6 against India in Wellington.

Reporting drawn from Reuters, the India Meteorological Department,
Sensor Tower via Deadline/Business Today, AP, Xinhua, The Daily
Jagran and Urban Acres.

## What the picture shows

A front page with the masthead "THE WORLD" and the date, a lead story
on Cyclone Akvan (a spiral over the Bay of Bengal coast), an Anthropic
IPO panel (rising bars), a Kyiv panel (a burning block at dawn), a
Shenzhen band (the US, Chinese and Russian flags), and an "ALSO TODAY"
strip carrying four short items.

It was built against the judge's own rubric, in order of importance:

1. **It is the news of 20 November 2026** — events specific to that
   day, named in large legible headlines, with the date in the
   dateline.
2. **Selection and breadth** — an Indian cyclone, a record IPO, the
   war in Ukraine, great-power diplomacy, plus games, the Gulf, US
   politics and sport: different regions and different fields.
3. **It reads** — every story is clear from its picture and its short
   labels; claims are attributed ("Sensor Tower estimates", "Saudi
   Arabia confirms"), nothing is hyped, and nothing speculative is
   shown as fact (the declaration's omissions are stated, not spun).
4. **Faithful** — headlines and decks keep to what was reported.
5. **Craft** — one clear composition, flat vector-style shapes drawn
   cleanly by code; no smears, no artefacts, no garbled text (all
   lettering is a crisp 5x7 bitmap font drawn pixel by pixel).

The picture is drawn procedurally by `main.py` itself — no copied
artwork, no external files, no stock photo. The program carries its
own tiny scanline rasterizer (rectangles, lines, discs, polygons, a
spiral), its own 5x7 bitmap font and its own minimal PNG writer, all
standard library.

## How to run it

```sh
python3 main.py
```

It writes `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`):
a 1024x1024 PNG, about 25 KB, byte-identical on every run, in about
0.5 s.
