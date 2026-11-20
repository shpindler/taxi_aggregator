# views.py или services.py
import random
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from smsru_api import Client
import os

from .models import PhoneVerification


@api_view(['POST'])
def send_sms_code(request):
    phone = request.data.get('phone')
    if not phone:
        return Response({'error': 'Необходимо указать номер телефона'}, status=400)

    # 1. Сгенерировать 6-значный код
    code = str(random.randint(100000, 999999))

    # 2. Сохранить в базу данных (привязать к пользователю или сессии)
    # Здесь предполагается, что вы получаете или создаёте экземпляр verification
    verification, _ = PhoneVerification.objects.get_or_create(user=request.user)
    verification.phone_number = phone
    verification.otp_code = code
    verification.created_at = timezone.now()
    verification.attempts = 0
    verification.save()

    # 3. Отправить SMS через SMS.RU
    api_key = os.environ.get('SMSRU_API_KEY')
    try:
        with Client(api_key) as smsru:
            response = smsru.send(phone, message=f'Ваш код подтверждения: {code}')
        
        # Проверить статус ответа (библиотека возвращает dict)
        if response.get('status') == 'OK':
            return Response({'status': 'sent'})
        else:
            return Response({'error': 'Не удалось отправить SMS'}, status=500)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def verify_sms_code(request):
    phone_number = request.data.get('phone')
    code = request.data.get('code')
    session_token = request.data.get('session_token')

    if not all([phone_number, code, session_token]):
        return Response({'error': 'Недостаточно параметров'}, status=400)

    try:
        verify_security_code(phone_number, code, session_token)
        return Response({'verified': True})
    except Exception as e:
        # Здесь можно обработать различные ошибки, например, истечение срока действия кода, неверный код и т.д.
        return Response({'verified': False, 'error': str(e)}, status=400)