import hashlib
import logging
from datetime import datetime
from decimal import Decimal

from domain.ledger.models.ledger_models import JournalEntry, LedgerLine
from shared.db import db

logger = logging.getLogger(__name__)

class LedgerService:
    """
    Çift Taraflı Muhasebe (Double Entry Accounting) Kurallarını İşleten Servis
    """

    @staticmethod
    def get_last_hash(tenant_id: str) -> str:
        """Belirtilen tenant için son yevmiye fişinin hash değerini getirir."""
        last_entry = JournalEntry.query.filter_by(tenant_id=tenant_id)\
            .order_by(JournalEntry.id.desc()).first()

        if last_entry:
            return last_entry.hash
        return "GENESIS"

    @staticmethod
    def calculate_hash(date: str, description: str, debit_sum, credit_sum, previous_hash: str) -> str:
        """Yeni yevmiye fişi için SHA-256 hash üretir."""
        debit = Decimal(str(debit_sum)).quantize(Decimal("0.01"))
        credit = Decimal(str(credit_sum)).quantize(Decimal("0.01"))
        raw_str = f"{date}|{description}|{debit}|{credit}|{previous_hash}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    @classmethod
    def record_transaction(cls, tenant_id: str, date: str, description: str, lines: list[dict], user_id: int = None) -> JournalEntry:
        """
        Yeni bir yevmiye kaydı oluşturur.
        lines formatı: [{"account_id": 1, "debit": Decimal('100.0000'), "credit": Decimal('0.0000')}, ...]
        """
        if not lines or len(lines) < 2:
            raise ValueError("Bir yevmiye fişinde en az iki satır (Borç/Alacak) olmalıdır.")

        total_debit = Decimal('0.0000')
        total_credit = Decimal('0.0000')

        for line in lines:
            total_debit += line.get('debit', Decimal('0.0000'))
            total_credit += line.get('credit', Decimal('0.0000'))

        if total_debit != total_credit:
            raise ValueError(f"Çift taraflı muhasebe ihlali: Toplam Borç ({total_debit}) != Toplam Alacak ({total_credit})")

        if total_debit <= 0:
            raise ValueError("İşlem tutarı 0'dan büyük olmalıdır.")

        prev_hash = cls.get_last_hash(tenant_id)
        # float yerine string'e çevirerek decimal doğruluğunu koruyoruz
        new_hash = cls.calculate_hash(date, description, str(total_debit), str(total_credit), prev_hash)

        je = JournalEntry(
            tenant_id=tenant_id,
            date=date,
            description=description,
            hash=new_hash,
            previous_hash=prev_hash,
            status='Posted',
            created_by=user_id
        )
        db.session.add(je)
        db.session.flush() # ID almak için

        for line in lines:
            ll = LedgerLine(
                journal_entry_id=je.id,
                account_id=line['account_id'],
                debit=line.get('debit', Decimal('0.0000')),
                credit=line.get('credit', Decimal('0.0000')),
                currency=line.get('currency', 'TRY')
            )
            db.session.add(ll)

        return je

    @classmethod
    def reverse_entry(cls, journal_entry_id: int, user_id: int = None) -> JournalEntry:
        """
        Immutable Ledger (Değiştirilemez Defter) kuralı gereği, hatalı bir işlemi
        silmek yerine onu nötrleyen ters kayıt atılır.
        """
        original_je = db.session.get(JournalEntry, journal_entry_id)
        if not original_je:
            raise ValueError("Orijinal yevmiye fişi bulunamadı.")

        if original_je.status == 'Reversed':
            raise ValueError("Bu işlem zaten iptal edilmiş.")

        lines = []
        for orig_line in original_je.lines:
            # Borçları alacak, alacakları borç yapıyoruz
            lines.append({
                "account_id": orig_line.account_id,
                "debit": orig_line.credit, # Yer değiştiriyor
                "credit": orig_line.debit, # Yer değiştiriyor
                "currency": orig_line.currency
            })

        reversing_desc = f"[İPTAL] {original_je.description}"
        reversing_je = cls.record_transaction(
            tenant_id=original_je.tenant_id,
            date=datetime.now().strftime('%Y-%m-%d'),
            description=reversing_desc,
            lines=lines,
            user_id=user_id
        )

        original_je.status = 'Reversed'
        db.session.add(original_je)

        return reversing_je
