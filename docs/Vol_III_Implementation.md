# Volume III: Implementation Deep Dive

## Spatial-Aware Regex Parsing

One of the biggest technical challenges was extracting tabular financial data from unstructured PDFs. Standard text extraction tools (like `PyMuPDF`) flatten text, destroying the spatial relationships between a label ("Secured Loans") and its value ("$5,000,000").

We implemented a **Layout-Aware Regex Engine**.

### Example: Extracting Direct Expenses
In Indian Trading Accounts, "Direct Expenses" (like manufacturing or freight) appear after "Purchases" but before "Gross Profit".

```python
# Our solution uses a non-greedy regex to capture the entire block of text 
# between these two critical anchors, and then sums the numbers found within.
manufacturing_match = re.search(r'TO\s+PURCHASES?.*?(?:BY\s+CLOSING\s+STOCK|TO\s+GROSS\s+PROFIT)', trading_text, re.DOTALL | re.IGNORECASE)
```

## Self-Contained Dashboards

Most reporting solutions require hosting a separate frontend server (React/Vue). CUIS takes a different approach: **Zero-Dependency HTML Compilation**.

The `build_dashboard.py` script takes the data from the SQLite database, serializes it into a JSON string, and dynamically injects it directly into a single `<script>` block inside an HTML template.

This means the resulting `dashboard.html` file is a completely self-contained application. A credit officer can email this HTML file to the sanctioning committee, and it will render interactive Chart.js graphs, 3-year historical tables, and Working Capital gauges without requiring internet access or a web server.
