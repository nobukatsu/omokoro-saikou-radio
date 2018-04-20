from apscheduler.schedulers.blocking import BlockingScheduler
import main

scheduler = BlockingScheduler()


@scheduler.scheduled_job("cron", day_of_week="fri", hour=0, minute=10, timezone="Asia/Tokyo")
def execute():
    main.main()


scheduler.start()
