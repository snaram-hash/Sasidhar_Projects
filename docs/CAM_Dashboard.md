# CAM Generator & Dashboard

## 🎯 Purpose
To present the reconciled facts and risk policy outputs in the exact formats required by the business: a printable, bank-ready Excel file (the CAM) and an interactive web dashboard for real-time risk assessment.

## 📥 Inputs
- **Central SQLite DB:** Pulls the fully calculated and reconciled `cam_record` table.

## 📤 Outputs
- `CAM_{ID}_FY24.xlsx`: A strictly formatted Microsoft Excel document.
- `dashboard.html`: A self-contained HTML file.

## 🏗️ Architecture & Implementation
**The Zero-Dependency Dashboard Strategy:**
Most web dashboards require standing up a backend server (like Django or Node.js). However, credit officers often need to attach dashboards to offline emails.
CUIS solves this by serializing all data into JSON and embedding it directly into the `<script>` tag of a single `dashboard.html` template. This means the HTML file is 100% portable and requires no internet connection or server to render its beautiful Chart.js graphics and glassmorphism UI.

**The Excel Injection Method:**
Instead of building an Excel file from scratch (which ruins formatting), CUIS uses `openpyxl` to open a pristine, pre-formatted `CAM_Template.xlsx` and strictly injects the data into specific cell coordinates (e.g., `B44 = Tangible_Net_Worth`). This guarantees that the final output perfectly matches the Credit Committee's expected layout.

## 🔮 Future Improvements
- Automated PDF generation of the CAM directly from the HTML dashboard.
- Real-time websocket updates if the underlying SQLite database changes.
