"""
벡터 인덱스 구축 Django 관리 명령

사용법:
    python manage.py build_vector_index
    python manage.py build_vector_index --rebuild  (강제 재구축)
"""
from django.core.management.base import BaseCommand
from chatbot.vector_store import get_vector_store


class Command(BaseCommand):
    help = 'RAG 시스템용 벡터 인덱스 구축 또는 재구축'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='캐시 무시하고 강제로 재구축',
        )

    def handle(self, *args, **options):
        force_rebuild = options['rebuild']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        if force_rebuild:
            self.stdout.write(self.style.WARNING('벡터 인덱스 재구축 시작...'))
        else:
            self.stdout.write(self.style.SUCCESS('벡터 인덱스 초기화 시작...'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        try:
            vector_store = get_vector_store()
            vector_store.build_index(force_rebuild=force_rebuild)

            self.stdout.write(self.style.SUCCESS('\n[SUCCESS] 벡터 인덱스 구축 완료!'))
            self.stdout.write(self.style.SUCCESS(f'   총 {len(vector_store.product_metadata)}개 상품이 인덱싱되었습니다.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n[ERROR] 오류 발생: {e}'))
            raise
