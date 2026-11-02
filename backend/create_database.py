"""Create the MySQL database MlimiSmart uses."""
import re
import sys
from urllib.parse import unquote, urlparse

from sqlalchemy import create_engine, text

from app.config import settings


def main() -> int:
    url = settings.database_url
    if not url.startswith("mysql"):
        print("DATABASE_URL is not a MySQL URL:")
        print(f"  {url}")
        print()
        print("Nothing to do. Point DATABASE_URL at MySQL in backend/.env first,")
        print("for example:  mysql+pymysql://root:@localhost:3306/mlimismart")
        return 1

    parsed = urlparse(url)
    schema = parsed.path.lstrip("/")
    if not schema or not re.fullmatch(r"\w+", schema):
        print(f"Could not read a valid database name from DATABASE_URL: {url!r}")
        return 1

    # Reconnect to the same server with no schema selected.
    server_url = url.rsplit("/", 1)[0] + "/"
    user = unquote(parsed.username or "root")
    host = parsed.hostname or "localhost"
    port = parsed.port or 3306

    print(f"Connecting to MySQL at {host}:{port} as {user} ...")
    try:
        engine = create_engine(server_url, future=True)
        with engine.connect() as connection:
            version = connection.execute(text("SELECT VERSION()")).scalar()
            print(f"Connected. MySQL version {version}")
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{schema}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            connection.commit()
        print(f"Database `{schema}` is ready (utf8mb4, so Chichewa text is safe).")
        print()
        print("Next:  python seed.py")
        return 0
    except Exception as exc:  # noqa: BLE001 - report clearly instead of a traceback
        print()
        print("Could not connect to MySQL.")
        print(f"  {exc.__class__.__name__}: {exc}")
        print()
        print("Check that:")
        print("  1. WAMP is started and its tray icon is green.")
        print("  2. MySQL is running (left-click the tray icon -> MySQL -> Service).")
        print("  3. The user and password in backend/.env match your MySQL.")
        print("     WAMP's default is user 'root' with an empty password.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
