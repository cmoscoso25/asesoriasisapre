from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0003_lead_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='edad',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Edad'),
        ),
        migrations.AddField(
            model_name='lead',
            name='prevision_actual',
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name='Previsión actual',
                choices=[
                    ('fonasa', 'Fonasa'),
                    ('banmedica', 'Banmédica'),
                    ('colmena', 'Colmena'),
                    ('consalud', 'Consalud'),
                    ('cruzblanca', 'Cruz Blanca'),
                    ('masvida', 'MasVida'),
                    ('vidatres', 'Vida Tres'),
                    ('nueva_masvida', 'Nueva MásVida'),
                    ('esencial', 'Esencial'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='lead',
            name='pago_actual',
            field=models.IntegerField(blank=True, null=True, verbose_name='Pago actual (CLP/mes)'),
        ),
        migrations.AddField(
            model_name='lead',
            name='preferencia',
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name='Preferencia',
                choices=[
                    ('economica', 'Más económica'),
                    ('cobertura', 'Mayor cobertura'),
                    ('equilibrio', 'Equilibrio precio/cobertura'),
                ],
            ),
        ),
    ]
