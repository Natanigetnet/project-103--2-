
from django.contrib import admin
from django.urls import path
from news.views import home,members,visitors,Category_view,detail,about,contact,register,edit,delete_member,comm_edit,comm_delete,category_list,delete_cat,cat_edit,ques_list,ques_edit,signup,loginUser,logoutUser,user_list,delete_user,ques_delete,response,response_list,response_edit,response_delete
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home,name='home_url'),
    path('about/',about,name='about_url'),
    path('contact/',contact,name='contact_url'),
    path('register/',register,name='register_url'),
    path('members/',members,name='members_url'),
    path('visitors/',visitors,name='visitors_url'),
    path('category_view/<str:category_name>',Category_view,name='Category_view_url'),
    path('detail/<str:name>',detail,name='detail_url'),
    path('category_list/',category_list,name='cat_list_url'),
    path('edit/<str:name>/',edit,name='edit_url'),
    path('delete/<str:name>/', delete_member, name='delete_m_url'),
    path('comment_edit/<int:comment_id>/', comm_edit, name='comm_edit_url'),
    path('delete_comment/<int:comment_id>/',comm_delete, name='comm_delete_url'),
    path('delete_cat/<int:cat_id>/',delete_cat,name='delete_cat_url'),
    path('category/edit/<int:cat_id>/', cat_edit, name='cat_edit_url'),
    path('questions-log/',ques_list , name='ques_list_url'),
    path('edit-question/<int:q_id>/', ques_edit, name='ques_edit_url'),
    path('ques_delete/<int:q_id>/',ques_delete,name='ques_delete_url'),
    path('response/<int:q_id>/',response,name='response_url'),
    path('response_list/',response_list,name='response_list_url'),
    path('response_edit/<int:r_id>/',response_edit,name='response_edit_url'),
    path('response_delete/<int:r_id>/',response_delete, name='response_delete_url'),
    path('signup/', signup, name='signup_url'),
    path('login/', loginUser, name='login_url'),
    path('logout/', logoutUser, name='logout_url'),
    path('manage-users/', user_list, name='user_management_url'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user_url'),
    
    ]
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
