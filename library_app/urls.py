from django.urls import path
from . import views

urlpatterns = [
    # General Public Views
    path('', views.top_view, name='top'),
    path('search/', views.search_view, name='search'),
    
    # Authentications
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Librarian Operations
    path('menu/', views.menu_view, name='menu'),
    path('user/', views.user_mgmt_view, name='user_mgmt'),
    path('user/toggle/<str:user_id>/', views.toggle_user_view, name='toggle_user'),
    path('book/', views.book_mgmt_view, name='book_mgmt'),
    path('book/add_copy/<str:isbn>/', views.add_copy_view, name='add_copy'),
    path('loan/', views.loan_view, name='loan'),
    path('return/', views.return_book_view, name='return_book'),
    
    # Async Fetch API Endpoints
    path('api/validate_user/', views.api_validate_user, name='api_validate_user'),
    path('api/validate_copy/', views.api_validate_copy, name='api_validate_copy'),
    path('api/create_loan/', views.api_create_loan, name='api_create_loan'),
    path('api/run_scenario/', views.api_run_scenario, name='api_run_scenario'),
]
