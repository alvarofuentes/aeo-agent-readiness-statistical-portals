# World Bank evidence log — 2026-08-22

This file records primary URLs and observed facts used in the AEO audit. The terminal could not initialize in this environment, so this is a manually curated evidence log rather than a byte-for-byte HTTP capture.

## Primary URLs

- https://data.worldbank.org/
- https://data.worldbank.org/indicator/SP.POP.TOTL
- https://data.worldbank.org/static/pages/en/about/get-started.html
- https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
- https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL

## Observations

1. The portal home page identifies itself as World Bank Open Data and says it provides free and open access to global development data. It exposes search by economy or indicator and links DataBank, Microdata Library, Data Catalog, help and developer resources.
2. The indicator page has a stable code-based URL, title Population, total, source references to UN/NSO/Eurostat, CC BY-4.0 license, 1960–2025 coverage, chart controls, download links for CSV/XML/Excel, DataBank and WDI tables.
3. In text-only rendering, the All Countries and Economies section exposes table headings but no country values. This is recorded as partial JavaScript/rendering dependency, not as proof that the site lacks values.
4. Official API documentation states that Indicators API v2 provides programmatic access to nearly 16,000 time-series indicators and requires no authentication.
5. Official API documentation lists JSON, XML, JSON-stat, CSV, Excel and query features including date ranges, pagination, multiple indicators, MRV/MRNEV and footnotes.
6. Direct opening of robots.txt and API URLs with query strings was rejected by the web client security layer; robots and JSON-LD are therefore no-verificado, not absent.

## Reproducible query

https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?date=2024&format=json

