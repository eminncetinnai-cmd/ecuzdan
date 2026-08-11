"""Form DTO construction and validation."""

from datetime import datetime

from dtos.financial import LogbookEntryDTO, PaymentFormDTO, PlanFormDTO, TransactionFormDTO
from shared.decimal_precision import to_decimal


def transaction_form_from_request(form):
    amount_raw = form.get('amount', 0)
    try:
        amount = to_decimal(amount_raw)
    except Exception as e:
        raise ValueError(f"Geçersiz tutar değeri: {amount_raw}. {str(e)}")
    if amount <= 0:
        raise ValueError("Tutar sıfırdan büyük olmalıdır.")
    return TransactionFormDTO(
        amount=amount,
        category=form.get('category', '').strip(),
        description=form.get('description', '').strip(),
        status=form.get('status', 'Ödendi'),
        date=form.get('date', ''),
        note=form.get('note', '').strip(),
    )


def plan_form_from_request(form):
    amount = to_decimal(form.get('amount', 0) or 0)
    dto = PlanFormDTO(
        action=form.get('action'),
        name=form.get('name', '').strip(),
        category=form.get('category', '').strip(),
        amount=amount,
        installments=int(form.get('installments', 0) or 0),
        payment_day=int(form.get('payment_day', 0) or 0),
        note=form.get('note', '').strip() or None,
        plan_id=form.get('plan_id') or None,
        start_date=form.get('start_date') or None,
        plan_type=form.get('plan_type', 'Taksit'),
        frequency=form.get('frequency', 'Aylık'),
        end_date=form.get('end_date') or None,
        target_asset_id=int(form.get('target_asset_id')) if form.get('target_asset_id') else None
    )
    if dto.amount <= 0 or dto.installments < 0 or dto.payment_day < 1 or dto.payment_day > 31:
        raise ValueError("Tutar ve gün değerleri geçerli olmalıdır. Süresiz için taksit sayısı 0 veya 9999 olmalıdır.")
    if dto.action not in ['add_income_plan', 'add_expense_plan', 'add_investment_plan']:
        raise ValueError("Geçersiz işlem.")
    if dto.start_date:
        try:
            datetime.strptime(dto.start_date, '%Y-%m-%d')
        except ValueError as exc:
            raise ValueError("Geçersiz başlangıç tarihi formatı. YYYY-AA-GG formatında girin.") from exc
    return dto


def payment_form_from_request(form):
    amount = to_decimal(form.get('amount', 0))
    dto = PaymentFormDTO(
        plan_id=form.get('plan_id'),
        amount=amount,
        payment_date=form.get('payment_date'),
        installment_number=int(form.get('installment_number', 1)),
        notes=form.get('notes', '').strip() or None,
    )
    if not dto.plan_id:
        raise ValueError("Ödeme planı belirtilmedi.")
    if dto.amount <= 0:
        raise ValueError("Geçerli bir ödeme tutarı girin.")
    if not dto.payment_date:
        raise ValueError("Ödeme tarihi gerekli.")
    try:
        datetime.strptime(dto.payment_date, '%Y-%m-%d')
    except ValueError as exc:
        raise ValueError("Geçersiz tarih formatı. YYYY-AA-GG formatında girin.") from exc
    if dto.installment_number < 1:
        raise ValueError("Taksit numarası en az 1 olmalıdır.")
    return dto


def logbook_entry_from_request(form):
    dto = LogbookEntryDTO(
        title=form.get('title', '').strip(),
        content=form.get('content', '').strip(),
        entry_date=form.get('entry_date', ''),
        category=form.get('category', 'Finansal'),
        sentiment=form.get('sentiment', 'Nötr'),
        asset_id=form.get('asset_id') or None,
        transaction_id=form.get('transaction_id') or None,
    )
    if not dto.title:
        raise ValueError("Başlık zorunludur.")
    if not dto.content:
        raise ValueError("İçerik zorunludur.")
    if not dto.entry_date:
        raise ValueError("Tarih zorunludur.")
    return dto

