"""Daily report bot: reads a CSV of records (sales, signups, inventory - any
dated data), builds a summary with a chart, and emails it as an HTML report.

Setup:
  pip install pandas matplotlib
  Point CSV_IN at your data file (needs a date column and a numeric column).
  Fill in the SMTP settings to send by email; without them it just writes
  report.html + report_chart.png so you can preview.

Run:
  python daily_report.py

Ships with sample_sales.csv so it works out of the box.
"""
import os
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV_IN = "sample_sales.csv"
DATE_COL = "date"
VALUE_COL = "revenue"
GROUP_COL = "product"        # set to None if you don't have a category column

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
REPORT_TO = os.environ.get("REPORT_TO", "")


def build_report(df):
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    daily = df.groupby(df[DATE_COL].dt.date)[VALUE_COL].sum()

    # chart
    fig, ax = plt.subplots(figsize=(9, 4))
    daily.plot(ax=ax, marker="o")
    ax.set_title(f"{VALUE_COL} by day")
    ax.set_xlabel("")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("report_chart.png", dpi=120)

    total = df[VALUE_COL].sum()
    last_day = daily.index[-1]
    last_val = daily.iloc[-1]
    prev_val = daily.iloc[-2] if len(daily) > 1 else 0
    change = last_val - prev_val

    lines = [
        f"<h2>Report - {datetime.now():%Y-%m-%d}</h2>",
        f"<p>Rows: {len(df)} | Total {VALUE_COL}: {total:,.2f}</p>",
        f"<p>Latest day ({last_day}): {last_val:,.2f} "
        f"({'+' if change >= 0 else ''}{change:,.2f} vs prior day)</p>",
    ]
    if GROUP_COL and GROUP_COL in df.columns:
        top = df.groupby(GROUP_COL)[VALUE_COL].sum().sort_values(ascending=False).head(5)
        rows = "".join(f"<tr><td>{k}</td><td align=right>{v:,.2f}</td></tr>" for k, v in top.items())
        lines.append(f"<h3>Top {GROUP_COL}s</h3><table border=1 cellpadding=4>{rows}</table>")
    lines.append('<p><img src="cid:chart"></p>')
    return "\n".join(lines)


def send_email(html):
    import smtplib
    from email.message import EmailMessage
    em = EmailMessage()
    em["From"] = SMTP_USER
    em["To"] = REPORT_TO
    em["Subject"] = f"Daily report {datetime.now():%Y-%m-%d}"
    em.set_content("HTML report attached (open in an email client that shows HTML).")
    em.add_alternative(html, subtype="html")
    with open("report_chart.png", "rb") as f:
        em.get_payload()[1].add_related(f.read(), "image", "png", cid="chart")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(em)


def main():
    df = pd.read_csv(CSV_IN)
    html = build_report(df)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote report.html + report_chart.png")
    if SMTP_HOST and SMTP_USER and REPORT_TO:
        send_email(html)
        print(f"emailed report to {REPORT_TO}")
    else:
        print("(no SMTP settings - skipped email, preview report.html)")


if __name__ == "__main__":
    main()
