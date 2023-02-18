from distutils.util import strtobool
from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Shop
from .serializers import ShopSerializer
from .tasks import get_import


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For shops only'}, status=status.HTTP_403_FORBIDDEN)

        url = request.data.get('url')
        if url:
            try:
                task = get_import.delay(request.user.id, url)
            except IntegrityError as e:
                return JsonResponse({'Status': False,
                                     'Errors': f'Integrity Error: {e}'})

            return JsonResponse({'Status': True}, status=status.HTTP_200_OK)

        return JsonResponse({'Status': False, 'Errors': 'All necessary arguments are not specified'},
                        status=status.HTTP_400_BAD_REQUEST)


class PartnerState(APIView):
    """
    Класс для работы со статусом поставщика
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For shops only'}, status=status.HTTP_403_FORBIDDEN)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For shop only'}, status=status.HTTP_403_FORBIDDEN)
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True}, status=status.HTTP_200_OK)
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'All necessary arguments are not specified'})



