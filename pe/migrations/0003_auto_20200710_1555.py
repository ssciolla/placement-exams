# Generated by Django 3.0.7 on 2020-07-10 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pe', '0002_auto_20200622_1053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='submitted_timestamp',
            field=models.DateTimeField(null=True, verbose_name='Submitted At Date & Time'),
        ),
    ]
