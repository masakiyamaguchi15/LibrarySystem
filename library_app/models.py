from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class LibraryUser(models.Model):
    STATUS_CHOICES = [
        ('Active', '適格（有効）'),
        ('Suspended', '不適格（停止中）'),
    ]
    
    user_id = models.CharField('利用者カード番号', max_length=10, primary_key=True)
    name = models.CharField('氏名', max_length=100)
    address = models.CharField('現住所', max_length=255)
    phone = models.CharField('電話番号', max_length=20)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField('登録日時', auto_now_add=True)
    
    class Meta:
        verbose_name = '登録利用者'
        verbose_name_plural = '登録利用者一覧'
        ordering = ['user_id']
        
    def __str__(self):
        return f"{self.name} ({self.user_id})"


class Book(models.Model):
    CATEGORY_CHOICES = [
        ('IT・技術', 'IT・技術'),
        ('文学', '文学'),
        ('ビジネス', 'ビジネス'),
        ('サイエンス', 'サイエンス'),
        ('教育', '教育'),
        ('その他', 'その他'),
    ]
    
    isbn = models.CharField('ISBNコード', max_length=20, primary_key=True)
    title = models.CharField('書名', max_length=255)
    author = models.CharField('著者名', max_length=255)
    price = models.IntegerField('価格（円）')
    publisher = models.CharField('出版社', max_length=100)
    category = models.CharField('カテゴリ', max_length=50, choices=CATEGORY_CHOICES, default='IT・技術')
    
    class Meta:
        verbose_name = '書籍目録'
        verbose_name_plural = '書籍目録一覧'
        ordering = ['title']

    @property
    def total_copies(self):
        return self.copies.count()

    @property
    def available_copies(self):
        return self.copies.filter(status='Available').count()

    @property
    def all_copies(self):
        return self.copies.all()

    def __str__(self):
        return self.title


class BookCopy(models.Model):
    STATUS_CHOICES = [
        ('Available', '貸出可能'),
        ('Loaned', '貸出中'),
        ('Lost', '紛失'),
        ('Maintenance', 'メンテナンス中'),
    ]
    
    copy_id = models.CharField('蔵書ID', max_length=10, primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies', verbose_name='書籍')
    status = models.CharField('状態', max_length=20, choices=STATUS_CHOICES, default='Available')
    added_at = models.DateTimeField('登録日時', auto_now_add=True)
    
    class Meta:
        verbose_name = '蔵書コピー'
        verbose_name_plural = '蔵書コピー一覧'
        ordering = ['copy_id']
        
    def __str__(self):
        return f"{self.book.title} [コピー: {self.copy_id}] ({self.get_status_display()})"


class Loan(models.Model):
    STATUS_CHOICES = [
        ('Active', '貸出中'),
        ('Returned', '返却済み'),
        ('Overdue', '返却遅延'),
    ]
    
    loan_id = models.CharField('貸出ID', max_length=10, unique=True)
    copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='loans', verbose_name='蔵書コピー')
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='loans', verbose_name='利用者')
    librarian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='担当司書')
    loan_date = models.DateTimeField('貸出日', default=timezone.now)
    due_date = models.DateTimeField('返却期限日')
    return_date = models.DateTimeField('実際の返却日', null=True, blank=True)
    status = models.CharField('状況', max_length=20, choices=STATUS_CHOICES, default='Active')
    
    class Meta:
        verbose_name = '貸出台帳'
        verbose_name_plural = '貸出台帳一覧'
        ordering = ['-loan_date']
        
    def save(self, *args, **kwargs):
        if not self.due_date:
            # Set default due date to 14 days from loan date
            self.due_date = self.loan_date + timedelta(days=14)
        super().save(*args, **kwargs)
        
    @property
    def is_overdue(self):
        if self.status == 'Returned' or not self.due_date:
            return False
        return timezone.now() > self.due_date
        
    @property
    def overdue_days(self):
        if not self.is_overdue:
            return 0
        diff = timezone.now() - self.due_date
        return max(0, diff.days)

    def __str__(self):
        return f"貸出 {self.loan_id} ({self.user.name} - {self.copy.copy_id})"
