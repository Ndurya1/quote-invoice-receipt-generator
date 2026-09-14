import unittest

from pydantic import BaseModel, ValidationError

from app.common.currency import CurrencyCode, validate_currency_code


class CurrencyRequest(BaseModel):
    currency: CurrencyCode


class CurrencyTests(unittest.TestCase):
    def test_valid_codes_are_returned_unchanged(self):
        # This task checks format rather than membership in a currency registry.
        for code in ('KES', 'USD', 'EUR', 'GBP', 'ZZZ'):
            with self.subTest(code=code):
                self.assertEqual(validate_currency_code(code), code)
                self.assertEqual(CurrencyRequest(currency=code).model_dump(), {'currency': code})

    def test_invalid_values_are_rejected_directly_and_by_request_schemas(self):
        for value in ('', 'KE', 'KESS', 'kes', 'Kes', ' KES', 'KES ', 'KES\n',
                      'K\tS', 'K3S', '123', 'K$S', '\u212aES', '\uff2b\uff25\uff33',
                      None, 123, 1.5, True, b'KES', ['KES'], {'currency': 'KES'}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_currency_code(value)
                with self.assertRaises(ValidationError) as error:
                    CurrencyRequest(currency=value)
                self.assertEqual(error.exception.errors()[0]['loc'], ('currency',))

    def test_request_field_is_required(self):
        with self.assertRaises(ValidationError):
            CurrencyRequest()

    def test_json_requests_use_the_same_validation(self):
        self.assertEqual(CurrencyRequest.model_validate_json('{"currency":"KES"}').currency, 'KES')
        for payload in ('{"currency":"kes"}', '{"currency":123}', '{"currency":null}'):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                CurrencyRequest.model_validate_json(payload)
