from django.apps import AppConfig


class FinancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finances'

    def ready(self):
        """
        서버 시작 시 자동으로 예/적금 데이터 동기화
        """
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            from .utils import fetch_deposit_products, fetch_saving_products
            from .models import DepositProducts, DepositOptions, SavingProducts, SavingOptions

            print("=" * 60)
            print("[서버 시작] 예/적금 데이터 자동 동기화 시작...")
            print("=" * 60)

            try:
                # 예금 데이터 동기화
                print("\n[예금] 데이터 확인 중...")
                deposit_count = DepositProducts.objects.count()

                if deposit_count == 0:
                    print("[예금] 데이터가 없습니다. 동기화를 시작합니다...")
                    data = fetch_deposit_products()
                    if data:
                        saved_products = 0
                        saved_options = 0

                        for prod in data.get("baseList", []):
                            _, created = DepositProducts.objects.update_or_create(
                                fin_prdt_cd=prod["fin_prdt_cd"],
                                defaults={
                                    "kor_co_nm": prod.get("kor_co_nm", ""),
                                    "fin_prdt_nm": prod.get("fin_prdt_nm", ""),
                                    "join_way": prod.get("join_way"),
                                    "join_deny": prod.get("join_deny", 1),
                                    "join_member": prod.get("join_member"),
                                    "spcl_cnd": prod.get("spcl_cnd"),
                                },
                            )
                            if created:
                                saved_products += 1

                        def to_float_or_none(v):
                            if v is None or v == "":
                                return None
                            return float(v)

                        for opt in data.get("optionList", []):
                            try:
                                product = DepositProducts.objects.get(fin_prdt_cd=opt["fin_prdt_cd"])
                                _, created = DepositOptions.objects.update_or_create(
                                    product=product,
                                    save_trm=int(opt.get("save_trm", 0) or 0),
                                    rsrv_type=opt.get("rsrv_type"),
                                    defaults={
                                        "intr_rate": to_float_or_none(opt.get("intr_rate")),
                                        "intr_rate2": to_float_or_none(opt.get("intr_rate2")),
                                    },
                                )
                                if created:
                                    saved_options += 1
                            except DepositProducts.DoesNotExist:
                                continue

                        print(f"[예금] 동기화 완료: 상품 {saved_products}개, 옵션 {saved_options}개")
                    else:
                        print("[예금] API 호출 실패")
                else:
                    print(f"[예금] 데이터 이미 존재: {deposit_count}개 상품")

                # 적금 데이터 동기화
                print("\n[적금] 데이터 확인 중...")
                saving_count = SavingProducts.objects.count()

                if saving_count == 0:
                    print("[적금] 데이터가 없습니다. 동기화를 시작합니다...")
                    data = fetch_saving_products()
                    if data:
                        saved_products = 0
                        saved_options = 0

                        for prod in data.get("baseList", []):
                            _, created = SavingProducts.objects.update_or_create(
                                fin_prdt_cd=prod["fin_prdt_cd"],
                                defaults={
                                    "kor_co_nm": prod.get("kor_co_nm", ""),
                                    "fin_prdt_nm": prod.get("fin_prdt_nm", ""),
                                    "join_way": prod.get("join_way"),
                                    "join_deny": prod.get("join_deny", 1),
                                    "join_member": prod.get("join_member"),
                                    "spcl_cnd": prod.get("spcl_cnd"),
                                    "mtrt_int": prod.get("mtrt_int"),
                                },
                            )
                            if created:
                                saved_products += 1

                        def to_float_or_none(v):
                            if v is None or v == "":
                                return None
                            return float(v)

                        for opt in data.get("optionList", []):
                            product = SavingProducts.objects.filter(fin_prdt_cd=opt["fin_prdt_cd"]).first()
                            if not product:
                                continue

                            _, created = SavingOptions.objects.update_or_create(
                                product=product,
                                save_trm=int(opt.get("save_trm", 0) or 0),
                                rsrv_type=opt.get("rsrv_type"),
                                intr_rate_type=opt.get("intr_rate_type"),
                                defaults={
                                    "intr_rate": to_float_or_none(opt.get("intr_rate")),
                                    "intr_rate2": to_float_or_none(opt.get("intr_rate2")),
                                    "rsrv_type_nm": opt.get("rsrv_type_nm"),
                                    "intr_rate_type_nm": opt.get("intr_rate_type_nm"),
                                },
                            )
                            if created:
                                saved_options += 1

                        print(f"[적금] 동기화 완료: 상품 {saved_products}개, 옵션 {saved_options}개")
                    else:
                        print("[적금] API 호출 실패")
                else:
                    print(f"[적금] 데이터 이미 존재: {saving_count}개 상품")

                print("\n" + "=" * 60)
                print("[완료] 예/적금 데이터 자동 동기화 완료!")
                print("=" * 60 + "\n")

            except Exception as e:
                print(f"\n[오류] 자동 동기화 중 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                print("\n[경고] 서버는 계속 실행되지만 데이터가 비어있을 수 있습니다.")
