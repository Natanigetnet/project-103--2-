from django.contrib import admin
from .models import names,Category,comments,questions,response_model,TrainingSession,TrainingSpace,BodyMetric,MembershipPayment,UserProfile,MemberID,AttendanceLog,TrainerRating,TrainerChangeRequest,TrainerPayment,TrainerSchedule
# Register your models here.
admin.site.register(names)
admin.site.register(Category)
admin.site.register(comments)
admin.site.register(questions)
admin.site.register(response_model)
admin.site.register(TrainingSession)
admin.site.register(TrainingSpace)
admin.site.register(BodyMetric)
admin.site.register(MembershipPayment)
admin.site.register(UserProfile)
admin.site.register(MemberID)
admin.site.register(AttendanceLog)
admin.site.register(TrainerRating)
admin.site.register(TrainerChangeRequest)
admin.site.register(TrainerPayment)
admin.site.register(TrainerSchedule)
