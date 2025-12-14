from django.db import models


class News(models.Model):
    title = models.CharField(max_length=255, unique=True)  # 제목 기준 중복 방지
    description = models.TextField(blank=True)
    link = models.URLField()
    pub_date = models.CharField(max_length=100)  # 문자열로 먼저 저장 (나중에 DateTimeField로 바꿔도 됨)
    is_bookmarked = models.BooleanField(default=False)  # F04에서 사용할 필드

    def __str__(self):
        return self.title