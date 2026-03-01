from django.contrib import admin
from .models import names,Category,comments,questions,response_model
# Register your models here.
admin.site.register(names)
admin.site.register(Category)
admin.site.register(comments)
admin.site.register(questions)
admin.site.register(response_model)
