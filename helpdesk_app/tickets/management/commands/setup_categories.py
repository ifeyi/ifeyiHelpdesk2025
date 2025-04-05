# tickets/management/commands/setup_categories.py
from django.core.management.base import BaseCommand
from tickets.models import Category

class Command(BaseCommand):
    help = 'Sets up initial ticket categories'

    def handle(self, *args, **kwargs):
        # Create main categories
        hardware, created = Category.objects.get_or_create(
            name='Hardware',
            defaults={
                'description': 'Hardware-related issues',
                'icon': 'bi-pc-display',
                'color': '#FF5733'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {hardware.name}'))
        
        software, created = Category.objects.get_or_create(
            name='Software',
            defaults={
                'description': 'Software-related issues',
                'icon': 'bi-windows',
                'color': '#33A1FF'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {software.name}'))
        
        network, created = Category.objects.get_or_create(
            name='Network',
            defaults={
                'description': 'Network-related issues',
                'icon': 'bi-ethernet',
                'color': '#33FF57'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {network.name}'))
            
        # Create software subcategories
        office, created = Category.objects.get_or_create(
            name='Office',
            defaults={
                'description': 'Microsoft Office issues',
                'parent': software,
                'icon': 'bi-file-earmark-text',
                'color': '#3358FF'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created subcategory: {office.name}'))
            
        # Create Office subcategories
        word, created = Category.objects.get_or_create(
            name='Word',
            defaults={
                'description': 'Microsoft Word issues',
                'parent': office,
                'icon': 'bi-file-word',
                'color': '#3358FF'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created subcategory: {word.name}'))
            
        excel, created = Category.objects.get_or_create(
            name='Excel',
            defaults={
                'description': 'Microsoft Excel issues',
                'parent': office,
                'icon': 'bi-file-excel',
                'color': '#33FF57'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created subcategory: {excel.name}'))
            
        outlook, created = Category.objects.get_or_create(
            name='Outlook',
            defaults={
                'description': 'Microsoft Outlook issues',
                'parent': office,
                'icon': 'bi-envelope',
                'color': '#33A1FF'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created subcategory: {outlook.name}'))
            
        # Add other subcategories as needed