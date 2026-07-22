from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reunion',
            name='recordatorio_enviado',
            field=models.BooleanField(default=False),
        ),
    ]
