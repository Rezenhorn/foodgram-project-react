# Generated by Django 3.2.16 on 2022-12-05 18:44

from django.db import migrations


INITIAL_TAGS = [
    {'color': '#FFA500', 'name': 'Завтрак', 'slug': 'breakfast'},
    {'color': '#008000', 'name': 'Обед', 'slug': 'lunch'},
    {'color': '#8B00FF', 'name': 'Ужин', 'slug': 'dinner'},
]


def add_tags(apps, schema_editor):
    Tags = apps.get_model('recipes', 'Tags')
    for tag in INITIAL_TAGS:
        new_tag = Tags(**tag)
        new_tag.save()


def remove_tags(apps, schema_editor):
    Tags = apps.get_model('recipes', 'Tags')
    for tag in INITIAL_TAGS:
        Tags.objects.get(slug=tag['slug']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_tags,
            remove_tags
        )
    ]
