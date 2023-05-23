from django.db import models
from django.contrib.auth.models import User

# # Create your models here.

class AppSlider(models.Model):
    title = models.CharField(max_length=524, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    rank = models.PositiveSmallIntegerField(blank=True, null=True)
    silder_image = models.ImageField(upload_to='android/slider', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class AppTestimonial(models.Model):
    title = models.CharField(max_length=524, blank=True, null=True)
    description = models.CharField(max_length=256, blank=True, null=True)
    testimonial_image = models.ImageField(upload_to='android/testimonial', null=True, blank=True)
    is_active = models.BooleanField(default=True)
   
    def __str__(self):
        return self.title



class AppBlogCategory(models.Model):
    title = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)
   
    def __str__(self):
        return self.title


class AppBlog(models.Model):
    title=models.CharField(max_length=255, blank=True, null=True)
    author=models.CharField(max_length=14, blank=True, null=True)
    appblogcategory = models.ForeignKey(AppBlogCategory, blank=True, null=True, on_delete=models.CASCADE)
    timeStamp=models.DateTimeField(blank=True)
    content=models.TextField()
    image = models.ImageField(upload_to='android/blog', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.title + " by " + self.author


class AppYoutubeCategory(models.Model):
    title = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)
   
    def __str__(self):
        return self.title


class AppYoutube(models.Model):
    title=models.CharField(max_length=255, blank=True, null=True)
    urllink = models.CharField(max_length=524, blank=True, null=True)
    appyoutubecategory = models.ForeignKey(AppYoutubeCategory, blank=True, null=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.title 

class AppDiseaseCategory(models.Model):
    title = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)
   
    def __str__(self):
        return self.title


class AppDisease(models.Model):
    title=models.CharField(max_length=255, blank=True, null=True)
    appdiseasecategory = models.ForeignKey(AppDiseaseCategory, blank=True, null=True, on_delete=models.CASCADE)
    timeStamp=models.DateTimeField(blank=True)
    content=models.TextField()
    recommended=models.TextField()
    image = models.ImageField(upload_to='android/disease', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.title 


