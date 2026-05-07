# Golem Theater Dashboard

![Example of the dashboard](<captura.png>)

An interactive, data-driven dashboard for visualizing movie sessions and seat availability at **Cine Golem** . 

## One-Command Launch

To start the dashboard locally on `http://localhost:8000`, simply run:

```bash
python3 crawler.py
```

### What this command does:
1. **Silent Scraping:** Launches a headless browser to fetch the latest movie sessions and seat availability from the website.
2. **Data Update:** Saves the results into `movies_data.json` (this file is ignored by Git to keep your repository clean).
3. **Auto-Deploy:** Starts a local web server and **automatically opens your browser** to the dashboard.

## Project Structure

- `index.html`: The core application (Dashboard + Rendering Engine).
- `crawler.py`: The unified scraper and server script.

