from datetime import datetime

import argparse
from dotenv import load_dotenv
import time
from core.job import run_job
from web.db import init_db
from web import scheduler


def main():
    load_dotenv()
    init_db()

    parser = argparse.ArgumentParser(description="Instagram Countdown Bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate image but skip uploading and posting",
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run the job immediately without scheduling (for testing)",
    )
    args = parser.parse_args()
    if args.dry_run or args.now:
        from core.job import run_job
        from web.repository import load_config_from_db,create_run_log,finalize_run_log
        config = load_config_from_db()
        log_id = create_run_log()
        result = run_job(config, dry_run=args.dry_run)
        finalize_run_log(log_id=log_id, result=result)
        print("[Info] Job result:", result)
        return
    
    scheduler.start()
    print("[Info] Countdown bot scheduler started.")
    try: 
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[Info] Shutting down scheduler...")
        scheduler.shutdown()
        print("[Info] Scheduler stopped. Exiting.")


if __name__ == "__main__":
    main()
