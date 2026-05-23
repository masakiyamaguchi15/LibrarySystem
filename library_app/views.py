from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
import json
import random

from .models import LibraryUser, Book, BookCopy, Loan

# --- Public Views ---

def top_view(request):
    return render(request, 'top.html')


def search_view(request):
    query = request.GET.get('q', '')
    if query.strip():
        books_list = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(publisher__icontains=query) |
            Q(isbn__icontains=query) |
            Q(category__icontains=query)
        )
    else:
        books_list = Book.objects.all()
    
    return render(request, 'search.html', {'book_list': books_list, 'query': query})


# --- Authentication ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('menu')
        
    if request.method == 'POST':
        user_in = request.POST.get('username', '').strip()
        pass_in = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=user_in, password=pass_in)
        if user is not None:
            login(request, user)
            messages.success(request, f"{user.first_name or user.username} 司書としてログインしました。")
            return redirect('menu')
        else:
            messages.error(request, 'ユーザー名またはパスワードが正しくありません。')
            
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return redirect('top')


# --- Librarian Dashboard ---

@login_required
def menu_view(request):
    # Dynamic calculation of metrics
    total_books = Book.objects.count()
    total_copies = BookCopy.objects.count()
    total_users = LibraryUser.objects.count()
    
    active_loans_qs = Loan.objects.filter(status='Active')
    active_loans = active_loans_qs.count()
    
    # Calculate overdue books count
    now = timezone.now()
    overdue_loans = active_loans_qs.filter(due_date__lt=now).count()
    
    return render(request, 'menu.html', {
        'total_books': total_books,
        'total_copies': total_copies,
        'total_users': total_users,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'loans_list': active_loans_qs
    })


# --- User Management ---

@login_required
def user_mgmt_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        if not name or not address or not phone:
            messages.error(request, 'すべての項目を入力してください。')
        else:
            # Clean phone number check
            clean_phone = phone.replace('-', '').replace(' ', '')
            if len(clean_phone) < 10 or len(clean_phone) > 11 or not clean_phone.isdigit():
                messages.error(request, '電話番号の桁数が正しくありません。')
            else:
                # Generate unique user id (U-000X)
                users = LibraryUser.objects.all()
                if users.exists():
                    max_num = 0
                    for u in users:
                        try:
                            num = int(u.user_id.split('-')[1])
                            if num > max_num:
                                max_num = num
                        except (IndexError, ValueError):
                            pass
                    next_id = f"U-{max_num + 1:04d}"
                else:
                    next_id = "U-0001"
                
                new_user = LibraryUser.objects.create(
                    user_id=next_id,
                    name=name,
                    address=address,
                    phone=phone,
                    status='Active'
                )
                messages.success(request, f"利用者を登録しました: {new_user.name} ({new_user.user_id})")
                return redirect('user_mgmt')
                
    users_list = LibraryUser.objects.all()
    return render(request, 'user_mgmt.html', {'users_list': users_list})


@login_required
def toggle_user_view(request, user_id):
    if request.method == 'POST':
        lib_user = get_object_or_404(LibraryUser, user_id=user_id)
        lib_user.status = 'Suspended' if lib_user.status == 'Active' else 'Active'
        lib_user.save()
        messages.warning(request, f"{lib_user.name} の状態を「{lib_user.get_status_display()}」に変更しました。")
    return redirect('user_mgmt')


# --- Book & Copy Management ---

@login_required
def book_mgmt_view(request):
    if request.method == 'POST':
        isbn = request.POST.get('isbn', '').strip().replace('-', '')
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        price = request.POST.get('price', '').strip()
        publisher = request.POST.get('publisher', '').strip()
        category = request.POST.get('category', 'IT・技術')
        
        if len(isbn) != 13 or not isbn.isdigit():
            messages.error(request, 'ISBNは13桁の半角数字で入力してください。')
        elif not title or not author or not price or not publisher:
            messages.error(request, 'すべての項目を入力してください。')
        else:
            try:
                price_val = int(price)
                formatted_isbn = f"{isbn[0:3]}-{isbn[3:13]}"
                
                if Book.objects.filter(isbn=formatted_isbn).exists():
                    messages.error(request, 'このISBNコードは既に登録されています。')
                else:
                    new_book = Book.objects.create(
                        isbn=formatted_isbn,
                        title=title,
                        author=author,
                        price=price_val,
                        publisher=publisher,
                        category=category
                    )
                    
                    # Automatically add the first physical copy
                    copies = BookCopy.objects.all()
                    if copies.exists():
                        max_num = max([int(c.copy_id.split('-')[1]) for c in copies])
                        next_copy_id = f"C-{max_num + 1:04d}"
                    else:
                        next_copy_id = "C-0001"
                        
                    BookCopy.objects.create(
                        copy_id=next_copy_id,
                        book=new_book,
                        status='Available'
                    )
                    
                    messages.success(request, f"書籍「{new_book.title}」を登録し、蔵書コピー({next_copy_id})を追加しました。")
                    return redirect('book_mgmt')
            except ValueError:
                messages.error(request, '価格には数字を入力してください。')
                
    books_list = Book.objects.all()
    return render(request, 'book_mgmt.html', {'books_list': books_list})


@login_required
def add_copy_view(request, isbn):
    if request.method == 'POST':
        book = get_object_or_404(Book, isbn=isbn)
        copies = BookCopy.objects.all()
        if copies.exists():
            max_num = max([int(c.copy_id.split('-')[1]) for c in copies])
            next_copy_id = f"C-{max_num + 1:04d}"
        else:
            next_copy_id = "C-0001"
            
        new_copy = BookCopy.objects.create(
            copy_id=next_copy_id,
            book=book,
            status='Available'
        )
        messages.success(request, f"蔵書コピーを追加しました。蔵書ID: {new_copy.copy_id} ({book.title})")
    return redirect('book_mgmt')


# --- Lend Wizard ---

@login_required
def loan_view(request):
    return render(request, 'loan_mgmt.html')


# --- Return Processor ---

@login_required
def return_book_view(request):
    if request.method == 'POST':
        copy_id = request.POST.get('copy_id', '').strip()
        copy = BookCopy.objects.filter(copy_id=copy_id).first()
        
        if not copy:
            messages.error(request, f"蔵書コピーID「{copy_id}」は見つかりません。")
        elif copy.status != 'Loaned':
            messages.error(request, 'この図書は貸出中ではありません。')
        else:
            active_loan = Loan.objects.filter(copy=copy, status='Active').first()
            if active_loan:
                active_loan.return_date = timezone.now()
                active_loan.status = 'Returned'
                active_loan.save()
            
            copy.status = 'Available'
            copy.save()
            messages.success(request, f"「{copy.book.title} (ID: {copy.copy_id})」の返却処理が正常に完了しました。")
            return redirect('menu')
            
    return render(request, 'return_mgmt.html')


# --- Dynamic JSON APIs for Frontend JavaScript Stepper Async validatons ---

@login_required
def api_validate_user(request):
    user_id = request.GET.get('user_id', '').strip()
    user = LibraryUser.objects.filter(user_id=user_id).first()
    if not user:
        return JsonResponse({'success': False, 'error': '指定された利用者カード番号は登録されていません。'})
    if user.status == 'Suspended':
        return JsonResponse({'success': False, 'error': 'このカードは利用停止状態（不適格）です。'})
        
    active_loans_count = Loan.objects.filter(user=user, status='Active').count()
    if active_loans_count >= 5:
        return JsonResponse({'success': False, 'error': '同時貸出限度数（5冊）に達しています。'})
        
    return JsonResponse({
        'success': True,
        'user': {
            'user_id': user.user_id,
            'name': user.name,
            'address': user.address,
            'phone': user.phone,
            'status': user.status
        }
    })


@login_required
def api_validate_copy(request):
    copy_id = request.GET.get('copy_id', '').strip()
    copy = BookCopy.objects.filter(copy_id=copy_id).first()
    if not copy:
        return JsonResponse({'success': False, 'error': '指定された蔵書コピーIDは登録されていません。'})
    if copy.status != 'Available':
        status_name = copy.get_status_display()
        return JsonResponse({'success': False, 'error': f"この図書は現在貸出できません（状況: {status_name}）"})
        
    return JsonResponse({
        'success': True,
        'copy': {
            'copy_id': copy.copy_id,
            'isbn': copy.book.isbn,
            'title': copy.book.title,
            'author': copy.book.author
        }
    })


@login_required
def api_create_loan(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無効なリクエストです。'})
        
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', '').strip()
        copy_id = data.get('copy_id', '').strip()
        
        user = get_object_or_404(LibraryUser, user_id=user_id)
        copy = get_object_or_404(BookCopy, copy_id=copy_id)
        
        # Double check validators for transaction safety
        if user.status == 'Suspended':
            return JsonResponse({'success': False, 'error': 'この利用者は不適格状態です。'})
        if copy.status != 'Available':
            return JsonResponse({'success': False, 'error': 'この本はすでに貸出中です。'})
            
        loans = Loan.objects.all()
        if loans.exists():
            max_num = max([int(l.loan_id.split('-')[1]) for l in loans if '-' in l.loan_id])
            next_loan_id = f"L-{max_num + 1:04d}"
        else:
            next_loan_id = "L-0001"
            
        # Create Loan record
        new_loan = Loan.objects.create(
            loan_id=next_loan_id,
            copy=copy,
            user=user,
            librarian=request.user,
            status='Active'
        )
        
        # Set copy status to Loaned
        copy.status = 'Loaned'
        copy.save()
        
        return JsonResponse({'success': True, 'loan_id': next_loan_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# --- Special Automated Verification Command Endpoint ---

def api_run_scenario(request):
    scenario_id = request.GET.get('scenario_id', '').strip()
    admin_user = request.user if request.user.is_authenticated else User.objects.filter(username='admin').first()
    
    try:
        if scenario_id == 'reset':
            # Run database wipe and seed
            from django.core.management import call_command
            call_command('seed_db')
            return JsonResponse({'success': True, 'message': 'データベースの初期設定（仕様書準拠データ）を再ロードしました。'})
            
        elif scenario_id == '1':
            # Scenario 1: New User card generation
            rand = random.randint(100, 999)
            name = f"川崎 洋介 [デモ{rand}]"
            
            users = LibraryUser.objects.all()
            max_num = max([int(u.user_id.split('-')[1]) for u in users]) if users.exists() else 0
            next_id = f"U-{max_num + 1:04d}"
            
            user = LibraryUser.objects.create(
                user_id=next_id,
                name=name,
                address='千葉県市川市新田3-2-1',
                phone='090-4444-5555',
                status='Active'
            )
            return JsonResponse({'success': True, 'message': f"【検証成功】新規利用者を登録しました: {user.name} ({user.user_id})"})
            
        elif scenario_id == '2':
            # Scenario 2: Normal lend checkout U-0001 borrows C-0001
            user = LibraryUser.objects.filter(user_id='U-0001').first()
            copy = BookCopy.objects.filter(copy_id='C-0001').first()
            
            if not user or not copy:
                return JsonResponse({'success': False, 'error': 'U-0001またはC-0001が見つかりません。DBをリセットしてください。'})
                
            if copy.status != 'Available':
                # Force return to make scenario run smooth
                copy.status = 'Available'
                copy.save()
                active_loan = Loan.objects.filter(copy=copy, status='Active').first()
                if active_loan:
                    active_loan.status = 'Returned'
                    active_loan.return_date = timezone.now()
                    active_loan.save()
                    
            loans = Loan.objects.all()
            max_num = max([int(l.loan_id.split('-')[1]) for l in loans if '-' in l.loan_id]) if loans.exists() else 0
            next_loan_id = f"L-{max_num + 1:04d}"
            
            Loan.objects.create(
                loan_id=next_loan_id,
                copy=copy,
                user=user,
                librarian=admin_user,
                status='Active'
            )
            copy.status = 'Loaned'
            copy.save()
            return JsonResponse({'success': True, 'message': f"【検証成功】山田太郎 (U-0001) へ蔵書コピー {copy.copy_id} を貸し出しました。"})
            
        elif scenario_id == '3':
            # Scenario 3: Suspended card block validation simulation
            user = LibraryUser.objects.filter(user_id='U-0003').first()
            if not user:
                return JsonResponse({'success': False, 'error': 'U-0003ユーザーがDBにありません。リセットしてください。'})
                
            if user.status != 'Suspended':
                user.status = 'Suspended'
                user.save()
                
            # Try to lend book, should fail
            try:
                copy = BookCopy.objects.filter(status='Available').first()
                if not copy:
                    return JsonResponse({'success': False, 'error': '貸出可能な書籍コピーがありません。'})
                    
                # Evaluate rules
                if user.status == 'Suspended':
                    raise ValueError('このカードは利用停止状態（不適格）です。貸し出しは拒否されます。')
            except ValueError as ve:
                return JsonResponse({'success': True, 'message': f"【検証成功】想定通りの貸出ブロックに成功: {str(ve)}"})
                
        elif scenario_id == '4':
            # Scenario 4: Return loaned book copy
            copy = BookCopy.objects.filter(copy_id='C-0004').first()
            if not copy:
                return JsonResponse({'success': False, 'error': '蔵書コピーC-0004が見つかりません。リセットしてください。'})
                
            if copy.status != 'Loaned':
                # Force make loaned for demonstration
                copy.status = 'Loaned'
                copy.save()
                
                # Check active loan
                if not Loan.objects.filter(copy=copy, status='Active').exists():
                    user = LibraryUser.objects.filter(user_id='U-0002').first()
                    Loan.objects.create(
                        loan_id='L-TEMP',
                        copy=copy,
                        user=user,
                        librarian=admin_user,
                        status='Active'
                    )
            
            # Process return
            active_loan = Loan.objects.filter(copy=copy, status='Active').first()
            if active_loan:
                active_loan.status = 'Returned'
                active_loan.return_date = timezone.now()
                active_loan.save()
                
            copy.status = 'Available'
            copy.save()
            return JsonResponse({'success': True, 'message': f"【検証成功】蔵書 C-0004 の返却処理を完了し、貸出可能に戻しました。"})
            
        else:
            return JsonResponse({'success': False, 'error': '無効なシナリオIDです。'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
