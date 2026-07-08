from django_cron import CronJobBase, Schedule
from django.core.management import call_command

class CheckAlertesCronJob(CronJobBase):
    RUN_AT_TIMES = ['18:00']  # Tous les jours à 18h
    
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'check_alertes_cron'
    
    def do(self):
        call_command('check_alertes')