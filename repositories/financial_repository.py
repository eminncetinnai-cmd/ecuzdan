"""Read repositories for financial screens."""

from datetime import datetime

from models import Asset, Category, Payment, RecurringPlan, Transaction
from werkzeug.exceptions import NotFound

from .base import BaseRepository
from .contracts import BaseRepositoryContract, FinancialRepositoryContract


class FinancialRepository(BaseRepository, BaseRepositoryContract, FinancialRepositoryContract):
    def _resolve_tenant_id(self, tenant_id=None):
        if tenant_id:
            return tenant_id
        try:
            from flask import g
            tenant_id = g.get('tenant_id')
        except Exception:
            tenant_id = None
        if not tenant_id:
            raise RuntimeError("Tenant context bulunamadı.")
        return tenant_id

    def transaction_page(self, page=1, per_page=50, tenant_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        return Transaction.query.filter_by(tenant_id=tenant_id).order_by(Transaction.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_transaction(self, transaction_id, tenant_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        return Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id).first()

    def list_transactions(self, tenant_id=None, order_desc=True):
        query = Transaction.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        order = Transaction.date.desc() if order_desc else Transaction.date.asc()
        return query.order_by(order).all()

    def add_transaction(self, date, category, description, type_, amount, status, note=None, source_id=None, source_type=None, installment_number=None, tenant_id=None):
        from flask import g
        from domain.ledger.services.ledger_service import LedgerService
        from domain.ledger.models.ledger_models import Account
        from decimal import Decimal

        tenant_id = tenant_id or g.get('tenant_id')
        transaction = Transaction(
            date=date,
            category=category,
            description=(description or '').strip(),
            note=(note or '').strip() or None,
            type=type_,
            amount=amount,
            status=status,
            installment_number=installment_number,
            source_id=source_id,
            source_type=source_type,
            tenant_id=tenant_id,
        )
        self.session.add(transaction)
        
        # Dual-Write for Immutable Ledger
        if status == 'Ödendi':
            cash_acct = Account.query.filter_by(tenant_id=tenant_id, name='Nakit Kasa', type='Asset').first()
            target_acct = Account.query.filter_by(tenant_id=tenant_id, name=category).first()
            if not target_acct:
                target_acct = cash_acct
                
            if cash_acct and target_acct:
                dec_amount = Decimal(str(amount))
                if type_ == 'Gelir':
                    lines = [
                        {"account_id": cash_acct.id, "debit": dec_amount, "credit": Decimal('0.0000')},
                        {"account_id": target_acct.id, "debit": Decimal('0.0000'), "credit": dec_amount}
                    ]
                else:
                    lines = [
                        {"account_id": cash_acct.id, "debit": Decimal('0.0000'), "credit": dec_amount},
                        {"account_id": target_acct.id, "debit": dec_amount, "credit": Decimal('0.0000')}
                    ]
                LedgerService.record_transaction(
                    tenant_id=tenant_id,
                    date=date,
                    description=transaction.description or category,
                    lines=lines
                )
                
        self.commit()
        return transaction

    def update_transaction(self, transaction_id, date, category, description, amount, status, note=None, tenant_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        transaction = Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id).first()
        if not transaction:
            raise NotFound("İşlem bulunamadı.")
        category_obj = Category.query.filter_by(name=category).first()
        if not category_obj:
            raise ValueError("Geçersiz Kategori")

        # In a fully implemented ledger, we would reverse the old journal entry 
        # and create a new one here. For this phase, we update the transaction table.
        # This keeps the dashboard working while we transition.
        transaction.date = date
        transaction.category = category
        transaction.description = (description or '').strip()
        transaction.note = (note or '').strip() or None
        transaction.amount = amount
        transaction.status = status
        transaction.type = category_obj.type
        self.commit()
        return transaction

    def delete_transaction(self, transaction_id, tenant_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        transaction = Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id).first()
        if not transaction:
            raise NotFound("İşlem bulunamadı.")
        self.session.delete(transaction)
        self.commit()

    def pending_transactions_between(self, start, end, tenant_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        return Transaction.query.filter(
            Transaction.type.in_(['Gider', 'Yatırım']),
            Transaction.status == 'Bekliyor',
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.tenant_id == tenant_id,
        ).order_by(Transaction.date).all()

    def _plan_description(self, plan, index):
        return f"{plan.name} ({index + 1}/{plan.installments})"

    def _create_transactions_from_plan(self, plan):
        plan_note = (plan.note or '').strip() or None

        if plan.start_date:
            try:
                start_date = datetime.strptime(plan.start_date, '%Y-%m-%d')
                start_year = start_date.year
                start_month = start_date.month
            except ValueError:
                start_year = datetime.now().year
                start_month = datetime.now().month
        else:
            start_year = datetime.now().year
            start_month = datetime.now().month

        # Yeni Faz 2 Mantığı: Plan tipine göre işlem (transaction) üretimi
        # Abonelik, DCA ve Süresiz (installments=0) planlar için rolling (kayan) 3 aylık üretim
        if plan.plan_type == 'Abonelik' or plan.plan_type == 'DCA' or plan.installments == 0 or plan.installments == 9999:
            tx_count = 3
        elif plan.plan_type == 'Dönemsel':
            freq_map = {'Aylık': 1, '3-Aylık': 3, 'Yıllık': 12, 'Haftalık': 0} # Şimdilik kaba eşleme
            tx_count = freq_map.get(plan.frequency, 1)
        else:
            tx_count = plan.installments
            
        if tx_count > 360: # Maksimum 30 yil (mantik siniri)
            tx_count = 360

        for i in range(tx_count):
            year = start_year + (start_month + i - 1) // 12
            month = (start_month + i - 1) % 12 + 1
            day = min(plan.payment_day, 28)
            self.session.add(Transaction(
                date=f"{year}-{month:02d}-{day:02d}",
                category=plan.category,
                description=self._plan_description(plan, i),
                note=plan_note,
                type=plan.flow_type,
                amount=plan.amount,
                status="Bekliyor",
                installment_number=i + 1,  # Eksik alan eklendi: create_payment() bu numarayla eslesiyor
                source_id=plan.id,
                source_type='plan',
                tenant_id=plan.tenant_id,
            ))

    def add_recurring_plan(self, name, category, amount, installments, payment_day, note=None, start_date=None, tenant_id=None, plan_type='Taksit', end_date=None, frequency='Aylık', target_asset_id=None, status='Aktif'):
        from flask import g

        tenant_id = tenant_id or g.get('tenant_id')
        cat = Category.query.filter_by(name=category).first()
        if not cat:
            raise ValueError("Geçersiz kategori")
        
        # DCA için kategori tipi Yatırım olabilir
        if cat.type not in ('Gelir', 'Gider', 'Yatırım'):
            raise ValueError("Plan yalnızca gelir, gider veya yatırım kategorisiyle oluşturulabilir")

        # installments limit kontrolü (Faz 1)
        if installments > 0 and installments > 600:
            raise ValueError("Taksit sayısı 600'ü geçemez. Süresiz plan için 0 girin.")

        plan = RecurringPlan(
            name=name,
            category=category,
            flow_type=cat.type,
            amount=amount,
            installments=installments,
            payment_day=payment_day,
            start_date=start_date,
            note=(note or '').strip() or None,
            tenant_id=tenant_id,
            plan_type=plan_type,
            end_date=end_date,
            frequency=frequency,
            status=status,
            target_asset_id=target_asset_id
        )
        self.session.add(plan)
        self.session.flush()
        self._create_transactions_from_plan(plan)
        self.commit()
        return plan

    def generate_rolling_transactions(self, tenant_id=None):
        """
        Faz 2: Süresiz (installments=0) olan Abonelik, DCA ve Dönemsel planlar için 
        ileriye dönük daima 3 aylık 'Bekliyor' işleminin hazır olmasını sağlar.
        """
        from models import Transaction
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        from sqlalchemy import or_
        
        query = RecurringPlan.query.filter(
            or_(RecurringPlan.installments == 0, RecurringPlan.installments == 9999),
            RecurringPlan.status == 'Aktif'
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
            
        active_infinite_plans = query.all()
        
        for plan in active_infinite_plans:
            pending_txs = Transaction.query.filter_by(
                source_id=plan.id,
                source_type='plan',
                status='Bekliyor',
                tenant_id=plan.tenant_id
            ).order_by(Transaction.date.desc()).all()
            
            target_pending = 3
            current_pending_count = len(pending_txs)
            
            if current_pending_count < target_pending:
                if pending_txs:
                    last_tx = pending_txs[0]
                    last_installment_number = last_tx.installment_number or 1
                    try:
                        last_date = datetime.strptime(last_tx.date, '%Y-%m-%d')
                    except ValueError:
                        last_date = datetime.now()
                else:
                    last_paid_tx = Transaction.query.filter_by(
                        source_id=plan.id,
                        source_type='plan',
                        tenant_id=plan.tenant_id
                    ).order_by(Transaction.installment_number.desc()).first()
                    
                    if last_paid_tx:
                        last_installment_number = last_paid_tx.installment_number or 0
                        try:
                            last_date = datetime.strptime(last_paid_tx.date, '%Y-%m-%d')
                        except ValueError:
                            last_date = datetime.now()
                    else:
                        last_installment_number = 0
                        try:
                            last_date = datetime.strptime(plan.start_date, '%Y-%m-%d')
                            last_date = last_date - relativedelta(months=1)
                        except (ValueError, TypeError):
                            last_date = datetime.now() - relativedelta(months=1)
                            
                for _ in range(target_pending - current_pending_count):
                    last_installment_number += 1
                    if plan.frequency == '3-Aylık':
                        next_date = last_date + relativedelta(months=3)
                    elif plan.frequency == 'Yıllık':
                        next_date = last_date + relativedelta(years=1)
                    else:
                        next_date = last_date + relativedelta(months=1)
                        
                    day = min(plan.payment_day, 28)
                    next_date = next_date.replace(day=day)
                    last_date = next_date
                    
                    self.session.add(Transaction(
                        date=next_date.strftime('%Y-%m-%d'),
                        category=plan.category,
                        description=self._plan_description(plan, last_installment_number - 1),
                        note=plan.note,
                        type=plan.flow_type,
                        amount=plan.amount,
                        status="Bekliyor",
                        installment_number=last_installment_number,
                        source_id=plan.id,
                        source_type='plan',
                        tenant_id=plan.tenant_id,
                    ))
        self.session.commit()

    def create_payment(self, plan_id, amount, payment_date, installment_number, notes=None, tenant_id=None):
        from flask import g

        tenant_id = tenant_id or g.get('tenant_id')

        if amount <= 0:
            raise ValueError("Ödeme tutarı sıfırdan büyük olmalıdır.")

        plan = self.db.get_or_404(RecurringPlan, plan_id)
        if plan.tenant_id != tenant_id:
            raise ValueError("Plan bulunamadı.")
        if installment_number < 1 or installment_number > plan.installments:
            raise ValueError("Geçersiz taksit numarası.")

        existing_payment = Payment.query.filter_by(
            plan_id=plan_id,
            installment_number=installment_number,
            tenant_id=tenant_id,
        ).first()
        if existing_payment:
            raise ValueError("Bu taksit için zaten bir ödeme kaydı mevcut.")

        transaction_match = Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            installment_number=installment_number,
            tenant_id=tenant_id,
        ).first()

        payment = Payment(
            plan_id=plan_id,
            amount=amount,
            payment_date=payment_date,
            installment_number=installment_number,
            notes=notes,
            tenant_id=tenant_id,
        )
        self.session.add(payment)

        if transaction_match:
            transaction_match.status = 'Ödendi'
            transaction_match.date = payment_date
            transaction_match.amount = amount
            transaction_match.note = (transaction_match.note or '')
            if notes:
                transaction_match.note = f"{transaction_match.note} | Ödeme notu: {notes}" if transaction_match.note else f"Ödeme notu: {notes}"
            self.session.flush()
            payment.transaction_id = transaction_match.id
        else:
            paid_tx = self.add_transaction(
                payment_date,
                plan.category,
                f"{plan.name} ({installment_number}/{plan.installments})",
                plan.flow_type,
                amount,
                'Ödendi',
                note=notes,
                source_id=plan_id,
                source_type='plan',
                installment_number=installment_number,
                tenant_id=tenant_id,
            )
            payment.transaction_id = paid_tx.id

        self.commit()
        return payment

    def update_recurring_plan(self, plan_id, name, category, amount, installments, payment_day, note=None, start_date=None, tenant_id=None, plan_type=None, frequency=None, end_date=None, target_asset_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        cat = Category.query.filter_by(name=category).first()
        if not cat:
            raise ValueError("Geçersiz kategori")
        if cat.type not in ('Gelir', 'Gider', 'Yatırım'):
            raise ValueError("Plan yalnızca gelir, gider veya yatırım kategorisiyle güncellenebilir")

        plan = RecurringPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first()
        if not plan:
            raise NotFound("Plan bulunamadı.")
        plan.name = name
        plan.category = category
        plan.flow_type = cat.type
        plan.amount = amount
        plan.installments = installments
        if plan_type is not None:
            plan.plan_type = plan_type
        if frequency is not None:
            plan.frequency = frequency
        if end_date is not None:
            plan.end_date = end_date
        if target_asset_id is not None:
            plan.target_asset_id = target_asset_id
        plan.payment_day = payment_day
        plan.start_date = start_date
        plan.note = (note or '').strip() or None

        # KRITIK DUZELTME: Sadece 'Bekliyor' durumundaki transaction'lar silinir.
        # 'Odendi' durumundaki transaction'lar (odeme gecmisi) korunur.
        # Onceki hata: status filtresi yoktu, tum transaction'lar siliniyordu → tarihsel veri kaybi.
        Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            status='Bekliyor',
            tenant_id=tenant_id,
        ).delete()
        self._create_transactions_from_plan(plan)

        self.commit()
        return plan

    def delete_plan(self, plan_id, tenant_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        plan = RecurringPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first()
        if not plan:
            return False

        Payment.query.filter_by(plan_id=plan_id, tenant_id=tenant_id).delete(synchronize_session=False)

        pending_txs = Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            status='Bekliyor',
            tenant_id=tenant_id,
        ).all()
        for tx in pending_txs:
            self.session.delete(tx)

        paid_txs = Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            status='Ödendi',
            tenant_id=tenant_id,
        ).all()
        for tx in paid_txs:
            tx.source_id = None
            tx.source_type = None

        self.session.delete(plan)
        self.commit()

        return {
            'success': True,
            'paid_count': len(paid_txs),
            'pending_count': len(pending_txs),
        }

    def list_recurring_plans(self, flow_type=None, tenant_id=None):
        query = RecurringPlan.query
        if flow_type:
            query = query.filter_by(flow_type=flow_type)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(RecurringPlan.name).all()

    def get_recurring_plan_for_tenant(self, plan_id, tenant_id):
        return RecurringPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first()

    def list_assets(self, tenant_id=None):
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()

    def list_assets_by_name(self, tenant_id=None):
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Asset.name).all()

    def asset_page(self, page=1, per_page=20, tenant_id=None):
        query = Asset.query.order_by(Asset.last_updated.desc(), Asset.id.desc())
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def get_asset_for_tenant(self, asset_id, tenant_id=None):
        query = Asset.query.filter_by(id=asset_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
