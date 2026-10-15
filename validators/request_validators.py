"""Form DTO construction and validation."""

import calendar
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from application.dtos.financial import LogbookEntryDTO, PaymentFormDTO, PlanFormDTO, TransactionFormDTO
from shared.decimal_precision import to_decimal


def transaction_form_from_request(form):
    amount_raw = form.get('amount', 0)
    try:
        amount = to_decimal(amount_raw)
    except Exception as e:
        raise ValueError(f"Geçersiz tutar değeri: {amount_raw}. {str(e)}")
    if amount <= 0:
        raise ValueError("Tutar sıfırdan büyük olmalıdır.")
    bank_account_raw = str(form.get('bank_account_id') or '').strip()
    if bank_account_raw and not bank_account_raw.isdigit():
        raise ValueError('Banka hesabı kimliği geçersiz.')
    bank_account_id = int(bank_account_raw) if bank_account_raw else None
    return TransactionFormDTO(
        amount=amount,
        category=form.get('category', '').strip(),
        description=form.get('description', '').strip(),
        status=form.get('status', 'Ödendi'),
        date=form.get('date', ''),
        note=form.get('note', '').strip(),
        idempotency_key=(form.get('idempotency_key') or '').strip() or None,
        version=int(form.get('version')) if str(form.get('version') or '').strip().isdigit() else None,
        bank_account_id=bank_account_id,
    )


def _calc_installments(start_date: date, end_date: date, frequency: str = "Aylık") -> int:
    if end_date < start_date:
        return 1
    if frequency == "Haftalık":
        return max(1, (end_date - start_date).days // 7 + 1)
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day >= start_date.day:
        months += 1
    if frequency == "3-Aylık":
        return max(1, (months + 2) // 3)
    if frequency == "Yıllık":
        return max(1, (months + 11) // 12)
    return max(1, months)


def _calc_end_date(start_date: date, installments: int, frequency: str = "Aylık") -> date:
    inst = max(1, int(installments or 1))
    if frequency == "Haftalık":
        return start_date + timedelta(days=(inst - 1) * 7)
    if frequency == "3-Aylık":
        return start_date + relativedelta(months=(inst - 1) * 3)
    if frequency == "Yıllık":
        return start_date + relativedelta(years=(inst - 1))
    return start_date + relativedelta(months=(inst - 1))


def plan_form_from_request(form):
    amount = to_decimal(form.get('amount', 0) or 0)
    status_val = (form.get('status') or 'Aktif').strip()
    if status_val not in {'Aktif', 'Duraklatıldı', 'Tamamlandı', 'İptal'}:
        raise ValueError("Geçersiz plan durumu.")

    action_val = form.get('action')
    name_val = form.get('name', '').strip()
    category_val = form.get('category', '').strip()
    installments_raw = form.get('installments')
    try:
        installments_val = int(installments_raw) if installments_raw is not None and str(installments_raw).strip() != '' else 0
    except (TypeError, ValueError):
        installments_val = 0
    payment_day_val = int(form.get('payment_day', 0) or 0)
    note_val = form.get('note', '').strip() or None
    plan_id_val = form.get('plan_id') or None
    start_date_val = (form.get('start_date') or '').strip() or None
    end_date_val = (form.get('end_date') or '').strip() or None
    plan_type_val = form.get('plan_type', 'Taksit')
    frequency_val = form.get('frequency', 'Aylık')
    target_asset_id_val = int(form.get('target_asset_id')) if form.get('target_asset_id') else None
    version_val = int(form.get("version")) if str(form.get("version") or "").strip().isdigit() else None

    # Parse and safely validate start_date
    start_value = None
    if start_date_val:
        try:
            start_value = datetime.strptime(start_date_val, '%Y-%m-%d')
        except ValueError as exc:
            # Handle possible day overflow on month change (e.g. 2026-02-30 or 2026-04-31)
            parts = start_date_val.split('-')
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= m <= 12:
                    max_d = calendar.monthrange(y, m)[1]
                    clamped_d = min(max(d, 1), max_d)
                    start_value = datetime(y, m, clamped_d)
                    start_date_val = start_value.strftime('%Y-%m-%d')
            if start_value is None:
                raise ValueError("Geçersiz başlangıç tarihi formatı. YYYY-AA-GG formatında girin.") from exc

    # Parse and safely validate end_date
    end_value = None
    if end_date_val:
        try:
            end_value = datetime.strptime(end_date_val, '%Y-%m-%d')
        except ValueError as exc:
            parts = end_date_val.split('-')
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= m <= 12:
                    max_d = calendar.monthrange(y, m)[1]
                    clamped_d = min(max(d, 1), max_d)
                    end_value = datetime(y, m, clamped_d)
                    end_date_val = end_value.strftime('%Y-%m-%d')
            if end_value is None:
                raise ValueError("Geçersiz bitiş tarihi formatı. YYYY-AA-GG formatında girin.") from exc

    # Clamping payment day safely to month limit if within valid 1..31 range
    if start_value and 1 <= payment_day_val <= 31:
        max_d = calendar.monthrange(start_value.year, start_value.month)[1]
        payment_day_val = min(payment_day_val, max_d)

    # Duration auto-derivation & simplification:
    is_indefinite = (plan_type_val == 'Abonelik' or (plan_type_val == 'DCA' and installments_val in (0, 9999))) and not end_date_val
    if not is_indefinite and start_value:
        if end_value and installments_val <= 0:
            # User specified end_date only; auto-calculate installments
            if end_value >= start_value:
                installments_val = _calc_installments(start_value.date(), end_value.date(), frequency_val)
            elif action_val in ['update_plan', 'edit_plan']:
                # User changed start month past old end date during edit; extend end date to preserve 1 period
                installments_val = 1
                end_value = start_value
                end_date_val = end_value.strftime('%Y-%m-%d')
        elif installments_val > 0 and not end_value:
            # User specified installments only; auto-calculate end_date
            computed_end = _calc_end_date(start_value.date(), installments_val, frequency_val)
            end_value = datetime.combine(computed_end, datetime.min.time())
            end_date_val = computed_end.strftime('%Y-%m-%d')
        elif end_value and installments_val > 0:
            if end_value < start_value:
                if action_val in ['update_plan', 'edit_plan']:
                    # User changed start month past end date during edit:
                    # preserve installment count from the new start date by shifting end_date forward
                    computed_end = _calc_end_date(start_value.date(), installments_val, frequency_val)
                    end_value = datetime.combine(computed_end, datetime.min.time())
                    end_date_val = computed_end.strftime('%Y-%m-%d')
                else:
                    raise ValueError("Bitiş tarihi başlangıç tarihinden önce olamaz.")

    # Reject end_date before start_date if still invalid
    if start_value and end_value and end_value < start_value:
        raise ValueError("Bitiş tarihi başlangıç tarihinden önce olamaz.")

    dto = PlanFormDTO(
        action=action_val,
        name=name_val,
        category=category_val,
        amount=amount,
        installments=installments_val,
        payment_day=payment_day_val,
        note=note_val,
        plan_id=plan_id_val,
        start_date=start_date_val,
        plan_type=plan_type_val,
        frequency=frequency_val,
        end_date=end_date_val,
        target_asset_id=target_asset_id_val,
        version=version_val,
        status=status_val,
    )
    if dto.amount <= 0 or dto.installments < 0 or dto.payment_day < 1 or dto.payment_day > 31:
        raise ValueError("Tutar ve gün değerleri geçerli olmalıdır. Süresiz için taksit sayısı 0 veya 9999 olmalıdır.")
    if dto.action not in ['add_income_plan', 'add_expense_plan', 'add_investment_plan', 'update_plan', 'edit_plan']:
        raise ValueError("Geçersiz işlem.")
    if dto.plan_type not in {'Taksit', 'Abonelik', 'DCA', 'Dönemsel'}:
        raise ValueError("Geçersiz plan tipi.")
    if dto.frequency not in {'Aylık', '3-Aylık', 'Yıllık', 'Haftalık'}:
        raise ValueError("Geçersiz plan sıklığı.")

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
