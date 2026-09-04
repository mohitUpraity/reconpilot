import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database import init_db, get_conn
from db.repository import resolve_case_manually


def test_manual_approve_match_roundtrip():
    init_db()
    conn=get_conn()
    inv=conn.execute("SELECT * FROM financial_records WHERE record_type='invoice' ORDER BY record_id LIMIT 1").fetchone()
    pay=conn.execute("SELECT * FROM financial_records WHERE record_type='payment' ORDER BY record_id LIMIT 1").fetchone()
    conn.execute("""
      INSERT OR REPLACE INTO reconciliation_cases(
        case_id,merchant_id,case_type,status,confidence,primary_record_id,matched_record_id,
        decision_source,reason,created_at,updated_at
      ) VALUES('CASE-TEST-HUMAN','merchant_demo','invoice_to_payment','REVIEW',0.4,?,?,?,?,?,?)
    """, (inv['record_id'],None,'ai','needs review', '2026-09-04T00:00:00+00:00','2026-09-04T00:00:00+00:00'))
    conn.execute("DELETE FROM reconciliation_links WHERE case_id='CASE-TEST-HUMAN'")
    conn.execute("DELETE FROM exceptions WHERE case_id='CASE-TEST-HUMAN'")
    conn.execute("INSERT INTO exceptions(exception_id,case_id,severity,reason,status,created_at) VALUES('EX-TEST-HUMAN','CASE-TEST-HUMAN','medium','test','OPEN','2026-09-04T00:00:00+00:00')")
    conn.commit(); conn.close()

    updated=resolve_case_manually('CASE-TEST-HUMAN','approve_match',pay['source_record_id'],'confirmed by reviewer','tester')
    assert updated['status']=='RECONCILED'
    assert updated['decision_source']=='human'

    conn=get_conn()
    link=conn.execute("SELECT * FROM reconciliation_links WHERE case_id='CASE-TEST-HUMAN'").fetchone()
    exc=conn.execute("SELECT * FROM exceptions WHERE case_id='CASE-TEST-HUMAN'").fetchone()
    audit=conn.execute("SELECT * FROM audit_events WHERE case_id='CASE-TEST-HUMAN' ORDER BY event_id DESC LIMIT 1").fetchone()
    conn.close()
    assert link is not None and link['decision_source']=='human'
    assert exc['status']=='RESOLVED'
    assert audit['event_type']=='human_review_resolution'
