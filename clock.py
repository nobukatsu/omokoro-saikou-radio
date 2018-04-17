from apscheduler.schedulers.blocking import BlockingScheduler
import main

scheduler = BlockingScheduler()


@scheduler.scheduled_job("cron", hour=1)
def execute():
    main.main()


scheduler.start()
