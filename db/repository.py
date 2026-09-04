
from __future__ import annotations
import json, uuid
from .database import get_conn, now

def upsert_financial_record(
    merchant_id, source, source_record_id, record_type, event_date,
    amount, currency, direction, customer_name, reference,
    description, raw
):
    rid = f"{source}:{source_record_id}"
    ts = now()
    conn = get_conn()
    conn.execute("""
    INSERT INTO financial_records(
        record_id, merchant_id, source, source_record_id, record_type,
        event_date, amount, currency, direction, customer_name, reference,
        description, raw_json, created_at, updated_at
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(record_id) DO UPDATE SET
        event_date=excluded.event_date,
        amount=excluded.amount,
        currency=excluded.currency,
        direction=excluded.direction,
        customer_name=excluded.customer_name,
        reference=excluded.reference,
        description=excluded.description,
        raw_json=excluded.raw_json,
        updated_at=excluded.updated_at
    """, (
        rid, merchant_id, source, source_record_id, record_type,
        event_date, amount, currency, direction, customer_name,
        reference, description, json.dumps(raw, separators=(",",":")),
        ts, ts
    ))
    conn.commit()
    conn.close()
    return rid

def create_case(
    merchant_id, case_type, status, confidence,
    primary_record_id, matched_record_id, decision_source, reason
):
    cid = f"CASE-{uuid.uuid4().hex[:10].upper()}"
    conn = get_conn()
    ts = now()
    conn.execute("""
    INSERT INTO reconciliation_cases(
        case_id,merchant_id,case_type,status,confidence,
        primary_record_id,matched_record_id,decision_source,reason,
        created_at,updated_at
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, (
        cid, merchant_id, case_type, status, confidence,
        primary_record_id, matched_record_id, decision_source, reason, ts, ts
    ))
    conn.commit(); conn.close()
    return cid

def create_link(case_id, from_record_id, to_record_id, link_type, confidence, decision_source):
    conn = get_conn()
    conn.execute("""
    INSERT OR IGNORE INTO reconciliation_links(
        case_id,from_record_id,to_record_id,link_type,confidence,decision_source,created_at
    ) VALUES(?,?,?,?,?,?,?)
    """, (case_id,from_record_id,to_record_id,link_type,confidence,decision_source,now()))
    conn.commit(); conn.close()

def create_exception(case_id, severity, reason):
    eid=f"EX-{uuid.uuid4().hex[:10].upper()}"
    conn=get_conn()
    conn.execute("""
    INSERT INTO exceptions(exception_id,case_id,severity,reason,status,created_at)
    VALUES(?,?,?,?,?,?)
    """,(eid,case_id,severity,reason,"OPEN",now()))
    conn.commit(); conn.close()
    return eid

def audit(merchant_id,event_type,actor,payload,case_id=None):
    conn=get_conn()
    conn.execute("""
    INSERT INTO audit_events(merchant_id,case_id,event_type,actor,payload_json,created_at)
    VALUES(?,?,?,?,?,?)
    """,(merchant_id,case_id,event_type,actor,json.dumps(payload,separators=(",",":")),now()))
    conn.commit(); conn.close()

def save_webhook_event(event_id,merchant_id,provider,event_type,signature_valid,payload):
    conn=get_conn()
    cur=conn.execute("""
    INSERT OR IGNORE INTO webhook_events(
        event_id,merchant_id,provider,event_type,signature_valid,payload_json,received_at
    ) VALUES(?,?,?,?,?,?,?)
    """,(event_id,merchant_id,provider,event_type,int(signature_valid),
        json.dumps(payload,separators=(",",":")),now()))
    inserted=cur.rowcount==1
    conn.commit(); conn.close()
    return inserted

def clear_reconciliation_results(merchant_id):
    conn=get_conn()
    conn.execute("""DELETE FROM reconciliation_links
                    WHERE case_id IN (SELECT case_id FROM reconciliation_cases WHERE merchant_id=?)""",(merchant_id,))
    conn.execute("""DELETE FROM exceptions
                    WHERE case_id IN (SELECT case_id FROM reconciliation_cases WHERE merchant_id=?)""",(merchant_id,))
    conn.execute("DELETE FROM reconciliation_cases WHERE merchant_id=?",(merchant_id,))
    conn.commit(); conn.close()

def list_records(merchant_id, source=None, record_type=None):
    conn=get_conn()
    q="SELECT * FROM financial_records WHERE merchant_id=?"
    params=[merchant_id]
    if source: q += " AND source=?"; params.append(source)
    if record_type: q += " AND record_type=?"; params.append(record_type)
    q+=" ORDER BY event_date,record_id"
    rows=conn.execute(q,params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_cases(merchant_id,status=None):
    conn=get_conn()
    q="SELECT * FROM reconciliation_cases WHERE merchant_id=?"
    params=[merchant_id]
    if status: q+=" AND status=?"; params.append(status)
    q+=" ORDER BY updated_at DESC"
    rows=conn.execute(q,params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_case(case_id):
    conn=get_conn()
    r=conn.execute("SELECT * FROM reconciliation_cases WHERE case_id=?",(case_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def list_case_links(case_id):
    conn=get_conn()
    rows=conn.execute("""
    SELECT l.*,
           f1.source AS from_source,f1.source_record_id AS from_source_record_id,
           f2.source AS to_source,f2.source_record_id AS to_source_record_id
    FROM reconciliation_links l
    JOIN financial_records f1 ON f1.record_id=l.from_record_id
    JOIN financial_records f2 ON f2.record_id=l.to_record_id
    WHERE l.case_id=? ORDER BY l.link_id
    """,(case_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_case_exceptions(case_id):
    conn=get_conn()
    rows=conn.execute("SELECT * FROM exceptions WHERE case_id=? ORDER BY created_at DESC",(case_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resolve_case_manually(case_id: str, action: str, payment_id: str | None, note: str, actor: str):
    """Resolve an open review atomically and append an audit trail."""
    conn=get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        case=conn.execute("SELECT * FROM reconciliation_cases WHERE case_id=?",(case_id,)).fetchone()
        if not case:
            raise ValueError("Case not found")
        if case["status"] not in {"REVIEW","UNRESOLVED"}:
            raise ValueError("Case is not open for human review")

        if action == "approve_match":
            if not payment_id:
                raise ValueError("payment_id is required for approve_match")
            pay=conn.execute("""
                SELECT * FROM financial_records
                WHERE record_id=? AND merchant_id=? AND record_type='payment'
            """,(f"payment:{payment_id}",case["merchant_id"])).fetchone()
            if not pay:
                raise ValueError("Payment not found for this merchant")
            conn.execute("""
                INSERT OR IGNORE INTO reconciliation_links(
                    case_id,from_record_id,to_record_id,link_type,confidence,decision_source,created_at
                ) VALUES(?,?,?,?,?,?,?)
            """,(case_id,case["primary_record_id"],pay["record_id"],"invoice_payment",1.0,"human",now()))
            conn.execute("""
                UPDATE reconciliation_cases
                SET status='RECONCILED', confidence=1.0, matched_record_id=?,
                    decision_source='human', reason=?, updated_at=?
                WHERE case_id=?
            """,(pay["record_id"],note or "Human reviewer approved match.",now(),case_id))
        else:
            conn.execute("""
                UPDATE reconciliation_cases
                SET status='REJECTED', matched_record_id=NULL, decision_source='human',
                    reason=?, updated_at=? WHERE case_id=?
            """,(note or "Human reviewer rejected the proposed match.",now(),case_id))

        resolved=now()
        conn.execute("""
            UPDATE exceptions SET status='RESOLVED', resolved_at=?
            WHERE case_id=? AND status='OPEN'
        """,(resolved,case_id))
        conn.execute("""
            INSERT INTO audit_events(merchant_id,case_id,event_type,actor,payload_json,created_at)
            VALUES(?,?,?,?,?,?)
        """,(case["merchant_id"],case_id,"human_review_resolution",actor,
              json.dumps({"action":action,"payment_id":payment_id,"note":note},separators=(",",":")),resolved))
        conn.commit()
        return dict(conn.execute("SELECT * FROM reconciliation_cases WHERE case_id=?",(case_id,)).fetchone())
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
