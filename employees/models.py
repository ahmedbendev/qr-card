from django.db import models
from django.urls import reverse
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify
import os

class Employee(models.Model):
    full_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    role = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    landing_url = models.URLField(blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('employee_landing', kwargs={'slug': self.slug})

    def generate_qr_code(self):
        """Generate QR code for this employee"""
        # Generate the URL for this employee's landing page
        domain = "http://localhost:8000"  # Change this to your actual domain in production
        qr_url = f"{domain}{self.get_absolute_url()}"
        self.landing_url = qr_url

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)

        # Save QR image to model
        filename = f'qr_{self.slug}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        # Check if this is a new instance (no pk means it's being created)
        is_new = self.pk is None
        
        # Create slug from full name if not exists
        if not self.slug:
            self.slug = slugify(self.full_name)

        # Save first to ensure we have a pk and slug
        super().save(*args, **kwargs)

        # Only generate QR code for new employees (first time creation)
        if is_new:
            self.generate_qr_code()
            # Save again to update QR code and landing URL fields
            super().save(update_fields=['qr_code', 'landing_url'])