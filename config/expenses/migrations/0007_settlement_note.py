from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0006_settlement"),
    ]

    operations = [
        migrations.AddField(
            model_name="settlement",
            name="note",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
