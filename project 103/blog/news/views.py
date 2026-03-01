from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse   
from .models import names,comments,Category,questions,response_model
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test


def signup(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST) 
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username}!")
            return redirect('login_url')
    else:
        form = UserRegisterForm()
    return render(request, 'signup.html', {'form': form})

def loginUser(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user) 
            return redirect('home_url')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logoutUser(request):
    logout(request) 
    return redirect('login_url')
@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'user_management.html', {'users': users})

@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    if not user_to_delete.is_superuser: 
        user_to_delete.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('user_management_url')
def home(request):
    Names = names.objects.all().order_by('-date')
    return render(request,'home.html',{'names':Names})
def about(request):
    return render(request,'about.html')
def contact(request):
    if request.method=='POST':
        name=request.POST.get('full name')
        email=request.POST.get('email')
        quest=request.POST.get('question')
        question=questions()
        question.name=name
        question.email=email
        question.quest=quest
        question.save()
    return render(request,'contact.html')
@login_required(login_url='login_url')
def members(request):
    if request.user.is_superuser:
        all_members = names.objects.all()
    else:
        all_members = names.objects.filter(trainer=request.user)
    
    return render(request, 'members.html', {'members': all_members})
def visitors(request):
    Names = names.objects.all()
    return render(request,"visitors.html",{'names':Names})
def Category_view(request,category_name):
    Names = names.objects.filter(category__name=category_name).order_by('-date')
    return render(request,'home.html',{'names':Names})
@login_required(login_url='login_url')
def register(request):
    if request.method == 'POST':
        name = request.POST.get('full_name')
        detail = request.POST.get('detail')
        category_id = request.POST.get('category')
        image = request.FILES.get('profile_image')
        

        names.objects.create(
            name=name,
            detail=detail,
            category_id=category_id,
            image=image,
            trainer=request.user
        )
        return redirect('members_url')

    all_categories = Category.objects.all()
    
    return render(request, 'register.html', {
        'categories': all_categories  
    })
def detail(request, name):
    member = get_object_or_404(names, name=name)

    if request.method == 'POST':
        email = request.POST.get('user_email')
        text = request.POST.get('user_comment')
        if email and text:
            comment_obj = comments(email=email, comment=text, post=member)
            comment_obj.save()
        return redirect('detail_url', name=member.name)

    comment_list = comments.objects.filter(post=member).order_by('-id')
    return render(request, 'detail.html', {'name': member, 'comments': comment_list})
def category_list(request):
    if request.method == 'POST':
        cat_name = request.POST.get('category_name')
        
        if cat_name:
            obj = Category()
            obj.name = cat_name
            obj.save()
            return redirect('cat_list_url')

    all_categories = Category.objects.all()
    return render(request, 'cat_list.html', {'categories': all_categories})
def delete_cat(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id)
    cat.delete()
    return redirect('cat_list_url')
def cat_edit(request, cat_id):
    category = get_object_or_404(Category, id=cat_id)

    if request.method == 'POST':
        new_name = request.POST.get('category_name')
        if new_name:
            category.name = new_name
            category.save()
            return redirect('cat_list_url')

    return render(request, 'cat_edit.html', {'category': category})
@login_required
def ques_list(request):
    if request.user.is_superuser:
        question = questions.objects.all().order_by('-id')
    else:
        question = questions.objects.filter(email=request.user.email).order_by('-id')
    
    return render(request, 'ques_list.html', {'quest': question})
def ques_edit(request, q_id):
    item = get_object_or_404(questions, id=q_id)

    if request.method == 'POST':
        item.name = request.POST.get('user_name')
        item.email = request.POST.get('user_email')
        item.quest = request.POST.get('user_quest')
        item.save()
        return redirect('ques_list_url')

    return render(request, 'ques_edit.html', {'item': item})
def ques_delete(request,q_id):
    item=get_object_or_404(questions, id=q_id)
    item.delete()
    return redirect('ques_list_url')
@user_passes_test(lambda u: u.is_superuser)
def response(request, q_id):
    # Fetch the specific question being answered
    question_obj = get_object_or_404(questions, id=q_id)

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text')
        
        if answer_text:
            new_response = response_model() 
            new_response.name = request.user
            new_response.quest = question_obj
            new_response.text = answer_text
            new_response.save()
            
            messages.success(request, "Your response has been recorded.")
            return redirect('ques_list_url')

    return render(request, 'response.html', {'question': question_obj})
@login_required
def response_list(request):
    if request.user.is_superuser:
        # Admin sees every answer given
        responses = response_model.objects.all().order_by('-id')
    else:
        # Trainers only see answers where the original question's name matches theirs
        responses = response_model.objects.filter(quest__name=request.user.username).order_by('-id')
    
    return render(request, 'response_list.html', {'responses': responses})
@user_passes_test(lambda u: u.is_superuser)
def response_delete(request,r_id):
    resp=get_object_or_404(response_model,id=r_id)
    resp.delete()
    return redirect('response_list_url')


@user_passes_test(lambda u: u.is_superuser)
def response_edit(request,r_id):
    resp=get_object_or_404(response_model,id=r_id)
    if request.method == 'POST':
        resp.text = request.POST.get('text')
        resp.save()
        return redirect('response_list_url')

    return render(request, 'response_edit.html', {'item': resp})



def newpeeps(request):
    memb=comments.objects.all()
    if request.method=='POST':
        name=request.POST.get('name')
        detail=request.POST.get('detail')
        Category=request.POST.get('category')

        obj=comments()
        obj.comment=comment
        obj.save()
    return render(request,'anonymous_com.html',{'cComments':cComments})
def edit(request, name):
    member = get_object_or_404(names, name=name)
    
    if request.method == 'POST':
        member.name = request.POST.get('full_name')
        member.detail = request.POST.get('detail')
        member.category_id = request.POST.get('category')        
        new_image = request.FILES.get('profile_image')
        if new_image:
            member.image = new_image
            
        member.save()

    all_categories = Category.objects.all()
    return render(request, 'edit.html', {
        'member': member,
        'categories': all_categories
    })
def delete_member(request, name):
    member = get_object_or_404(names, name=name)
    member.delete()
    return redirect('home_url')
def comm_edit(request, comment_id):
    comment_item = get_object_or_404(comments, id=comment_id)
    
    if request.method == 'POST':
        updated_text = request.POST.get('user_comment')
        
        if updated_text:
            comment_item.comment = updated_text
            comment_item.save()
            
           
            return redirect('detail_url', name=comment_item.post.name)

    return render(request, 'comm_edit.html', {'comment': comment_item})
    
def comm_delete(request, comment_id):
    com = get_object_or_404(comments, id=comment_id)
    
    member_name = com.post.name
    
    com.delete()
    
    return redirect('detail_url', name=member_name)