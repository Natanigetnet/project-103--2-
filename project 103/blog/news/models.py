from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User 


class Category(models.Model):
    name=models.CharField(max_length=500)
    description=models.TextField(blank=True, null=True, help_text='Description shown on category catalog pages')
    def str(self):
        return self.name
class questions(models.Model):
    name=models.CharField(max_length=500)
    email=models.EmailField(max_length=500)
    quest=models.TextField(max_length=5000)
    ai_answered = models.BooleanField(default=False)
    def __str__(self):
        return self.name

    @property
    def has_unread(self):
        return self.response_model_set.filter(is_read=False).exists()

    @property
    def is_trainer_change_request(self):
        return 'Trainer change' in self.quest
class response_model(models.Model):
    name=models.ForeignKey(User,on_delete=models.SET_NULL,related_name='trainer_answers',null=True)
    quest=models.ForeignKey(questions,on_delete=models.SET_NULL,null=True)
    text=models.TextField()
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return self.name
class names(models.Model):
    ROLE_TRAINER = 'trainer'
    ROLE_TRAINEE = 'trainee'
    ROLE_CHOICES = [
        (ROLE_TRAINER, 'Trainer'),
        (ROLE_TRAINEE, 'Trainee'),
    ]
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
    ]

    name=models.CharField(max_length=40,null=True)
    email=models.EmailField(max_length=254,null=True,blank=True)
    phone_number=models.CharField(max_length=20,null=True,blank=True)
    detail=models.CharField(max_length=500, blank=True)
    date= models.DateTimeField(auto_now_add=True)
    image=models.ImageField(null=True,blank=True)
    role=models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_TRAINEE)
    gender=models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    trainer=models.ForeignKey(User,on_delete=models.SET_NULL,related_name='trainees',null=True, blank=True)
    preferred_trainer=models.ForeignKey(User,on_delete=models.SET_NULL,related_name='preferred_by',null=True, blank=True)
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True, blank=True)

    def __str__(self):
        return self.name
class comments(models.Model):
    email  = models.EmailField(("user email"), max_length=254)
    comment  = models.TextField()
    post  = models.ForeignKey(names, on_delete=models.CASCADE,null=True, blank=True) 


class UserProfile(models.Model):
    ROLE_TRAINER = 'trainer'
    ROLE_TRAINEE = 'trainee'
    ROLE_REGISTRAR = 'registrar'
    ROLE_CHOICES = [
        (ROLE_TRAINER, 'Trainer'),
        (ROLE_TRAINEE, 'Trainee'),
        (ROLE_REGISTRAR, 'Registrar'),
    ]
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_OTHER = 'other'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_OTHER, 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_TRAINEE)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, help_text='Trainer primary category')
    medical_info = models.TextField(blank=True, help_text='Medical notes, conditions, allergies, or emergency info')
    image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_trainer(self):
        return self.role == self.ROLE_TRAINER

    @property
    def is_registrar(self):
        return self.role == self.ROLE_REGISTRAR
class MembershipPayment(models.Model):
    # Link to the User (Athlete)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField() # The date they actually paid
    entry_date = models.DateTimeField(auto_now_add=True) # When this record was created
    
    # Type of payment (Cash, Bank Transfer, etc.)
    payment_method = models.CharField(max_length=50, choices=[
        ('CASH', 'Cash'),
        ('TRANSFER', 'Bank Transfer'),
        ('OTHER', 'Other')
    ])
    
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False) # Admin can check this off

    def __str__(self):
        return f"{self.user.username} - {self.amount} on {self.payment_date}"


class BodyMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='body_metrics')
    weight = models.FloatField(help_text='Weight in kg')
    height = models.FloatField(help_text='Height in cm')
    bmi = models.FloatField(editable=False)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        height_m = self.height / 100.0
        self.bmi = round(self.weight / (height_m ** 2), 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - BMI {self.bmi} ({self.recorded_at.date()})"

class TrainingSpace(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='training_spaces')
    description = models.TextField(blank=True, null=True)
    is_under_maintenance = models.BooleanField(default=False, help_text='When checked, this space will be unavailable for session creation')

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class TrainingSession(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    session_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    space = models.ForeignKey(TrainingSpace, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')

    # Links to the instructor ('names' profile object where role == 'trainer')
    trainer = models.ForeignKey('names', on_delete=models.CASCADE, related_name='created_sessions')
    
    # Capacity constraints configuration 
    max_trainees = models.PositiveIntegerField()
    
    # Many-to-many relationship registry holding authorized athletes who booked a slot
    registered_trainees = models.ManyToManyField('names', blank=True, related_name='registered_sessions')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.registered_trainees.count()}/{self.max_trainees})"

    @property
    def is_full(self):
        return self.registered_trainees.count() >= self.max_trainees

    @property
    def slots_left(self):
        return max(0, self.max_trainees - self.registered_trainees.count())

    @property
    def end_time(self):
        from datetime import timedelta
        return self.session_date + timedelta(minutes=self.duration_minutes)

    @property
    def is_past(self):
        from django.utils import timezone
        return self.end_time < timezone.now()


class MemberID(models.Model):
    member = models.OneToOneField('names', on_delete=models.CASCADE, related_name='member_id')
    unique_id = models.CharField(max_length=64, unique=True)
    qr_code = models.ImageField(upload_to='member_qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID: {self.member.name} ({self.unique_id[:12]}...)"


class AttendanceLog(models.Model):
    member = models.ForeignKey('names', on_delete=models.CASCADE, related_name='attendance_logs')
    session = models.ForeignKey('TrainingSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_logs')
    checked_in_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='scanned_attendance')
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)
    checked_out_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='checkout_attendance')
    notes = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.member.name} checked in at {self.check_in.strftime('%Y-%m-%d %H:%M')}"

class TrainerRating(models.Model):
    trainee = models.ForeignKey('names', on_delete=models.CASCADE, related_name='ratings_given')
    trainer = models.ForeignKey('names', on_delete=models.CASCADE, related_name='ratings_received')
    rating = models.IntegerField(choices=[(i, i) for i in range(0, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trainee', 'trainer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trainee.name} -> {self.trainer.name}: {self.rating}/5"


class TrainerChangeRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_DENIED = 'denied'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_DENIED, 'Denied'),
    ]

    trainee = models.ForeignKey('names', on_delete=models.CASCADE, related_name='change_requests')
    current_trainer = models.ForeignKey('names', on_delete=models.SET_NULL, null=True, related_name='change_requests_received')
    reason = models.TextField(help_text='Mandatory reason for requesting a trainer change')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trainee.name} wants to change from {self.current_trainer.name} ({self.status})"


class TrainingPlan(models.Model):
    SPLIT_UPPER_LOWER = 'upper_lower'
    SPLIT_PUSH_PULL_LEGS = 'push_pull_legs'
    SPLIT_LEG_ARM_CHEST_BACK = 'leg_arm_chest_back'
    SPLIT_FULL_BODY = 'full_body'
    SPLIT_BRO_SPLIT = 'bro_split'
    SPLIT_CUSTOM = 'custom'
    SPLIT_CHOICES = [
        (SPLIT_UPPER_LOWER, 'Upper / Lower'),
        (SPLIT_PUSH_PULL_LEGS, 'Push / Pull / Legs'),
        (SPLIT_LEG_ARM_CHEST_BACK, 'Leg / Arm / Chest / Back'),
        (SPLIT_FULL_BODY, 'Full Body'),
        (SPLIT_BRO_SPLIT, 'Bro Split (Chest/Back/Shoulders/Legs/Arms)'),
        (SPLIT_CUSTOM, 'Custom'),
    ]

    trainee = models.ForeignKey('names', on_delete=models.CASCADE, related_name='training_plans')
    trainer = models.ForeignKey('names', on_delete=models.CASCADE, related_name='created_training_plans')
    split_type = models.CharField(max_length=50, choices=SPLIT_CHOICES, default=SPLIT_UPPER_LOWER)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True, help_text='General notes for this training plan')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.trainer.name} → {self.trainee.name}: {self.get_split_type_display()} ({self.start_date} - {self.end_date})"

    @property
    def split_days(self):
        mapping = {
            self.SPLIT_UPPER_LOWER: ['Upper Body', 'Lower Body', 'Upper Body', 'Lower Body'],
            self.SPLIT_PUSH_PULL_LEGS: ['Push', 'Pull', 'Legs', 'Push', 'Pull', 'Legs'],
            self.SPLIT_LEG_ARM_CHEST_BACK: ['Legs', 'Arms', 'Chest', 'Back'],
            self.SPLIT_FULL_BODY: ['Full Body', 'Full Body', 'Full Body'],
            self.SPLIT_BRO_SPLIT: ['Chest', 'Back', 'Shoulders', 'Legs', 'Arms'],
            self.SPLIT_CUSTOM: [],
        }
        return mapping.get(self.split_type, [])


class TrainingPlanDay(models.Model):
    plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name='days')
    day_index = models.IntegerField(help_text='0-based index within the split')
    day_label = models.CharField(max_length=100, blank=True, help_text='e.g. Upper Body, Push, etc.')
    is_rest_day = models.BooleanField(default=False)
    exercises = models.JSONField(default=list, blank=True, help_text='List of {name, sets, reps, weight, notes}')

    class Meta:
        ordering = ['plan', 'day_index']
        unique_together = ['plan', 'day_index']

    def __str__(self):
        return f"{self.plan} - Day {self.day_index + 1}: {self.day_label or 'Rest'}"


class TrainerPayment(models.Model):
    FREQ_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ]
    trainer = models.OneToOneField('names', on_delete=models.CASCADE, related_name='payment_info')
    salary = models.DecimalField(max_digits=10, decimal_places=2, help_text='Monthly salary amount')
    last_payment_date = models.DateField(null=True, blank=True, help_text='Date of last payment')
    payment_frequency = models.CharField(max_length=10, choices=FREQ_CHOICES, default='monthly')
    payment_day = models.IntegerField(default=1, help_text='Constant day of month for payment (1-28)')
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trainer.name} - {self.salary}"

    @property
    def next_payment_due(self):
        from datetime import date
        import calendar
        today = date.today()
        day = min(max(self.payment_day, 1), 28)
        # Try current month first
        last_day = calendar.monthrange(today.year, today.month)[1]
        pay_day = min(day, last_day)
        due = date(today.year, today.month, pay_day)
        if due <= today:
            # Move to next month
            month = today.month + 1
            year = today.year
            if month > 12:
                month = 1
                year += 1
            last_day = calendar.monthrange(year, month)[1]
            pay_day = min(day, last_day)
            due = date(year, month, pay_day)
        return due

    @property
    def days_until_payment(self):
        if not self.next_payment_due:
            return None
        from datetime import date
        return (self.next_payment_due - date.today()).days


class TrainerSchedule(models.Model):
    DAY_CHOICES = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]
    trainer = models.ForeignKey('names', on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ['trainer', 'day_of_week']
        ordering = ['trainer', 'day_of_week']

    def __str__(self):
        day_label = self.get_day_of_week_display()
        return f"{self.trainer.name} - {day_label} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"