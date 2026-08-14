# Label Organizer Generator

Printable labels, box IDs, and home inventory pages from browser-only tools.

This is a $0 incremental-cost autonomous static business site.

- GitHub Pages hosting
- GitHub Actions build, validation, deploy, and optimization reports
- Python standard-library generation
- Browser-native JavaScript tools
- No paid APIs, subscriptions, customer accounts, checkout handling, inventory, fulfillment, or support queue

## Monetization

Amazon search links use the public Associates tag configured in `data/monetization.json`. Digital checkout links are placeholders until a no-monthly-fee Payhip or Gumroad product is connected.

## Local Commands

```powershell
python scripts/build.py --out site
python scripts/validate.py --dist site
python scripts/optimize.py --out reports
python -m unittest discover -s tests
```

