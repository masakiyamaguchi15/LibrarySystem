from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from library_app.models import LibraryUser, Book, BookCopy, Loan
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = '図書館データベースに仕様書準拠の初期デモデータを投入します。'

    def handle(self, *args, **options):
        self.stdout.write('デモデータの投入を開始します...')

        # 1. 司書（管理者）の作成
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': '山口 雅樹',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('password')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('司書「admin (山口 雅樹)」を作成しました。パスワード: password'))
        else:
            self.stdout.write('司書「admin」はすでに存在します。')

        # 2. 書籍目録の作成
        books_data = [
            {
                'isbn': '978-4798157573',
                'title': 'オブジェクト指向分析設計とUML',
                'author': 'アイ・ラーニング',
                'price': 3200,
                'publisher': '翔泳社',
                'category': 'IT・技術'
            },
            {
                'isbn': '978-4798151120',
                'title': 'オブジェクト指向における再利用のためのデザインパターン',
                'author': 'Erich Gamma',
                'price': 4800,
                'publisher': 'ソフトバンククリエイティブ',
                'category': 'IT・技術'
            },
            {
                'isbn': '978-4061543201',
                'title': 'UMLモデリング教科書 L1',
                'author': '竹政 昭利',
                'price': 2980,
                'publisher': '翔泳社',
                'category': '教育'
            },
            {
                'isbn': '978-4822285142',
                'title': 'リーダブルコード',
                'author': 'Dustin Boswell',
                'price': 2640,
                'publisher': '丸善出版',
                'category': 'IT・技術'
            }
        ]

        for b_info in books_data:
            book, b_created = Book.objects.get_or_create(
                isbn=b_info['isbn'],
                defaults={
                    'title': b_info['title'],
                    'author': b_info['author'],
                    'price': b_info['price'],
                    'publisher': b_info['publisher'],
                    'category': b_info['category']
                }
            )
            if b_created:
                self.stdout.write(f"書籍「{book.title}」を登録しました。")

        # 3. 蔵書コピーの作成
        copies_data = [
            {'copy_id': 'C-0001', 'isbn': '978-4798157573', 'status': 'Available'},
            {'copy_id': 'C-0002', 'isbn': '978-4798157573', 'status': 'Available'},
            {'copy_id': 'C-0003', 'isbn': '978-4798151120', 'status': 'Available'},
            {'copy_id': 'C-0004', 'isbn': '978-4798151120', 'status': 'Loaned'},
            {'copy_id': 'C-0005', 'isbn': '978-4061543201', 'status': 'Available'},
            {'copy_id': 'C-0006', 'isbn': '978-4822285142', 'status': 'Available'}
        ]

        for c_info in copies_data:
            try:
                book = Book.objects.get(isbn=c_info['isbn'])
                copy, c_created = BookCopy.objects.get_or_create(
                    copy_id=c_info['copy_id'],
                    defaults={
                        'book': book,
                        'status': c_info['status']
                    }
                )
                if c_created:
                    self.stdout.write(f"蔵書コピー「{copy.copy_id} ({book.title})」を登録しました。")
            except Book.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"ISBN {c_info['isbn']} の書籍が見つかりません。"))

        # 4. 利用者の作成
        users_data = [
            {
                'user_id': 'U-0001',
                'name': '山田 太郎',
                'address': '東京都品川区大井1-2-3',
                'phone': '090-1234-5678',
                'status': 'Active'
            },
            {
                'user_id': 'U-0002',
                'name': '佐藤 明美',
                'address': '神奈川県横浜市中区桜木町4-5-6',
                'phone': '080-9876-5432',
                'status': 'Active'
            },
            {
                'user_id': 'U-0003',
                'name': '不適格ユーザー (デモ用)',
                'address': '千葉県浦安市美浜7-8-9',
                'phone': '070-5555-4444',
                'status': 'Suspended'
            }
        ]

        for u_info in users_data:
            u_user, u_created = LibraryUser.objects.get_or_create(
                user_id=u_info['user_id'],
                defaults={
                    'name': u_info['name'],
                    'address': u_info['address'],
                    'phone': u_info['phone'],
                    'status': u_info['status']
                }
            )
            if u_created:
                self.stdout.write(f"利用者「{u_user.name} ({u_user.user_id})」を登録しました。")

        # 5. 過去・現在の貸出台帳レコード作成
        # C-0004が現在 U-0002 に貸出中であることを表すレコードを生成
        try:
            copy = BookCopy.objects.get(copy_id='C-0004')
            user = LibraryUser.objects.get(user_id='U-0002')
            
            # すでに貸出レコードがあるか確認
            loan_exists = Loan.objects.filter(copy=copy, user=user, status='Active').exists()
            if not loan_exists:
                loan_date = timezone.now() - timedelta(days=6)
                due_date = loan_date + timedelta(days=14)
                
                loan = Loan.objects.create(
                    loan_id='L-0001',
                    copy=copy,
                    user=user,
                    librarian=admin_user,
                    loan_date=loan_date,
                    due_date=due_date,
                    status='Active'
                )
                
                # コピーのステータスを確実に「貸出中」にセット
                copy.status = 'Loaned'
                copy.save()
                
                self.stdout.write(self.style.SUCCESS(f"貸出中レコード「{loan.loan_id} (利用者: {user.name})」を生成しました。"))
        except (BookCopy.DoesNotExist, LibraryUser.DoesNotExist):
            self.stdout.write(self.style.ERROR('貸出中デモデータの作成に必要なレコードが存在しません。'))

        self.stdout.write(self.style.SUCCESS('デモデータの投入が完了しました！'))
