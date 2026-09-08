# daily-report-bot

Reads a CSV (sales, signups, inventory - anything with a date and a number), builds a daily summary with a chart, emails it as HTML. Without SMTP settings it writes report.html so you can preview.

Ships with sample_sales.csv.

```
pip install pandas matplotlib
python daily_report.py
```
