# CAM & Dashboard Generation

The Presentation Layer is responsible for delivering intelligence in formats that business users actually use.

## 1. The Excel CAM Generator
Instead of building a spreadsheet programmatically from scratch (which breaks formatting), CUIS uses Python's `openpyxl` to open a pristine, pre-formatted `CAM_Template.xlsx` and strictly injects data into precise cell coordinates (e.g., `B44 = Tangible_Net_Worth`). 
This guarantees the output is immediately ready for Credit Committee review.

## 2. The Interactive HTML Dashboard
CUIS compiles a zero-dependency HTML dashboard. By serializing the database outputs into a JSON string and embedding it directly inside an HTML template along with Chart.js, it creates a fully interactive web app that fits in a single file. 
This file can be emailed to underwriters and opened offline, preserving high-end UI features like glassmorphism and animated working-capital gauges.
