from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User 

class Category(models.Model):
    name=models.CharField(max_length=500)
    def str(self):
        return self.name
class questions(models.Model):
    name=models.CharField(max_length=500)
    email=models.EmailField(max_length=500)
    quest=models.TextField(max_length=5000)
    def str(self):
        return self.name
class response_model(models.Model):
    name=models.ForeignKey(User,on_delete=models.SET_NULL,related_name='trainer_answers',null=True)
    quest=models.ForeignKey(questions,on_delete=models.SET_NULL,null=True)
    text=models.TextField()
    def __str__(self):
        return self.name
class names(models.Model):
    name=models.CharField(max_length=40,null=True)
    detail=models.CharField(max_length=500)
    date= models.DateTimeField(auto_now_add=True)
    image=models.ImageField(null=True,blank=True)
    trainer=models.ForeignKey(User,on_delete=models.SET_NULL,related_name='trainees',null=True)
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True)
    def __str__(self):
        return self.name
class comments(models.Model):
    email  = models.EmailField(("user email"), max_length=254)
    comment  = models.TextField()
    post  = models.ForeignKey(names, on_delete=models.CASCADE,null=True, blank=True) 
