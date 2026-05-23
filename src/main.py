import argparse
from dotenv import load_dotenv
from web.db import init_db
import uvicorn


def main():
    load_dotenv()
    init_db()
    parser = argparse.ArgumentParser(description="Exam Countdown")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the web server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the web server on")
    args = parser.parse_args()
    uvicorn.run("web.app:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
