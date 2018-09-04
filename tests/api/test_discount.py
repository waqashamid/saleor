import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.discount import (
    DiscountValueType, VoucherType)
from saleor.graphql.discount.types import (
    DiscountValueTypeEnum, VoucherTypeEnum)

from .utils import assert_no_permission, assert_read_only_mode


def test_voucher_permissions(
        staff_api_client, staff_user, permission_manage_discounts):
    query = """
    query vouchers{
        vouchers(first: 1) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    # Query to ensure user with no permissions can't see vouchers
    response = staff_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    message = 'You do not have permission to perform this action'
    assert content['errors'][0]['message'] == message

    # Give staff user proper permissions
    staff_user.user_permissions.add(permission_manage_discounts)

    # Query again
    response = staff_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content


def test_voucher_query(
        admin_api_client, voucher):
    query = """
    query vouchers{
        vouchers(first: 1) {
            edges {
                node {
                    type
                    name
                    code
                    usageLimit
                    used
                    startDate
                    discountValueType
                    discountValue
                }
            }
        }
    }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['vouchers']['edges'][0]['node']
    assert data['type'] == voucher.type.upper()
    assert data['name'] == voucher.name
    assert data['code'] == voucher.code
    assert data['usageLimit'] == voucher.usage_limit
    assert data['used'] == voucher.used
    assert data['startDate'] == voucher.start_date.isoformat()
    assert data['discountValueType'] == voucher.discount_value_type.upper()
    assert data['discountValue'] == voucher.discount_value


def test_sale_query(
        admin_api_client, sale):
    query = """
        query sales{
            sales(first: 1) {
                edges {
                    node {
                        type
                        name
                        value
                        startDate
                    }
                }
            }
        }
        """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['sales']['edges'][0]['node']
    assert data['type'] == sale.type.upper()
    assert data['name'] == sale.name
    assert data['value'] == sale.value
    assert data['startDate'] == sale.start_date.isoformat()


def test_create_voucher(user_api_client, admin_api_client):
    query = """
    mutation  voucherCreate(
        $type: VoucherTypeEnum, $name: String, $code: String,
        $discountValueType: DiscountValueTypeEnum,
        $discountValue: Decimal, $minAmountSpent: Decimal) {
            voucherCreate(input: {
            name: $name, type: $type, code: $code,
            discountValueType: $discountValueType, discountValue: $discountValue,
            minAmountSpent: $minAmountSpent}) {
                errors {
                    field
                    message
                }
                voucher {
                    type
                    minAmountSpent {
                        amount
                    }
                    name
                    code
                    discountValueType
                }
            }
        }
    """
    variables = json.dumps({
        'name': 'test voucher',
        'type': VoucherTypeEnum.VALUE.name,
        'code': 'testcode123',
        'discountValueType': DiscountValueTypeEnum.FIXED.name,
        'discountValue': '10.12',
        'minAmountSpent': '1.12'})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)


def test_update_voucher(user_api_client, admin_api_client, voucher):
    query = """
    mutation  voucherUpdate($code: String,
        $discountValueType: DiscountValueTypeEnum, $id: ID!) {
            voucherUpdate(id: $id, input: {
                code: $code, discountValueType: $discountValueType}) {
                errors {
                    field
                    message
                }
                voucher {
                    code
                    discountValueType
                }
            }
        }
    """
    # Set discount value type to 'fixed' and change it in mutation
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save()
    assert voucher.code != 'testcode123'
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Voucher', voucher.id),
        'code': 'testcode123',
        'discountValueType': DiscountValueTypeEnum.PERCENTAGE.name})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)


def test_voucher_delete_mutation(user_api_client, admin_api_client, voucher):
    query = """
        mutation DeleteVoucher($id: ID!) {
            voucherDelete(id: $id) {
                voucher {
                    name
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Voucher', voucher.id)})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)


def test_create_sale(user_api_client, admin_api_client):
    query = """
    mutation  saleCreate(
        $type: DiscountValueTypeEnum, $name: String, $value: Decimal) {
            saleCreate(input: {name: $name, type: $type, value: $value}) {
                errors {
                    field
                    message
                }
                sale {
                    type
                    name
                    value
                }
            }
        }
    """
    variables = json.dumps({
        'name': 'test sale',
        'type': DiscountValueTypeEnum.FIXED.name,
        'value': '10.12'})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)


def test_update_sale(user_api_client, admin_api_client, sale):
    query = """
    mutation  saleUpdate($type: DiscountValueTypeEnum, $id: ID!) {
            saleUpdate(id: $id, input: {type: $type}) {
                errors {
                    field
                    message
                }
                sale {
                    type
                }
            }
        }
    """
    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.save()
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Sale', sale.id),
        'type': DiscountValueTypeEnum.PERCENTAGE.name})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)


def test_sale_delete_mutation(user_api_client, admin_api_client, sale):
    query = """
        mutation DeleteSale($id: ID!) {
            saleDelete(id: $id) {
                sale {
                    name
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Sale', sale.id)})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)


def test_validate_voucher(voucher, admin_api_client):
    query = """
    mutation  voucherUpdate(
        $id: ID!, $type: VoucherTypeEnum) {
            voucherUpdate(
            id: $id, input: {type: $type}) {
                errors {
                    field
                    message
                }
            }
        }
    """
    variables = json.dumps({
        'type': VoucherTypeEnum.PRODUCT.name,
        'id': graphene.Node.to_global_id('Voucher', voucher.id)})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_read_only_mode(response)