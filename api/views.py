import uuid
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.conf import settings as main_settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from sslcommerz_lib import SSLCOMMERZ
from orders.models import Order, OrderItem


def redirect_from_base(request):
    return redirect('/swagger/')


@swagger_auto_schema(
    method='post',
    operation_summary="Initiate SSLCommerz Payment",
    operation_description="Creates a payment session with SSLCommerz and returns the gateway payment URL.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['amount', 'orderId'],
        properties={
            'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total amount in BDT', example=1000.00),
            'orderId': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the order to pay for', example=12),
            'numItems': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of items in the order', example=1),
        }
    ),
    responses={
        200: openapi.Response(
            description="Payment session created successfully",
            examples={"application/json": {"payment_url": "https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=..."}}
        ),
        400: openapi.Response(
            description="Payment initiation failed",
            examples={"application/json": {"error": "Invalid store or parameters"}}
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    user = request.user
    amount = request.data.get("amount")
    order_id = request.data.get("orderId")
    num_items = request.data.get("numItems")

    ssl_settings = {
        'store_id': getattr(main_settings, 'SSLCOMMERZ_STORE_ID', 'servi68c02a8fe33a3'),
        'store_pass': getattr(main_settings, 'SSLCOMMERZ_STORE_PASS', 'servi68c02a8fe33a3@ssl'),
        'issandbox': getattr(main_settings, 'SSLCOMMERZ_IS_SANDBOX', True)
    }
    sslcz = SSLCOMMERZ(ssl_settings)

    profile = getattr(user, 'profile', None)

    post_body = {
        'total_amount': amount,
        'currency': "BDT",
        'tran_id': f"txn_{order_id}_{uuid.uuid4().hex[:6]}",
        'success_url': f"{main_settings.BACKEND_URL}/api/payment/success/",
        'fail_url': f"{main_settings.BACKEND_URL}/api/payment/fail/",
        'cancel_url': f"{main_settings.BACKEND_URL}/api/payment/cancel/",
        'emi_option': 0,
        'cus_name': f"{user.first_name} {user.last_name}".strip() or "Customer",
        'cus_email': user.email or "customer@example.com",
        'cus_phone': getattr(profile, "phone_number", "01711111111") if profile else "01711111111",
        'cus_add1': getattr(profile, "address", "Dhaka") if profile else "Dhaka",
        'cus_city': "Chattogram",
        'cus_country': "Bangladesh",
        'shipping_method': "NO",
        'multi_card_name': "",
        'num_of_item': num_items or 1,
        'product_name': "Digital Games",
        'product_category': "Gaming",
        'product_profile': "digital",
    }

    response = sslcz.createSession(post_body)

    if response.get("status") == 'SUCCESS':
        return Response({"payment_url": response['GatewayPageURL']})

    return Response({"error": response.get("failedreason", "Payment initiation failed")}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="Payment Success Callback",
    operation_description="Callback URL hit by SSLCommerz upon successful payment. Updates order status and redirects the user.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'tran_id': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction ID generated during initiation')
        }
    ),
    responses={
        302: "Redirects to the frontend success page."
    }
)
@api_view(['POST'])
def payment_success(request):
    tran_id = request.data.get("tran_id", "")
    if tran_id and "_" in tran_id:
        try:
            order_id = tran_id.split('_')[1]
            order = Order.objects.get(id=order_id)
            order.status = "Processing"
            order.save()
        except (Order.DoesNotExist, IndexError, ValueError):
            pass

    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/payment/success/")


@swagger_auto_schema(
    method='post',
    operation_summary="Payment Cancel Callback",
    operation_description="Callback URL hit by SSLCommerz when a payment is cancelled. Redirects the user.",
    responses={
        302: "Redirects to the frontend cancel page."
    }
)
@api_view(['POST'])
def payment_cancel(request):
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/payment/cancel/")


@swagger_auto_schema(
    method='post',
    operation_summary="Payment Failure Callback",
    operation_description="Callback URL hit by SSLCommerz when a payment fails. Redirects the user.",
    responses={
        302: "Redirects to the frontend failure page."
    }
)
@api_view(['POST'])
def payment_fail(request):
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/payment/fail/")