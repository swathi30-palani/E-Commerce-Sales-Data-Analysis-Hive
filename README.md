# E-Commerce Sales Analysis (Flask + Apache Hive)

Hive is the only database. Connection: localhost:10000, user `hive`, auth NONE, table `ecommerce.sales`.

## IMPORTANT: how to open
Do NOT open `templates/index.html` with Live Server / double-click. Those files are Jinja templates and only
work when Flask serves them. Start the app and open **http://localhost:5000**

## Steps
1. Start Hadoop + HiveServer2 (port 10000).
2. (First time only) create the table: `beeline -u jdbc:hive2://localhost:10000 -n hive -f setup_hive.sql`
3. Windows: double-click `run.bat`  |  Linux/Mac: `./run.sh`
   (or manually: `python -m venv venv`, activate, `pip install -r requirements.txt`, `python app.py`)
4. Open http://localhost:5000

## Modules
| Page | URL | Backend function |
|---|---|---|
| Dashboard (totals, search) | `/` | `get_summary()` |
| Sales Data + search | `/sales` | `get_all_sales()`, `search_sales()` |
| Category / Region / Product / Payment analysis | `/analysis/<kind>` | `get_groups()`, `get_sales_by()` |
| Add New Sale | `/add` | `order_exists()`, `insert_sale()` |

## Files
- `app.py` Flask routes   - `hive_db.py` all Hive queries   - `templates/` HTML pages   - `static/style.css` styling

## Notes
- Windows: do NOT install `sasl` (needs C++ build tools). This project uses pure-sasl via PyHive[hive_pure_sasl].
- Each insert launches a Hive job (a few seconds). The app waits for the job to finish and confirms the row exists.
