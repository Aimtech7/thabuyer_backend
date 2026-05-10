import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestProductsApp:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='sellerprod@test.com', password='password123',
            name='Seller User', role='seller'
        )
        self.client.force_authenticate(user=self.user)

    def test_category_creation(self):
        category = Category.objects.create(name='Electronics', slug='electronics')
        assert category.slug == 'electronics'
        assert Category.objects.count() == 1

    def test_ai_describe_endpoint_validation(self):
        url = reverse('ai-describe')
        response = self.client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ai_describe_endpoint_success(self):
        url = reverse('ai-describe')
        response = self.client.post(url, {
            'make': 'Sony',
            'model': 'WH-1000XM5',
            'type': 'Headphones'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'description' in response.data
