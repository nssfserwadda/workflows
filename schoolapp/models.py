from django.db import models

# Create your models here.

class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),

    )

    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100)
    other_name = models.CharField(max_length=100, blank=True)  # Optional field
    student_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.second_name} ({self.student_number})"
    

class SpreadsheetData(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    salary = models.FloatField()

    def __str__(self):
        return self.name
