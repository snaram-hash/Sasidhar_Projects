# Risk Policy Engine

## 🎯 Purpose
The Risk Policy Engine sits at the absolute center of the Clean Architecture. It acts as the "Brain" of CUIS, taking perfectly parsed facts from the database and applying rigid banking mandates to them.

## 📥 Inputs
- **Reconciled Facts:** Data points from the SQLite Database (Current Ratio, Bounce Rate, CIBIL Score).

## 📤 Outputs
- **Risk Alerts:** Hard warnings for policy breaches (e.g., "Current Ratio < 1.0").
- **Final Risk Score:** An aggregated numerical score indicating the overall health of the proposal.

## 🏗️ Architecture
The engine is decoupled from the UI and the Database. It receives a dictionary of parameters and runs them through a sequential ruleset. This guarantees that **Business Logic is separated from Application Logic.**

## ⚙️ Algorithms & Business Logic
**The Policy Execution Loop:**
```python
def check_policy(financial_data):
    alerts = []
    if financial_data.current_ratio < 1.33:
        alerts.append("Current Ratio is below banking norms.")
    if financial_data.debt_equity > 3.0:
        alerts.append("Highly leveraged: D/E exceeds 3.0")
    return alerts
```
Because the rules are centralized here, a non-technical Credit Manager can easily request updates to the thresholds without risking breaking the parser engines.

## 🔮 Future Improvements
- Externalize the rules into a JSON or YAML configuration file so users can upload custom banking policies per product line.
