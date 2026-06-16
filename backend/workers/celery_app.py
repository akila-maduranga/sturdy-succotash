from celery import Celery
from config import settings

celery_app = Celery(
    "trading_bot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "run-strategy-every-5-minutes": {
            "task": "workers.tasks.run_strategy_task",
            "schedule": 300.0,  # every 5 minutes
        },
        "update-prices-every-30-seconds": {
            "task": "workers.tasks.update_prices_task",
            "schedule": 30.0,
        },
        "check-open-trades-every-minute": {
            "task": "workers.tasks.check_open_trades_task",
            "schedule": 60.0,
        },
        "reset-daily-limits-at-midnight": {
            "task": "workers.tasks.reset_daily_limits_task",
            "schedule": 86400.0,
        },
    },
    task_always_eager=False,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
