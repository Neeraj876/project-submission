from django.core.management.base import BaseCommand
from django.utils import timezone
from dataops.models import DataJob, DataRun
from dataops.services import load_config, load_input_df, apply_steps, write_output

class Command(BaseCommand):
    help = "Run a data job from a YAML config path"

    def add_arguments(self, parser):
        parser.add_argument("--config", required=True)

    def handle(self, *args, **options):
        cfg = load_config(options["config"])
        job = DataJob.objects.create(name="cli_job", config_yaml=str(cfg))
        run = DataRun.objects.create(job=job, status="running")

        try:
            df = load_input_df(cfg["source"])
            df = apply_steps(df, cfg.get("steps", []))
            out = write_output(df, cfg["destination"], run=run)
            run.status = "success"
            run.output_path = out
            run.ended_at = timezone.now()
            run.save()
            self.stdout.write(self.style.SUCCESS(f"Done: {out}"))
        except Exception as e:
            run.status = "failed"
            run.message = str(e)
            run.ended_at = timezone.now()
            run.save()
            raise
