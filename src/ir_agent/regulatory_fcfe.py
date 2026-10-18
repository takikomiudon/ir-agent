"""Damodaran (2009), financial-service firms p22: NI minus regulatory reinvestment.

Pure intermediate arithmetic. Definitions, annual periods, source references
and capital policy are caller declarations; none is independently certified.
No required-capital/target selection, terminal value, forecast or price follows.
Shared strict JSON/source/decimal helpers are reused from stable_reinvestment.
"""
from decimal import Context, DecimalException, InvalidOperation, Overflow, ROUND_HALF_UP, localcontext
import re

from .models import day
from .stable_reinvestment import _copy_request, _decimal, _fields, _sources, _text
from .valuation import _ratio

_BASIS = {'company_id', 'currency', 'amount_unit', 'entity_scope', 'equity_scope'}
_DATA_KINDS = {'reported_fact', 'issuer_guidance', 'author_estimate', 'explicit_assumption', 'synthetic_example'}
_ASSESSMENT = {'capital_definition_rationale', 'capital_target_and_buffer_rationale',
               'equity_claim_scope_rationale', 'forecast_comparability_rationale', 'source_refs'}


def _basis(value, label):
    _fields(value, _BASIS, label)
    for key in _BASIS:
        _text(value[key], label + '.' + key)
    if re.fullmatch(r'[A-Z]{3}', value['currency']) is None:
        raise ValueError(label + '.currency must be an uppercase three-letter label')
    if value['amount_unit'] not in {'units', 'thousands', 'millions', 'billions'}:
        raise ValueError(label + '.amount_unit is unsupported; no conversion is performed')


def _period(value, label):
    _fields(value, {'kind', 'label', 'start', 'end'}, label)
    _text(value['label'], label + '.label')
    if value['kind'] != 'full_fiscal_year':
        raise ValueError(label + ' must declare a full fiscal year; quarter/YTD is outside this API scope')
    start, end = day(value['start'], label + '.start'), day(value['end'], label + '.end')
    if start > end:
        raise ValueError(label + ' ends before it starts')
    return start, end


def _amount(value, concept, basis, period, label):
    _fields(value, {'value', 'concept', 'basis', 'period', 'measurement_basis',
                    'data_kind', 'source_refs', 'rationale'}, label)
    if value['concept'] != concept:
        raise ValueError(label + '.concept must be ' + concept + '; no profit/capital conversion is performed')
    _basis(value['basis'], label + '.basis')
    if value['basis'] != basis or value['period'] != period:
        raise ValueError(label + ' must match the row period and common company/currency/unit/entity/equity scope')
    _text(value['measurement_basis'], label + '.measurement_basis')
    _text(value['data_kind'], label + '.data_kind')
    if value['data_kind'] not in _DATA_KINDS:
        raise ValueError(label + '.data_kind is unsupported')
    _text(value['rationale'], label + '.rationale')
    _sources(value['source_refs'], label + '.source_refs')
    return _decimal(value['value'], label + '.value')


def calculate_regulatory_fcfe(request):
    """Subtract explicit annual regulatory reinvestment; never prepare it."""
    try:
        value, digest = _copy_request(request)
    except (ValueError, TypeError) as error:
        raise ValueError('Regulatory FCFE request must be finite UTF8 JSON within the shared resource limits') from error
    _fields(value, {'method', 'basis', 'rows', 'assessment'}, 'regulatory FCFE request')
    if value['method'] != 'financial_regulatory_fcfe':
        raise ValueError('method must explicitly be financial_regulatory_fcfe')
    _basis(value['basis'], 'basis')
    if not isinstance(value['rows'], list) or not value['rows']:
        raise ValueError('rows must be a nonempty array')
    assessment = value['assessment']
    _fields(assessment, _ASSESSMENT, 'assessment')
    unset = []
    for key in sorted(_ASSESSMENT - {'source_refs'}):
        if assessment[key] is None:
            unset.append('assessment.' + key)
        else:
            _text(assessment[key], 'assessment.' + key)
    _sources(assessment['source_refs'], 'assessment.source_refs')
    arithmetic, labels, previous_end = [], set(), None
    for index, row in enumerate(value['rows']):
        label = 'rows[' + str(index) + ']'
        _fields(row, {'period', 'net_income', 'regulatory_capital_reinvestment'}, label)
        start, end = _period(row['period'], label + '.period')
        if row['period']['label'] in labels or (previous_end is not None and start <= previous_end):
            raise ValueError('Annual rows must have unique labels and increasing nonoverlapping periods')
        labels.add(row['period']['label']); previous_end = end
        income = _amount(row['net_income'], 'net_income_to_equity_holders', value['basis'],
                         row['period'], label + '.net_income')
        reinvestment = _amount(row['regulatory_capital_reinvestment'], 'regulatory_capital_reinvestment',
                               value['basis'], row['period'], label + '.regulatory_capital_reinvestment')
        lowest_exponent = min(income.as_tuple().exponent, reinvestment.as_tuple().exponent)
        precision = max(80, max(income.adjusted(), reinvestment.adjusted()) - lowest_exponent + 3)
        try:
            with localcontext(Context(prec=precision, rounding=ROUND_HALF_UP,
                                      Emin=-999999, Emax=999999,
                                      traps=[InvalidOperation, Overflow])):
                fcfe = income - reinvestment
                arithmetic.append({'period': dict(row['period']), 'net_income': _ratio(income),
                    'regulatory_capital_reinvestment': _ratio(reinvestment), 'fcfe': _ratio(fcfe),
                    'working_precision_digits': precision})
        except DecimalException as error:
            raise ValueError('Regulatory FCFE arithmetic exceeds the supported decimal range') from error
    return {'status': 'intermediate_only', 'adoption': 'unresolved', 'request': value,
            'request_sha256': digest, 'basis': dict(value['basis']), 'arithmetic': arithmetic,
            'calculation': {'formula': 'FCFE = NetIncome - ReinvestmentInRegulatoryCapital',
                'rounding': 'ROUND_HALF_UP', 'display_quantization': None,
                'author_reference': {'author': 'Aswath Damodaran', 'title': 'Valuing Financial Service Firms',
                    'year': 2009, 'source_id': 'damodaran.financial-services.2009', 'pdf_page': 22,
                    'pdf_sha256': '2e1b2d45a8d04ab14b8ed48825b64e7765dd896d59e1db34cce32ded23d07472'},
                'project_adaptation': 'Strict metadata and an initial explicit annual-row scope; not a universal investor rule.'},
            'assessment_fields_unset': unset,
            'verification': {'source_references': 'unverified', 'basis_and_equity_attribution': 'unverified',
                'annual_period_and_comparability': 'unverified', 'required_capital_and_policy': 'unverified',
                'forward_reinvestment_and_forecast': 'unverified', 'funding_and_distribution': 'unverified'},
            'limitations': [
                'Measurement definitions for income and capital remain distinct. Equal metadata does not prove equivalent accounting, regulatory or equity claims.',
                'Values and source/quote references are caller declarations. Empty references or written rationales do not verify a forecast or adopt an input.',
                'Signed NI, reinvestment and FCFE are retained. Negative reinvestment is not certified releasable capital; negative FCFE is not clamped or a sell instruction.',
                'No capital ratio/RWA/balance-difference calibration, terminal value, discounting, equity/share value, automatic growth/dilution, IR action or order is performed.',
            ]}
