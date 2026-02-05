"""
Scheduler for background scraping jobs
"""
import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime

logger = logging.getLogger(__name__)


class ScrapeScheduler:
    """Manage scheduled scraping jobs"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Scrape scheduler started")
    
    def schedule_daily_job(self, job_func, hour: int = 2, minute: int = 0):
        """Schedule a daily job"""
        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id='daily_scrape',
            name='Daily funding news scrape',
            replace_existing=True,
        )
        logger.info(f"Scheduled daily job at {hour:02d}:{minute:02d}")
    
    def schedule_weekly_job(self, job_func, day_of_week: int = 0, hour: int = 3, minute: int = 0):
        """Schedule a weekly job (0=Monday, 6=Sunday)"""
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id='weekly_scrape',
            name='Weekly full refresh scrape',
            replace_existing=True,
        )
        logger.info(f"Scheduled weekly job on day {day_of_week} at {hour:02d}:{minute:02d}")
    
    def add_one_time_job(self, job_func, run_date: datetime):
        """Add a one-time job"""
        trigger = DateTrigger(run_date=run_date)
        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=f'on_demand_{run_date.timestamp()}',
            name='On-demand scrape',
        )
        logger.info(f"Added one-time job for {run_date}")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scrape scheduler shut down")
